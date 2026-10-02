#!/usr/bin/env python3
"""
MEXC Event Futures V0.8 — OPTIONS-SPOTPERP signal transfer.

Consumes immutable parent signal ledgers from prior GitHub Actions artifacts.
Uses public MEXC standard-futures BTC index Min5 history as an Event Futures outcome proxy.

Research only. No auth, no orders, no account mutation, no 2026 source access.
"""
import csv
import json
import math
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from scipy.stats import binomtest

BASE="https://contract.mexc.com"
SYMBOL="BTC_USDT"
HORIZONS=[10,30,60,1440]
P0=1/1.8
PAYOUT=0.80
BH_Q=0.05
Z95=1.959963984540054
STEP=300
MIN_DISC_N=500
MIN_OOS_N=250
MIN_COVERAGE=0.95
UTC=timezone.utc
NO_2026=int(datetime(2026,1,1,tzinfo=UTC).timestamp())

def find_one(root:Path,name:str)->Path:
    hits=list(root.rglob(name))
    if len(hits)!=1:
        raise RuntimeError(f"expected exactly one {name} under {root}, got {len(hits)}")
    return hits[0]

def read_parent_ledger(path:Path,expected_rows:int,stage:str):
    rows=[]
    with path.open(newline="",encoding="utf-8") as f:
        for r in csv.DictReader(f):
            d=datetime.fromisoformat(r["signal_date"]).date()
            pos=int(float(r["position"]))
            rows.append({"signal_date":d,"position":pos})
    if len(rows)!=expected_rows:
        raise RuntimeError(f"{stage}: expected {expected_rows} ledger rows, got {len(rows)}")
    if any(r["signal_date"].year>=2026 for r in rows):
        raise RuntimeError(f"{stage}: protected 2026 signal row")
    return rows

def fetch_json(url,params,retries=5):
    last=None
    for i in range(retries):
        try:
            r=requests.get(url,params=params,timeout=30)
            r.raise_for_status()
            j=r.json()
            if isinstance(j,dict) and j.get("success") is True:
                return j
            last=RuntimeError(f"non-success payload {j}")
        except Exception as e:
            last=e
        time.sleep(0.7*(i+1))
    raise last

def fetch_prices(start_ts,end_ts):
    if end_ts>=NO_2026:
        raise RuntimeError("FAIL-CLOSED attempted 2026 MEXC source request")
    url=f"{BASE}/api/v1/contract/kline/index_price/{SYMBOL}"
    out={}
    reqs=0
    chunk=5*24*3600
    raw_start=start_ts-STEP
    t=raw_start
    while t<=end_ts-STEP:
        e=min(t+chunk,end_ts-STEP)
        j=fetch_json(url,{"interval":"Min5","start":t,"end":e})
        reqs+=1
        d=j.get("data") or {}
        for s,p in zip(d.get("time") or [],d.get("close") or []):
            try:
                s=int(s); p=float(p)
            except Exception:
                continue
            if s>=NO_2026:
                raise RuntimeError("FAIL-CLOSED source returned 2026 row")
            mapped=s+STEP
            if start_ts<=mapped<=end_ts:
                out[mapped]=p
        t=e+STEP
        time.sleep(0.10)
    return out,reqs

def entry_ts(signal_date):
    d=signal_date+timedelta(days=1)
    return int(datetime(d.year,d.month,d.day,tzinfo=UTC).timestamp())

def wilson_lower(w,l):
    n=w+l
    if not n: return None
    p=w/n
    z2=Z95*Z95
    return (p+z2/(2*n)-Z95*math.sqrt((p*(1-p)+z2/(4*n))/n))/(1+z2/n)

def exact_p(w,l):
    n=w+l
    return None if not n else float(binomtest(w,n,P0,alternative="greater").pvalue)

