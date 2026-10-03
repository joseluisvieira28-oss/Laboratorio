#!/usr/bin/env python3
"""Merge OPTIONS-VOL-FWD-001 V0.2 source-only calibration chunks."""
import argparse,json,math
from pathlib import Path

SYMBOLS=("BTC","ETH")

def load(paths):
    out=[]
    for p in paths:
        for line in Path(p).read_text().splitlines():
            if line.strip(): out.append(json.loads(line))
    return out

def canon(x):
    return json.dumps(x,sort_keys=True,separators=(",",":"),allow_nan=False)

def p95(vals):
    s=sorted(vals)
    if not s:return None
    return s[math.ceil(.95*len(s))-1]

def merge(paths,out):
    raw=load(paths);dedup={};conflicts=[]
    for r in raw:
        key=(r.get("currency"),r.get("minute_start_ms"))
        if key[0] not in SYMBOLS or not isinstance(key[1],int):
            conflicts.append({"type":"INVALID_KEY","row":r});continue
        if key in dedup and canon(dedup[key])!=canon(r):
            conflicts.append({"type":"CONFLICTING_DUPLICATE","key":key})
        else:
            dedup[key]=r
    rows=sorted(dedup.values(),key=lambda r:(r["minute_start_ms"],r["currency"]))
    counts={};thresholds={}
    for s in SYMBOLS:
        sr=[r for r in rows if r["currency"]==s]
        valid=[r for r in sr if r.get("valid") is True]
        vals=[float(r["abs_skew_pp"]) for r in valid]
        counts[s]={"unique_minutes":len(sr),"valid_pairs":len(valid),"missing_or_invalid":len(sr)-len(valid)}
        thresholds[s]=p95(vals) if len(sr)>=1440 and len(valid)>=1200 else None
    ready=not conflicts and all(counts[s]["unique_minutes"]>=1440 and counts[s]["valid_pairs"]>=1200 for s in SYMBOLS)
    result={
      "family_id":"OPTIONS-VOL-FWD-001",
      "family_version":"0.2-calibration",
      "status":"READY_FOR_NUMERIC_ACTIVATION_FREEZE" if ready else ("BLOCKED_CONFLICT" if conflicts else "SOURCE_CALIBRATION_INCOMPLETE"),
      "raw_rows":len(raw),"unique_rows":len(rows),"counts":counts,
      "p95_abs_skew_pp":thresholds,"conflicts":conflicts,
      "threshold_committed":False,"mexc_accessed":False,"research_outcomes_opened":0
    }
    Path(out).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))
    if conflicts: raise SystemExit(2)

def selftest():
    rows=[]
    for s in SYMBOLS:
        for i in range(1440):
            valid=i<1250
            rows.append({"currency":s,"minute_start_ms":1_800_000_000_000+i*60000,
                         "valid":valid,"abs_skew_pp":float((i%100)+1)/100 if valid else None})
    p=Path("/tmp/options_v02_merge_selftest.jsonl")
    p.write_text("\n".join(json.dumps(r,sort_keys=True) for r in rows)+"\n")
    o="/tmp/options_v02_merge_result.json"
    merge([str(p)],o)
    j=json.loads(Path(o).read_text())
    assert j["status"]=="READY_FOR_NUMERIC_ACTIVATION_FREEZE"
    print("OPTIONS_V02_CALIBRATION_MERGE_SELFTEST_PASS; SYNTHETIC_ONLY; OUTCOMES_OPENED=0")

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--self-test",action="store_true")
    ap.add_argument("--input",action="append")
    ap.add_argument("--output")
    a=ap.parse_args()
    if a.self_test:selftest()
    else:
        if not a.input or not a.output:ap.error("--input and --output required")
        merge(a.input,a.output)
