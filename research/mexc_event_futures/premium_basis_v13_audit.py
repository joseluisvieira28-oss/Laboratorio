#!/usr/bin/env python3
"""
MEXC Event Futures Premium Basis V1.3
Post-holdout integrity and robustness audit for the exact frozen five-cell family.

No October outcomes. No strategy retuning. Public MEXC sources only.
"""
import json, math, os, time
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
import requests

BASE="https://contract.mexc.com"
SYMBOL="MUSTOCK_USDT"
STEP=300
ROLL_SEC=24*3600
ROLL_MAX=288
ROLL_MIN=240

AUDIT_START=int(datetime(2026,4,1,tzinfo=timezone.utc).timestamp())
AUDIT_END=int(datetime(2026,10,1,tzinfo=timezone.utc).timestamp())
FETCH_START=AUDIT_START-2*24*3600
FETCH_END_RAW=AUDIT_END-2*STEP

CELLS=[
    {"id":"MU_10_Z1.0_FOLLOW","h":10,"th":1.0},
    {"id":"MU_10_Z1.5_FOLLOW","h":10,"th":1.5},
    {"id":"MU_10_Z2.0_FOLLOW","h":10,"th":2.0},
    {"id":"MU_30_Z1.5_FOLLOW","h":30,"th":1.5},
    {"id":"MU_30_Z2.0_FOLLOW","h":30,"th":2.0},
]
EXPECTED_SEP={
    "MU_10_Z1.0_FOLLOW":{"wins":901,"losses":603,"non_ties":1504},
    "MU_10_Z1.5_FOLLOW":{"wins":439,"losses":245,"non_ties":684},
    "MU_10_Z2.0_FOLLOW":{"wins":195,"losses":88,"non_ties":283},
    "MU_30_Z1.5_FOLLOW":{"wins":149,"losses":76,"non_ties":225},
    "MU_30_Z2.0_FOLLOW":{"wins":71,"losses":21,"non_ties":92},
}

def fetch_json(url,params,retries=5):
    last=None
    for i in range(retries):
        try:
            r=requests.get(url,params=params,timeout=30)
            r.raise_for_status()
            j=r.json()
            if isinstance(j,dict) and j.get("success") is True:
                return j
            last=RuntimeError(f"non-success payload: {j}")
        except Exception as e:
            last=e
        time.sleep(0.5*(i+1))
    raise last

def fetch_series(kind):
    route="index_price" if kind=="index" else "fair_price"
    url=f"{BASE}/api/v1/contract/kline/{route}/{SYMBOL}"
    raw_seen=Counter()
    out={}
    requests_count=0
    out_of_boundary=[]
    t=FETCH_START-STEP
    chunk=5*24*3600
    last_raw=None
    raw_nonmonotonic=0
    while t<=FETCH_END_RAW:
        e=min(t+chunk,FETCH_END_RAW)
        j=fetch_json(url,{"interval":"Min5","start":t,"end":e})
        requests_count+=1
        d=j.get("data") or {}
        pairs=[]
        for s,p in zip(d.get("time") or [],d.get("close") or []):
            try:
                s=int(s); p=float(p)
            except Exception:
                continue
            pairs.append((s,p))
        # endpoint arrays should be monotonic within each response
        for s,p in pairs:
            if last_raw is not None and s<last_raw:
                raw_nonmonotonic+=1
            last_raw=s
            mapped=s+STEP
            raw_seen[mapped]+=1
            if mapped>=AUDIT_END:
                out_of_boundary.append(mapped)
                continue
            if FETCH_START<=mapped<AUDIT_END:
                out[mapped]=p
        t=e+STEP
        time.sleep(0.08)

    mapped=sorted(out)
    strict_increasing=all(mapped[i]>mapped[i-1] for i in range(1,len(mapped)))
    duplicates=sum(v-1 for v in raw_seen.values() if v>1 and FETCH_START<=next((k for k,val in raw_seen.items() if val==v),FETCH_START)<AUDIT_END)
    # exact duplicate count across all mapped timestamps inside boundary
    duplicates=sum(max(0,count-1) for ts,count in raw_seen.items() if FETCH_START<=ts<AUDIT_END)
    integrity={
        "requests":requests_count,
        "rows":len(out),
        "raw_duplicate_mapped_timestamp_count":duplicates,
        "raw_nonmonotonic_transition_count":raw_nonmonotonic,
        "canonical_strict_increasing":strict_increasing,
        "out_of_boundary_return_count":len(out_of_boundary),
        "first":mapped[0] if mapped else None,
        "last":mapped[-1] if mapped else None,
    }
    return out,integrity

