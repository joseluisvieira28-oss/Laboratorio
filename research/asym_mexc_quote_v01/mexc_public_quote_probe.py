#!/usr/bin/env python3
"""MEXC futures quote SOURCE/contract-unit feasibility only. No accounts/keys/orders."""
import argparse, hashlib, json, time, urllib.parse, urllib.request
from decimal import Decimal, ROUND_DOWN
from datetime import datetime, timezone
from pathlib import Path

BASE="https://contract.mexc.com"
SYMBOLS=["BTC_USDT","ETH_USDT","SOL_USDT","BNB_USDT"]
SIZES=["10","25","50","100"]
OUTPUT=Path(__file__).with_name("MEXC_PUBLIC_QUOTE_SAMPLE_RECEIPT.json")
MAX_MS=2000

def clock(): return time.time_ns()//1000000

def dec(s):
    x=Decimal(str(s))
    if not x.is_finite() or x<=0: raise ValueError("NONPOSITIVE_VALUE")
    return x

def get(path,params=None):
    url=BASE+path+("?" + urllib.parse.urlencode(params) if params else "")
    t0=clock()
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-MEXC-Futures-Source/0.1"},method="GET")
    with urllib.request.urlopen(req,timeout=12) as r: raw=r.read()
    t1=clock()
    o=json.loads(raw)
    if not isinstance(o,dict) or not o.get("success") or o.get("code",0)!=0:
        raise ValueError("API_SOURCE_RESPONSE_FAILED")
    return o["data"], {"path":path,"params":params or {}, "request_at_ms":t0,
       "received_at_ms":t1,"latency_ms":t1-t0, "sha256":hashlib.sha256(raw).hexdigest()}

def getinfo(data,symbol):
    if isinstance(data,dict): data=[data]
    hits=[v for v in data if v.get("symbol")==symbol]
    if len(hits)!=1: raise ValueError("SYMBOL_NOT_IN_DETAIL")
    s=hits[0]
    if s.get("state")!=0 or s.get("settleCoin")!="USDT" or s.get("quoteCoin")!="USDT":
        raise ValueError("NONTRADING_CONTRACT_STATE")
    if s.get("futureType") is not None and s["futureType"]!=1:
        raise ValueError("NONPERPETUAL_CONTRACT")
    return {"contractSize":dec(s["contractSize"]), "minVol":dec(s["minVol"]),
            "volUnit":dec(s["volUnit"]), "maxVol":dec(s["maxVol"]),
            "apiAllowed":s.get("apiAllowed"),"takerFeeRate":str(s.get("takerFeeRate","UNBOUND")),
            "state":s["state"]}

def levels(v,side):
    if not isinstance(v,list) or not v: raise ValueError("EMPTY_DEPTH_"+side)
    out=[]
    for z in v[:20]:
        if not isinstance(z,list) or len(z)<2: raise ValueError("MALFORMED_LEVEL")
        out.append((dec(z[0]),dec(z[1])))
    for a,b in zip(out,out[1:]):
        if side=="bids" and not a[0]>b[0]: raise ValueError("NON_DESCENDING_BIDS")
        if side=="asks" and not a[0]<b[0]: raise ValueError("NON_ASCENDING_ASKS")
    return out

def vwap(ls,contracts):
    rem=contracts; price_sum=Decimal("0")
    for price,avail in ls:
        qty=min(rem,avail); price_sum+=qty*price; rem-=qty
        if rem<=0: return price_sum/contracts
    raise ValueError("DEPTH_INSUFFICIENT")

def adjudicate(book,timing,info):
    ts=int(book["timestamp"]); age=timing["received_at_ms"]-ts
    if timing["latency_ms"]<0 or timing["latency_ms"]>MAX_MS: raise ValueError("SLOW_REQUEST")
    if not 0<=age<=MAX_MS: raise ValueError("STALE_OR_FUTURE_DEPTH")
    if int(book.get("version",0))<=0: raise ValueError("INVALID_BOOK_VERSION")
    bids=levels(book["bids"],"bids"); asks=levels(book["asks"],"asks")
    if bids[0][0]>=asks[0][0]: raise ValueError("CROSSED_BOOK")
    mid=(bids[0][0]+asks[0][0])/2
    values={}
    for nominal in SIZES:
        # MEXC depth size is CONTRACT COUNT, not base-asset size or USDT.
        n=Decimal(nominal)
        contracts=(n/(asks[0][0]*info["contractSize"])/info["volUnit"]).to_integral_value(rounding=ROUND_DOWN)*info["volUnit"]
        if contracts<info["minVol"] or contracts>info["maxVol"]:
            values[nominal]={"status":"LOT_SIZE_BLOCKED","contracts":str(contracts)}
            continue
        try:
            buy=vwap(asks,contracts); sell=vwap(bids,contracts)
            mechanical=(buy-sell)/buy*10000
            values[nominal]={"status":"SAMPLE_DEPTH_SUFFICIENT","contracts":str(contracts),
               "base_asset_units":str(contracts*info["contractSize"]),
               "buy_vwap":str(buy),"sell_vwap":str(sell),
               "actual_buy_notional_usdt":str(contracts*info["contractSize"]*buy),
               "same_snapshot_book_cross_cost_bps":float(mechanical)}
        except ValueError:
            values[nominal]={"status":"DEPTH_BLOCKED"}
    return {"status":"SOURCE_SAMPLE_PASS" if all(
       y["status"]=="SAMPLE_DEPTH_SUFFICIENT" for y in values.values()) else "SMALL_SIZE_BLOCKED",
       "snapshot_age_at_receipt_ms":age,
       "spread_bps":float((asks[0][0]-bids[0][0])/mid*10000),
       "best_bid":str(bids[0][0]),"best_ask":str(asks[0][0]),
       "book_version":book["version"],"contract":{"contractSize":str(info["contractSize"]),
       "minVol":str(info["minVol"]),"volUnit":str(info["volUnit"]),"maxVol":str(info["maxVol"]),
       "apiAllowed":info["apiAllowed"],"takerFeeRate":info["takerFeeRate"]},
       "scenarios_usdt":values}

