#!/usr/bin/env python3
from __future__ import annotations

import hashlib, json, time
from datetime import datetime, timezone, timedelta
from pathlib import Path
import requests

CBASE="https://contract.mexc.com/api/v1/contract"
SBASE="https://api.mexc.com/api/v3"
CONTRACTS=["BTC_USDT","BTC_USDC","BTC_USD1","ETH_USDT","ETH_USDC","ETH_USD1"]
SPOT_REQUIRED=["USDCUSDT","USD1USDT"]
SPOT_DIAG=["USD1USDC"]
DATES=["2026-09-07","2026-09-10","2026-09-14","2026-09-17","2026-09-21","2026-09-24","2026-09-28","2026-10-01","2026-10-04","2026-10-06"]
UA={"User-Agent":"CryptoLab-MultiStable-CoverageRemediation/0.2.1"}
OUT=Path("artifacts/mexc_multistable_basis/coverage_v021/report.json")

def get(url,params=None,sleep=0.14):
    t=time.perf_counter()
    r=requests.get(url,params=params,headers=UA,timeout=15)
    dt=time.perf_counter()-t
    body=r.content
    try: j=r.json()
    except Exception: j=None
    time.sleep(sleep)
    return r,j,{
        "status":r.status_code,
        "latency_ms":round(dt*1000,3),
        "sha256":hashlib.sha256(body).hexdigest(),
        "bytes":len(body)
    }

def expected(day):
    start=datetime.fromisoformat(day+"T00:00:00+00:00")
    return [int((start+timedelta(minutes=i)).timestamp()) for i in range(60)]

def contract_probe(sym,day):
    exp=expected(day); start=exp[0]; end=start+3599
    r,j,e=get(f"{CBASE}/kline/{sym}",{"interval":"Min1","start":str(start),"end":str(end)})
    times=[]
    http_ok=r.status_code==200 and isinstance(j,dict) and j.get("success") is True
    if http_ok:
        d=j.get("data") or {}
        times=[int(x) for x in (d.get("time") or []) if isinstance(x,(int,float))]
    u=sorted(set(times))
    return {
        "ok":u==exp,
        "http_ok":http_ok,
        "rows":len(times),
        "unique_timestamps":len(u),
        "first_timestamp":u[0] if u else None,
        "last_timestamp":u[-1] if u else None,
        "evidence":e
    }

def spot_probe(sym,day):
    start_dt=datetime.fromisoformat(day+"T00:00:00+00:00")
    start_ms=int(start_dt.timestamp()*1000)
    end_ms=start_ms+3600*1000-1
    r,j,e=get(f"{SBASE}/klines",{"symbol":sym,"interval":"1m","startTime":str(start_ms),"endTime":str(end_ms),"limit":100})
    times=[]
    http_ok=r.status_code==200 and isinstance(j,list)
    if http_ok:
        for row in j:
            if isinstance(row,list) and row and isinstance(row[0],(int,float)):
                times.append(int(row[0])//1000)
    u=sorted(set(times)); exp=expected(day)
    return {
        "ok":u==exp,
        "http_ok":http_ok,
        "rows":len(times),
        "unique_timestamps":len(u),
        "first_timestamp":u[0] if u else None,
        "last_timestamp":u[-1] if u else None,
        "evidence":e
    }

def main():
    report={
        "family_id":"MEXC-MULTI-STABLE-BASIS-001",
        "phase":"SOURCE_ONLY_HISTORICAL_COVERAGE_REMEDIATION",
        "dates":DATES,
        "contracts":{},
        "spot_required":{},
        "spot_diagnostic":{},
        "economic_outcomes_opened":False,
        "ohlc_values_reported":False,
        "basis_calculated":False,
        "returns_calculated":False,
        "pnl_calculated":False,
    }
    common_pass_dates=[]
    for day in DATES:
        day_ok=True
        report["contracts"][day]={}
        for sym in CONTRACTS:
            row=contract_probe(sym,day)
            report["contracts"][day][sym]=row
            day_ok = day_ok and row["ok"]
        report["spot_required"][day]={}
        for sym in SPOT_REQUIRED:
            row=spot_probe(sym,day)
            report["spot_required"][day][sym]=row
            day_ok = day_ok and row["ok"]
        report["spot_diagnostic"][day]={}
        for sym in SPOT_DIAG:
            report["spot_diagnostic"][day][sym]=spot_probe(sym,day)
        if day_ok:
            common_pass_dates.append(day)

    # We are not inferring hidden daily continuity between sparse anchors.
    # The frozen 60-day historical gate cannot pass unless evidence spans >=60 calendar days
    # with all tested required anchors passing; any failure among the predeclared anchors blocks it.
    first = common_pass_dates[0] if common_pass_dates else None
    last = common_pass_dates[-1] if common_pass_dates else None
    span_days = None
    if first and last:
        span_days=(datetime.fromisoformat(last)-datetime.fromisoformat(first)).days+1
    all_required_anchors_pass=(len(common_pass_dates)==len(DATES))
    historical_pass=bool(all_required_anchors_pass and span_days is not None and span_days>=60)
    verdict="HISTORICAL_SOURCE_PASS" if historical_pass else "HISTORICAL_SOURCE_BLOCKED_INSUFFICIENT_COMMON_COVERAGE"

    report["common_pass_dates"]=common_pass_dates
    report["observed_common_anchor_span_days"]=span_days
    report["all_required_anchors_pass"]=all_required_anchors_pass
    report["historical_gate_min_days"]=60
    report["verdict"]=verdict
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True))
    print(json.dumps({
        "verdict":verdict,
        "common_pass_dates":common_pass_dates,
        "observed_common_anchor_span_days":span_days,
        "all_required_anchors_pass":all_required_anchors_pass,
        "economic_outcomes_opened":False,
        "ohlc_values_reported":False,
        "basis_calculated":False
    },sort_keys=True))

if __name__=="__main__":
    main()
