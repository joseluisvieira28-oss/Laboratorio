#!/usr/bin/env python3
from __future__ import annotations

import argparse, json, math, statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

EXPECTED_VERSION="0.3"
EXPECTED_THRESHOLD_COMMIT="289fddb48ffbe34421914d2356eb5fa7f7f20ea7"
SUPERSEDED_SEGMENTS={"2026-10-07_1600_1859"}
COOLDOWN_SEC=900
MIN_EVENTS=40
MIN_DATES=7
MIN_UNDERLYING=10
MAX_DATE_SHARE=0.35
MIN_SCAN_COMPLETENESS=0.99
MIN_EXEC_COMPLETENESS=0.95
PRIMARY_KEY="25"
PRIMARY_FEE_BPS=8.0
STRESS_FEE_BPS=12.0

def mean(xs): return sum(xs)/len(xs) if xs else None
def median(xs): return statistics.median(xs) if xs else None

def load_receipts(root):
    rows=[]
    for p in sorted(Path(root).glob("**/receipt_*.json")):
        try: rows.append((p,json.loads(p.read_text())))
        except Exception: pass
    return rows

def parse_triggers(trigger_dir):
    out={}
    if not trigger_dir:return out
    for p in sorted(Path(trigger_dir).glob("*.json")):
        try:
            j=json.loads(p.read_text()); seg=j["segment"]
            if seg in SUPERSEDED_SEGMENTS:continue
            st=datetime.fromisoformat(j["start"].replace("Z","+00:00"))
            en=datetime.fromisoformat(j["end"].replace("Z","+00:00"))
            out[seg]=int((en-st).total_seconds()//60)+1
        except Exception:
            continue
    return out

def valid_underlying_execution(asset,key=PRIMARY_KEY):
    if asset.get("ineligible_reason")=="FUNDING_WINDOW_INELIGIBLE":
        return None
    # A raw trigger with technical entry failure remains in the completeness denominator.
    if not asset.get("eligible") or not asset.get("entry_timing_valid") or not asset.get("exit_timing_valid"):
        return False
    ef=(asset.get("entry_fills") or {}).get(key) or {}
    xf=(asset.get("exit_fills") or {}).get(key) or {}
    r=ef.get("rich_short") or {}; c=ef.get("cheap_long") or {}
    xr=xf.get("rich_cover") or {}; xc=xf.get("cheap_sell") or {}
    return bool(r.get("fillable") and c.get("fillable") and xf.get("fillable") and xr.get("fillable") and xc.get("fillable"))

def asset_return(asset,fee_bps):
    ef=(asset["entry_fills"])[PRIMARY_KEY]
    xf=(asset["exit_fills"])[PRIMARY_KEY]
    r=ef["rich_short"]; c=ef["cheap_long"]
    xr=xf["rich_cover"]; xc=xf["cheap_sell"]
    rich_entry_conv=float(r["settle_to_usdt"])
    cheap_entry_conv=float(c["settle_to_usdt"])
    rich_exit_conv=float(xf["rich_exit_settle_to_usdt"])
    cheap_exit_conv=float(xf["cheap_exit_settle_to_usdt"])
    rich_entry=float(r["quote_notional_settle"]); rich_exit=float(xr["quote_notional_settle"])
    cheap_entry=float(c["quote_notional_settle"]); cheap_exit=float(xc["quote_notional_settle"])
    pnl=(rich_entry-rich_exit)*rich_exit_conv + (cheap_exit-cheap_entry)*cheap_exit_conv
    fee=(fee_bps/10000.0)*(rich_entry*rich_entry_conv+rich_exit*rich_exit_conv+cheap_entry*cheap_entry_conv+cheap_exit*cheap_exit_conv)
    exposure=rich_entry*rich_entry_conv+cheap_entry*cheap_entry_conv
    if exposure<=0:raise ValueError("BAD_EXPOSURE")
    return 10000.0*(pnl-fee)/exposure

def sign_test_p(values):
    n=len(values)
    wins=sum(1 for x in values if x>0)
    # Zero counts conservatively as a non-win.
    return sum(math.comb(n,k) for k in range(wins,n+1))/(2.0**n) if n else None

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",required=True)
    ap.add_argument("--trigger-dir")
    ap.add_argument("--out",required=True)
    a=ap.parse_args()

    source_conflicts=[]
    receipts=[]
    seen_segments={}
    for p,r in load_receipts(a.root):
        seg=r.get("segment")
        if seg in SUPERSEDED_SEGMENTS:continue
        if r.get("forward_version")!=EXPECTED_VERSION or r.get("threshold_receipt_commit")!=EXPECTED_THRESHOLD_COMMIT:
            source_conflicts.append({"file":str(p),"error":"WRONG_AUTHORITY"})
            continue
        if seg in seen_segments:
            source_conflicts.append({"segment":seg,"error":"DUPLICATE_SEGMENT_RECEIPT"})
            continue
        seen_segments[seg]=str(p); receipts.append(r)

    triggers=parse_triggers(a.trigger_dir)
    expected_total=sum(triggers.values()) if triggers else sum(int(r.get("expected_scan_minutes") or 0) for r in receipts)

    scans_by_ts={}
    duplicate_scan_conflicts=[]
    raw_events_by_ts={}
    duplicate_event_conflicts=[]
    for r in receipts:
        for s in r.get("scan_records") or []:
            ts=s.get("signal_close_utc")
            if ts in scans_by_ts and json.dumps(scans_by_ts[ts],sort_keys=True)!=json.dumps(s,sort_keys=True):
                duplicate_scan_conflicts.append(ts)
            else:scans_by_ts[ts]=s
        for ev in r.get("events") or []:
            ts=int(ev["timestamp"])
            if ts in raw_events_by_ts and json.dumps(raw_events_by_ts[ts],sort_keys=True)!=json.dumps(ev,sort_keys=True):
                duplicate_event_conflicts.append(ts)
            else:raw_events_by_ts[ts]=ev

    complete_scans=sum(1 for s in scans_by_ts.values() if s.get("complete"))
    scan_completeness=(complete_scans/expected_total) if expected_total else 0.0

    raw_events=[raw_events_by_ts[t] for t in sorted(raw_events_by_ts)]
    exec_den=0; exec_num=0
    for ev in raw_events:
        for asset in ev.get("assets") or []:
            v=valid_underlying_execution(asset)
            if v is None:continue
            exec_den+=1
            if v:exec_num+=1
    exec_completeness=(exec_num/exec_den) if exec_den else 1.0

    # Canonical global cooldown across segments.
    admitted=[]; last=None
    for ev in raw_events:
        # Need at least one funding-eligible underlying, regardless of execution completeness.
        elig=[x for x in ev.get("assets") or [] if x.get("ineligible_reason")!="FUNDING_WINDOW_INELIGIBLE"]
        if not elig:continue
        ts=int(ev["timestamp"])
        if last is not None and ts-last<COOLDOWN_SEC:continue
        admitted.append(ev); last=ts

    dates=[datetime.fromtimestamp(int(ev["timestamp"]),timezone.utc).date().isoformat() for ev in admitted]
    date_counts=Counter(dates)
    distinct_dates=len(date_counts)
    max_date_share=max(date_counts.values())/len(admitted) if admitted else None

    underlying_counts=Counter()
    for ev in admitted:
        for asset in ev.get("assets") or []:
            if valid_underlying_execution(asset):
                underlying_counts[str(asset.get("underlying"))]+=1

    sample_ready=(
        len(admitted)>=MIN_EVENTS and
        distinct_dates>=MIN_DATES and
        underlying_counts["BTC"]>=MIN_UNDERLYING and
        underlying_counts["ETH"]>=MIN_UNDERLYING and
        max_date_share is not None and max_date_share<=MAX_DATE_SHARE
    )
    data_ready=(
        scan_completeness>=MIN_SCAN_COMPLETENESS and
        exec_completeness>=MIN_EXEC_COMPLETENESS and
        not source_conflicts and not duplicate_scan_conflicts and not duplicate_event_conflicts
    )

    report={
        "family_id":"MEXC-MULTI-STABLE-BASIS-001",
        "authority":"V0.3",
        "receipt_files":len(receipts),
        "expected_scan_minutes":expected_total,
        "observed_unique_scan_minutes":len(scans_by_ts),
        "complete_scan_minutes":complete_scans,
        "scan_completeness":scan_completeness,
        "raw_event_timestamps":len(raw_events),
        "execution_completeness_denominator":exec_den,
        "execution_complete":exec_num,
        "execution_completeness":exec_completeness,
        "admitted_event_baskets":len(admitted),
        "distinct_utc_dates":distinct_dates,
        "underlying_complete_counts":dict(underlying_counts),
        "max_single_date_share":max_date_share,
        "source_conflicts":source_conflicts,
        "duplicate_scan_conflicts":sorted(set(duplicate_scan_conflicts)),
        "duplicate_event_conflicts":sorted(set(duplicate_event_conflicts)),
        "economic_metrics_opened":False,
    }

    if not sample_ready:
        report["verdict"]="PROSPECTIVE_ACCUMULATING"
        report["reason"]="FROZEN_MINIMUM_EVIDENCE_NOT_REACHED"
    elif not data_ready:
        report["verdict"]="BLOCKED_DATA_QUALITY"
        report["reason"]="FROZEN_SOURCE_OR_EXECUTION_COMPLETENESS_GATE_FAILED"
    else:
        # First lawful opening of economics once readiness gates are met.
        event_rows=[]
        invalid_after_ready=[]
        for ev in admitted:
            vals_p=[]; vals_s=[]
            for asset in ev.get("assets") or []:
                if not valid_underlying_execution(asset):continue
                try:
                    vals_p.append(asset_return(asset,PRIMARY_FEE_BPS))
                    vals_s.append(asset_return(asset,STRESS_FEE_BPS))
                except Exception as exc:
                    invalid_after_ready.append({"timestamp":ev["timestamp"],"underlying":asset.get("underlying"),"error":str(exc)})
            if vals_p:
                event_rows.append({
                    "timestamp":int(ev["timestamp"]),
                    "date":datetime.fromtimestamp(int(ev["timestamp"]),timezone.utc).date().isoformat(),
                    "primary_net_bps":mean(vals_p),
                    "stress_net_bps":mean(vals_s),
                })
        if invalid_after_ready or len(event_rows)!=len(admitted):
            report["verdict"]="BLOCKED_DATA_QUALITY"
            report["reason"]="ECONOMIC_EVENT_INCOMPLETE_AFTER_READINESS"
            report["invalid_after_ready"]=invalid_after_ready
        else:
            p=[x["primary_net_bps"] for x in event_rows]
            s=[x["stress_net_bps"] for x in event_rows]
            k=len(p)//2
            first=mean(p[:k]); second=mean(p[k:])
            loo={}
            for d in sorted(set(x["date"] for x in event_rows)):
                xs=[x["primary_net_bps"] for x in event_rows if x["date"]!=d]
                loo[d]=mean(xs)
            metrics={
                "mean_primary_net_bps":mean(p),
                "median_primary_net_bps":median(p),
                "chronological_half_means_primary_net_bps":[first,second],
                "sign_test_one_sided_p":sign_test_p(p),
                "leave_one_date_out_mean_primary_net_bps":loo,
                "mean_stress_net_bps":mean(s),
                "event_count":len(p),
            }
            passed=(
                metrics["mean_primary_net_bps"]>0 and
                metrics["median_primary_net_bps"]>0 and
                first is not None and first>0 and second is not None and second>0 and
                metrics["sign_test_one_sided_p"]<0.05 and
                all(v is not None and v>0 for v in loo.values()) and
                metrics["mean_stress_net_bps"]>0
            )
            report["economic_metrics_opened"]=True
            report["metrics"]=metrics
            report["verdict"]="SURVIVES_PROSPECTIVE_MULTI_STABLE_BASIS_V03" if passed else "NO_EDGE_PROSPECTIVE_AT_FROZEN_V03_GATE"

    out=Path(a.out); out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2,sort_keys=True))
    print(json.dumps(report,sort_keys=True))

if __name__=="__main__":
    main()
