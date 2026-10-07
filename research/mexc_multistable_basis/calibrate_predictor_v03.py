#!/usr/bin/env python3
from __future__ import annotations

import hashlib, json, math, time
from datetime import datetime, timezone, timedelta
from pathlib import Path
import requests

CBASE="https://contract.mexc.com/api/v1/contract"
SBASE="https://api.mexc.com/api/v3"
UA={"User-Agent":"CryptoLab-MultiStable-Calibrator/0.3"}
ASSETS={
    "BTC":{"USDT":"BTC_USDT","USDC":"BTC_USDC","USD1":"BTC_USD1"},
    "ETH":{"USDT":"ETH_USDT","USDC":"ETH_USDC","USD1":"ETH_USD1"},
}
NORM={"USDC":"USDCUSDT","USD1":"USD1USDT"}
START=datetime(2026,9,29,tzinfo=timezone.utc)
END=datetime(2026,10,7,tzinfo=timezone.utc)
EXPECTED=int((END-START).total_seconds()//60)
MIN_COVERAGE=0.95
OUT=Path("artifacts/mexc_multistable_basis/calibration_v03/threshold_receipt.json")

def get(url,params=None,sleep=0.13):
    t=time.perf_counter()
    r=requests.get(url,params=params,headers=UA,timeout=20)
    dt=time.perf_counter()-t
    body=r.content
    try: j=r.json()
    except Exception: j=None
    ev={
        "status":r.status_code,
        "latency_ms":round(dt*1000,3),
        "sha256":hashlib.sha256(body).hexdigest(),
        "bytes":len(body),
        "url":r.url,
    }
    time.sleep(sleep)
    return r,j,ev

def contract_day(symbol,day):
    st=int(day.timestamp()); en=int((day+timedelta(days=1)).timestamp())-1
    r,j,ev=get(f"{CBASE}/kline/{symbol}",{"interval":"Min1","start":str(st),"end":str(en)})
    out={}
    ok=r.status_code==200 and isinstance(j,dict) and j.get("success") is True
    if ok:
        d=j.get("data") or {}
        for t,c in zip(d.get("time") or [],d.get("close") or []):
            out[int(t)]=float(c)
    return out,ev,ok

def spot_chunk(symbol,start_dt,minutes):
    st=int(start_dt.timestamp()*1000)
    en=int((start_dt+timedelta(minutes=minutes)).timestamp()*1000)-1
    r,j,ev=get(f"{SBASE}/klines",{"symbol":symbol,"interval":"1m","startTime":str(st),"endTime":str(en),"limit":1000})
    out={}
    ok=r.status_code==200 and isinstance(j,list)
    if ok:
        for row in j:
            if isinstance(row,list) and len(row)>=7:
                out[int(row[0])//1000]=float(row[4])
    return out,ev,ok

def spot_day(symbol,day):
    out={}; evidence=[]; ok=True
    for offset in (0,480,960):
        d,ev,good=spot_chunk(symbol,day+timedelta(minutes=offset),480)
        out.update(d); evidence.append(ev); ok=ok and good
    return out,evidence,ok

def nearest_rank_q(xs,q):
    if not xs: raise ValueError("EMPTY")
    ys=sorted(xs)
    rank=max(1,min(len(ys),math.ceil(q*len(ys))))
    return ys[rank-1],rank

def main():
    series={}
    evidence=[]
    day=START
    while day<END:
        for asset,legs in ASSETS.items():
            for coin,sym in legs.items():
                key=f"{asset}_{coin}"
                series.setdefault(key,{})
                d,ev,ok=contract_day(sym,day)
                evidence.append({"route":sym,"day":day.date().isoformat(),"ok":ok,**ev})
                series[key].update(d)
        for coin,sym in NORM.items():
            key=f"NORM_{coin}"
            series.setdefault(key,{})
            d,evs,ok=spot_day(sym,day)
            for ev in evs:
                evidence.append({"route":sym,"day":day.date().isoformat(),"ok":ok,**ev})
            series[key].update(d)
        day+=timedelta(days=1)

    receipt={
        "family_id":"MEXC-MULTI-STABLE-BASIS-001",
        "phase":"PREDICTOR_ONLY_CALIBRATION",
        "freeze_commit":"bbc8291d0302f6776f75cb19d8c62df16b68bf25",
        "calibration_start_utc":START.isoformat(),
        "calibration_end_exclusive_utc":END.isoformat(),
        "expected_minutes":EXPECTED,
        "minimum_coverage_fraction":MIN_COVERAGE,
        "assets":{},
        "economic_outcomes_opened":False,
        "forward_returns_calculated":False,
        "execution_pnl_calculated":False,
        "alternative_horizons_tested":False,
        "source_evidence":evidence,
    }

    all_pass=True
    for asset in ASSETS:
        keys=[f"{asset}_USDT",f"{asset}_USDC",f"{asset}_USD1","NORM_USDC","NORM_USD1"]
        common=set(range(int(START.timestamp()),int(END.timestamp()),60))
        for k in keys:
            common &= set(series[k].keys())
        common=sorted(common)
        coverage=len(common)/EXPECTED
        ranges=[]
        for t in common:
            p_usdt=series[f"{asset}_USDT"][t]
            p_usdc=series[f"{asset}_USDC"][t]*series["NORM_USDC"][t]
            p_usd1=series[f"{asset}_USD1"][t]*series["NORM_USD1"][t]
            if min(p_usdt,p_usdc,p_usd1)<=0:
                continue
            logs=[math.log(p_usdt),math.log(p_usdc),math.log(p_usd1)]
            ranges.append(10000.0*(max(logs)-min(logs)))
        q99,rank=nearest_rank_q(ranges,0.99) if ranges else (None,None)
        passed=coverage>=MIN_COVERAGE and len(ranges)==len(common) and q99 is not None
        all_pass=all_pass and passed
        receipt["assets"][asset]={
            "common_exact_minutes":len(common),
            "coverage_fraction":coverage,
            "valid_predictor_minutes":len(ranges),
            "q99_nearest_rank":q99,
            "q99_rank":rank,
            "calibration_source_gate_pass":passed,
        }

    receipt["verdict"]="CALIBRATION_THRESHOLD_PASS" if all_pass else "PROSPECTIVE_SOURCE_BLOCKED_CALIBRATION"
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True))
    print(json.dumps({
        "verdict":receipt["verdict"],
        "BTC":receipt["assets"]["BTC"],
        "ETH":receipt["assets"]["ETH"],
        "economic_outcomes_opened":False,
        "forward_returns_calculated":False,
        "execution_pnl_calculated":False,
    },sort_keys=True))

if __name__=="__main__":
    main()
