#!/usr/bin/env python3
"""OPTIONS-VOL-FWD-001 V0.2 source-only forward calibration chunk."""
import argparse, hashlib, json, math, os, time
from pathlib import Path

from priority_source_gates_v013 import Evidence, now_ms
from options_pair_source_v013 import options_round

SYMBOLS=("BTC","ETH")

def sha_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def pair_row(currency,pair,minute_ms):
    if not pair.get("passed"):
        return {
            "currency":currency,
            "minute_start_ms":minute_ms,
            "valid":False,
            "reason":"INVALID_OR_MISSING_PAIR",
        }
    by={x["option_type"]:x for x in pair["selected_pair"]}
    if "call" not in by or "put" not in by:
        return {
            "currency":currency,
            "minute_start_ms":minute_ms,
            "valid":False,
            "reason":"PAIR_SIDE_MISSING",
        }
    c=by["call"]; p=by["put"]
    skew=float(p["ticker"]["mark_iv"])-float(c["ticker"]["mark_iv"])
    if not math.isfinite(skew):
        return {
            "currency":currency,
            "minute_start_ms":minute_ms,
            "valid":False,
            "reason":"NONFINITE_SKEW",
        }
    return {
        "currency":currency,
        "minute_start_ms":minute_ms,
        "valid":True,
        "expiry_ms":pair["expiry_ms"],
        "skew_pp":skew,
        "abs_skew_pp":abs(skew),
        "call_instrument":c["instrument"],
        "put_instrument":p["instrument"],
        "call_mark_iv":float(c["ticker"]["mark_iv"]),
        "put_mark_iv":float(p["ticker"]["mark_iv"]),
        "call_delta":float(c["ticker"]["greeks"]["delta"]),
        "put_delta":float(p["ticker"]["greeks"]["delta"]),
        "call_source_ts_ms":int(c["ticker"]["timestamp"]),
        "put_source_ts_ms":int(p["ticker"]["timestamp"]),
        "call_received_at_ms":int(c["received_at_ms"]),
        "put_received_at_ms":int(p["received_at_ms"]),
        "call_raw_sha256":c["raw_sha256"],
        "put_raw_sha256":p["raw_sha256"],
        "metadata_sha256":c["metadata_sha256"],
        "selection_summary_sha256":c["selection_summary_sha256"],
    }

def nearest_rank_p95(values):
    if not values: return None
    s=sorted(values)
    rank=math.ceil(.95*len(s))
    return s[rank-1]

def main(minutes,output,boundary_ms):
    if minutes<=0:
        raise SystemExit("minutes must be positive")
    if boundary_ms>=now_ms():
        raise SystemExit("boundary must precede collection")
    ev=Evidence(output)
    root=Path(output)
    rows=[]
    errors=[]
    first=((now_ms()//60000)+1)*60000
    end=first+minutes*60000

    while now_ms()<first:
        time.sleep(min(.5,max(.01,(first-now_ms())/1000)))

    for i in range(minutes):
        target=first+i*60000
        while now_ms()<target:
            time.sleep(min(.5,max(.01,(target-now_ms())/1000)))
        round_id=f"cal-{i+1:04d}-{target}"
        pairs,errs=options_round(ev,round_id)
        errors.extend(errs)
        for c in SYMBOLS:
            rows.append(pair_row(c,pairs.get(c,{"passed":False}),target))
        # Never retry inside the same minute.
        if i+1<minutes:
            next_target=first+(i+1)*60000
            if now_ms()>=next_target:
                errors.append({
                    "round":round_id,
                    "type":"ROUND_OVERRAN_NEXT_MINUTE",
                    "finished_at_ms":now_ms(),
                    "next_target_ms":next_target,
                })

    ledger=root/"source_calibration_rows.jsonl"
    with ledger.open("w",encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r,sort_keys=True,allow_nan=False)+"\n")
    ev.entries.append({"path":ledger.name,"sha256":sha_file(ledger),"bytes":ledger.stat().st_size})

    counts={}
    for c in SYMBOLS:
        cr=[r for r in rows if r["currency"]==c]
        valid=[r for r in cr if r.get("valid")]
        vals=[r["abs_skew_pp"] for r in valid]
        counts[c]={
            "minutes_observed":len(cr),
            "valid_pairs":len(valid),
            "missing_or_invalid":len(cr)-len(valid),
            "source_only_preview_p95_abs_skew_pp":nearest_rank_p95(vals),
            "min_skew_pp":min((r["skew_pp"] for r in valid),default=None),
            "max_skew_pp":max((r["skew_pp"] for r in valid),default=None),
            "max_abs_skew_pp":max(vals,default=None),
        }

    min_complete=all(counts[c]["minutes_observed"]>=1440 and counts[c]["valid_pairs"]>=1200 for c in SYMBOLS)
    status="SOURCE_CALIBRATION_READY_FOR_THRESHOLD_FREEZE" if min_complete and not errors else "SOURCE_CALIBRATION_INCOMPLETE"
    receipt={
        "family_id":"OPTIONS-VOL-FWD-001",
        "family_version":"0.2-calibration",
        "status":status,
        "boundary_ms":boundary_ms,
        "first_minute_ms":first,
        "minutes_requested":minutes,
        "counts":counts,
        "errors":errors,
        "threshold_committed":False,
        "event_futures_outcomes_opened":0,
        "mexc_data_accessed":False,
        "statistics_run":False,
        "safety":{
            "DERIBIT_PUBLIC_ONLY":True,
            "NO_AUTH":True,
            "NO_PRIVATE":True,
            "NO_MEXC":True,
            "NO_ORDERS":True,
            "NO_TRADING":True,
        },
    }
    ev.finish(receipt)
    print(json.dumps(receipt,indent=2,sort_keys=True))

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--minutes",type=int,required=True)
    ap.add_argument("--output",required=True)
    ap.add_argument("--boundary-ms",type=int,required=True)
    a=ap.parse_args()
    main(a.minutes,a.output,a.boundary_ms)
