#!/usr/bin/env python3
"""Forward as-of Binance perp vs MEXC index PRICE comparability; no 10min outcomes or orders."""
import asyncio, datetime as dt, hashlib, json, math, pathlib, statistics, time
import websockets

BIN="wss://fstream.binance.com/market/stream?streams=btcusdt@aggTrade/ethusdt@aggTrade"
MEX="wss://futures.mexc.com/edge"
SYMS=("BTC","ETH")
DURATION=180
OUT=pathlib.Path("artifacts/event10m_mexc_public_resub_v03")

def current():
    return {"recv_utc_ms":time.time_ns()//1_000_000,"recv_monotonic_ns":time.monotonic_ns()}
def hashraw(raw):
    return hashlib.sha256(raw.encode("utf-8") if isinstance(raw,str) else raw).hexdigest()
def valid_index(msg):
    if not isinstance(msg,dict) or msg.get("channel")!="push.index.price":return None
    d=msg.get("data")
    if not isinstance(d,dict):return None
    s=msg.get("symbol") or d.get("symbol")
    if s not in ("BTC_USDT","ETH_USDT"):return None
    try:p=float(d.get("price"))
    except (TypeError,ValueError):return None
    if not(math.isfinite(p) and p>0):return None
    ts=msg.get("ts")
    ts=int(ts) if isinstance(ts,(int,float)) and 1600000000000<int(ts)<2100000000000 else None
    return {"symbol":s.split("_")[0],"server_ts_ms":ts,"price":p}
def valid_binance(msg):
    if not isinstance(msg,dict):return None
    d=msg.get("data",msg)
    if not isinstance(d,dict) or d.get("e")!="aggTrade":return None
    s=d.get("s")
    if s not in ("BTCUSDT","ETHUSDT"):return None
    if d.get("st") not in (None,1):return None
    try:price=float(d.get("p"));quantity=float(d.get("q"))
    except (ValueError,TypeError):return None
    if not (math.isfinite(price) and price>0 and math.isfinite(quantity) and quantity>0):
        return None
    E=d.get("E");T=d.get("T")
    if not isinstance(E,int) or not isinstance(T,int) or not 1600000000000<E<2100000000000 or not 1600000000000<T<2100000000000:return None
    return {"symbol":s.removesuffix("USDT"),"event_ts_ms":E,"trade_ts_ms":T,"price":price}
def quantile(nums,f):
    if not nums:return None
    arr=sorted(nums)
    idx=round((len(arr)-1)*f)
    return arr[idx]
def test_parsers():
    assert valid_index({"channel":"push.index.price","symbol":"BTC_USDT","data":{"price":"80000"},"ts":1790000000000})["symbol"]=="BTC"
    assert valid_index({"channel":"push.index.price","symbol":"BTC_USDT","data":{"price":"-3"}}) is None
    assert valid_index({"channel":"push.order","symbol":"BTC_USDT","data":{"price":"1"}}) is None
    d={"e":"aggTrade","s":"ETHUSDT","p":"3000","q":"1","E":1790000000100,"T":1790000000050,"m":False}
    assert valid_binance({"stream":"ethusdt@aggTrade","data":d})["symbol"]=="ETH"
    assert valid_binance({"data":dict(d,st=2)}) is None
    assert quantile([100,10,50],.5)==50

async def collect_bin(report,starts,stop_ns):
    side=report["streams"]["binance"]
    side["opened_utc_ms"]=None
    try:
        async with websockets.connect(BIN,open_timeout=18,close_timeout=3,ping_interval=20,ping_timeout=12,max_size=2_000_000) as ws:
            side["opened_utc_ms"]=current()["recv_utc_ms"]
            starts["binance"]=time.monotonic_ns()
            frames=0
            while time.monotonic_ns()<stop_ns and frames<10000:
                try:raw=await asyncio.wait_for(ws.recv(),timeout=1.5)
                except asyncio.TimeoutError:continue
                frames+=1
                tick=current()
                if isinstance(raw,bytes):
                    side["binary_frames"]+=1;continue
                try:message=json.loads(raw)
                except ValueError:side["invalid_json"]+=1;continue
                obs=valid_binance(message)
                if obs is None:side["irrelevant_or_invalid"]+=1;continue
                sym=obs["symbol"];sid=report["per_symbol"][sym]
                sid["bin_count"]+=1
                report["observations"][sym]["binance"].append([tick["recv_monotonic_ns"],obs["price"],tick["recv_utc_ms"],hashraw(raw)])
                sid["last_bin_recv_monotonic_ns"]=tick["recv_monotonic_ns"]
                if sid["first_bin_utc_ms"] is None:sid["first_bin_utc_ms"]=tick["recv_utc_ms"]
                sid["last_bin_utc_ms"]=tick["recv_utc_ms"]
                sid["bin_source_clock_offset_ms"].append(tick["recv_utc_ms"]-obs["event_ts_ms"])
                sid["bin_trade_clock_offset_ms"].append(tick["recv_utc_ms"]-obs["trade_ts_ms"])
                mx=sid["last_mexc_recv_monotonic_ns"]
                if mx is not None and mx<=tick["recv_monotonic_ns"]:
                    sid["mexc_prior_age_when_bin_ms"].append((tick["recv_monotonic_ns"]-mx)/1e6)
                if len(sid["raw_receipt_samples"]["bin"])<5:
                    sid["raw_receipt_samples"]["bin"].append({**tick,**obs,"raw_sha256":hashraw(raw)})
            side["raw_frames"]=frames
            side["closed_utc_ms"]=current()["recv_utc_ms"]
    except Exception as e:
        side["error"]=type(e).__name__+":"+str(e)[:220]
async def collect_mexc(report,starts,stop_ns):
    side=report["streams"]["mexc"]
    side["opened_utc_ms"]=None
    try:
        async with websockets.connect(MEX,origin="https://www.mexc.com",open_timeout=18,close_timeout=3,ping_interval=15,ping_timeout=10,max_size=3_000_000) as ws:
            side["opened_utc_ms"]=current()["recv_utc_ms"]
            starts["mexc"]=time.monotonic_ns()
            for sym in SYMS:await ws.send(json.dumps({"method":"sub.index.price","param":{"symbol":sym+"_USDT"}},separators=(",",":")))
            side["public_subscribe_refresh_events"]=[]
            refresh_at_ns=time.monotonic_ns()+40_000_000_000
            frames=0
            while time.monotonic_ns()<stop_ns and frames<2000:
                if time.monotonic_ns()>=refresh_at_ns:
                    for sym in SYMS:
                        await ws.send(json.dumps({"method":"sub.index.price","param":{"symbol":sym+"_USDT"}},separators=(",",":")))
                    side["public_subscribe_refresh_events"].append({"utc_ms":current()["recv_utc_ms"],
                        "method":"sub.index.price","symbols":["BTC_USDT","ETH_USDT"]})
                    refresh_at_ns+=40_000_000_000
                try:raw=await asyncio.wait_for(ws.recv(),timeout=1.5)
                except asyncio.TimeoutError:continue
                frames+=1
                tick=current()
                if isinstance(raw,bytes):
                    side["binary_frames"]+=1;continue
                try:message=json.loads(raw)
                except ValueError:side["invalid_json"]+=1;continue
                obs=valid_index(message)
                if obs is None:side["irrelevant_or_invalid"]+=1;continue
                sym=obs["symbol"];sid=report["per_symbol"][sym]
                sid["mexc_count"]+=1
                report["observations"][sym]["mexc"].append([tick["recv_monotonic_ns"],obs["price"],tick["recv_utc_ms"],hashraw(raw)])
                sid["last_mexc_recv_monotonic_ns"]=tick["recv_monotonic_ns"]
                if sid["first_mexc_utc_ms"] is None:sid["first_mexc_utc_ms"]=tick["recv_utc_ms"]
                sid["last_mexc_utc_ms"]=tick["recv_utc_ms"]
                if obs["server_ts_ms"] is not None:
                    sid["mexc_source_clock_offset_ms"].append(tick["recv_utc_ms"]-obs["server_ts_ms"])
                bi=sid["last_bin_recv_monotonic_ns"]
                if bi is not None and bi<=tick["recv_monotonic_ns"]:
                    sid["bin_prior_age_when_mexc_ms"].append((tick["recv_monotonic_ns"]-bi)/1e6)
                if len(sid["raw_receipt_samples"]["mexc"])<5:
                    sid["raw_receipt_samples"]["mexc"].append({**tick,**obs,"raw_sha256":hashraw(raw)})
            side["raw_frames"]=frames
            for sym in SYMS:
                try:await ws.send(json.dumps({"method":"unsub.index.price","param":{"symbol":sym+"_USDT"}},separators=(",",":")))
                except Exception:pass
            side["closed_utc_ms"]=current()["recv_utc_ms"]
    except Exception as e:
        side["error"]=type(e).__name__+":"+str(e)[:220]
def stats(nums):
    return {"n":len(nums),"minimum_ms":min(nums) if nums else None,
            "median_ms":quantile(nums,.5),"p95_ms":quantile(nums,.95)}
def make_symbol():
    return {"bin_count":0,"mexc_count":0,
            "first_bin_utc_ms":None,"last_bin_utc_ms":None,
            "first_mexc_utc_ms":None,"last_mexc_utc_ms":None,
            "last_bin_recv_monotonic_ns":None,"last_mexc_recv_monotonic_ns":None,
            "bin_source_clock_offset_ms":[],"bin_trade_clock_offset_ms":[],
            "mexc_source_clock_offset_ms":[],"bin_prior_age_when_mexc_ms":[],
            "mexc_prior_age_when_bin_ms":[],
            "raw_receipt_samples":{"bin":[],"mexc":[]}}
def recent(rows, t):
    # Strict as-of: accept only a received price no later than the grid boundary.
    import bisect
    times=[r[0] for r in rows]
    n=bisect.bisect_right(times,t)-1
    if n<0:return None
    rec=rows[n]
    age=t-rec[0]
    if age<0 or age>5_000_000_000:return None
    return rec[1],age
def parity(rows_b,rows_m,origin,end):
    results=[]
    t=origin+15_000_000_000
    while t<=end:
        vals=[recent(rows_b,t),recent(rows_b,t-15_000_000_000),
              recent(rows_m,t),recent(rows_m,t-15_000_000_000)]
        if all(x is not None for x in vals):
            b,b0,m,m0=vals
            bret=10000*math.log(b[0]/b0[0])
            mret=10000*math.log(m[0]/m0[0])
            results.append({"grid_offset_s":round((t-origin)/1e9,3),
              "binance_last15s_bps":round(bret,8),"mexc_last15s_bps":round(mret,8),
              "binance_stale_ms":round(b[1]/1e6,3),"mexc_stale_ms":round(m[1]/1e6,3)})
        t+=5_000_000_000
    both=[(x["binance_last15s_bps"],x["mexc_last15s_bps"]) for x in results]
    nonzero=[(a,b) for a,b in both if abs(a)>1e-9 and abs(b)>1e-9]
    shocks=[x for x in results if abs(x["binance_last15s_bps"])>=5.0]
    corr=None
    if len(both)>=3:
        ax=[z[0] for z in both];ay=[z[1] for z in both]
        xbar=sum(ax)/len(ax);ybar=sum(ay)/len(ay)
        cov=sum((x-xbar)*(y-ybar) for x,y in both)
        xx=sum((x-xbar)**2 for x in ax);yy=sum((y-ybar)**2 for y in ay)
        if xx>0 and yy>0:corr=cov/math.sqrt(xx*yy)
    return {"paired_asof_grid_points":len(results),
            "nonzero_binance":sum(abs(a)>1e-9 for a,b in both),
            "nonzero_mexc":sum(abs(b)>1e-9 for a,b in both),
            "both_nonzero":len(nonzero),
            "contemporaneous_sign_agreement":sum(a*b>0 for a,b in nonzero),
            "contemporaneous_pearson_overlapping_returns":corr,
            "binance_5bps_15s_backward_shocks":len(shocks),
            "contemporaneous_mexc_shock_sign_agreement":
                sum(x["binance_last15s_bps"]*x["mexc_last15s_bps"]>0 for x in shocks),
            "all_grid_observations":results}
def parity_tests():
    test=[(100,10.0,0,"x"),(200,11.0,0,"y"),(300,12.0,0,"z")]
    assert recent(test,199)==(10.0,99)
    assert recent(test,200)==(11.0,0)
    assert recent(test,99) is None
    assert recent(test,300+5_000_000_001) is None
    assert abs(10000*math.log(math.exp(.01)/1.)-100)<1e-8

async def main():
    test_parsers()
    parity_tests()
    OUT.mkdir(parents=True,exist_ok=True)
    report={"lab":"E10M_XVENUE_MEXC_INDEX_RESUB_V03","gate":"STARTING",
      "started_utc_ms":current()["recv_utc_ms"],"duration_seconds_requested":DURATION,
      "source_urls":{"binance":BIN,"mexc":MEX},
      "nvidia_excluded":True,"account_or_orders":0,"telegram_messages":0,
      "market_direction_outcomes_opened":0,"historical_holdout_accessed":False,
      "predictive_model_frozen":False,"can_prove_human_delivery":False,
      "can_prove_event_futures_fill_parity":False,
      "per_symbol":{s:make_symbol() for s in SYMS},
      "observations":{s:{"binance":[],"mexc":[]} for s in SYMS},
      "streams":{venue:{"raw_frames":0,"binary_frames":0,
          "irrelevant_or_invalid":0,"invalid_json":0} for venue in ("binance","mexc")}}
    starts={}
    begin=time.monotonic_ns()
    stop_ns=begin+DURATION*1_000_000_000
    try:
        await asyncio.gather(collect_bin(report,starts,stop_ns),collect_mexc(report,starts,stop_ns))
        joined_seconds=(min((report["streams"][v].get("closed_utc_ms") or current()["recv_utc_ms"]) for v in ("binance","mexc"))-max((report["streams"][v].get("opened_utc_ms") or current()["recv_utc_ms"]) for v in ("binance","mexc")))/1000
        report["overlap_seconds"]=max(0,round(joined_seconds,2))
        gate=all(report["per_symbol"][s]["bin_count"]>=20 and report["per_symbol"][s]["mexc_count"]>=2 for s in SYMS) and report["overlap_seconds"]>=20
        report["transport_gate"]="SOURCE_FEASIBLE_NO_EDGE" if gate else "SOURCE_INCOMPLETE_NO_EDGE"
        observations=report["observations"]
        starts=[observations[s][v][0][0] for s in SYMS for v in ("binance","mexc") if observations[s][v]]
        origin=max(starts) if len(starts)==4 else None
        end=time.monotonic_ns()
        report["price_asof"]={s:parity(observations[s]["binance"],observations[s]["mexc"],origin,end)
           if origin is not None else {"paired_asof_grid_points":0,"nonzero_binance":0,"nonzero_mexc":0} for s in SYMS}
        parity_ok=all(report["price_asof"][s]["paired_asof_grid_points"]>=18 and
           report["price_asof"][s]["nonzero_binance"]>=10 and
           report["price_asof"][s]["nonzero_mexc"]>=10 for s in SYMS)
        clean=all(not report["streams"][v].get("error") for v in ("binance","mexc"))
        report["gate"]="PRICE_COMPARABILITY_SOURCE_PASS" if gate and parity_ok and clean and report["overlap_seconds"]>=120 else "PRICE_SOURCE_INCOMPLETE"
        report["no_10minute_price_outcomes"]=True
        report["same_instrument_price_parity_proven"]=False
        report["economic_or_prediction_edge_certified"]=False
    except Exception as e:
        report["gate"]="SOURCE_BLOCKED_NO_EDGE"
        report["fatal"]=type(e).__name__+":"+str(e)[:160]
    finally:
        for sym,sid in report["per_symbol"].items():
            sid["age_statistics"]={key:stats(sid.pop(key)) for key in ("bin_source_clock_offset_ms","bin_trade_clock_offset_ms","mexc_source_clock_offset_ms","bin_prior_age_when_mexc_ms","mexc_prior_age_when_bin_ms")}
            sid.pop("last_bin_recv_monotonic_ns")
            sid.pop("last_mexc_recv_monotonic_ns")
        report["ended_utc_ms"]=current()["recv_utc_ms"]
        report["economic_verdict"]="NO_CERTIFIED_PREDICTIVE_10MIN_EDGE"
        report["human_alert_execution_verdict"]="BLOCKED_NO_TELEGRAM_DELIVERY_OR_HUMAN_ACTION_RECEIPT"
        (OUT/"source_receipt.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
        summary={"gate":report["gate"],"overlap_seconds":report.get("overlap_seconds"),
          "price_asof":{sym:{k:v for k,v in rec.items() if k!="all_grid_observations"} for sym,rec in report.get("price_asof",{}).items()},
          "streams":report["streams"],
          "counts":{sym:{"binance_aggtrade":sid["bin_count"],
                         "mexc_index":sid["mexc_count"],
                         "age_statistics":sid["age_statistics"]} for sym,sid in report["per_symbol"].items()},
          "forecast_outcomes":0,"live_orders":0}
        print(json.dumps(summary,indent=2,sort_keys=True),flush=True)
    if report["gate"]!="PRICE_COMPARABILITY_SOURCE_PASS":raise SystemExit(2)
if __name__=="__main__":asyncio.run(main())
