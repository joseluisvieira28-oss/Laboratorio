#!/usr/bin/env python3
"""BTC 10m ONE-SHOT FOUR-LEG SOURCE PREFLIGHT. NO DIRECTION, FORECAST OR OUTCOME."""
import asyncio,concurrent.futures,datetime as dt,hashlib,json,math,pathlib,time,urllib.parse,urllib.request
from playwright.async_api import async_playwright
from btc_event10m_source_gates_v04 import asof
OUT=pathlib.Path("artifacts/btc_event10m_source_v04")
RAW=OUT/"raw"
ASSET="BTC_USDT"
PAGE="https://www.mexc.com/en-GB/futures/event-futures/BTC_USDT"
DETAIL="/api/platform/futures/api/v1/event_contract/detail"
SENSITIVE=("/private/","/account","/balance","/wallet","/positions","/order","/user/","/api_key","/apikey")
def ms():return int(time.time()*1000)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def fetch(url,filename):
    req=urllib.request.Request(url,headers={"Accept":"application/json","User-Agent":"BTC-Event10m-PublicSourceOnly-V04"})
    with urllib.request.urlopen(req,timeout=14) as resp:
        if resp.status!=200:raise ValueError("PUBLIC_HTTP_FAIL")
        raw=resp.read(1500001)
    if len(raw)>1500000:raise ValueError("PUBLIC_RESPONSE_TOO_LARGE")
    end=ms();(RAW/filename).write_bytes(raw)
    return json.loads(raw),{"url":url,"filename":filename,"sha256":sha(raw),"received_ms":end}
def positive(x):
    try:
        f=float(x)
        if not(math.isfinite(f) and f>0):raise ValueError("BAD_POSITIVE")
        return f
    except (ValueError,TypeError):raise ValueError("INVALID_NUMERIC")
def book_stats(bids,asks):
    def parsed(rows,reverse):
        if not isinstance(rows,list) or len(rows)<5:raise ValueError("SHALLOW_BOOK")
        a=[(positive(x[0]),positive(x[1])) for x in rows[:20]]
        if any((a[i][0]<a[i+1][0] if reverse else a[i][0]>a[i+1][0])
               for i in range(len(a)-1)):
            raise ValueError("BAD_BOOK_ORDER")
        return a
    b=parsed(bids,True);a=parsed(asks,False)
    if b[0][0]>=a[0][0]:raise ValueError("CROSSED_BOOK")
    bn=sum(p*q for p,q in b[:5]);an=sum(p*q for p,q in a[:5])
    spread=20000*(a[0][0]-b[0][0])/(a[0][0]+b[0][0])
    if spread<=0 or spread>10:raise ValueError("SPREAD_OUT_OF_FROZEN_GATE")
    return {"imbalance":(bn-an)/(bn+an),"spread_bps":spread,
            "bid_notional":bn,"ask_notional":an}
def okx_book(n):
    url="https://www.okx.com/api/v5/market/books?instId=BTC-USDT&sz=20"
    data,rec=fetch(url,"okx_book_%d.json"%n)
    rows=data.get("data") or []
    if str(data.get("code"))!="0" or len(rows)!=1:raise ValueError("OKX_SOURCE_SCHEMA")
    book=rows[0];t=int(book.get("ts") or 0)
    if not(0<=rec["received_ms"]-t<=2000):raise ValueError("OKX_STALE_OR_FUTURE")
    metrics=book_stats(book.get("bids"),book.get("asks"))
    return {"venue":"OKX_SPOT","received_ms":rec["received_ms"],"server_ms":t,
            "sha256":rec["sha256"],"raw_file":rec["filename"],**metrics}
def mexc_book(n):
    url="https://contract.mexc.com/api/v1/contract/depth/BTC_USDT?limit=20"
    data,rec=fetch(url,"mexc_book_%d.json"%n)
    if data.get("success") is not True or not isinstance(data.get("data"),dict):
        raise ValueError("MEXC_DEPTH_SCHEMA")
    v=data["data"];metrics=book_stats(v.get("bids"),v.get("asks"))
    return {"venue":"MEXC_PERPETUAL","received_ms":rec["received_ms"],
        "book_server_ms_unverified":v.get("timestamp"),
        "sha256":rec["sha256"],"raw_file":rec["filename"],**metrics}
def index():
    url="https://contract.mexc.com/api/v1/contract/index_price/BTC_USDT"
    data,rec=fetch(url,"mexc_index.json")
    val=data.get("data") or {}
    if data.get("success") is not True or val.get("symbol")!=ASSET:
        raise ValueError("MEXC_INDEX_SCHEMA")
    t=val.get("timestamp")
    if type(t)!=int or not(0<=rec["received_ms"]-t<=2000):
        raise ValueError("INDEX_SERVER_CLOCK_STALE")
    return {"symbol":ASSET,"received_ms":rec["received_ms"],"server_ms":t,
       "index_price":positive(val.get("indexPrice")),"sha256":rec["sha256"],
       "raw_file":rec["filename"]}
async def book_pair(n):
    loop=asyncio.get_running_loop()
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        a=loop.run_in_executor(pool,okx_book,n)
        b=loop.run_in_executor(pool,mexc_book,n)
        okx,mexc=await asyncio.gather(a,b)
    return {"asset":ASSET,"received_ms":max(okx["received_ms"],mexc["received_ms"]),
       "okx_spot":okx,"mexc_futures":mexc}
