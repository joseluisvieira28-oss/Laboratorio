#!/usr/bin/env python3
"""Read-only 10m exact products and source-only top-of-book microstructure snapshot."""
import asyncio,datetime as dt,hashlib,json,math,pathlib,time,urllib.error,urllib.parse,urllib.request
from playwright.async_api import async_playwright
OUT=pathlib.Path("artifacts/event10m_live_sources_v01")
PAGE="https://www.mexc.com/en-GB/futures/event-futures/BTC_USDT"
DETAIL="/api/platform/futures/api/v1/event_contract/detail"
SENSITIVE=("/private/","/account","/balance","/wallet","/positions","/order","/user/","/api_key","/apikey")
def now():return dt.datetime.now(dt.timezone.utc).isoformat()
def milli():return int(time.time()*1000)
def sha(x):return hashlib.sha256(x).hexdigest()
def numeric(x):
    try:
        v=float(x)
        return v if math.isfinite(v) and v>0 else None
    except (ValueError,TypeError):return None
def get_public(url):
    req=urllib.request.Request(url,headers={"Accept":"application/json","User-Agent":"CryptoLab-Event10m-PublicSourceV01"})
    with urllib.request.urlopen(req,timeout=16) as res:
        if res.status!=200:raise RuntimeError("NON_200")
        raw=res.read(1800001)
    if len(raw)>1800000:raise RuntimeError("BODY_TOO_LARGE")
    return json.loads(raw),{"url":url,"sha256":sha(raw),"bytes":len(raw),"received_ms":milli()}
def breaks(q):
    v=numeric(q)
    return 1/(1+v) if v is not None else None
async def events():
    output={"provider":"MEXC_EXACT_PUBLIC_EVENT_FUTURES_DETAIL",
        "blocked_non_get_count":0,"blocked_sensitive_get_count":0,
        "snapshots":[],"status":"STARTING"}
    async with async_playwright() as browser_tool:
        browser=await browser_tool.chromium.launch(headless=True)
        try:
            ctx=await browser.new_context(locale="en-GB",service_workers="block")
            await ctx.clear_cookies()
            page=await ctx.new_page()
            async def safe(route):
                req=route.request;u=req.url.lower()
                if req.method.upper()!="GET":
                    output["blocked_non_get_count"]+=1;await route.abort()
                elif any(t in u for t in SENSITIVE):
                    output["blocked_sensitive_get_count"]+=1;await route.abort()
                else:await route.continue_()
            await ctx.route("**/*",safe)
            first=asyncio.Event()
            seen=[]
            async def capture(resp):
                if DETAIL not in resp.url or resp.status!=200:return
                try:
                    raw=await resp.body()
                    if len(raw)>2000000:return
                    obj=json.loads(raw)
                    if obj.get("success") is True and isinstance(obj.get("data"),list):
                        seen.append((milli(),resp.url,raw,obj))
                        first.set()
                except Exception:return
            page.on("response",capture)
            await page.goto(PAGE,wait_until="domcontentloaded",timeout=55000)
            try:await asyncio.wait_for(first.wait(),timeout=12)
            except asyncio.TimeoutError:pass
            for shot in range(3):
                # An explicit anonymous refetch ensures product rates are fresh.
                data=await page.evaluate("""async()=>{const x=await fetch(
                  '/api/platform/futures/api/v1/event_contract/detail',
                  {method:'GET',credentials:'omit',cache:'no-store'});
                  return {status:x.status,ok:x.ok};
                }""")
                await asyncio.sleep(.6)
                if not seen:raise RuntimeError("NO_PUBLIC_EVENT_DETAILS")
                receiver,url,raw,obj=seen[-1]
                allrows=[]
                for prod in obj["data"]:
                    cycles=(prod.get("cycleConfigMap") or {}).get("MINUTE") or []
                    for item in cycles:
                        if item.get("val")!=10:continue
                        allrows.append({"symbol":prod.get("symbol"),"contract_id":prod.get("contractId"),
                          "state":prod.get("state"),"horizon_min":10,
                          "up_payout":numeric(item.get("upPayRate")),
                          "down_payout":numeric(item.get("downPayRate")),
                          "up_required_win_rate":breaks(item.get("upPayRate")),
                          "down_required_win_rate":breaks(item.get("downPayRate"))})
                allrows.sort(key=lambda a:str(a["symbol"]))
                output["snapshots"].append({"shot":shot,"request_status":data["status"],
                    "response_received_ms":receiver,"url":url,
                    "raw_sha256":sha(raw),"product_total":len(obj["data"]),
                    "ten_minute_product_count":len(allrows),"ten_minute_products":allrows})
                if shot<2:await asyncio.sleep(6)
            if len(output["snapshots"])!=3:raise RuntimeError("THREE_REQUIRED_SNAPSHOTS")
            if any(x["request_status"]!=200 for x in output["snapshots"]):
                raise RuntimeError("PRODUCT_REFRESH_NON_200")
            output["status"]="THREE_PUBLIC_EVENT_PRODUCT_SNAPSHOTS_RECEIVED"
        except Exception as e:
            output["status"]="SOURCE_BLOCKED"
            output["error"]=type(e).__name__+":"+str(e)[:200]
        finally:await browser.close()
    return output