def selftest():
    info={"contractSize":Decimal("0.0001"),"minVol":Decimal("1"),"volUnit":Decimal("1"),
          "maxVol":Decimal("10000"),"apiAllowed":True,"takerFeeRate":"0.0006"}
    t={"received_at_ms":100000,"latency_ms":50}
    book={"timestamp":99950,"version":2,
          "bids":[[10000,1000],[9990,1000]],"asks":[[10001,1000],[10002,1000]]}
    r=adjudicate(book,t,info)
    assert r["status"]=="SOURCE_SAMPLE_PASS",r
    assert r["scenarios_usdt"]["10"]["contracts"]=="9",r
    for b in [{**book,"timestamp":97000},{**book,"bids":[[10001,1000]]},
              {**book,"bids":[[9990,1000],[10000,1000]]}]:
        try: adjudicate(b,t,info)
        except ValueError: pass
        else: raise AssertionError("FAIL_CLOSED_MISSING")
    small={**info,"minVol":Decimal("100")}
    assert adjudicate(book,t,small)["status"]=="SMALL_SIZE_BLOCKED"
    print("MEXC_SOURCE_SYNTHETIC_TESTS_PASS:5")

def live():
    result={"experiment":"ASYM-MEXC-FUTURES-QUOTE-V0.1",
            "source":"PUBLIC_GET_ONLY","run_sha":__import__("os").environ.get("GITHUB_SHA"),
            "started_at_utc":datetime.now(timezone.utc).isoformat(),
            "source_receipts":[],"symbols":{},"blockers":[],
            "warning":"Source-only single snapshot, not demonstrated trading or Binance-strategy transfer"}
    try:
        tm,t=get("/api/v1/contract/ping");result["source_receipts"].append(t)
        skew=int(tm)-(t["received_at_ms"]+t["request_at_ms"])//2
        result["clock_skew_ms"]=skew
        if abs(skew)>1000 or t["latency_ms"]>MAX_MS: raise ValueError("CLOCK_OR_NETWORK_INVALID")
        for symbol in SYMBOLS:
            try:
                d,dr=get("/api/v1/contract/detail",{"symbol":symbol});result["source_receipts"].append(dr)
                contract=getinfo(d,symbol)
                b,br=get("/api/v1/contract/depth/"+symbol,{"limit":20});result["source_receipts"].append(br)
                status=adjudicate(b,br,contract)
                result["symbols"][symbol]=status
                if status["status"]!="SOURCE_SAMPLE_PASS":result["blockers"].append(symbol+":"+status["status"])
            except Exception as e:
                result["symbols"][symbol]={"status":"SOURCE_BLOCKED","reason":str(e)}
                result["blockers"].append(symbol+":"+str(e))
    except Exception as e: result["blockers"].append("GLOBAL_SOURCE:"+str(e))
    result["completed_at_utc"]=datetime.now(timezone.utc).isoformat()
    result["classification"]="SOURCE_SAMPLE_PASS_NO_EXECUTION_PROOF" if len(result["symbols"])==4 and not result["blockers"] else "SOURCE_BLOCKED_NO_TRADING"
    OUTPUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"classification":result["classification"],"blockers":result["blockers"],
          "symbols":{s:{"status":v["status"],"spread_bps":v.get("spread_bps"),
            "apiAllowed":v.get("contract",{}).get("apiAllowed"),
            "takerFeeRate":v.get("contract",{}).get("takerFeeRate"),
            "scenarios":{k:q["status"] for k,q in v.get("scenarios_usdt",{}).items()}}
            for s,v in result["symbols"].items()}},indent=2))
    if result["classification"]!="SOURCE_SAMPLE_PASS_NO_EXECUTION_PROOF":
        raise SystemExit("SOURCE_BLOCKED")

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--self-test",action="store_true");p.add_argument("--live",action="store_true");a=p.parse_args()
    if a.self_test:selftest()
    elif a.live:live()
    else:raise SystemExit("Specify --self-test or --live")
