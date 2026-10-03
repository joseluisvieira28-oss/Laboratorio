#!/usr/bin/env python3
"""Merge LIQUIDATION-FLOW-FWD-001 forward calibration chunks, fail closed on conflicts."""
import argparse, hashlib, json, math
from pathlib import Path

SYMBOLS=("BTCUSDT","ETHUSDT")

def load(paths):
    rows=[]
    for p in paths:
        for line in Path(p).read_text().splitlines():
            if line.strip():
                rows.append(json.loads(line))
    return rows

def canonical(r):
    return json.dumps(r,sort_keys=True,separators=(",",":"),allow_nan=False)

def nearest_rank(values,q):
    s=sorted(values)
    if not s: return None
    return s[math.ceil(q*len(s))-1]

def merge(paths,out):
    raw=load(paths)
    dedup={}
    conflicts=[]
    for r in raw:
        key=(r.get("symbol"),r.get("minute_start_ms"))
        if key[0] not in SYMBOLS or not isinstance(key[1],int):
            conflicts.append({"type":"INVALID_KEY","row":r}); continue
        if key in dedup and canonical(dedup[key])!=canonical(r):
            conflicts.append({"type":"CONFLICTING_DUPLICATE","key":key})
        else:
            dedup[key]=r
    rows=sorted(dedup.values(),key=lambda r:(r["minute_start_ms"],r["symbol"]))
    counts={}
    thresholds={}
    for s in SYMBOLS:
        sr=[r for r in rows if r["symbol"]==s]
        healthy=[r for r in sr if r.get("healthy") is True]
        nonzero=[r for r in healthy if isinstance(r.get("total_notional_proxy"),(int,float))
                 and r["total_notional_proxy"]>0]
        vals=[float(r["total_notional_proxy"]) for r in nonzero]
        counts[s]={
            "unique_bins":len(sr),
            "healthy_bins":len(healthy),
            "nonzero_healthy_bins":len(nonzero),
        }
        thresholds[s]=nearest_rank(vals,.95) if len(healthy)>=1440 and len(nonzero)>=100 else None
    ready=not conflicts and all(counts[s]["healthy_bins"]>=1440 and counts[s]["nonzero_healthy_bins"]>=100 for s in SYMBOLS)
    result={
        "family_id":"LIQUIDATION-FLOW-FWD-001",
        "phase":"SOURCE_ONLY_CALIBRATION_MERGE",
        "status":"READY_FOR_NUMERIC_ACTIVATION_FREEZE" if ready else ("BLOCKED_CONFLICT" if conflicts else "CALIBRATION_INCOMPLETE"),
        "input_files":[str(p) for p in paths],
        "raw_rows":len(raw),
        "unique_rows":len(rows),
        "counts":counts,
        "p95_nonzero_total_notional_proxy":thresholds,
        "conflicts":conflicts,
        "threshold_committed":False,
        "mexc_accessed":False,
        "research_outcomes_opened":0,
    }
    Path(out).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))
    if conflicts: raise SystemExit(2)

def selftest():
    rows=[]
    for s in SYMBOLS:
        for i in range(1440):
            total=float(i+1) if i<120 else 0.0
            rows.append({"symbol":s,"minute_start_ms":1_800_000_000_000+i*60000,
                         "healthy":True,"total_notional_proxy":total})
    p=Path("/tmp/liq_cal_merge_selftest.jsonl")
    p.write_text("\n".join(json.dumps(r,sort_keys=True) for r in rows)+"\n")
    out="/tmp/liq_cal_merge_selftest_result.json"
    merge([str(p)],out)
    j=json.loads(Path(out).read_text())
    assert j["status"]=="READY_FOR_NUMERIC_ACTIVATION_FREEZE"
    assert all(j["counts"][s]["healthy_bins"]==1440 for s in SYMBOLS)
    print("LIQUIDATION_CALIBRATION_MERGE_SELFTEST_PASS; SYNTHETIC_ONLY; OUTCOMES_OPENED=0")

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--self-test",action="store_true")
    ap.add_argument("--input",action="append")
    ap.add_argument("--output")
    a=ap.parse_args()
    if a.self_test:
        selftest()
    else:
        if not a.input or not a.output: ap.error("--input and --output required")
        merge(a.input,a.output)
