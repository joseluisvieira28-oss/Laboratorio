#!/usr/bin/env python3
from __future__ import annotations

import argparse, csv, json, math, random
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

LAB_ID="ABSORPTION-FAILED-AUCTION-001"
BASELINE=288
Q_EXTREME=0.90
Q_LOW=0.30
Q_HIGH=0.70
HORIZONS=(5,15,30,60,240)
MIN_GROUP=100
MIN_DATES=30
MIN_COVERAGE=0.95
BOOT_N=10000


class LabError(ValueError): pass


def q(vals, p):
    vals=sorted(v for v in vals if math.isfinite(v))
    if not vals: return math.nan
    x=(len(vals)-1)*p
    lo=int(math.floor(x)); hi=int(math.ceil(x))
    if lo==hi: return vals[lo]
    w=x-lo
    return vals[lo]*(1-w)+vals[hi]*w


def median(vals): return q(vals,0.5)


def wilson_lower(k,n,z=1.959963984540054):
    if n<=0: return math.nan
    ph=k/n
    den=1+z*z/n
    centre=ph+z*z/(2*n)
    adj=z*math.sqrt((ph*(1-ph)+z*z/(4*n))/n)
    return (centre-adj)/den


def classify(rows):
    out=[]
    for i,row in enumerate(rows):
        rec=dict(row)
        rec["event_class"]="WARMUP"
        if i < BASELINE:
            out.append(rec); continue
        hist=rows[i-BASELINE:i]
        absd=[abs(r["agg_delta_pct"]) for r in hist]
        eff=[r["ltf_path_efficiency"] for r in hist]
        absret=[abs(r["bar_return_bps"]) for r in hist]
        thr_d=q(absd,Q_EXTREME); thr_lo=q(eff,Q_LOW); thr_hi=q(eff,Q_HIGH); thr_ret=q(absret,Q_LOW)
        d=1 if row["agg_delta_pct"]>0 else -1 if row["agg_delta_pct"]<0 else 0
        rec.update({"q90_abs_delta":thr_d,"q30_eff":thr_lo,"q70_eff":thr_hi,"q30_abs_ret":thr_ret})
        if d==0 or abs(row["agg_delta_pct"]) < thr_d:
            rec["event_class"]="NON_EXTREME"; out.append(rec); continue
        weak=(d*row["bar_return_bps"]<=0) or (abs(row["bar_return_bps"])<=thr_ret)
        if row["ltf_path_efficiency"]<=thr_lo and d*row["poc_migration_bps"]<=0 and weak:
            rec["event_class"]="FAILED_AUCTION"
        elif row["ltf_path_efficiency"]>=thr_hi and d*row["poc_migration_bps"]>0 and d*row["bar_return_bps"]>0:
            rec["event_class"]="EFFICIENT_ACCEPTANCE"
        else:
            rec["event_class"]="UNCLASSIFIED_EXTREME"
        rec["direction"]=d
        out.append(rec)
    return out


def bootstrap_ci(a,b,n=BOOT_N,seed=20260924):
    rng=random.Random(seed)
    diffs=[]
    for _ in range(n):
        aa=[a[rng.randrange(len(a))] for __ in range(len(a))]
        bb=[b[rng.randrange(len(b))] for __ in range(len(b))]
        diffs.append(median(bb)-median(aa))
    return q(diffs,.025), q(diffs,.975)


def adjudicate(rows,parent_state):
    if parent_state!="PASS_STRONG":
        return {"lab_id":LAB_ID,"classification":"SENSOR_BLOCKED","parent_state":parent_state}
    groups=defaultdict(list)
    for r in rows:
        if r.get("event_class") in ("FAILED_AUCTION","EFFICIENT_ACCEPTANCE"):
            groups[r["event_class"]].append(r)
    fa=groups["FAILED_AUCTION"]; ea=groups["EFFICIENT_ACCEPTANCE"]
    dates={r["utc_date"] for r in fa+ea}
    if len(fa)<MIN_GROUP or len(ea)<MIN_GROUP or len(dates)<MIN_DATES:
        return {"lab_id":LAB_ID,"classification":"INSUFFICIENT_SAMPLE","failed_auction_n":len(fa),"efficient_acceptance_n":len(ea),"distinct_utc_dates":len(dates)}
    for r in fa+ea:
        if "R60" not in r or not math.isfinite(r["R60"]):
            raise LabError("terminal adjudication requires finite R60 for every primary event")
    fa60=[r["R60"] for r in fa]; ea60=[r["R60"] for r in ea]
    mfa=median(fa60); mea=median(ea60)
    lo,hi=bootstrap_ci(fa60,ea60)
    rev=sum(x<0 for x in fa60); rev_rate=rev/len(fa60); wlo=wilson_lower(rev,len(fa60))
    survive=(mfa<0 and mea>0 and mea-mfa>0 and lo>0 and rev_rate>0.5 and wlo>0.5)
    return {
      "lab_id":LAB_ID,
      "classification":"MECHANISM_SURVIVES" if survive else "NO_MECHANISM",
      "failed_auction_n":len(fa),
      "efficient_acceptance_n":len(ea),
      "distinct_utc_dates":len(dates),
      "failed_median_R60":mfa,
      "efficient_median_R60":mea,
      "median_contrast_R60":mea-mfa,
      "bootstrap95_contrast":[lo,hi],
      "failed_reversal_rate_R60":rev_rate,
      "failed_reversal_wilson_lower95":wlo,
      "live_trading_authority":"NONE"
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--parent-state",required=True)
    ap.add_argument("--features")
    ap.add_argument("--out")
    args=ap.parse_args()
    if args.parent_state!="PASS_STRONG":
        result=adjudicate([],args.parent_state)
    else:
        if not args.features: raise SystemExit("--features required after PASS_STRONG")
        raise SystemExit("Real-outcome loader intentionally not enabled in V0.1 freeze commit.")
    s=json.dumps(result,indent=2,sort_keys=True)
    if args.out: Path(args.out).write_text(s+"\n")
    print(s)

if __name__=="__main__": main()
