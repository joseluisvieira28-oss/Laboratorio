#!/usr/bin/env python3
import asyncio, hashlib, json, os, re
from urllib.parse import urlparse
from playwright.async_api import async_playwright

ENTRY_URLS=[
 "https://www.mexc.com/en-GB/futures/event-futures/BTC_USDT",
 "https://www.mexc.com/en-US/futures/prediction-futures/BTC_USDT",
]
KEYWORDS=["payout","prediction","event future","event-futures","prediction-futures","timeunit","btc_usdt","btc usdt","10 minutes","30 minutes","1 hour","1 day","80%"]
MAX_NET=120
MAX_PREVIEWS=80
MAX_JS=60
MAX_JS_BYTES=8*1024*1024

def sha(b): return hashlib.sha256(b).hexdigest()
def allowed_host(url):
    h=(urlparse(url).hostname or "").lower()
    return h=="mexc.com" or h.endswith(".mexc.com") or h.endswith(".mocortech.com")

def text_hits(text, source):
    low=text.lower()
    out=[]
    for kw in KEYWORDS:
        i=low.find(kw.lower())
        if i>=0:
            out.append({"keyword":kw,"source":source,"snippet":text[max(0,i-180):i+len(kw)+260].replace("\n"," ")})
    return out

async def main():
    os.makedirs("artifacts/mexc_event_futures",exist_ok=True)
    evidence={
      "lab":"MEXC_EVENT_FUTURES_BROWSER_SOURCE_V0.11",
      "authenticated_requests":0,"orders":0,"account_mutations":0,
      "pages":[],"network_gets":[],"aborted_non_gets":[],"response_previews":[],
      "js_assets":[],"matches":[],"candidate_routes":[]
    }
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True,args=["--disable-blink-features=AutomationControlled"])
        ctx=await browser.new_context(locale="en-GB",timezone_id="UTC")
        await ctx.clear_cookies()
        page=await ctx.new_page()

        async def route_handler(route):
            req=route.request
            if req.method.upper()!="GET":
                if len(evidence["aborted_non_gets"])<120:
                    evidence["aborted_non_gets"].append({"method":req.method,"url":req.url})
                await route.abort()
            else:
                await route.continue_()
        await page.route("**/*",route_handler)

        async def on_response(resp):
            if len(evidence["network_gets"])<MAX_NET:
                u=resp.url
                if any(k in u.lower() for k in ["event","predict","future","payout","contract","api","market"]):
                    evidence["network_gets"].append({"url":u,"status":resp.status,"content_type":resp.headers.get("content-type")})
            if len(evidence["response_previews"])>=MAX_PREVIEWS:
                return
            ct=(resp.headers.get("content-type") or "").lower()
            if not any(x in ct for x in ["json","javascript","text"]):
                return
            u=resp.url
            if not allowed_host(u):
                return
            try:
                b=await resp.body()
            except Exception:
                return
            if len(b)>MAX_JS_BYTES:
                return
            t=b.decode("utf-8","replace")
            if any(k in t.lower() for k in ["payout","prediction-futures","event-futures","timeunit","btc_usdt"]):
                rec={"url":u,"status":resp.status,"content_type":ct,"bytes":len(b),"sha256":sha(b),"preview":t[:2000]}
                evidence["response_previews"].append(rec)
                evidence["matches"].extend(text_hits(t,u)[:20])
                for m in re.finditer(r'["\']([^"\']{1,260})["\']',t):
                    s=m.group(1)
                    sl=s.lower()
                    if any(k in sl for k in ["event","predict","payout","timeunit"]) and (s.startswith("/") or "api" in sl or "http" in sl):
                        evidence["candidate_routes"].append(s)

        page.on("response",on_response)

        for entry in ENTRY_URLS:
            rec={"entry_url":entry}
            try:
                resp=await page.goto(entry,wait_until="domcontentloaded",timeout=60000)
                await page.wait_for_timeout(20000)
                rec.update({
                    "status":resp.status if resp else None,
                    "final_url":page.url,
                    "title":await page.title(),
                })
                body=await page.locator("body").inner_text(timeout=10000)
                rec["body_chars"]=len(body)
                rec["body_sha256"]=sha(body.encode())
                hits=text_hits(body,page.url)
                rec["visible_matches"]=hits[:40]
                evidence["matches"].extend(hits[:40])

                # Directly loaded JS only.
                scripts=await page.locator("script[src]").evaluate_all("(els)=>els.map(e=>e.src)")
                for u in scripts:
                    if len(evidence["js_assets"])>=MAX_JS: break
                    if not allowed_host(u): continue
                    try:
                        r=await ctx.request.get(u,timeout=25000)
                        if not r.ok: 
                            evidence["js_assets"].append({"url":u,"status":r.status})
                            continue
                        b=await r.body()
                        if len(b)>MAX_JS_BYTES:
                            evidence["js_assets"].append({"url":u,"status":r.status,"too_large":True,"bytes":len(b)})
                            continue
                        t=b.decode("utf-8","replace")
                        evidence["js_assets"].append({"url":u,"status":r.status,"bytes":len(b),"sha256":sha(b)})
                        hits=text_hits(t,u)
                        if hits:
                            evidence["matches"].extend(hits[:20])
                        for m in re.finditer(r'["\']([^"\']{1,260})["\']',t):
                            s=m.group(1); sl=s.lower()
                            if any(k in sl for k in ["event","predict","payout","timeunit"]) and (s.startswith("/") or "api" in sl or "http" in sl):
                                evidence["candidate_routes"].append(s)
                    except Exception as e:
                        evidence["js_assets"].append({"url":u,"error":repr(e)})
                evidence["pages"].append(rec)
                if rec["visible_matches"]:
                    break
            except Exception as e:
                rec["error"]=repr(e)
                evidence["pages"].append(rec)

        await browser.close()

    evidence["candidate_routes"]=sorted(set(evidence["candidate_routes"]))[:300]
    exact_get=False
    visible=False
    candidate=False
    for p in evidence["response_previews"]:
        low=(p.get("preview") or "").lower()
        if "payout" in low and any(k in low for k in ["event","prediction","timeunit","btc_usdt"]):
            exact_get=True
    for p in evidence["pages"]:
        if p.get("visible_matches"):
            kws={x["keyword"].lower() for x in p["visible_matches"]}
            if "payout" in kws or "80%" in kws:
                visible=True
    if evidence["candidate_routes"] or evidence["aborted_non_gets"]:
        candidate=True

    if exact_get:
        verdict="EXACT_PUBLIC_GET_ROUTE_FOUND"
    elif visible:
        verdict="VISIBLE_EXACT_PRODUCT_DATA_FOUND_NO_ROUTE"
    elif candidate:
        verdict="CANDIDATE_ROUTE_IDENTIFIED_BUT_BLOCKED"
    elif any(p.get("status") in (403,429) or "challenge" in (p.get("title") or "").lower() for p in evidence["pages"]):
        verdict="BROWSER_SOURCE_BLOCKED"
    else:
        verdict="NO_EXACT_PRODUCT_SOURCE_FOUND"

    evidence["verdict"]=verdict
    evidence["counters"]={
      "pages":len(evidence["pages"]),"network_gets":len(evidence["network_gets"]),
      "aborted_non_gets":len(evidence["aborted_non_gets"]),
      "response_previews":len(evidence["response_previews"]),
      "js_assets":len(evidence["js_assets"]),"matches":len(evidence["matches"]),
      "candidate_routes":len(evidence["candidate_routes"])
    }
    path="artifacts/mexc_event_futures/browser_source_v011.json"
    with open(path,"w",encoding="utf-8") as f: json.dump(evidence,f,indent=2,sort_keys=True)
    summary={"verdict":verdict,**evidence["counters"],
      "authenticated_requests":0,"orders":0,"account_mutations":0}
    print(json.dumps(summary,indent=2,sort_keys=True))
    print("VISIBLE_MATCHES_SAMPLE=")
    print(json.dumps(evidence["matches"][:25],indent=2,sort_keys=True))
    print("CANDIDATE_ROUTES_SAMPLE=")
    print(json.dumps(evidence["candidate_routes"][:40],indent=2,sort_keys=True))
    print("ABORTED_NON_GETS_SAMPLE=")
    unique=[]
    seen=set()
    for x in evidence["aborted_non_gets"]:
        key=(x.get("method"),x.get("url"))
        if key in seen: continue
        seen.add(key); unique.append(x)
        if len(unique)>=40: break
    print(json.dumps(unique,indent=2,sort_keys=True))
    print("NETWORK_GETS_SAMPLE=")
    print(json.dumps(evidence["network_gets"][:40],indent=2,sort_keys=True))
    print("WROTE",path)

if __name__=="__main__":
    asyncio.run(main())