def build_premium_z(index,fair):
    premium={}
    for t in sorted(set(index).intersection(fair)):
        ip=index[t]; fp=fair[t]
        if ip>0 and math.isfinite(ip) and math.isfinite(fp):
            premium[t]=(fp-ip)/ip*10000.0

    z={}
    window_meta={}
    q=deque()
    s=ss=0.0
    for t in sorted(premium):
        x=premium[t]
        q.append((t,x)); s+=x; ss+=x*x
        cutoff=t-ROLL_SEC+STEP
        while q and q[0][0]<cutoff:
            _,old=q.popleft(); s-=old; ss-=old*old
        while len(q)>ROLL_MAX:
            _,old=q.popleft(); s-=old; ss-=old*old
        n=len(q)
        if n<ROLL_MIN:
            continue
        mean=s/n
        var=(ss-n*mean*mean)/(n-1) if n>1 else 0.0
        if var<=0 or not math.isfinite(var):
            continue
        sd=math.sqrt(max(var,0.0))
        z[t]=(x-mean)/sd
        window_meta[t]={
            "window_first":q[0][0],
            "window_last":q[-1][0],
            "n":n,
        }
    return premium,z,window_meta

def aligned(start,end,h):
    sec=h*60
    t=((start+sec-1)//sec)*sec
    while t<end:
        yield t
        t+=sec

def month_key(t):
    return datetime.fromtimestamp(t,tz=timezone.utc).strftime("%Y-%m")

def quantile(xs,q):
    if not xs: return None
    ys=sorted(xs)
    if len(ys)==1: return ys[0]
    pos=(len(ys)-1)*q
    lo=int(math.floor(pos)); hi=int(math.ceil(pos))
    if lo==hi: return ys[lo]
    f=pos-lo
    return ys[lo]*(1-f)+ys[hi]*f

def summarize_outcomes(rows):
    w=sum(1 for r in rows if r["outcome"]=="WIN")
    l=sum(1 for r in rows if r["outcome"]=="LOSS")
    ties=sum(1 for r in rows if r["outcome"]=="TIE")
    n=w+l
    total=w+l+ties
    return {
        "wins":w,"losses":l,"ties":ties,"non_ties":n,
        "accuracy":(w/n) if n else None,
        "ev80":((w*0.8-l)/total) if total else None,
        "ev70":((w*0.7-l)/total) if total else None,
        "required_payout_for_ev0":(l/w) if w else None,
        "tie_rate":(ties/total) if total else None,
    }

def build_cell(index,z,window_meta,premium,cell):
    h=cell["h"]; th=cell["th"]
    signals=[]
    aligned_total=0
    missing_required=0
    forward_feature_violations=0
    outcome_timestamp_violations=0

    for t in aligned(AUDIT_START,AUDIT_END,h):
        aligned_total+=1
        after=t+h*60
        if after>=AUDIT_END:
            continue
        if t not in index or after not in index or t not in z or t not in window_meta:
            missing_required+=1
            continue

        meta=window_meta[t]
        if meta["window_last"]>t or meta["window_first"]>t:
            forward_feature_violations+=1
        if after!=t+h*60 or after<=t:
            outcome_timestamp_violations+=1

        zz=z[t]
        if abs(zz)<th or zz==0:
            continue

        sig=1 if zz>0 else -1
        fut=index[after]-index[t]
        if fut==0:
            outcome="TIE"
        elif (fut>0 and sig>0) or (fut<0 and sig<0):
            outcome="WIN"
        else:
            outcome="LOSS"

        signals.append({
            "t":t,"target_t":after,"signal":sig,"z":zz,"abs_z":abs(zz),
            "premium_bps":premium[t],
            "outcome":outcome,
            "hour_utc":datetime.fromtimestamp(t,tz=timezone.utc).hour,
            "weekday_utc":datetime.fromtimestamp(t,tz=timezone.utc).strftime("%a").upper(),
            "month":month_key(t),
        })

    # same-cell overlap check
    overlap_violations=0
    ordered=sorted(signals,key=lambda x:x["t"])
    for prev,cur in zip(ordered,ordered[1:]):
        if cur["t"]<prev["target_t"]:
            overlap_violations+=1

    # one-bar delay report-only, original signal preserved
    delayed=[]
    for r in ordered:
        enter=r["t"]+STEP
        target=enter+h*60
        if target>=AUDIT_END:
            continue
        if enter not in index or target not in index:
            continue
        fut=index[target]-index[enter]
        if fut==0:
            out="TIE"
        elif (fut>0 and r["signal"]>0) or (fut<0 and r["signal"]<0):
            out="WIN"
        else:
            out="LOSS"
        delayed.append({"outcome":out})

    monthly={}
    for m in [f"2026-{x:02d}" for x in range(4,10)]:
        monthly[m]=summarize_outcomes([r for r in ordered if r["month"]==m])

    sign_split={
        "POSITIVE_Z":summarize_outcomes([r for r in ordered if r["signal"]>0]),
        "NEGATIVE_Z":summarize_outcomes([r for r in ordered if r["signal"]<0]),
    }
    hour_counts=dict(sorted(Counter(r["hour_utc"] for r in ordered).items()))
    weekday_counts=dict(sorted(Counter(r["weekday_utc"] for r in ordered).items()))

    pvals=[r["premium_bps"] for r in ordered]
    az=[r["abs_z"] for r in ordered]
    diagnostics={
        "monthly":monthly,
        "sign_split":sign_split,
        "hour_utc_counts":hour_counts,
        "weekday_utc_counts":weekday_counts,
        "signal_quantiles":{
            "premium_bps":{"q05":quantile(pvals,.05),"q25":quantile(pvals,.25),"q50":quantile(pvals,.5),"q75":quantile(pvals,.75),"q95":quantile(pvals,.95)},
            "abs_z":{"q05":quantile(az,.05),"q25":quantile(az,.25),"q50":quantile(az,.5),"q75":quantile(az,.75),"q95":quantile(az,.95)},
        },
        "one_bar_delay_stress":summarize_outcomes(delayed),
    }

    return {
        "cell_id":cell["id"],"horizon_min":h,"z_threshold":th,
        "aligned_entries":aligned_total,
        "missing_required_source_at_aligned_entry":missing_required,
        "source_missing_fraction":(missing_required/aligned_total) if aligned_total else None,
        "feature_forward_violations":forward_feature_violations,
        "outcome_timestamp_violations":outcome_timestamp_violations,
        "same_cell_overlap_violations":overlap_violations,
        "signals":ordered,
        "overall":summarize_outcomes(ordered),
        "diagnostics":diagnostics,
    }

def main():
    outdir="artifacts/mexc_event_futures"
    os.makedirs(outdir,exist_ok=True)

    index,index_integrity=fetch_series("index")
    fair,fair_integrity=fetch_series("fair")
    premium,z,window_meta=build_premium_z(index,fair)

    cell_reports=[build_cell(index,z,window_meta,premium,c) for c in CELLS]

    # exact parent September reproduction
    reproduction=[]
    reproduction_ok=True
    for cr in cell_reports:
        sep=cr["diagnostics"]["monthly"]["2026-09"]
        expected=EXPECTED_SEP[cr["cell_id"]]
        ok=(sep["wins"]==expected["wins"] and sep["losses"]==expected["losses"] and sep["non_ties"]==expected["non_ties"])
        reproduction.append({"cell_id":cr["cell_id"],"expected":expected,"observed":{k:sep[k] for k in ["wins","losses","non_ties","accuracy"]},"match":ok})
        reproduction_ok=reproduction_ok and ok

    # simultaneous nested signal counts across frozen cells
    simultaneous=Counter()
    for cr in cell_reports:
        for r in cr["signals"]:
            simultaneous[r["t"]]+=1
    max_sim=max(simultaneous.values()) if simultaneous else 0
    simultaneous_hist=dict(sorted(Counter(simultaneous.values()).items()))

    hard_gates={
        "index_no_duplicate_mapped_timestamps":index_integrity["raw_duplicate_mapped_timestamp_count"]==0,
        "fair_no_duplicate_mapped_timestamps":fair_integrity["raw_duplicate_mapped_timestamp_count"]==0,
        "index_canonical_strict_increasing":index_integrity["canonical_strict_increasing"],
        "fair_canonical_strict_increasing":fair_integrity["canonical_strict_increasing"],
        "index_no_out_of_boundary_return":index_integrity["out_of_boundary_return_count"]==0,
        "fair_no_out_of_boundary_return":fair_integrity["out_of_boundary_return_count"]==0,
        "no_feature_forward_violations":all(c["feature_forward_violations"]==0 for c in cell_reports),
        "no_outcome_timestamp_violations":all(c["outcome_timestamp_violations"]==0 for c in cell_reports),
        "no_same_cell_overlap_violations":all(c["same_cell_overlap_violations"]==0 for c in cell_reports),
        "exact_september_parent_reproduction":reproduction_ok,
    }
    integrity_pass=all(hard_gates.values())

    # remove per-signal ledgers from JSON summary but write a compact ledger separately
    ledger=[]
    for cr in cell_reports:
        for r in cr["signals"]:
            ledger.append({
                "cell_id":cr["cell_id"],"horizon_min":cr["horizon_min"],"z_threshold":cr["z_threshold"],
                **r
            })

    report={
        "lab":"MEXC_EVENT_FUTURES_PREMIUM_BASIS_V1.3_AUDIT",
        "generated_at_utc":datetime.now(timezone.utc).isoformat(),
        "audit_entry_window":["2026-04-01T00:00:00Z","2026-10-01T00:00:00Z"],
        "october_outcomes_accessed":False,
        "source":{
            "symbol":SYMBOL,
            "index_integrity":index_integrity,
            "fair_integrity":fair_integrity,
            "index_rows":len(index),"fair_rows":len(fair),
            "premium_rows":len(premium),"z_rows":len(z),
        },
        "hard_integrity_gates":hard_gates,
        "parent_september_reproduction":reproduction,
        "nested_family":{
            "max_simultaneous_frozen_cell_signals":max_sim,
            "simultaneous_signal_count_histogram":simultaneous_hist,
            "interpretation":"Five thresholds/horizons are a nested correlated family, not five independent edges."
        },
        "cells":[{
            k:v for k,v in cr.items() if k!="signals"
        } for cr in cell_reports],
        "audit_classification":"INTEGRITY_PASS_ROBUSTNESS_REPORTED" if integrity_pass else "INTEGRITY_FAIL",
        "strategy_retuned":False,
        "new_threshold_selected":False,
        "exact_event_futures_settlement":"NOT_PROVEN",
        "historical_payout_series":"NOT_AVAILABLE",
        "live_trading_authorized":False,
    }

    jp=f"{outdir}/premium_basis_v13_audit.json"
    jl=f"{outdir}/premium_basis_v13_signal_ledger.jsonl"
    with open(jp,"w",encoding="utf-8") as f:
        json.dump(report,f,indent=2,sort_keys=True)
    with open(jl,"w",encoding="utf-8") as f:
        for row in sorted(ledger,key=lambda x:(x["t"],x["cell_id"])):
            f.write(json.dumps(row,sort_keys=True)+"\n")

    print(json.dumps({
        "audit_classification":report["audit_classification"],
        "hard_integrity_gates":hard_gates,
        "parent_september_reproduction":reproduction,
        "max_simultaneous_frozen_cell_signals":max_sim,
        "cells":[{
            "cell_id":c["cell_id"],
            "overall":c["overall"],
            "one_bar_delay_stress":c["diagnostics"]["one_bar_delay_stress"],
            "monthly":c["diagnostics"]["monthly"],
            "sign_split":c["diagnostics"]["sign_split"],
            "source_missing_fraction":c["source_missing_fraction"],
            "overlap_violations":c["same_cell_overlap_violations"],
        } for c in report["cells"]],
        "october_outcomes_accessed":False,
    },indent=2,sort_keys=True))
    print("WROTE",jp)
    print("WROTE",jl)

if __name__=="__main__":
    main()
