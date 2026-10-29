#!/usr/bin/env python3
"""Frozen one-day EXPLORATORY signed-aggressor-flow proxy (NOT Event Futures PnL)."""
import csv
import datetime as dt
import gzip
import hashlib
import json
import math
import pathlib
import urllib.parse
import urllib.request

ROOT=pathlib.Path("artifacts/event_futures_ati_source_v01")
OUT=pathlib.Path("artifacts/event_futures_ati_proxy_v01")
OUT.mkdir(parents=True,exist_ok=True)
START=int(dt.datetime(2026,4,1,tzinfo=dt.timezone.utc).timestamp())
END=START+86400
HORIZONS=(10,30)
PAYOUTS=(0.4,0.8,0.85)
SYMBOLS=(("BTCUSDT","BTC_USDT"),("ETHUSDT","ETH_USDT"))

def read_flow(symbol):
    path=ROOT/(symbol+"_minute_source_only.csv.gz")
    receipt=json.loads((ROOT/"receipt.json").read_text())
    if receipt.get("gate")!="HISTORICAL_AGGRESSOR_SOURCE_PASS":
        raise RuntimeError("PARENT_SOURCE_NOT_PASS")
    expected=next(x["derived_sha256"] for x in receipt["records"] if x["symbol"]==symbol)
    if hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
        raise RuntimeError("DERIVED_SOURCE_SHA_MISMATCH")
    records={}
    with gzip.open(path,"rt",newline="",encoding="utf-8") as f:
        for row in csv.DictReader(f):
            t=int(row["minute_start_utc_ms"])//1000
            if not START<=t<END or t%60:raise RuntimeError("INVALID_MINUTE_TS")
            records[t]=(float(row["taker_buy_notional"]),float(row["taker_sell_notional"]))
            if not all(math.isfinite(z) and z>=0 for z in records[t]):
                raise RuntimeError("INVALID_FLOW_NOTIONAL")
    if len(records)<1000:raise RuntimeError("LOW_FLOW_MINUTES")
    return records,expected

def index_source(symbol):
    u=("https://contract.mexc.com/api/v1/contract/kline/index_price/"+symbol+
       "?"+urllib.parse.urlencode({"interval":"Min5","start":START,"end":END-300}))
    req=urllib.request.Request(u,headers={"User-Agent":"CryptoLab-Research-ReadOnly/0.1"})
    with urllib.request.urlopen(req,timeout=45) as r:
        if r.status!=200:raise RuntimeError("MEXC_SOURCE_HTTP_FAIL")
        raw=r.read(2_000_001)
    if len(raw)>2_000_000:raise RuntimeError("SOURCE_TOO_LARGE")
    j=json.loads(raw)
    d=j.get("data",{})
    if j.get("success") is not True or not isinstance(d,dict):
        raise RuntimeError("INDEX_SOURCE_INVALID")
    x=d.get("time");o=d.get("open")
    if not isinstance(x,list) or not isinstance(o,list) or len(x)!=len(o):
        raise RuntimeError("INDEX_SCHEMA")
    prices={}
    for t,p in zip(x,o):
        t=int(t);p=float(p)
        if not START<=t<END or t%300 or not math.isfinite(p) or p<=0:
            raise RuntimeError("BAD_INDEX_PRICE_OR_TIME")
        if t in prices and prices[t]!=p:raise RuntimeError("DUPLICATE_CONFLICT")
        prices[t]=p
    if len(prices)<270:raise RuntimeError("INDEX_COVERAGE_LOW")
    return prices,hashlib.sha256(raw).hexdigest(),u

def score(rows):
    n=len(rows)
    if not n:return None
    w=sum(x=="WIN" for x in rows);l=sum(x=="LOSS" for x in rows);ties=n-w-l
    return {"n":n,"wins":w,"losses":l,"ties":ties,
            "accuracy_ex_ties":w/(w+l) if w+l else None,
            "hypothetical_unit_ev":{
                str(q):round((q*w-l)/n,8) for q in PAYOUTS}}

def main():
    results={"study":"ATI_3M_ONE_DAY_HIST_PROXY_V01","date":"2026-04-01",
             "historical_period_previously_exposed":True,
             "model":"signed taker NOTIONAL last 3 completed one-minute bins; sign positive UP, negative DOWN",
             "benchmark":"always UP on identical decisions",
             "model_was_frozen_before_this_run":True,
             "real_event_futures_payouts":False,"exact_server_open_price":False,
             "holdout_september_2026_opened":False,"no_real_orders":True,
             "status":"SOURCE_STARTING","cells":[]}
    try:
        for raw,contract in SYMBOLS:
            flow,flow_hash=read_flow(raw)
            idx,index_hash,index_url=index_source(contract)
            for h in HORIZONS:
                model=[];baseline=[];skips=0
                for t in range(START+1200,END-h*60,h*60):
                    # At t, strictly completed minute bins t-3m,t-2m,t-1m.
                    ts=[t-180,t-120,t-60]
                    if t not in idx or t+h*60 not in idx or any(z not in flow for z in ts):
                        skips+=1;continue
                    buy=sum(flow[z][0] for z in ts)
                    sell=sum(flow[z][1] for z in ts)
                    if buy==sell:
                        skips+=1;continue
                    signed=1 if buy>sell else -1
                    price_delta=idx[t+h*60]-idx[t]
                    def outcome(direction):
                        if price_delta==0:return "TIE"
                        return "WIN" if price_delta*direction>0 else "LOSS"
                    model.append(outcome(signed))
                    baseline.append(outcome(1))
                results["cells"].append({
                    "symbol":contract,"horizon_minutes":h,"skipped":skips,
                    "aggressor_rule":score(model),"always_up_baseline":score(baseline),
                    "flow_sha256":flow_hash,"index_response_sha256":index_hash,
                    "index_url":index_url,
                    "note":"Historical exchange event time does not establish collector arrival time."
                })
        results["status"]="HISTORICAL_DESCRIPTIVE_PROXY_ONLY"
    except Exception as ex:
        results["status"]="SOURCE_OR_JOIN_BLOCKED"
        results["reason"]=str(ex)
        raise
    finally:
        (OUT/"report.json").write_text(json.dumps(results,sort_keys=True,indent=2)+"\n")
        print(json.dumps(results,sort_keys=True,indent=2))

if __name__=="__main__":main()