async def collect(target_boundary_ms=None):
    report={"study":"BTC_EVENT10M_SINGLE_SOURCE_PREFLIGHT_V04",
        "scope":"SOURCE_ONLY_NO_FORECAST_NO_OUTCOME","started_ms":ms(),
        "status":"BLOCKED","samples":[],"market_return_labels_read":0,
        "signals_issued":0,"positions_orders_accounts_private_calls":0,
        "protected_holdout_reads":0,"scheduled_prospective_runner_active":False,
        "actual_event_server_price_parity_proven":False}
    samples=[];product=None;index_tick=None
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        try:
            ctx=await browser.new_context(locale="en-GB",service_workers="block")
            await ctx.clear_cookies()
            page=await ctx.new_page()
            async def guard(route):
                u=route.request.url.lower()
                if route.request.method.upper()!="GET" or any(x in u for x in SENSITIVE):
                    await route.abort()
                else:await route.continue_()
            await ctx.route("**/*",guard)
            captured=[]
            async def onresponse(res):
                if DETAIL not in res.url or res.status!=200:return
                try:
                    raw=await res.body()
                    if len(raw)>2000000:return
                    obj=json.loads(raw)
                    if obj.get("success") is True and isinstance(obj.get("data"),list):
                        captured.append((ms(),raw,obj))
                except Exception:return
            page.on("response",onresponse)
            await page.goto(PAGE,wait_until="domcontentloaded",timeout=50000)
            # Warm up browser before sampling, so no old book is reused.
            for _ in range(20):
                if captured:break
                await asyncio.sleep(.25)
            if not captured:raise ValueError("EVENT_DETAIL_NOT_PUBLICLY_ACCESSIBLE")
            if target_boundary_ms is not None:
                # Research-only future one-shot: three book pairs begin at :12,
                # :17, :22 of a predeclared UTC 10-minute boundary; no late retry.
                if type(target_boundary_ms) is not int or target_boundary_ms%600000:
                    raise ValueError("INVALID_UTC_SLOT_BOUNDARY")
                start_at=target_boundary_ms+12000
                if ms()>=start_at:raise ValueError("MISSED_FROZEN_PAPER_SLOT")
                await asyncio.sleep((start_at-ms())/1000)
            for n in range(3):
                if n:
                    target=samples[-1]["received_ms"]+5000
                    await asyncio.sleep(max(0,(target-ms())/1000))
                samples.append(await book_pair(n))
                if n==1:
                    before=len(captured)
                    fetchstatus=await page.evaluate("""async()=>{const r=await fetch(
                      '/api/platform/futures/api/v1/event_contract/detail',
                      {method:'GET',credentials:'omit',cache:'no-store'});
                      return r.status;}""")
                    for _ in range(20):
                        if len(captured)>before:break
                        await asyncio.sleep(.05)
                    if fetchstatus!=200 or len(captured)<=before:
                        raise ValueError("NO_FRESH_EVENT_PAYOUT_RESPONSE")
                    received,raw,obj=captured[-1]
                    matches=[v for v in obj["data"] if v.get("symbol")==ASSET]
                    if len(matches)!=1:raise ValueError("BTC_EVENT_PRODUCT_MISSING")
                    v=matches[0];ten=[c for c in ((v.get("cycleConfigMap") or {}).get("MINUTE") or [])
                         if c.get("val")==10]
                    if len(ten)!=1:raise ValueError("NO_10M_CYCLE")
                    RAW.joinpath("mexc_event_contract_detail.json").write_bytes(raw)
                    product={"symbol":ASSET,"duration_min":10,
                        "state":v.get("state"),"contract_id":v.get("contractId"),
                        "up_pay_rate":positive(ten[0].get("upPayRate")),
                        "down_pay_rate":positive(ten[0].get("downPayRate")),
                        "received_ms":received,"sha256":sha(raw),
                        "raw_file":"mexc_event_contract_detail.json"}
            # Final public index read after final book pair; clock gate <=2s.
            index_tick=await asyncio.to_thread(index)
            decision_ms=ms()
            source_gates=asof(samples,product,index_tick,decision_ms)
            report.update(samples=samples,product=product,index=index_tick,
                source_gates=source_gates,asof_ms=decision_ms,
                source_gate_all_pass=all(source_gates.values()),
                status="FOUR_LEG_ASOF_SOURCE_PASS" if all(source_gates.values())
                    else "ASOF_CLOCK_OR_PRODUCT_BLOCKED")
        except Exception as exc:
            report.update(status="SOURCE_BLOCKED",
                error=type(exc).__name__+":"+str(exc)[:260],
                samples=samples,product=product,index=index_tick)
        finally:
            await browser.close()
    report["completed_at_utc"]=dt.datetime.now(dt.timezone.utc).isoformat()
    report["finished_ms"]=ms()
    return report
async def main():
    OUT.mkdir(parents=True,exist_ok=True);RAW.mkdir(parents=True,exist_ok=True)
    report=await collect()
    (OUT/"source_receipt.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k not in ("samples",)},indent=2))
    if report["status"]!="FOUR_LEG_ASOF_SOURCE_PASS":raise SystemExit(2)
if __name__=="__main__":asyncio.run(main())
