#!/usr/bin/env python3
"""Locked same 80 cells on SECOND historical window: 26/27 Oct 2026, source only public GET."""
import datetime as dt
import hashlib,json,math,pathlib,urllib.parse,urllib.request
from zoneinfo import ZoneInfo
import multiasset_historical_v02 as parent

START=int(dt.datetime(2026,10,26,tzinfo=dt.timezone.utc).timestamp())
END=int(dt.datetime(2026,10,28,tzinfo=dt.timezone.utc).timestamp())
N=(END-START)//300
ASSETS=tuple(parent.ASSETS.keys())
assert N==576
assert len(ASSETS)==5
assert len(parent.RULES)==4 and len(parent.HORIZONS)==2 and len(parent.STRATA)==2

# DST-aware and frozen before source evaluation; same local 09:30-16:00 hours.
NY=ZoneInfo("America/New_York")
def regular(t,h):
    d=dt.datetime.fromtimestamp(t,NY)
    minutes=d.hour*60+d.minute
    return d.weekday()<5 and 570<=minutes and minutes+h<=960
assert regular(int(dt.datetime(2026,10,23,14,0,tzinfo=dt.timezone.utc).timestamp()),10)
assert not regular(int(dt.datetime(2026,10,26,14,0,tzinfo=dt.timezone.utc).timestamp()),10)
assert regular(int(dt.datetime(2026,10,26,14,30,tzinfo=dt.timezone.utc).timestamp()),10)
parent.regular=regular
parent.START=START
parent.END=END
parent.N_EXPECTED=N

OUT=pathlib.Path("artifacts/event_futures_multiasset_v03")
OUT.mkdir(parents=True,exist_ok=True)

def source(symbol):
    url=("https://contract.mexc.com/api/v1/contract/kline/index_price/"+
         symbol+"?"+urllib.parse.urlencode({"interval":"Min5","start":START,"end":END-300}))
    req=urllib.request.Request(url,headers={"Accept":"application/json","User-Agent":"CryptoLab-Multiasset-FrozenReplication/0.3"})
    with urllib.request.urlopen(req,timeout=40) as response:
        if response.status!=200:raise ValueError("SOURCE_HTTP_NOT_200")
        raw=response.read(2_000_001)
    if len(raw)>2_000_000:raise ValueError("SOURCE_TOO_LARGE")
    obj=json.loads(raw)
    if obj.get("success") is not True or not isinstance(obj.get("data"),dict):
        raise ValueError("SOURCE_SCHEMA")
    d=obj["data"];times=d.get("time");values=d.get("open")
    if not isinstance(times,list) or not isinstance(values,list) or len(times)!=len(values) or len(times)!=N:
        raise ValueError("INCOMPLETE_SOURCE")
    p={}
    for t,value in zip(times,values):
        t=int(t);value=float(value)
        if t%300 or not START<=t<END or t in p or not(math.isfinite(value) and value>0):
            raise ValueError("SOURCE_INVALID_CANDLE")
        p[t]=value
    if len(p)!=N or any(t not in p for t in range(START,END,300)):
        raise ValueError("MISSING_PRICE_BAR")
    return p,{"symbol":symbol,"url":url,"response_sha256":hashlib.sha256(raw).hexdigest(),"bars":N}
def main():
    report={"study":"MEXC_EVENT_FUTURES_ALL_CELL_HIST_REPLICATION_V03",
            "start":"2026-10-26T00:00:00Z","end_exclusive":"2026-10-28T00:00:00Z",
            "frozen_rule_source":"multiasset_historical_v02.py",
            "window_not_used_to_select_model_in_this_experiment":True,
            "independent_protected_holdout_claim":False,
            "mli_identity":"UNVERIFIED_EXCLUDED",
            "actual_historical_event_futures_payout":False,
            "exact_product_entry_expiry_prices":False,
            "historical_event_product_state":"UNKNOWN",
            "trading_or_private_calls":0,
            "source_status":"STARTING","sources":[],"cells":[]}
    try:
        for symbol in ASSETS:
            p,receipt=source(symbol)
            report["sources"].append(receipt)
            for h in parent.HORIZONS:
                for rule in parent.RULES:
                    for stratum in parent.STRATA:
                        x=parent.score(p,rule,h,stratum)
                        report["cells"].append({"symbol":symbol,"horizon_minutes":h,
                                                "rule":rule,"stratum":stratum,**x})
        if len(report["cells"])!=80:raise ValueError("CELL_COUNT_MISMATCH")
        report["source_status"]="SOURCE_GRID_PASS"
        report["verdict"]="HISTORICAL_REPLICATION_ONLY_NO_CERTIFIED_EVENT_FUTURES_EDGE"
    except Exception as e:
        report["source_status"]="BLOCKED"
        report["error"]=type(e).__name__+":"+str(e)[:250]
        raise
    finally:
        (OUT/"replication.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
        print(json.dumps(report,indent=2,sort_keys=True))
if __name__=="__main__":main()
