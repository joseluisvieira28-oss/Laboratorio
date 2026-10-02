#!/usr/bin/env python3
import asyncio, hashlib, json, os, re
from datetime import datetime, timezone
from playwright.async_api import async_playwright

ASSETS={
 "BTCUSDT":"BTC_USDT",
 "ETHUSDT":"ETH_USDT",
 "NVDAUSDT":"NVIDIA_USDT",
 "MUUSDT":"MUSTOCK_USDT",
 "SPCXUSDT":"SPCXSTOCK_USDT",
}
HORIZONS=["10m","30m","1h","1d"]
BASE="https://www.mexc.com/futures/event-futures/"

def sha(s):
    return hashlib.sha256(s.encode("utf-8","ignore")).hexdigest()

def payouts(body):
    up=re.findall(r'(?i)(?:Up\s*Payout|Payout\s*Up)\s*[:\-]?\s*(\d{1,3}(?:\.\d+)?)\s*%',body)
    dn=re.findall(r'(?i)(?:Down\s*Payout|Payout\s*Down)\s*[:\-]?\s*(\d{1,3}(?:\.\d+)?)\s*%',body)
    return (up[0] if up else None, dn[0] if dn else None)

async def visible_exact_count(page,label):
    return await page.evaluate("""
      (label) => {
        const els=[...document.querySelectorAll('button,[role="button"],div,span')];
        const vis=els.filter(el=>{
          const t=(el.innerText||'').trim();
          if(t!==label) return false;
          const s=getComputedStyle(el), r=el.getBoundingClientRect();
          if(s.display==='none'||s.visibility==='hidden'||r.width<=0||r.height<=0) return false;
          // avoid counting wrapper duplicates that contain a child with same exact text
          const child=[...el.children].some(c=>(c.innerText||'').trim()===label);
          return !child;
        });
        return vis.length;
      }
    """,label)

async def click_unique_exact(page,label):
    return await page.evaluate("""
      (label) => {
        const els=[...document.querySelectorAll('button,[role="button"],div,span')];
        const vis=els.filter(el=>{
          const t=(el.innerText||'').trim();
          if(t!==label) return false;
          const s=getComputedStyle(el), r=el.getBoundingClientRect();
          if(s.display==='none'||s.visibility==='hidden'||r.width<=0||r.height<=0) return false;
          const child=[...el.children].some(c=>(c.innerText||'').trim()===label);
          return !child;
        });
        if(vis.length!==1) return {clicked:false,count:vis.length};
        vis[0].click();
        return {clicked:true,count:1,tag:vis[0].tagName,cls:vis[0].className};
      }
    """,label)

async def inspect(browser,display,symbol):
    ctx=await browser.new_context()
    page=await ctx.new_page()
    async def route_handler(route,request):
        if request.method.upper()!="GET":
            await route.abort()
        else:
            await route.continue_()
    await page.route("**/*",route_handler)

    rec={"asset":display,"symbol":symbol,"page":BASE+symbol,"horizons":{}}
    try:
        await page.goto(BASE+symbol,wait_until="domcontentloaded",timeout=90000)
        await page.wait_for_timeout(9000)
        rec["initial_url"]=page.url
        rec["visible_exact_counts"]={}
        for h in HORIZONS:
            rec["visible_exact_counts"][h]=await visible_exact_count(page,h)

        for h in HORIZONS:
            c=rec["visible_exact_counts"][h]
            if c!=1:
                rec["horizons"][h]={"status":"SELECTOR_AMBIGUOUS" if c>1 else "SELECTOR_NOT_FOUND","count":c}
                continue
            click=await click_unique_exact(page,h)
            await page.wait_for_timeout(1800)
            body=await page.locator("body").inner_text()
            up,dn=payouts(body)
            rec["horizons"][h]={
              "status":"PASS" if up is not None and dn is not None else "PAYOUT_NOT_FOUND",
              "selector":click,
              "observed_at_utc":datetime.now(timezone.utc).isoformat(),
              "up_payout_pct":float(up) if up is not None else None,
              "down_payout_pct":float(dn) if dn is not None else None,
              "dom_sha256":sha(body)
            }
    except Exception as e:
        rec["error"]=repr(e)
    await ctx.close()
    return rec

async def main():
    out={"lab":"MEXC_EVENT_FUTURES_MULTI_HORIZON_DOM_SOURCE_V0.6.2","assets":[]}
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        for display,symbol in ASSETS.items():
            out["assets"].append(await inspect(browser,display,symbol))
        await browser.close()

    rows=[]
    for a in out["assets"]:
        for h,r in a.get("horizons",{}).items():
            if r.get("status")=="PASS":
                rows.append({
                  "asset":a["asset"],"symbol":a["symbol"],"horizon":h,
                  "observed_at_utc":r["observed_at_utc"],
                  "up_payout_pct":r["up_payout_pct"],"down_payout_pct":r["down_payout_pct"],
                  "source_kind":"PUBLIC_DOM","source_url":a["page"],"dom_sha256":r["dom_sha256"]
                })
    out["records"]=rows
    out["pass_count"]=len(rows)
    out["source_gate"]="PASS_MULTI_HORIZON_DOM_SOURCE" if len(rows)==20 else ("PARTIAL" if rows else "BLOCKED")

    os.makedirs("artifacts/mexc_event_futures",exist_ok=True)
    pth="artifacts/mexc_event_futures/multihorizon_dom_probe_v062.json"
    with open(pth,"w",encoding="utf-8") as f: json.dump(out,f,indent=2,sort_keys=True)
    print(json.dumps({
      "source_gate":out["source_gate"],"pass_count":out["pass_count"],
      "records":rows,
      "selector_counts":{a["asset"]:a.get("visible_exact_counts",{}) for a in out["assets"]}
    },indent=2))
    print("WROTE",pth)

if __name__=="__main__":
    asyncio.run(main())
