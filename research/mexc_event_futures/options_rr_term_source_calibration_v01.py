#!/usr/bin/env python3
"""OPTIONS-RR-TERM-FWD-001 V0.1 bounded source-only calibration chunk."""
import argparse, hashlib, json, math, time
from pathlib import Path

from priority_source_gates_v013 import Evidence, now_ms
from options_rr_term_source_gate_v01 import one_currency, CURRENCIES

def file_sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def p95(values):
    if not values:return None
    s=sorted(values)
    return s[math.ceil(.95*len(s))-1]

def compact(currency, minute_ms, row):
    if row.get("rr_term_pp") is None:
        return {
            "currency":currency,
            "minute_start_ms":minute_ms,
            "valid":False,
            "reason":"INVALID_OR_MISSING_DUAL_EXPIRY_SOURCE",
        }
    out={
        "currency":currency,
        "minute_start_ms":minute_ms,
        "valid":True,
        "rr_term_pp":float(row["rr_term_pp"]),
        "abs_rr_term_pp":abs(float(row["rr_term_pp"])),
        "cross_expiry_timestamp_spread_ms":int(row["cross_expiry_timestamp_spread_ms"]),
    }
    for bkey,name in (("short","SHORT"),("medium","MEDIUM")):
        b=row[bkey]
        by={x["option_type"]:x for x in b["selected_pair"]}
        out.update({
            f"{bkey}_expiry_ms":int(b["expiry_ms"]),
            f"{bkey}_dte_days":float(b["dte_days_at_metadata"]),
            f"{bkey}_rr_skew_pp":float(b["rr_skew_pp"]),
            f"{bkey}_call_instrument":by["call"]["instrument"],
            f"{bkey}_put_instrument":by["put"]["instrument"],
            f"{bkey}_call_delta":float(by["call"]["ticker"]["greeks"]["delta"]),
            f"{bkey}_put_delta":float(by["put"]["ticker"]["greeks"]["delta"]),
            f"{bkey}_call_mark_iv":float(by["call"]["ticker"]["mark_iv"]),
            f"{bkey}_put_mark_iv":float(by["put"]["ticker"]["mark_iv"]),
            f"{bkey}_call_raw_sha256":by["call"]["raw_sha256"],
            f"{bkey}_put_raw_sha256":by["put"]["raw_sha256"],
        })
    return out

def main(minutes,output,boundary_ms):
    if not 1<=minutes<=180:
        raise SystemExit("minutes must be 1..180 for frozen initial chunk")
    if boundary_ms>=now_ms():
        raise SystemExit("calibration boundary must precede collection")

    ev=Evidence(output)
    root=Path(output)
    rows=[];errors=[]
    first=((now_ms()//60000)+1)*60000

    while now_ms()<first:
        time.sleep(min(.5,max(.01,(first-now_ms())/1000)))

    for i in range(minutes):
        target=first+i*60000
        while now_ms()<target:
            time.sleep(min(.5,max(.01,(target-now_ms())/1000)))
        rid=f"cal-{i+1:04d}-{target}"
        for currency in CURRENCIES:
            try:
                row=one_currency(currency,ev,rid)
                rows.append(compact(currency,target,row))
            except Exception as exc:
                errors.append({
                    "minute_start_ms":target,"currency":currency,
                    "type":type(exc).__name__,"error":str(exc),
                })
                rows.append(compact(currency,target,{}))
        # no retry inside this UTC minute
        if i+1<minutes and now_ms()>=first+(i+1)*60000:
            errors.append({
                "minute_start_ms":target,
                "type":"ROUND_OVERRAN_NEXT_MINUTE",
                "finished_at_ms":now_ms(),
            })

    ledger=root/"source_calibration_rows.jsonl"
    with ledger.open("w",encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r,sort_keys=True,allow_nan=False)+"\n")
    ev.entries.append({"path":ledger.name,"sha256":file_sha(ledger),"bytes":ledger.stat().st_size})

    counts={}
    for c in CURRENCIES:
        cr=[r for r in rows if r["currency"]==c]
        valid=[r for r in cr if r.get("valid")]
        vals=[r["abs_rr_term_pp"] for r in valid]
        counts[c]={
            "minutes_observed":len(cr),
            "valid_dual_expiry_observations":len(valid),
            "missing_or_invalid":len(cr)-len(valid),
            "preview_p95_abs_rr_term_pp":p95(vals),
            "min_rr_term_pp":min((r["rr_term_pp"] for r in valid),default=None),
            "max_rr_term_pp":max((r["rr_term_pp"] for r in valid),default=None),
            "max_abs_rr_term_pp":max(vals,default=None),
        }
    receipt={
        "family_id":"OPTIONS-RR-TERM-FWD-001",
        "family_version":"0.1-calibration",
        "status":"SOURCE_CALIBRATION_INCOMPLETE",
        "boundary_ms":boundary_ms,
        "first_minute_ms":first,
        "minutes_requested":minutes,
        "counts":counts,
        "errors":errors,
        "threshold_committed":False,
        "mexc_accessed":False,
        "price_outcomes_opened":0,
        "event_futures_outcomes_opened":0,
        "directional_statistics_run":False,
    }
    ev.finish(receipt)

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--minutes",type=int,required=True)
    ap.add_argument("--output",required=True)
    ap.add_argument("--boundary-ms",type=int,required=True)
    a=ap.parse_args()
    main(a.minutes,a.output,a.boundary_ms)
