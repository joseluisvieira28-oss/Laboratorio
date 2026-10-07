#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
import requests

CBASE="https://contract.mexc.com/api/v1/contract"
SBASE="https://api.mexc.com/api/v3"
CONTRACTS=["BTC_USDT","BTC_USDC","BTC_USD1","ETH_USDT","ETH_USDC","ETH_USD1"]
SPOT=["USDCUSDT","USD1USDT","USD1USDC"]
ANCHORS=["2026-05-01","2026-06-01","2026-07-01","2026-08-01","2026-09-01","2026-10-01"]
UA={"User-Agent":"CryptoLab-MultiStable-Coverage/0.2"}
OUT=Path("artifacts/mexc_multistable_basis/coverage_v02/report.json")

def ev(r,dt):
    b=r.content
    return {"status":r.status_code,"latency_ms":round(dt*1000,3),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}

def get(url,params=None,sleep=0.13):
    t=time.perf_counter()
    r=requests.get(url,params=params,headers=UA,timeout=15)
    elapsed=time.perf_counter()-t
    try:
        j=r.json()
    except Exception:
        j=None
    time.sleep(sleep)
    return r,j,ev(r,elapsed)

def expected_seconds(day):
    start=datetime.fromisoformat(day+"T00:00:00+00:00")
    return [int((start+timedelta(minutes=i)).timestamp()) for i in range(60)]

def contract_window(sym,day):
    exp=expected_seconds(day)
    start=exp[0]
    end=start+3599
    r,j,e=get(f"{CBASE}/kline/{sym}",{"interval":"Min1","start":str(start),"end":str(end)})
    times=[]
    ok_http=r.status_code==200 and isinstance(j,dict) and j.get("success") is True
    if ok_http:
        d=j.get("data") or {}
        times=[int(x) for x in (d.get("time") or []) if isinstance(x,(int,float))]
    unique=sorted(set(times))
    exact=(unique==exp)
    return {
        "ok":bool(ok_http and exact),
        "http_ok":ok_http,
        "rows":len(times),
        "unique_timestamps":len(unique),
        "expected":60,
        "first_timestamp":unique[0] if unique else None,
        "last_timestamp":unique[-1] if unique else None,
        "exact_expected_minutes":exact,
        "evidence":e,
    }

def spot_window(sym,day):
    start_dt=datetime.fromisoformat(day+"T00:00:00+00:00")
    start_ms=int(start_dt.timestamp()*1000)
    end_ms=start_ms+60*60*1000-1
    r,j,e=get(f"{SBASE}/klines",{"symbol":sym,"interval":"1m","startTime":str(start_ms),"endTime":str(end_ms),"limit":100})
    times=[]
    ok_http=r.status_code==200 and isinstance(j,list)
    if ok_http:
        for row in j:
            if isinstance(row,list) and row and isinstance(row[0],(int,float)):
                times.append(int(row[0])//1000)
    unique=sorted(set(times))
    exp=expected_seconds(day)
    exact=(unique==exp)
    return {
        "ok":bool(ok_http and exact),
        "http_ok":ok_http,
        "rows":len(times),
        "unique_timestamps":len(unique),
        "expected":60,
        "first_timestamp":unique[0] if unique else None,
        "last_timestamp":unique[-1] if unique else None,
        "exact_expected_minutes":exact,
        "evidence":e,
    }

def main():
    report={
        "family_id":"MEXC-MULTI-STABLE-BASIS-001",
        "phase":"SOURCE_ONLY_HISTORICAL_COVERAGE",
        "anchors":ANCHORS,
        "contracts":{},
        "normalization":{},
        "economic_outcomes_opened":False,
        "ohlc_values_reported":False,
        "basis_calculated":False,
        "returns_calculated":False,
        "pnl_calculated":False,
    }
    failures=[]
    for sym in CONTRACTS:
        report["contracts"][sym]={}
        for day in ANCHORS:
            row=contract_window(sym,day)
            report["contracts"][sym][day]=row
            if not row["ok"]:
                failures.append({"route":sym,"day":day,"kind":"contract"})
    for sym in SPOT:
        report["normalization"][sym]={}
        for day in ANCHORS:
            row=spot_window(sym,day)
            report["normalization"][sym][day]=row
            if not row["ok"]:
                failures.append({"route":sym,"day":day,"kind":"spot"})
    verdict="COVERAGE_ANCHOR_PASS" if not failures else "COVERAGE_PARTIAL"
    report["verdict"]=verdict
    report["failures"]=failures
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True))
    print(json.dumps({
        "verdict":verdict,
        "failure_count":len(failures),
        "failures":failures,
        "economic_outcomes_opened":False,
        "ohlc_values_reported":False,
        "basis_calculated":False,
    },sort_keys=True))

if __name__=="__main__":
    main()
