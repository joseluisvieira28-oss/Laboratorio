#!/usr/bin/env python3
"""Fail-closed merger for OPTIONS-RR-TERM-FWD-001 source-only calibration chunks."""
import argparse,json,math
from pathlib import Path

CURRENCIES=("BTC","ETH")

def load(paths):
    rows=[]
    for p in paths:
        for line in Path(p).read_text().splitlines():
            if line.strip():
                rows.append(json.loads(line))
    return rows

def canon(x):
    return json.dumps(x,sort_keys=True,separators=(",",":"),allow_nan=False)

def p95(vals):
    s=sorted(vals)
    if not s:return None
    return s[math.ceil(.95*len(s))-1]

def merge(paths,out,boundary_ms):
    raw=load(paths);dedup={};conflicts=[]
    for r in raw:
        key=(r.get("currency"),r.get("minute_start_ms"))
        if key[0] not in CURRENCIES or not isinstance(key[1],int):
            conflicts.append({"type":"INVALID_KEY","row":r});continue
        if key[1]<=boundary_ms:
            conflicts.append({"type":"PRE_BOUNDARY_ROW","key":key});continue
        if key in dedup and canon(dedup[key])!=canon(r):
            conflicts.append({"type":"CONFLICTING_DUPLICATE","key":key})
        else:
            dedup[key]=r
    rows=sorted(dedup.values(),key=lambda r:(r["minute_start_ms"],r["currency"]))
    counts={};thresholds={}
    for c in CURRENCIES:
        cr=[r for r in rows if r["currency"]==c]
        valid=[r for r in cr if r.get("valid") is True]
        vals=[float(r["abs_rr_term_pp"]) for r in valid]
        counts[c]={
            "unique_minutes":len(cr),
            "valid_dual_expiry_observations":len(valid),
            "missing_or_invalid":len(cr)-len(valid)
        }
        thresholds[c]=p95(vals) if len(cr)>=1440 and len(valid)>=1200 else None
    ready=not conflicts and all(
        counts[c]["unique_minutes"]>=1440 and counts[c]["valid_dual_expiry_observations"]>=1200
        for c in CURRENCIES
    )
    result={
        "family_id":"OPTIONS-RR-TERM-FWD-001",
        "phase":"SOURCE_ONLY_CALIBRATION_MERGE",
        "status":"READY_FOR_NUMERIC_ACTIVATION_FREEZE" if ready else ("BLOCKED_CONFLICT" if conflicts else "SOURCE_CALIBRATION_INCOMPLETE"),
        "boundary_ms":boundary_ms,
        "raw_rows":len(raw),
        "unique_rows":len(rows),
        "counts":counts,
        "p95_abs_rr_term_pp":thresholds,
        "conflicts":conflicts,
        "threshold_committed":False,
        "mexc_accessed":False,
        "price_outcomes_opened":0,
        "event_futures_outcomes_opened":0
    }
    Path(out).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))
    if conflicts: raise SystemExit(2)

def selftest():
    boundary=1_800_000_000_000
    rows=[]
    for c in CURRENCIES:
        for i in range(1440):
            valid=i<1250
            rows.append({
                "currency":c,
                "minute_start_ms":boundary+60000*(i+1),
                "valid":valid,
                "abs_rr_term_pp":float((i%200)+1)/100 if valid else None
            })
    p=Path("/tmp/rrterm_merge_selftest.jsonl")
    p.write_text("\n".join(json.dumps(r,sort_keys=True) for r in rows)+"\n")
    out="/tmp/rrterm_merge_selftest_result.json"
    merge([str(p)],out,boundary)
    j=json.loads(Path(out).read_text())
    assert j["status"]=="READY_FOR_NUMERIC_ACTIVATION_FREEZE"
    assert all(j["counts"][c]["unique_minutes"]==1440 for c in CURRENCIES)
    assert all(j["counts"][c]["valid_dual_expiry_observations"]==1250 for c in CURRENCIES)
    print("RRTERM_CALIBRATION_MERGE_SELFTEST_PASS; SYNTHETIC_ONLY; OUTCOMES_OPENED=0")

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--self-test",action="store_true")
    ap.add_argument("--input",action="append")
    ap.add_argument("--output")
    ap.add_argument("--boundary-ms",type=int)
    a=ap.parse_args()
    if a.self_test:
        selftest()
    else:
        if not a.input or not a.output or a.boundary_ms is None:
            ap.error("--input --output --boundary-ms required")
        merge(a.input,a.output,a.boundary_ms)
