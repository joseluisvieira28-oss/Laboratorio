#!/usr/bin/env python3
"""Separate MEXC USD-M 1H signal and contemporaneous quote SOURCE GATE.
No orders, fills, positions, PnL, accounts, secrets, or retrospective forward credit.
"""
from __future__ import annotations
import argparse, hashlib, json, math, os, statistics, subprocess, time
import urllib.parse, urllib.request
from datetime import datetime, timezone
from decimal import Decimal, ROUND_DOWN
from pathlib import Path

SYMBOLS=("BTC_USDT","ETH_USDT","SOL_USDT","BNB_USDT")
BASE="https://contract.mexc.com"
HOUR_S=3600
HOUR_MS=HOUR_S*1000
WINDOW_MS=600000
MAX_CLOCK_SKEW_MS=1000
MAX_DELAY_MS=2000
NOTIONALS=(25,50,100)
ROOT=Path(__file__).resolve().parent
RECEIPT=ROOT/"MEXC_CONVEX_V01_GATEWAY_OBSERVATION.json"

def utc(ms=None):
    return datetime.fromtimestamp((ms if ms is not None else time.time_ns()/1e6)/1000,timezone.utc).isoformat()

def now_ms():return time.time_ns()//1000000

def d(v):
    x=Decimal(str(v))
    if not x.is_finite() or x<=0: raise ValueError("INVALID_NONPOSITIVE_NUMBER")
    return x

def fetch(path,query=None):
    if not (path in ("/api/v1/contract/ping",) or
            path.startswith("/api/v1/contract/depth/") or
            path.startswith("/api/v1/contract/kline/") or
            path=="/api/v1/contract/detail"):
        raise ValueError("ENDPOINT_NOT_ALLOWED")
    params=("?"+urllib.parse.urlencode(query)) if query else ""
    url=BASE+path+params
    start=now_ms()
    req=urllib.request.Request(url,method="GET",headers={"User-Agent":"CryptoLab-MEXC-1H-CausalGateway/0.1"})
    with urllib.request.urlopen(req, timeout=12) as r:raw=r.read()
    recv=now_ms()
    p=json.loads(raw)
    if not isinstance(p,dict) or not p.get("success") or p.get("code")!=0 or "data" not in p:
        raise ValueError("PUBLIC_API_RESPONSE_INVALID")
    return p["data"], {"endpoint":path,"parameters":query or {}, "request_ms":start,
       "receipt_ms":recv,"latency_ms":recv-start,"sha256":hashlib.sha256(raw).hexdigest()}

def contract(data,sym):
    data=data if isinstance(data,list) else [data]
    x=[z for z in data if z.get("symbol")==sym]
    if len(x)!=1:raise ValueError("SYMBOL_ABSENT")
    z=x[0]
    if (z.get("state"),z.get("futureType"),z.get("quoteCoin"),z.get("settleCoin"))!=(0,1,"USDT","USDT"):
        raise ValueError("NOT_TRADING_USDT_PERPETUAL")
    fields={q:d(z[q]) for q in ("contractSize","minVol","volUnit","maxVol")}
    fields["takerFeeRate"]=str(z.get("takerFeeRate","UNBOUND"))
    fields["apiAllowed"]=z.get("apiAllowed")
    return fields

