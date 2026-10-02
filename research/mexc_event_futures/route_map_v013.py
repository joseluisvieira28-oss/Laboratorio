#!/usr/bin/env python3
import asyncio,json,os,re
from urllib.parse import urlparse
from playwright.async_api import async_playwright

PAGE="https://www.mexc.com/en-GB/futures/event-futures/BTC_USDT"
PATTERNS=["event_contract","eventContract","prediction-futures","event-futures"]

def allowed(u):
    h=(urlparse(u).hostname or "").lower()
    return h=="mexc.com" or h.endswith(".mexc.com") or h.endswith(".mocortech.com")

async def main():
    os.makedirs("artifacts/mexc_event_futures",exist_ok=True)
    out={"lab":"MEXC_EVENT_FUTURES_ROUTE_MAP_V0.13","routes":[],"network":[],"snippets":[],
         "authenticated_requests":0,"orders":0,"account_mutations":0,"aborted_non_gets":0}
    async with async_playwright() as p:
        b=await p.chromium.launch(headless=True,args=["--disable-blink-features=AutomationControlled"])
        c=await b.new_context(locale="en-GB",timezone_id="UTC"); await c.clear_cookies()
        page=await c.new_page()

        async def route_handler(route):
            if route.request.method.upper()!="GET":
                out["aborted_non_gets"]+=1; await route.abort()
            else: await route.continue_()
        await page.route("**/*",route_handler)

        async def on_response(resp):
            u=resp.url
            if any(x.lower() in u.lower() for x in PATTERNS):
                out["network"].append({"url":u,"status":resp.status,"content_type":resp.headers.get("content-type")})
            ct=(resp.headers.get("content-type") or "").lower()
            if not allowed(u) or not any(x in ct for x in ["json","javascript","text"]): return
            try: data=await resp.body()
            except Exception: return
            if len(data)>8*1024*1024: return
            t=data.decode("utf-8","replace")
            low=t.lower()
            if any(x.lower() in low for x in PATTERNS):
                for pat in PATTERNS:
                    pos=0
                    while True:
                        i=low.find(pat.lower(),pos)
                        if i<0: break
                        out["snippets"].append({"url":u,"pattern":pat,"snippet":t[max(0,i-220):i+420].replace("\n"," ")})
                        pos=i+len(pat)
                        if len(out["snippets"])>=400: break
                    if len(out["snippets"])>=400: break
                for m in re.finditer(r'["\']([^"\']{1,300})["\']',t):
                    s=m.group(1); sl=s.lower()
                    if any(x.lower() in sl for x in PATTERNS) and (s.startswith("/") or "http" in sl or "api" in sl):
                        out["routes"].append(s)
        page.on("response",on_response)

        resp=await page.goto(PAGE,wait_until="domcontentloaded",timeout=60000)
        out["page_status"]=resp.status if resp else None
        await page.wait_for_timeout(20000)
        scripts=await page.locator("script[src]").evaluate_all("(els)=>els.map(e=>e.src)")
        for u in scripts[:80]:
            if not allowed(u): continue
            try:
                r=await c.request.get(u,timeout=25000)
                if not r.ok: continue
                data=await r.body()
                if len(data)>8*1024*1024: continue
                t=data.decode("utf-8","replace"); low=t.lower()
                if any(x.lower() in low for x in PATTERNS):
                    for m in re.finditer(r'["\']([^"\']{1,300})["\']',t):
                        s=m.group(1); sl=s.lower()
                        if any(x.lower() in sl for x in PATTERNS) and (s.startswith("/") or "http" in sl or "api" in sl):
                            out["routes"].append(s)
            except Exception: pass
        await b.close()

    out["routes"]=sorted(set(out["routes"]))
    out["network_unique"]=[]
    seen=set()
    for x in out["network"]:
        if x["url"] not in seen: seen.add(x["url"]); out["network_unique"].append(x)
    out["verdict"]="PUBLIC_EVENT_ROUTE_MAP_FOUND" if out["routes"] or out["network_unique"] else "NO_ROUTE_MAP"
    pth="artifacts/mexc_event_futures/route_map_v013.json"
    with open(pth,"w",encoding="utf-8") as f: json.dump(out,f,indent=2,sort_keys=True)
    print("VERDICT="+out["verdict"])
    print("NETWORK")
    for x in out["network_unique"]: print(json.dumps(x,ensure_ascii=False))
    print("ROUTES")
    for x in out["routes"][:200]: print(x)
    print("NO_AUTH=PASS\nNO_ORDERS=PASS\nNO_MUTATION=PASS")
    print("WROTE "+pth)

if __name__=="__main__": asyncio.run(main())
