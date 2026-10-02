#!/usr/bin/env python3
import asyncio, hashlib, json, os, re
from urllib.parse import urlparse
from playwright.async_api import async_playwright

ENTRY="https://www.mexc.com/en-GB/futures/event-futures/BTC_USDT"
MAX_JS=80
MAX_BYTES=8*1024*1024
TERMS=[
  "event_contract","getEventContract","event-futures","prediction-futures",
  "payout","payoutRate","upPayout","downPayout","timeUnit","cycleAmount",
  "tradDateTime","shieldTag","shieldCountry","event_contract/auth"
]

def sha(b): return hashlib.sha256(b).hexdigest()
def allowed(url):
    h=(urlparse(url).hostname or "").lower()
    return h=="mexc.com" or h.endswith(".mexc.com") or h.endswith(".mocortech.com")

def snippets(text,url):
    low=text.lower()
    out=[]
    for term in TERMS:
        pos=0; count=0
        while count<20:
            i=low.find(term.lower(),pos)
            if i<0: break
            a=max(0,i-500); b=min(len(text),i+len(term)+900)
            out.append({"term":term,"url":url,"offset":i,"snippet":text[a:b]})
            pos=i+len(term); count+=1
    return out

def routes_from(text):
    out=set()
    for m in re.finditer(r'["\']([^"\']{1,320})["\']',text):
        s=m.group(1); sl=s.lower()
        if any(k in sl for k in ["event_contract","event-futures","prediction-futures"]):
            if s.startswith("/") or "api" in sl or "http" in sl:
                out.add(s)
    for m in re.finditer(r'event_contract/[A-Za-z0-9_/?=&$\{\}.-]{1,180}',text,re.I):
        out.add(m.group(0))
    return sorted(out)

async def main():
    os.makedirs("artifacts/mexc_event_futures",exist_ok=True)
    ev={"lab":"MEXC_EVENT_FUTURES_BROWSER_API_MAP_V0.11.2","authenticated_requests":0,"orders":0,"account_mutations":0,
        "page":{},"js_assets":[],"snippets":[],"routes":[],"aborted_non_gets":[]}
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True,args=["--disable-blink-features=AutomationControlled"])
        ctx=await browser.new_context(locale="en-GB",timezone_id="UTC")
        await ctx.clear_cookies()
        page=await ctx.new_page()

        async def handler(route):
            req=route.request
            if req.method.upper()!="GET":
                if len(ev["aborted_non_gets"])<200:
                    ev["aborted_non_gets"].append({"method":req.method,"url":req.url})
                await route.abort()
            else:
                await route.continue_()
        await page.route("**/*",handler)

        resp=await page.goto(ENTRY,wait_until="domcontentloaded",timeout=60000)
        await page.wait_for_timeout(20000)
        ev["page"]={"status":resp.status if resp else None,"final_url":page.url,"title":await page.title()}

        scripts=await page.locator("script[src]").evaluate_all("(els)=>Array.from(new Set(els.map(e=>e.src)))")
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
                ss=snippets(t,u)
                if ss: ev["snippets"].extend(ss)
                ev["routes"].extend(routes_from(t))
            except Exception as e:
                ev["js_assets"].append({"url":u,"error":repr(e)})
        await browser.close()

    ev["routes"]=sorted(set(ev["routes"]))
    seen=set(); uniq=[]
    for x in ev["aborted_non_gets"]:
        k=(x["method"],x["url"])
        if k in seen: continue
        seen.add(k); uniq.append(x)
    ev["aborted_non_gets"]=uniq

    path="artifacts/mexc_event_futures/browser_api_map_v0112.json"
    with open(path,"w",encoding="utf-8") as f: json.dump(ev,f,indent=2,sort_keys=True)

    print("COUNTS="+json.dumps({
      "js_assets":len(ev["js_assets"]),"snippets":len(ev["snippets"]),
      "routes":len(ev["routes"]),"aborted_non_gets":len(ev["aborted_non_gets"]),
      "authenticated_requests":0,"orders":0,"account_mutations":0
    },sort_keys=True))
    print("ROUTES=")
    print(json.dumps(ev["routes"][:120],indent=2))
    print("EVENT_CONTRACT_SNIPPETS=")
    important=[x for x in ev["snippets"] if any(k in x["term"].lower() for k in ["event_contract","geteventcontract","payout","timeunit","tradatetime"])]
    print(json.dumps(important[:80],indent=2))
    print("ABORTED_NON_GETS=")
    print(json.dumps(ev["aborted_non_gets"][:80],indent=2))
    print("WROTE",path)

if __name__=="__main__":
    asyncio.run(main())