def candles(data,meta,at_ms):
    if meta["latency_ms"]<0 or meta["latency_ms"]>MAX_DELAY_MS:
        raise ValueError("SLOW_CANDLE_GET")
    fields=("time","open","high","low","close","vol")
    if not isinstance(data,dict) or any(not isinstance(data.get(k),list) for k in fields):
        raise ValueError("BAD_CANDLE_RESPONSE")
    ln=len(data["time"])
    if ln<400 or any(len(data[k])!=ln for k in fields):
        raise ValueError("INCOMPLETE_CANDLE_WARMUP")
    raw=[]
    for i in range(ln):
        ts=int(data["time"][i])
        if ts%HOUR_S:raise ValueError("NON_ALIGNED_1H_OPEN")
        vals=[float(data[k][i]) for k in fields[1:]]
        if any(not math.isfinite(x) for x in vals) or min(vals[0:4])<=0 or vals[4]<0:
            raise ValueError("INVALID_1H_OHLCV")
        if vals[1]<max(vals[0],vals[2],vals[3]) or vals[2]>min(vals[0],vals[1],vals[3]):
            raise ValueError("INVALID_1H_OHLC_ORDER")
        raw.append((ts,*vals))
    raw.sort(key=lambda x:x[0])
    if any(b[0]-a[0]!=HOUR_S for a,b in zip(raw,raw[1:])):
        raise ValueError("GAP_OR_DUPLICATE_1H")
    current_start_s=(at_ms//HOUR_MS)*HOUR_S
    complete=[z for z in raw if z[0]<current_start_s]
    if len(complete)<400:raise ValueError("INSUFFICIENT_CLOSED_1H")
    if complete[-1][0]!=current_start_s-HOUR_S:
        raise ValueError("LATEST_FULL_HOUR_MISSING")
    return complete[-400:], (complete[-1][0]+HOUR_S)*1000

def signal_parent_v5(bars):
    c=[a[4] for a in bars];v=[a[5] for a in bars]
    sma20=sum(c[-20:])/20
    sd=statistics.pstdev(c[-20:])
    sma200=sum(c[-200:])/200
    vol20=sum(v[-20:])/20
    gains=[max(c[i]-c[i-1],0) for i in range(1,len(c))]
    losses=[max(c[i-1]-c[i],0) for i in range(1,len(c))]
    ag=sum(gains[:14])/14;al=sum(losses[:14])/14
    for g,l in zip(gains[14:],losses[14:]):
        ag=(ag*13+g)/14;al=(al*13+l)/14
    rsi=100.0 if al==0 else 100-100/(1+ag/al)
    z=(c[-1]-sma20)/sd if sd>0 else None
    flags={"rsi_lt_30":rsi<30,"z_lt_minus_2":z is not None and z < -2.0,
           "below_bb_minus_2":c[-1]<sma20-2*sd if sd>0 else False,
           "volume_gt_sma20":v[-1]>vol20}
    score=sum(flags.values())
    regime=c[-1]>sma200
    return {"signal":bool(score>=3 and regime),"score":score,"flags":flags,
            "price_close":c[-1],"sma200":sma200,"z":z,"rsi14":rsi,
            "regime_above_sma200":regime}

def depth(data,meta,info,computed_at_ms):
    if meta["request_ms"]<computed_at_ms or meta["receipt_ms"]<meta["request_ms"]:
        raise ValueError("QUOTE_BEFORE_DECISION")
    if meta["latency_ms"]<0 or meta["latency_ms"]>MAX_DELAY_MS:
        raise ValueError("DEPTH_GET_SLOW")
    if not isinstance(data,dict) or int(data.get("version",0))<=0:
        raise ValueError("DEPTH_VERSION_MISSING")
    quote_ts=int(data["timestamp"])
    age=meta["receipt_ms"]-quote_ts
    if not 0<=age<=MAX_DELAY_MS:
        raise ValueError("STALE_OR_FUTURE_DEPTH")
    def levels(name):
        a=data[name]
        if not isinstance(a,list) or not 1<=len(a)<=20:
            raise ValueError("BAD_DEPTH_LEVELS")
        x=[(d(row[0]),d(row[1])) for row in a]
        if any((x[i][0]<=x[i+1][0] if name=="bids" else x[i][0]>=x[i+1][0])
               for i in range(len(x)-1)):
            raise ValueError("BAD_BOOK_ORDER")
        return x
    bids=levels("bids");asks=levels("asks")
    if bids[0][0]>=asks[0][0]:raise ValueError("CROSSED_BOOK")
    def vw(ls,qty):
        left=qty;paid=Decimal(0)
        for price,available in ls:
            n=min(available,left)
            paid+=price*n;left-=n
            if left<=0:return paid/qty
        raise ValueError("DEPTH_TOO_SHALLOW")
    mid=(asks[0][0]+bids[0][0])/2
    scenarios={}
    for nominal in NOTIONALS:
        qty=(Decimal(nominal)/asks[0][0]/info["contractSize"]/info["volUnit"]).to_integral_value(rounding=ROUND_DOWN)*info["volUnit"]
        if qty<info["minVol"] or qty>info["maxVol"]:
            scenarios[str(nominal)]={"status":"MIN_OR_MAX_LOT_BLOCKED","contracts":str(qty)}
            continue
        try:
            buy=vw(asks,qty);sell=vw(bids,qty)
            scenarios[str(nominal)]={"status":"QUOTE_SIZE_SAMPLE_PASS","contracts":str(qty),
                "notional_actual_usdt":str(qty*info["contractSize"]*buy),
                "bid_vwap":str(sell),"ask_vwap":str(buy),
                "same_book_cross_cost_bps":float((buy-sell)/buy*10000)}
        except ValueError:
            scenarios[str(nominal)]={"status":"DEPTH_BLOCKED"}
    return {"snapshot_exchange_ms":quote_ts,"snapshot_received_ms":meta["receipt_ms"],
        "quote_age_ms":age,"spread_bps":float((asks[0][0]-bids[0][0])/mid*10000),
        "best_bid":str(bids[0][0]),"best_ask":str(asks[0][0]),
        "contract_unit":{k:str(v) for k,v in info.items()},
        "scenarios":scenarios,"all_sizes_pass":all(z["status"]=="QUOTE_SIZE_SAMPLE_PASS"
                                                for z in scenarios.values())}

def activation_commit_time_ms():
    try:
        dte=subprocess.check_output(["git","show","-s","--format=%cI","HEAD"],text=True).strip()
        return int(datetime.fromisoformat(dte).timestamp()*1000)
    except (OSError,ValueError,subprocess.CalledProcessError) as exc:
        raise ValueError("ACTIVATION_COMMIT_TIME_UNAVAILABLE") from exc

def selftest():
    raw={"time":[],"open":[],"high":[],"low":[],"close":[],"vol":[]}
    at_ms=1700000000000
    floor=at_ms//HOUR_MS*HOUR_S
    for i in range(402):
        ts=floor-(401-i)*HOUR_S
        for k,val in [("time",ts),("open",99.9),("high",101),("low",99),("close",100),("vol",3)]:
            raw[k].append(val)
    # Replace future data nearest current close without accepting incomplete bar.
    b,close=candles(raw,{"latency_ms":70},at_ms)
    assert len(b)==400 and close==floor*1000
    assert signal_parent_v5(b)["signal"] is False
    invalid={k:list(v) for k,v in raw.items()};invalid["time"][-2]=invalid["time"][-3]
    try:candles(invalid,{"latency_ms":50},at_ms)
    except ValueError:pass
    else:raise AssertionError("GAP_NOT_BLOCKED")
    inf={"contractSize":Decimal("0.0001"),"minVol":Decimal(1),
         "volUnit":Decimal(1),"maxVol":Decimal(10000),"takerFeeRate":"0.0002","apiAllowed":True}
    t={"request_ms":at_ms+10,"receipt_ms":at_ms+30,"latency_ms":20}
    book={"timestamp":at_ms+20,"version":40,
          "asks":[[10000.2,10000]],"bids":[[10000.1,10000]]}
    assert depth(book,t,inf,at_ms)["all_sizes_pass"]
    for ba,meta,clock in [
        ({**book,"timestamp":at_ms-5000},t,at_ms),
        ({**book,"bids":[[10000.2,1]]},t,at_ms),
        (book,t,at_ms+11),
    ]:
        try:depth(ba,meta,inf,clock)
        except ValueError:pass
        else:raise AssertionError("DEPTH_FAIL_CLOSED_MISSING")
    print("MEXC_CAUSAL_GATEWAY_SYNTHETIC_TESTS_PASS")

def live():
    result={"experiment":"MEXC_CONVEX_V01_CAUSAL_GATEWAY",
      "run_commit":os.environ.get("GITHUB_SHA"),
      "started_utc":utc(),"type":"CAUSAL_SIGNAL_PUBLIC_QUOTE_SOURCE_GATE_NO_PNL",
      "freeze":"MEXC_CONVEX_V01_CAUSAL_GATEWAY_PREFREEZE_2026_10_09",
      "endpoint_base":BASE,"symbols":{},"blockers":[],"receipts":[],
      "economic_credit":"NONE","orders_created":False,"real_capital":False,
      "execution_fill_proven":False,
      "source_warning":"No account fees, simulated fill, actual execution or trade returns measured"}
    try:
        commit_time=activation_commit_time_ms()
        result["deployment_commit_time_ms"]=commit_time
        provider,tr=fetch("/api/v1/contract/ping")
        result["receipts"].append(tr)
        if tr["latency_ms"]>MAX_DELAY_MS:raise ValueError("PING_LATENCY")
        midpoint=(tr["request_ms"]+tr["receipt_ms"])//2
        skew=int(provider)-midpoint
        result["provider_clock_offset_ms"]=skew
        if abs(skew)>MAX_CLOCK_SKEW_MS:raise ValueError("CLOCK_SKEW")
        for index,symbol in enumerate(SYMBOLS):
            if index:time.sleep(5.3)
            node={"symbol":symbol,"receipts":[]}
            result["symbols"][symbol]=node
            try:
                infdata,im=fetch("/api/v1/contract/detail",{"symbol":symbol})
                node["receipts"].append(im)
                inf=contract(infdata,symbol)
                current_s=now_ms()//HOUR_MS*HOUR_S
                kd,km=fetch("/api/v1/contract/kline/"+symbol,
                            {"interval":"Min60","start":current_s-440*HOUR_S,"end":current_s})
                node["receipts"].append(km)
                processed_at=now_ms()
                bars,close_boundary=candles(kd,km,processed_at)
                sig=signal_parent_v5(bars)
                timing_valid=0<=processed_at-close_boundary<=WINDOW_MS and close_boundary>commit_time
                node["candidate_signal"]=sig
                node["signal_decision_utc"]=utc(processed_at)
                node["observed_bar_close_utc"]=utc(close_boundary)
                node["minutes_after_close"]=(processed_at-close_boundary)/60000
                node["signal_credit"]="TIMELY_POST_FREEZE" if timing_valid else "NOT_SCORABLE_BOUNDARY"
                # Public book is collected AFTER signal evaluation; never a historical 1H opening fill.
                book,bm=fetch("/api/v1/contract/depth/"+symbol,{"limit":20})
                node["receipts"].append(bm)
                node["book"]=depth(book,bm,inf,processed_at)
                if not node["book"]["all_sizes_pass"]:
                    node["status"]="SIZE_SOURCE_BLOCKED"
                    result["blockers"].append(symbol+":SIZE_OR_DEPTH")
                else:
                    node["status"]="QUOTE_SOURCE_PASS"
                node["paper_entry"]="NONE_NO_EXECUTION_AUTHORITY"
            except Exception as exc:
                node["status"]="SOURCE_BLOCKED"
                node["reason"]=str(exc)
                result["blockers"].append(symbol+":"+str(exc))
    except Exception as exc:
        result["blockers"].append("GLOBAL:"+str(exc))
    result["completed_utc"]=utc()
    result["classification"]="SOURCE_GATEWAY_PASS_NO_TRADING" if len(result["symbols"])==4 and not result["blockers"] else "SOURCE_GATEWAY_BLOCKED_NO_TRADING"
    result["timely_observations"]=sum(1 for v in result["symbols"].values()
                                     if v.get("status")=="QUOTE_SOURCE_PASS" and v.get("signal_credit")=="TIMELY_POST_FREEZE")
    RECEIPT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"classification":result["classification"],"blockers":result["blockers"],
      "timely_observations":result["timely_observations"],
      "symbols":{k:{"status":v.get("status"),"signal_credit":v.get("signal_credit"),
                    "signal":(v.get("candidate_signal") or {}).get("signal"),
                    "quote_age_ms":(v.get("book") or {}).get("quote_age_ms"),
                    "spread_bps":(v.get("book") or {}).get("spread_bps"),
                    "reason":v.get("reason")} for k,v in result["symbols"].items()}},indent=2))
    if result["blockers"]:raise SystemExit("SOURCE_GATEWAY_BLOCKED")

if __name__=="__main__":
    arg=argparse.ArgumentParser()
    arg.add_argument("--self-test",action="store_true")
    arg.add_argument("--live",action="store_true")
    a=arg.parse_args()
    if a.self_test:selftest()
    elif a.live:live()
    else:raise SystemExit("Use --self-test or --live; no trading supported.")