def evaluate(parent_rows,prices,horizon):
    total_nonzero=sum(1 for r in parent_rows if r["position"]!=0)
    w=l=ties=missing=0
    year_stats={}
    quarter_stats={}
    for r in parent_rows:
        pos=r["position"]
        if pos==0:
            continue
        t=entry_ts(r["signal_date"])
        after=t+horizon*60
        if after>=NO_2026:
            raise RuntimeError("FAIL-CLOSED V0.8 outcome enters 2026")
        if t not in prices or after not in prices:
            missing+=1
            continue
        d=prices[after]-prices[t]
        if d==0:
            ties+=1
            continue
        win=(d>0 and pos>0) or (d<0 and pos<0)
        if win: w+=1
        else: l+=1
        y=str(r["signal_date"].year)
        ys=year_stats.setdefault(y,[0,0])
        ys[0 if win else 1]+=1
        q=(r["signal_date"].month-1)//3+1
        qk=f"{r['signal_date'].year}-Q{q}"
        qs=quarter_stats.setdefault(qk,[0,0])
        qs[0 if win else 1]+=1
    n=w+l
    resolved=w+l+ties
    coverage=resolved/total_nonzero if total_nonzero else 0.0
    acc=w/n if n else None
    annual_acc={k:(a/(a+b) if a+b else None) for k,(a,b) in year_stats.items()}
    quarterly_acc={k:(a/(a+b) if a+b else None) for k,(a,b) in quarter_stats.items()}
    ev=((w*PAYOUT-l)/(w+l+ties)) if (w+l+ties) else None
    return {
        "parent_nonzero_signals":total_nonzero,
        "wins":w,"losses":l,"ties":ties,"missing":missing,
        "resolved_including_ties":resolved,
        "coverage":coverage,
        "non_ties":n,
        "accuracy":acc,
        "wilson95_lower":wilson_lower(w,l),
        "p_value_vs_be80":exact_p(w,l),
        "annual_accuracy":annual_acc,
        "quarterly_accuracy":quarterly_acc,
        "ev80":ev,
        "required_payout_for_ev0":(l/w if w else None),
    }

def disc_eligible(r):
    years=[r["annual_accuracy"].get(str(y)) for y in (2021,2022,2023,2024)]
    source_ok=r["coverage"]>=MIN_COVERAGE
    stats_ok=(
        r["non_ties"]>=MIN_DISC_N and
        r["accuracy"] is not None and r["accuracy"]>P0 and
        r["wilson95_lower"] is not None and r["wilson95_lower"]>0.50 and
        sum(1 for x in years if x is not None and x>0.50)>=3 and
        r["p_value_vs_be80"] is not None
    )
    return source_ok, stats_ok

def bh_select(cells):
    eligible=[x for x in cells if x["source_ok"] and x["stats_eligible"]]
    eligible.sort(key=lambda x:x["discovery"]["p_value_vs_be80"])
    m=len(eligible); cutoff=None
    for rank,x in enumerate(eligible,1):
        if x["discovery"]["p_value_vs_be80"] <= rank/m*BH_Q:
            cutoff=x["discovery"]["p_value_vs_be80"]
    selected=[] if cutoff is None else [x for x in eligible if x["discovery"]["p_value_vs_be80"]<=cutoff]
    return selected,m,cutoff

def oos_pass(r):
    qacc=list(r["quarterly_accuracy"].values())
    return (
        r["coverage"]>=MIN_COVERAGE and
        r["non_ties"]>=MIN_OOS_N and
        r["accuracy"] is not None and r["accuracy"]>P0 and
        r["wilson95_lower"] is not None and r["wilson95_lower"]>0.50 and
        r["p_value_vs_be80"] is not None and r["p_value_vs_be80"]<0.05 and
        r["ev80"] is not None and r["ev80"]>0 and
        sum(1 for x in qacc if x is not None and x>0.50)>=3
    )

