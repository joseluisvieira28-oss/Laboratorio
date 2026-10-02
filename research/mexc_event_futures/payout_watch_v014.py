#!/usr/bin/env python3
import asyncio,csv,json,os
from collections import defaultdict
from datetime import datetime,timezone
from playwright.async_api import async_playwright

PAGE="https://www.mexc.com/en-GB/futures/event-futures/BTC_USDT"
ROUTE="/api/platform/futures/api/v1/event_contract/detail"
SAMPLES=12
INTERVAL_SECONDS=30

def now():
    return datetime.now(timezone.utc).isoformat()

def flatten(ts,data):
    rows=[]
    for rec in data:
        if not isinstance(rec,dict): continue
        symbol=rec.get("symbol")
        state=rec.get("state")
        cmap=rec.get("cycleConfigMap") or {}
        for unit,items in cmap.items():
            for x in items or []:
                rows.append({
                    "observed_at_utc":ts,
                    "symbol":symbol,
                    "state":state,
                    "unit":unit,
                    "val":x.get("val"),
                    "upPayRate":x.get("upPayRate"),
                    "downPayRate":x.get("downPayRate"),
                    "investMinAmount":rec.get("investMinAmount"),
                    "investMaxAmount":rec.get("investMaxAmount"),
                })
    return rows

async def main():
    outdir="artifacts/mexc_event_futures"
    os.makedirs(outdir,exist_ok=True)
    snapshots=[]
    rows=[]
    aborted=0

    async with async_playwright() as p:
        b=await p.chromium.launch(headless=True,args=["--disable-blink-features=AutomationControlled"])
        c=await b.new_context(locale="en-GB",timezone_id="UTC")
        await c.clear_cookies()
        page=await c.new_page()

        async def rh(route):
            nonlocal aborted
            if route.request.method.upper()!="GET":
                aborted+=1
                await route.abort()
            else:
                await route.continue_()
        await page.route("**/*",rh)

        resp=await page.goto(PAGE,wait_until="domcontentloaded",timeout=60000)
        page_status=resp.status if resp else None
        await page.wait_for_timeout(5000)

        for i in range(SAMPLES):
            ts=now()
            try:
                result=await page.evaluate("""async (url) => {
                  const r = await fetch(url,{method:'GET',credentials:'omit',cache:'no-store'});
                  return {status:r.status, text:await r.text()};
                }""", ROUTE)
                snap={"observed_at_utc":ts,"sample_index":i,"status":result["status"]}
                try:
                    j=json.loads(result["text"])
                    snap["success"]=j.get("success") if isinstance(j,dict) else None
                    snap["code"]=j.get("code") if isinstance(j,dict) else None
                    data=j.get("data") if isinstance(j,dict) else None
                    snap["data"]=data
                    if isinstance(data,list):
                        rows.extend(flatten(ts,data))
                except Exception as e:
                    snap["parse_error"]=repr(e)
                    snap["body_preview"]=result["text"][:1000]
                snapshots.append(snap)
            except Exception as e:
                snapshots.append({"observed_at_utc":ts,"sample_index":i,"error":repr(e)})
            if i<SAMPLES-1:
                await page.wait_for_timeout(INTERVAL_SECONDS*1000)

        await b.close()

    series=defaultdict(list)
    for r in rows:
        key=(r["symbol"],r["unit"],r["val"])
        series[key].append((r["observed_at_utc"],r["upPayRate"],r["downPayRate"],r["state"]))
    stats=[]
    for key,vals in sorted(series.items()):
        ups=[v[1] for v in vals if isinstance(v[1],(int,float))]
        dns=[v[2] for v in vals if isinstance(v[2],(int,float))]
        changes=0
        prev=None
        for _,u,d,s in vals:
            cur=(u,d,s)
            if prev is not None and cur!=prev: changes+=1
            prev=cur
        stats.append({
            "symbol":key[0],"unit":key[1],"val":key[2],
            "samples":len(vals),
            "up_min":min(ups) if ups else None,"up_max":max(ups) if ups else None,
            "down_min":min(dns) if dns else None,"down_max":max(dns) if dns else None,
            "change_count":changes,
            "first":vals[0] if vals else None,
            "last":vals[-1] if vals else None,
        })

    report={
        "lab":"MEXC_EVENT_FUTURES_PAYOUT_WATCH_V0.14",
        "generated_at_utc":now(),
        "page_status":page_status,
        "samples_requested":SAMPLES,
        "interval_seconds":INTERVAL_SECONDS,
        "snapshots":snapshots,
        "stats":stats,
        "authenticated_requests":0,"orders":0,"account_mutations":0,
        "aborted_non_get_count":aborted,
        "verdict":"PROSPECTIVE_PAYOUT_SERIES_CAPTURED" if rows else "PAYOUT_SERIES_BLOCKED",
    }

    jp=f"{outdir}/payout_watch_v014.json"
    cp=f"{outdir}/payout_watch_v014.csv"
    with open(jp,"w",encoding="utf-8") as f: json.dump(report,f,indent=2,sort_keys=True)
    fields=["observed_at_utc","symbol","state","unit","val","upPayRate","downPayRate","investMinAmount","investMaxAmount"]
    with open(cp,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)

    print("VERDICT="+report["verdict"])
    print("PAGE_STATUS="+str(page_status))
    print("SNAPSHOTS="+str(len(snapshots)))
    print("FLAT_ROWS="+str(len(rows)))
    for x in stats:
        if x["change_count"]>0 or x["symbol"] in ("BTC_USDT","ETH_USDT"):
            print("PAYOUT_STAT="+json.dumps(x,ensure_ascii=False,sort_keys=True))
    print("NO_AUTH=PASS\nNO_ORDERS=PASS\nNO_MUTATION=PASS")
    print("WROTE "+jp)
    print("WROTE "+cp)

if __name__=="__main__":
    asyncio.run(main())
