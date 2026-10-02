#!/usr/bin/env python3
import asyncio, json, os, re
from playwright.async_api import async_playwright

URL="https://www.mexc.com/futures/event-futures/BTC_USDT"

async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(headless=True)
        ctx=await b.new_context()
        page=await ctx.new_page()
        async def route_handler(route,request):
            if request.method.upper()!="GET":
                await route.abort()
            else:
                await route.continue_()
        await page.route("**/*",route_handler)
        await page.goto(URL,wait_until="domcontentloaded",timeout=90000)
        await page.wait_for_timeout(9000)

        rows=await page.evaluate("""
        () => {
          const out=[];
          const all=[...document.querySelectorAll('button,[role="button"],div,span')];
          for(const el of all){
            const t=(el.innerText||'').trim();
            if(!/^\d+\s*[mMhHdD]$/.test(t)) continue;
            const s=getComputedStyle(el),r=el.getBoundingClientRect();
            if(s.display==='none'||s.visibility==='hidden'||r.width<=0||r.height<=0) continue;
            const child=[...el.children].some(c=>(c.innerText||'').trim()===t);
            if(child) continue;
            out.push({
              text:t,
              tag:el.tagName,
              class:String(el.className||''),
              role:el.getAttribute('role'),
              parent_text:((el.parentElement&&el.parentElement.innerText)||'').trim().slice(0,500),
              grandparent_text:((el.parentElement&&el.parentElement.parentElement&&el.parentElement.parentElement.innerText)||'').trim().slice(0,900),
              x:r.x,y:r.y,w:r.width,h:r.height
            });
          }
          return out;
        }
        """)
        body=await page.locator("body").inner_text()
        out={"url":page.url,"labels":rows,"body_excerpt":body[:25000]}
        os.makedirs("artifacts/mexc_event_futures",exist_ok=True)
        path="artifacts/mexc_event_futures/horizon_selector_census_v0621.json"
        with open(path,"w",encoding="utf-8") as f: json.dump(out,f,indent=2,sort_keys=True)
        print(json.dumps({"labels":rows},indent=2))
        print("WROTE",path)
        await ctx.close(); await b.close()

if __name__=="__main__":
    asyncio.run(main())
