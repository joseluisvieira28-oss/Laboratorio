#!/usr/bin/env python3
import asyncio, json, math, os, re, statistics
from datetime import datetime, timezone
import requests
from playwright.async_api import async_playwright

ASSETS={
 "BTCUSDT":"BTC_USDT",
 "ETHUSDT":"ETH_USDT",
 "NVDAUSDT":"NVIDIA_USDT",
 "MUUSDT":"MUSTOCK_USDT",
 "SPCXUSDT":"SPCXSTOCK_USDT",
}
PAGE="https://www.mexc.com/futures/event-futures/"
INDEX="https://contract.mexc.com/api/v1/contract/index_price/"
SAMPLES=12
SLEEP_MS=2000

def public_index(symbol):
    try:
        t0=datetime.now(timezone.utc).isoformat()
        r=requests.get(INDEX+symbol,timeout=15,headers={"User-Agent":"Mozilla/5.0"})
        j=r.json()
        d=(j or {}).get("data") or {}
        price=d.get("indexPrice") if "indexPrice" in d else d.get("price")
        return {
          "ok":bool((j or {}).get("success") is True and price is not None),
          "price":float(price) if price is not None else None,
          "exchange_timestamp":d.get("timestamp"),
          "requested_at_utc":t0,
          "received_at_utc":datetime.now(timezone.utc).isoformat(),
          "status_code":r.status_code,
          "url":r.url
        }
    except Exception as e:
        return {"ok":False,"error":repr(e)}

async def dom_index_close(page):
    ctx=await page.evaluate("""
    () => {
      const out=[];
      for(const el of [...document.querySelectorAll('div,span')]){
        const t=(el.innerText||'').trim();
        if(t!=='Index' && t!=='Index Price') continue;
        const s=getComputedStyle(el),r=el.getBoundingClientRect();
        if(s.display==='none'||s.visibility==='hidden'||r.width<=0||r.height<=0) continue;
        out.push({
          label:t,
          parent_text:((el.parentElement&&el.parentElement.innerText)||'').trim().slice(0,700),
          grandparent_text:((el.parentElement&&el.parentElement.parentElement&&el.parentElement.parentElement.innerText)||'').trim().slice(0,1600)
        });
      }
      return out;
    }
    """)
    for x in ctx:
        text=x.get("grandparent_text","")
        # strip directional/invisible marks; parse the current candle Close field
        clean=text.replace("\u200e","").replace("\u200f","")
        m=re.search(r'Close:\s*([^\n]+)',clean,re.I)
        if not m: continue
        raw=m.group(1).strip()
        raw=re.sub(r'[^0-9.,\-]','',raw).replace(',','')
        try:
            val=float(raw)
        except Exception:
            continue
        return {"ok":True,"price":val,"context":text[:1000],"observed_at_utc":datetime.now(timezone.utc).isoformat()}
    return {"ok":False,"contexts":ctx[:10],"observed_at_utc":datetime.now(timezone.utc).isoformat()}

async def inspect(browser,display,symbol):
    ctx=await browser.new_context()
    page=await ctx.new_page()
    async def guard(route,request):
        if request.method.upper()!="GET":
            await route.abort()
        else:
            await route.continue_()
    await page.route("**/*",guard)
    out={"asset":display,"symbol":symbol,"samples":[]}
    try:
        await page.goto(PAGE+symbol,wait_until="domcontentloaded",timeout=90000)
        await page.wait_for_timeout(9000)
        for i in range(SAMPLES):
            d=await dom_index_close(page)
            p=public_index(symbol)
            row={"sample":i+1,"dom":d,"public":p}
            if d.get("ok") and p.get("ok") and p.get("price") not in (None,0):
                diff=abs(d["price"]-p["price"])
                row["abs_difference"]=diff
                row["difference_bps"]=diff/p["price"]*10000.0
                row["valid_pair"]=True
            else:
                row["valid_pair"]=False
            out["samples"].append(row)
            if i<SAMPLES-1:
                await page.wait_for_timeout(SLEEP_MS)
    except Exception as e:
        out["error"]=repr(e)
    await ctx.close()
    return out

async def main():
    report={
      "lab":"MEXC_EVENT_FUTURES_INDEX_EQUIVALENCE_V0.6.4",
      "started_at_utc":datetime.now(timezone.utc).isoformat(),
      "assets":[]
    }
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        # sequential by asset keeps endpoint/browser load conservative
        for display,symbol in ASSETS.items():
            report["assets"].append(await inspect(browser,display,symbol))
        await browser.close()

    valid=[s for a in report["assets"] for s in a.get("samples",[]) if s.get("valid_pair")]
    bps=[s["difference_bps"] for s in valid]
    within=sum(x<=1.0 for x in bps)
    report["target_pairs"]=len(ASSETS)*SAMPLES
    report["valid_pairs"]=len(valid)
    report["within_1bp_count"]=within
    report["within_1bp_fraction"]=(within/len(valid)) if valid else None
    report["median_difference_bps"]=statistics.median(bps) if bps else None
    report["max_difference_bps"]=max(bps) if bps else None
    report["mean_difference_bps"]=statistics.fmean(bps) if bps else None

    passed=(
      len(valid)>=55
      and report["within_1bp_fraction"] is not None
      and report["within_1bp_fraction"]>=0.95
      and report["median_difference_bps"] is not None
      and report["median_difference_bps"]<=0.25
    )
    report["source_gate"]="PASS_CURRENT_DISPLAY_EQUIVALENCE_CANDIDATE" if passed else "FAIL_CURRENT_DISPLAY_EQUIVALENCE_GATE"
    report["settlement_equivalence"]="NOT_PROVEN"
    report["finished_at_utc"]=datetime.now(timezone.utc).isoformat()

    os.makedirs("artifacts/mexc_event_futures",exist_ok=True)
    path="artifacts/mexc_event_futures/index_equivalence_v064.json"
    with open(path,"w",encoding="utf-8") as f:
        json.dump(report,f,indent=2,sort_keys=True)

    print(json.dumps({
      "source_gate":report["source_gate"],
      "target_pairs":report["target_pairs"],
      "valid_pairs":report["valid_pairs"],
      "within_1bp_fraction":report["within_1bp_fraction"],
      "median_difference_bps":report["median_difference_bps"],
      "mean_difference_bps":report["mean_difference_bps"],
      "max_difference_bps":report["max_difference_bps"],
      "by_asset":{
        a["asset"]:{
          "valid":sum(s.get("valid_pair",False) for s in a.get("samples",[])),
          "bps":[s.get("difference_bps") for s in a.get("samples",[]) if s.get("valid_pair")]
        } for a in report["assets"]
      },
      "settlement_equivalence":report["settlement_equivalence"]
    },indent=2))
    print("WROTE",path)

if __name__=="__main__":
    asyncio.run(main())
