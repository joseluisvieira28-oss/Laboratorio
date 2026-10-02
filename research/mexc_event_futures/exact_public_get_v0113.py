#!/usr/bin/env python3
import asyncio, hashlib, json, os, re
from urllib.parse import urlparse
from playwright.async_api import async_playwright

ENTRY="https://www.mexc.com/en-GB/futures/event-futures/BTC_USDT"
MAX_JS=90
MAX_BYTES=8*1024*1024
PUBLIC_PATHS=[
  "/event_contract/detail",
  "/event_contract/trade_date_time?symbol=BTC_USDT",
  "/event_contract/last_trade_date_time?symbol=BTC_USDT",
  "/event_contract/listPlaceCarouse",
  "/event_contract/listWinCarouse",
]

def sha(b): return hashlib.sha256(b).hexdigest()
def allowed(url):
    h=(urlparse(url).hostname or "").lower()
    return h=="mexc.com" or h.endswith(".mexc.com") or h.endswith(".mocortech.com")

def host_candidates(text):
    out=set()
    # Absolute HTTPS bases and URLs near known API config terms.
    for m in re.finditer(r'https://[A-Za-z0-9._:-]+(?:/[A-Za-z0-9._~:/?#\[\]@!$&()*+,;=%-]*)?', text):
        u=m.group(0).rstrip('"\')]}>,;')
        if any(k in u.lower() for k in ["mexc","mocortech"]):
            out.add(u)
    # Collect compact source snippets around NEW_SWAP_API.
    snippets=[]
    low=text.lower()
    pos=0
    while True:
        i=low.find("new_swap_api",pos)
        if i<0: break
        snippets.append(text[max(0,i-700):min(len(text),i+1400)])
        pos=i+12
    return sorted(out), snippets

def infer_bases(urls,snippets):
    cands=set()
    for u in urls:
        try:
            p=urlparse(u)
            base=f"{p.scheme}://{p.netloc}"
            if p.netloc:
                cands.add(base)
        except Exception:
            pass
    # Explicit quoted strings in snippets that look like swap/contract API bases.
    for s in snippets:
        for m in re.finditer(r'["\'](https://[^"\']{5,220})["\']',s):
            u=m.group(1)
            if any(k in u.lower() for k in ["mexc","contract","futures","swap"]):
                cands.add(u.rstrip("/"))
    return sorted(cands)

async def main():
    os.makedirs("artifacts/mexc_event_futures",exist_ok=True)
    ev={
      "lab":"MEXC_EVENT_FUTURES_EXACT_PUBLIC_GET_V0.11.3",
      "authenticated_requests":0,"orders":0,"account_mutations":0,
      "page":{},"js_assets":[],"new_swap_api_snippets":[],"absolute_urls":[],
      "base_candidates":[],"probes":[]
    }
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True,args=["--disable-blink-features=AutomationControlled"])
        ctx=await browser.new_context(locale="en-GB",timezone_id="UTC")
        await ctx.clear_cookies()
        page=await ctx.new_page()

        async def handler(route):
            req=route.request
            if req.method.upper()!="GET":
                await route.abort()
            else:
                await route.continue_()
        await page.route("**/*",handler)

        resp=await page.goto(ENTRY,wait_until="domcontentloaded",timeout=60000)
        await page.wait_for_timeout(18000)
        ev["page"]={"status":resp.status if resp else None,"final_url":page.url,"title":await page.title()}

        scripts=await page.locator("script[src]").evaluate_all("(els)=>Array.from(new Set(els.map(e=>e.src)))")
        urls=set(); snips=[]
        for u in scripts[:MAX_JS]:
            if not allowed(u): continue
            try:
                r=await ctx.request.get(u,timeout=25000)
                if not r.ok:
                    ev["js_assets"].append({"url":u,"status":r.status}); continue
                b=await r.body()
                if len(b)>MAX_BYTES:
                    ev["js_assets"].append({"url":u,"status":r.status,"too_large":True,"bytes":len(b)}); continue
                t=b.decode("utf-8","replace")
                ev["js_assets"].append({"url":u,"status":r.status,"bytes":len(b),"sha256":sha(b)})
                us,ss=host_candidates(t)
                urls.update(us); snips.extend(ss)
            except Exception as e:
                ev["js_assets"].append({"url":u,"error":repr(e)})

        ev["absolute_urls"]=sorted(urls)
        ev["new_swap_api_snippets"]=snips[:80]
        bases=infer_bases(ev["absolute_urls"],ev["new_swap_api_snippets"])

        # Also include origins of observed GET requests whose path contains event_contract.
        observed=[]
        def obs(resp):
            try:
                if "event_contract" in resp.url.lower():
                    observed.append(resp.url)
            except Exception:
                pass
        page.on("response",obs)
        await page.reload(wait_until="domcontentloaded",timeout=60000)
        await page.wait_for_timeout(12000)
        for u in observed:
            p=urlparse(u)
            if p.scheme=="https" and p.netloc:
                bases.append(f"{p.scheme}://{p.netloc}")

        # Keep only MEXC-like public hosts; probe GET only.
        safe=[]
        for b in sorted(set(bases)):
            try:
                h=(urlparse(b).hostname or "").lower()
                if h=="mexc.com" or h.endswith(".mexc.com"):
                    safe.append(b.rstrip("/"))
            except Exception:
                pass
        ev["base_candidates"]=safe[:30]

        for base in ev["base_candidates"]:
            for path in PUBLIC_PATHS:
                url=base+path
                try:
                    r=await ctx.request.get(url,timeout=20000,headers={"Accept":"application/json,text/plain,*/*"})
                    body=await r.body()
                    text=body[:8000].decode("utf-8","replace")
                    ev["probes"].append({
                      "url":url,"status":r.status,"content_type":r.headers.get("content-type"),
                      "bytes":len(body),"sha256":sha(body),
                      "mentions_payout":"payout" in text.lower(),
                      "mentions_symbol":"btc_usdt" in text.lower(),
                      "mentions_time":"time" in text.lower(),
                      "preview":text[:3000],
                    })
                except Exception as e:
                    ev["probes"].append({"url":url,"error":repr(e)})
        await browser.close()

    exact=[]
    for x in ev["probes"]:
        if x.get("status")==200 and (x.get("mentions_payout") or x.get("mentions_symbol")):
            exact.append(x["url"])
    ev["exact_hits"]=exact
    ev["verdict"]="EXACT_PUBLIC_GET_ROUTE_FOUND" if exact else ("PUBLIC_GET_BASE_FOUND_BUT_PRODUCT_DATA_UNPROVEN" if ev["base_candidates"] else "NEW_SWAP_API_BASE_NOT_RESOLVED")

    path="artifacts/mexc_event_futures/exact_public_get_v0113.json"
    with open(path,"w",encoding="utf-8") as f: json.dump(ev,f,indent=2,sort_keys=True)
    print(json.dumps({
      "verdict":ev["verdict"],
      "base_candidates":ev["base_candidates"],
      "exact_hits":ev["exact_hits"],
      "probe_count":len(ev["probes"]),
      "authenticated_requests":0,"orders":0,"account_mutations":0
    },indent=2,sort_keys=True))
    print("PROBES=")
    print(json.dumps(ev["probes"][:80],indent=2,sort_keys=True))
    print("NEW_SWAP_API_SNIPPETS=")
    print(json.dumps(ev["new_swap_api_snippets"][:20],indent=2))
    print("WROTE",path)

if __name__=="__main__":
    asyncio.run(main())