def main():
    ap=__import__("argparse").ArgumentParser()
    ap.add_argument("--discovery-artifact",required=True)
    ap.add_argument("--oos-artifact",required=True)
    ap.add_argument("--output",default="artifacts/mexc_event_futures")
    a=ap.parse_args()

    disc_root=Path(a.discovery_artifact)
    oos_root=Path(a.oos_artifact)
    outdir=Path(a.output); outdir.mkdir(parents=True,exist_ok=True)

    disc_path=find_one(disc_root,"OPTIONS_SPOTPERP_001_DISCOVERY_LEDGER_V01.csv")
    oos_path=find_one(oos_root,"OPTIONS_SPOTPERP_001_V21_2025_OOS_LEDGER_V01.csv")
    disc_rows=read_parent_ledger(disc_path,1210,"DISCOVERY")
    oos_rows=read_parent_ledger(oos_path,363,"OOS2025")

    all_rows=disc_rows+oos_rows
    entries=[entry_ts(r["signal_date"]) for r in all_rows if r["position"]!=0]
    start=min(entries)
    end=max(t+max(HORIZONS)*60 for t in entries)
    if end>=NO_2026:
        raise RuntimeError("FAIL-CLOSED required source would cross 2026 boundary")

    prices,reqs=fetch_prices(start,end)
    source={
        "requests":reqs,
        "rows":len(prices),
        "first_timestamp":min(prices) if prices else None,
        "last_timestamp":max(prices) if prices else None,
        "start_requested":start,
        "end_requested":end,
        "year_2026_accessed":False,
    }

    cells=[]
    for h in HORIZONS:
        r=evaluate(disc_rows,prices,h)
        source_ok,stats_ok=disc_eligible(r)
        cells.append({
            "horizon_min":h,
            "source_ok":source_ok,
            "stats_eligible":stats_ok,
            "discovery":r,
        })

    selected,m,cutoff=bh_select(cells)
    survivors=[]
    oos_results=[]
    for c in selected:
        r=evaluate(oos_rows,prices,c["horizon_min"])
        passed=oos_pass(r)
        item={"horizon_min":c["horizon_min"],"oos":r,"pass":passed}
        oos_results.append(item)
        if passed:
            survivors.append({
                "horizon_min":c["horizon_min"],
                "discovery":c["discovery"],
                "oos":r,
            })

    any_source_blocked=any(not x["source_ok"] for x in cells)
    if not prices or all(not x["source_ok"] for x in cells):
        verdict="SOURCE_BLOCKED_MEXC_INDEX_HISTORY"
    elif survivors:
        verdict="EVENT_FUTURES_PROXY_CANDIDATE__OPTIONS_SIGNAL_TRANSFER"
    else:
        verdict="NO_PROXY_SURVIVOR_AT_FROZEN_V08_GATE"

    report={
        "lab":"MEXC_EVENT_FUTURES_OPTIONS_SIGNAL_TRANSFER_V0.8",
        "generated_at_utc":datetime.now(UTC).isoformat(),
        "source":"MEXC_STANDARD_FUTURES_INDEX_PRICE_MIN5_PROXY_CLOSE_AT_BUCKET_END",
        "exact_event_futures":"NOT_PROVEN",
        "reference_payout":PAYOUT,
        "reference_break_even_accuracy":P0,
        "parent_discovery_rows":len(disc_rows),
        "parent_oos_rows":len(oos_rows),
        "parent_artifacts":{
            "discovery_run_id":34858777691,
            "discovery_artifact_id":10354131731,
            "oos_run_id":35231711508,
            "oos_artifact_id":10504812106,
        },
        "source_receipt":source,
        "discovery_cells":cells,
        "bh_eligible_count":m,
        "bh_cutoff_p":cutoff,
        "bh_selected":[{"horizon_min":x["horizon_min"],"discovery":x["discovery"]} for x in selected],
        "oos_results":oos_results,
        "oos_survivors":survivors,
        "year_2026_accessed":False,
        "verdict":verdict,
        "promotion_status":"NO_EXACT_EVENT_FUTURES_PROMOTION",
    }

    p=outdir/"options_signal_transfer_v08.json"
    p.write_text(json.dumps(report,indent=2,sort_keys=True),encoding="utf-8")
    compact={
        "verdict":verdict,
        "mexc_rows":source["rows"],
        "mexc_requests":source["requests"],
        "discovery_cells":[{
            "horizon_min":x["horizon_min"],
            "coverage":x["discovery"]["coverage"],
            "n":x["discovery"]["non_ties"],
            "accuracy":x["discovery"]["accuracy"],
            "wilson95_lower":x["discovery"]["wilson95_lower"],
            "p":x["discovery"]["p_value_vs_be80"],
            "source_ok":x["source_ok"],
            "stats_eligible":x["stats_eligible"],
        } for x in cells],
        "bh_eligible_count":m,
        "bh_selected_count":len(selected),
        "bh_cutoff_p":cutoff,
        "oos_results":[{
            "horizon_min":x["horizon_min"],
            "coverage":x["oos"]["coverage"],
            "n":x["oos"]["non_ties"],
            "accuracy":x["oos"]["accuracy"],
            "wilson95_lower":x["oos"]["wilson95_lower"],
            "p":x["oos"]["p_value_vs_be80"],
            "ev80":x["oos"]["ev80"],
            "pass":x["pass"],
        } for x in oos_results],
        "oos_survivor_count":len(survivors),
        "year_2026_accessed":False,
        "exact_event_futures":"NOT_PROVEN",
    }
    print(json.dumps(compact,indent=2,sort_keys=True))
    print("WROTE",p)

if __name__=="__main__":
    main()