def book_stats(levels_bids,levels_asks):
    if not isinstance(levels_bids,list) or not isinstance(levels_asks,list):
        raise ValueError("DEPTH_ARRAY_SHAPE")
    def parse(rows):
        values=[]
        for x in rows[:20]:
            if not isinstance(x,(list,tuple)) or len(x)<2:raise ValueError("DEPTH_ROW")
            p=numeric(x[0]);q=numeric(x[1])
            if p is None or q is None:raise ValueError("DEPTH_PRICE_QTY")
            values.append((p,q))
        if len(values)<5:raise ValueError("DEPTH_TOO_SHALLOW")
        return values
    bids=parse(levels_bids);asks=parse(levels_asks)
    if not(bids[0][0]<asks[0][0]):raise ValueError("CROSSED_OR_LOCKED_BOOK")
    if any(bids[i][0]<bids[i+1][0] for i in range(len(bids)-1)):
        raise ValueError("BID_OUT_OF_ORDER")
    if any(asks[i][0]>asks[i+1][0] for i in range(len(asks)-1)):
        raise ValueError("ASK_OUT_OF_ORDER")
    bn=sum(p*q for p,q in bids[:5]);an=sum(p*q for p,q in asks[:5])
    return {"top5_bid_notional":bn,"top5_ask_notional":an,
      "top5_signed_imbalance":(bn-an)/(bn+an),
      "best_bid":bids[0][0],"best_ask":asks[0][0],
      "spread_bps":20000*(asks[0][0]-bids[0][0])/(asks[0][0]+bids[0][0]),
      "bid_levels":len(bids),"ask_levels":len(asks)}
def mexc_index(sym):
    out={"venue":"MEXC_STANDARD_FUTURES_INDEX","symbol":sym,"status":"SOURCE_BLOCKED"}
    try:
        data,rec=get_public("https://contract.mexc.com/api/v1/contract/index_price/"+sym)
        v=data.get("data") or {}
        price=numeric(v.get("indexPrice"));ts=v.get("timestamp")
        if data.get("success") is not True or v.get("symbol")!=sym or price is None or type(ts) is not int:
            raise RuntimeError("INDEX_SCHEMA_OR_PRICE")
        out.update(status="INDEX_PRESENT",receipt=rec,price=price,server_ms=ts,
                   local_minus_server_ms=rec["received_ms"]-ts)
    except Exception as e:out["error"]=type(e).__name__+":"+str(e)[:155]
    return out
