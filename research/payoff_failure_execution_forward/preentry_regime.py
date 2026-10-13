#!/usr/bin/env python3
"""Pre-entry descriptors only; never fit a filter or open sealed 2026 outcomes."""
from __future__ import annotations
import argparse,datetime as dt,json,math,statistics,sys
from pathlib import Path
H=3600000
BOUNDARY=1767225600000 # 2026-01-01T00 UTC; no 2026 permitted
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"payoff_40_10_btc_001"))
import engine

def table(src):
    if src.get("status")!="SOURCE_OK":raise ValueError("SOURCE_NOT_VERIFIED")
    bars=src["bars"]
    stamps=[int(b["t"]) for b in bars]
    if len(stamps)<202 or stamps[-1]>=BOUNDARY:raise ValueError("2026_OR_INSUFFICIENT_DATA")
    if any(b-a!=H for a,b in zip(stamps,stamps[1:])):raise ValueError("BAR_GAP")
    close=[float(x["close"]) for x in bars]
    sma200=engine.sma(close,200)
    up=[None]*len(close);dn=[None]*len(close)
    for i in range(1,len(close)):
        d=close[i]-close[i-1];up[i]=max(d,0);dn[i]=max(-d,0)
    au=engine.rma(up,14);ad=engine.rma(dn,14)
    out={}
    for i in range(201,len(close)):
        if sma200[i] is None or au[i] is None or ad[i] is None:continue
        past=[math.log(close[k]/close[k-1]) for k in range(i-19,i+1)]
        rsi=100 if ad[i]==0 else 100-100/(1+au[i]/ad[i])
        out[stamps[i]]={
            "preentry_sma200_distance_pct":100*(close[i]/sma200[i]-1),
            "preentry_20h_return_pct":100*(close[i]/close[i-20]-1),
            "preentry_realized_daily_vol_pct":100*statistics.pstdev(past)*math.sqrt(24),
            "preentry_rsi14":rsi}
    return out

def describe(trades,features):
    cols=("preentry_sma200_distance_pct","preentry_20h_return_pct",
          "preentry_realized_daily_vol_pct","preentry_rsi14")
    rows=[];missing=0
    for x in trades:
        f=features.get(int(x["entry_t"])-H)
        if f is None:missing+=1
        else:rows.append((f,float(x["net_pnl"])>0))
    return {"n_observed":len(rows),"missing":missing,
            "all":{k:statistics.mean(r[0][k] for r in rows) if rows else None for k in cols},
            "winners":{k:statistics.mean(r[0][k] for r in rows if r[1]) if any(r[1] for r in rows) else None for k in cols},
            "losers":{k:statistics.mean(r[0][k] for r in rows if not r[1]) if any(not r[1] for r in rows) else None for k in cols}}

def run(source,diagnostic):
    feats=table(source)
    if diagnostic.get("classification")!="EXPLORATORY_IN_SAMPLE_ZERO_PROMOTION":
        raise ValueError("DIAGNOSTIC_SOURCE_NOT_FROZEN")
    out={"classification":"RETRO_EXPLANATORY_PRE_ENTRY_NO_FILTER","source_manifest_count":len(source["manifests"]),"comparison":{}}
    for model in ("PARENT","4R"):
        trades=diagnostic["scenarios"]["BASE"][model]["ledger"]
        cohorts={"2022":[x for x in trades if dt.datetime.fromtimestamp(x["entry_t"]/1000,dt.timezone.utc).year==2022],
                 "2025":[x for x in trades if dt.datetime.fromtimestamp(x["entry_t"]/1000,dt.timezone.utc).year==2025],
                 "OTHER":[x for x in trades if dt.datetime.fromtimestamp(x["entry_t"]/1000,dt.timezone.utc).year not in (2022,2025)]}
        out["comparison"][model]={k:describe(v,feats) for k,v in cohorts.items()}
    return out

def main():
    p=argparse.ArgumentParser();p.add_argument("--source",type=Path,required=True)
    p.add_argument("--diagnostic",type=Path,required=True);p.add_argument("--output",type=Path,required=True)
    a=p.parse_args();src=json.loads(a.source.read_text());diag=json.loads(a.diagnostic.read_text())
    result=run(src,diag);a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))
if __name__=="__main__":main()
