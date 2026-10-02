#!/usr/bin/env python3
import asyncio, json, os, re
from urllib.parse import urlparse
from playwright.async_api import async_playwright

ENTRY="https://www.mexc.com/en-GB/futures/event-futures/BTC_USDT"
MAX_JS=100
MAX_BYTES=10*1024*1024

def allowed(url):
    h=(urlparse(url).hostname or "").lower()
    return h=="mexc.com" or h.endswith(".mexc.com") or h.endswith(".mocortech.com")

async def main():
    os.makedirs("artifacts/mexc_event_futures",exist_ok=True)
    out={"lab":"MEXC_EVENT_FUTURES_CONFIG_RESOLUTION_V0.11.4",
         "authenticated_requests":0,"orders":0,"account_mutations":0,
         "module_853411_snippets":[],"new_swap_api_occurrences":[],"url_literals":[],"js_assets":[]}

    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True,args=["--disable-blink-features=AutomationControlled"])
        ctx=await browser.new_context(locale="en-GB",timezone_id="UTC")
        await ctx.clear_cookies()
        page=await ctx.new_page()

        async def handler(route):
            if route.request.method.upper()!="GET":
                await route.abort()
            else:
                await route.continue_()
        await page.route("**/*",handler)

        await page.goto(ENTRY,wait_until="domcontentloaded",timeout=60000)
        await page.wait_for_timeout(15000)

        scripts=await page.locator("script[src]").evaluate_all("(els)=>Array.from(new Set(els.map(e=>e.src)))")
        for u in scripts[:MAX_JS]:
            if not allowed(u): continue
            try:
                r=await ctx.request.get(u,timeout=25000)
                if not r.ok:
                    out["js_assets"].append({"url":u,"status":r.status}); continue
                b=await r.body()
                if len(b)>MAX_BYTES:
                    out["js_assets"].append({"url":u,"status":r.status,"too_large":True,"bytes":len(b)}); continue
                t=b.decode("utf-8","replace")
                out["js_assets"].append({"url":u,"status":r.status,"bytes":len(b)})

                # Search module definition and every NEW_SWAP_API occurrence.
                for needle,store,span in [
                    ("853411,e=>","module_853411_snippets",5000),
                    ("NEW_SWAP_API","new_swap_api_occurrences",2500),
                ]:
                    pos=0; count=0
                    while count<25:
                        i=t.find(needle,pos)
                        if i<0: break
                        out[store].append({"url":u,"offset":i,"snippet":t[max(0,i-span):min(len(t),i+span)]})
                        pos=i+len(needle); count+=1

                # Absolute URL literals around likely futures/swap hosts.
                for m in re.finditer(r'https://[^"\']{5,240}',t):
                    s=m.group(0)
                    if any(k in s.lower() for k in ["mexc","swap","contract","future"]):
                        out["url_literals"].append(s.rstrip(');,}]'))
            except Exception as e:
                out["js_assets"].append({"url":u,"error":repr(e)})

        await browser.close()

    out["url_literals"]=sorted(set(out["url_literals"]))[:500]
    path="artifacts/mexc_event_futures/config_resolution_v0114.json"
    with open(path,"w",encoding="utf-8") as f: json.dump(out,f,indent=2,sort_keys=True)

    print("COUNTS="+json.dumps({
      "modules":len(out["module_853411_snippets"]),
      "new_swap_occurrences":len(out["new_swap_api_occurrences"]),
      "url_literals":len(out["url_literals"]),
      "authenticated_requests":0,"orders":0,"account_mutations":0
    },sort_keys=True))
    print("MODULE_853411=")
    print(json.dumps(out["module_853411_snippets"][:20],indent=2))
    print("NEW_SWAP_API_OCCURRENCES=")
    print(json.dumps(out["new_swap_api_occurrences"][:30],indent=2))
    print("URL_LITERALS=")
    print(json.dumps(out["url_literals"][:120],indent=2))
    print("WROTE",path)

if __name__=="__main__":
    asyncio.run(main())