def mexc_depth(sym):
    out={"venue":"MEXC_FUTURES_DEPTH","symbol":sym,"status":"SOURCE_BLOCKED"}
    try:
        data,rec=get_public("https://contract.mexc.com/api/v1/contract/depth/"+sym+"?limit=20")
        v=data.get("data") or {}
        if data.get("success") is not True:raise RuntimeError("DEPTH_RESPONSE_FAIL")
        stats=book_stats(v.get("bids"),v.get("asks"))
        out.update(status="ORDER_BOOK_PRESENT",receipt=rec,
             published_depth_timestamp=v.get("timestamp"),stats=stats)
    except Exception as e:out["error"]=type(e).__name__+":"+str(e)[:155]
    return out
def binance_depth(sym):
    out={"venue":"BINANCE_SPOT_DEPTH","symbol":sym,"status":"SOURCE_BLOCKED"}
    try:
        bin_sym=sym.replace("_","")
        data,rec=get_public("https://api.binance.com/api/v3/depth?"+urllib.parse.urlencode(
          {"symbol":bin_sym,"limit":20}))
        stats=book_stats(data.get("bids"),data.get("asks"))
        out.update(status="INDEPENDENT_SPOT_BOOK_PRESENT",receipt=rec,stats=stats,
             lastUpdateId=data.get("lastUpdateId"))
    except Exception as e:out["error"]=type(e).__name__+":"+str(e)[:155]
    return out
async def main():
    OUT.mkdir(parents=True,exist_ok=True)
    product=await events()
    depth=await asyncio.gather(*[asyncio.to_thread(fn,sym) for sym in ("BTC_USDT","ETH_USDT")
                       for fn in (mexc_index,mexc_depth,binance_depth)])
    snapshots=product.get("snapshots") or []
    active={}
    if snapshots:
        for row in snapshots[-1]["ten_minute_products"]:
            if row["state"]=="ONLINE" and row["up_payout"] is not None and row["down_payout"] is not None:
                active[row["symbol"]]=row
    status="PRODUCT_SNAPSHOT_PASS" if product["status"]=="THREE_PUBLIC_EVENT_PRODUCT_SNAPSHOTS_RECEIVED" else "PRODUCT_SOURCE_BLOCKED"
    market_gate={sym:all(x["status"] in ("INDEX_PRESENT","ORDER_BOOK_PRESENT","INDEPENDENT_SPOT_BOOK_PRESENT")
            for x in depth if x["symbol"]==sym) for sym in ("BTC_USDT","ETH_USDT")}
    out={"study":"CRYPTO_LAB_EVENT10M_CURRENT_LISTING_MICROSTRUCTURE_SOURCE_V01",
       "read_only":True,"captured_at_utc":now(),"event":product,"depth":depth,
       "active_10m_symbols":sorted(active.keys()),"active_10m_payouts":active,
       "independent_spot_and_mexc_book_gate":market_gate,
       "outcome_labels_opened":0,"forecasts_generated":0,"economic_ev_estimated":False,
       "historical_event_payout_inferred":False,
       "exact_server_event_settlement_index_parity_proven":False,
       "source_gate":status,"real_trades_or_orders":0,"account_or_wallet_reads":0,
       "protected_september_holdout_reads":0,"protected_oct05_30_NVDA_forward_reads":0}
    (OUT/"source_receipt.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    summary={k:v for k,v in out.items() if k not in ("event","depth","active_10m_payouts")}
    summary["active_10m_payouts"]=active
    summary["market_sources"]=[{"venue":v["venue"],"symbol":v["symbol"],"status":v["status"],
       "error":v.get("error"),"sha256":(v.get("receipt") or {}).get("sha256")}
       for v in depth]
    print(json.dumps(summary,indent=2,sort_keys=True),flush=True)
    if status!="PRODUCT_SNAPSHOT_PASS":raise SystemExit(2)
if __name__=="__main__":asyncio.run(main())
