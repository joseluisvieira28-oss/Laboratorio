#!/usr/bin/env python3
"""BINANCE005 fixed-004 multi-day offline receipt audit. No internet or trading.
Usage: python research/binance_diamante005/rollup.py evidence_by_run/<run_id> ...
Each directory contains original extracted binance004-evidence/ raw files.
"""
from __future__ import annotations
import datetime as dt
import hashlib
import json
import random
import statistics
import sys
from collections import defaultdict
from pathlib import Path

from guard import FIRST,LAST

BOOTSTRAP_SEED=20261123
BOOTSTRAP_REPS=10000
MIN_PRIMARY_EVENTS=200
MIN_PRIMARY_DAYS=20
STRESS_KEY="STRESS_5BPS_net_bps"
REFERENCE_NOTIONAL="1000"

def check_shafile(path, sig):
    declared=sig.read_text().split()[0]
    if hashlib.sha256(path.read_bytes()).hexdigest()!=declared:
        raise ValueError("SHA256_MISMATCH_"+path.name)

def session(path):
    """Recheck raw & manifests; fail closed on any missing or modified receipt."""
    path=Path(path)
    guard=path/"binance005_daily_guard.json"
    if not guard.exists():
        raise ValueError("MISSING_BINANCE005_SOURCE_GUARD")
    declared=json.loads(guard.read_text())
    day=dt.date.fromisoformat(declared["utc_date"])
    if not FIRST<=day<=LAST:raise ValueError("OUTSIDE_PREDECLARED_DATES")
    run_id=int(path.name)
    record={
        "run_id":run_id,"marker_utc_date":day.isoformat(),"day":day.isoformat(),
        "source_status":"MISSING","status":"BLOCKED","events":[],"provenance":{}
    }
    src=path/"source_manifest.json"
    if not src.exists():return record
    check_shafile(src,path/"source_manifest.sha256")
    source=json.loads(src.read_text())
    record["source_status"]=source.get("status","UNKNOWN")
    j=path/"journal.jsonl"
    if not j.exists():return record
    if hashlib.sha256(j.read_bytes()).hexdigest()!=source["journal_file_sha256"]:
        raise ValueError("RAW_JOURNAL_HASH_MISMATCH")
    first_ts=None
    last_ts=None
    with j.open(encoding="utf-8") as f:
        for line in f:
            parsed=json.loads(line)
            timestamp=parsed["utc_ns"]
            if type(timestamp) is not int:raise ValueError("INVALID_JOURNAL_TIMESTAMP")
            if first_ts is None:first_ts=timestamp
            if last_ts is not None and timestamp<last_ts:
                # Snapshot done in a background thread may be journaled after another WS
                # frame with a later arrival timestamp, which is an actual data-quality gate.
                raise ValueError("RECORD_CLOCK_REVERSED")
            last_ts=timestamp
    if first_ts is None:return record
    observed_start=dt.datetime.fromtimestamp(first_ts/1e9,dt.timezone.utc).date()
    observed_end=dt.datetime.fromtimestamp(last_ts/1e9,dt.timezone.utc).date()
    record["provenance"]={
        "journal_sha256":source["journal_file_sha256"],
        "journal_entries":source["captured_journal_events"],
        "observed_utc_start":str(observed_start),"observed_utc_end":str(observed_end)
    }
    if observed_start!=day or observed_end!=day:
        record["status"]="INVALID_CROSS_DAY_OR_WRONG_DATE"
        return record
    if source.get("status")!="SOURCE_CAPTURE_PASS_NO_ECONOMIC_INFERENCE":
        record["status"]="SOURCE_BLOCKED"
        return record
    vr=path/"forward_verdict.json"
    if not vr.exists():record["status"]="MISSING_FORWARD_VERDICT";return record
    check_shafile(vr,path/"forward_verdict.sha256")
    verdict=json.loads(vr.read_text())
    lr=path/"forward_ledger.json"
    if hashlib.sha256(lr.read_bytes()).hexdigest()!=verdict["ledger_sha256"]:
        raise ValueError("FROZEN_LEDGER_HASH_MISMATCH")
    ledger=json.loads(lr.read_text())
    if verdict["source_journal_sha256"]!=source["journal_file_sha256"]:
        raise ValueError("SOURCE_MANIFEST_CHAIN_DISAGREEMENT")
    if verdict["status"]!="SOURCE_PASS_SMALL_PROSPECTIVE_SAMPLE_NO_LIVE_GO":
        record["status"]="FORWARD_VERDICT_SOURCE_INVALID"
        return record
    # Re-open the whole source and recompute the original scientific analysis for
    # each archived day. Intentional exact-rule replication, NOT an independent model.
    lib=Path(__file__).resolve().parent.parent/"binance_diamante004"
    if str(lib) not in sys.path:sys.path.insert(0,str(lib))
    from study import run_study
    recomputed,rows=run_study(j)
    if rows!=ledger or recomputed["status"]!=verdict["status"]:
        raise ValueError("FROZEN_SOURCE_REPLAY_DECISION_MISMATCH")
    if verdict.get("economic_go") is not False or verdict.get("real_fills")!=0:
        raise ValueError("UNAUTHORIZED_TRADING_OR_GO_CLAIM")
    record["status"]="SOURCE_AND_FROZEN_LEDGER_PASS"
    record["events"]=ledger["events"]
    record["provenance"]["ledger_sha256"]=verdict["ledger_sha256"]
    record["provenance"]["windows_valid"]=verdict["window_valid"]
    return record

def event_net_bps(event,scenario=STRESS_KEY):
    if event["status"]!="MATURED_HYPOTHETICAL_NOT_FILLED":
        return None
    return float(event["returns"][REFERENCE_NOTIONAL][scenario])

def cluster_lower_bound(by_day):
    """Day-level fixed-seed cluster bootstrap, resamples WHOLE days, not trades."""
    days=sorted(by_day)
    if len(days)<MIN_PRIMARY_DAYS:return None
    rng=random.Random(BOOTSTRAP_SEED)
    values=[]
    for _ in range(BOOTSTRAP_REPS):
        chosen=[days[rng.randrange(len(days))] for j in days]
        x=[p for d in chosen for p in by_day[d]]
        values.append(statistics.mean(x))
    values.sort()
    return values[int(BOOTSTRAP_REPS*0.05)]

def analyze(records, audit_today=None):
    audit_today=audit_today or dt.datetime.now(dt.timezone.utc).date()
    days={}
    duplicates=[]
    for row in sorted(records,key=lambda r:(r["day"],r["run_id"])):
        d=row["day"]
        if d in days:
            duplicates.append({"day":d,"run_id":row["run_id"],"excluded":True})
            continue
        days[d]=row # first attempt gets the day, even if it failed!
    by_group=defaultdict(list)
    by_day=defaultdict(list)
    independent_primary_days=set()
    for day,row in sorted(days.items()):
        if row["status"]!="SOURCE_AND_FROZEN_LEDGER_PASS":continue
        for e in row["events"]:
            val=event_net_bps(e)
            if val is None:continue
            by_group[e["kind"]].append(val)
            if e["kind"]=="PRIMARY":
                by_day[day].append(val)
                independent_primary_days.add(day)
    primary=by_group["PRIMARY"]
    source_days=sum(v["status"]=="SOURCE_AND_FROZEN_LEDGER_PASS" for v in days.values())
    stats={}
    for group in ("PRIMARY","FLOW_ONLY_CONTROL","UNCONDITIONAL_BASELINE"):
        nums=by_group[group]
        stats[group]={"matured":len(nums),
                      "mean_stress_net_bps":statistics.mean(nums) if nums else None,
                      "positive_count":sum(x>0 for x in nums)}
    lower=cluster_lower_bound(by_day) if len(primary)>=MIN_PRIMARY_EVENTS else None
    positive_gains_by_day={d:sum(max(v,0) for v in vals) for d,vals in by_day.items()}
    pos_total=sum(positive_gains_by_day.values())
    largest_share=(max(positive_gains_by_day.values())/pos_total if pos_total>0 else None)
    baseline_ok=bool(by_group["FLOW_ONLY_CONTROL"] and by_group["UNCONDITIONAL_BASELINE"]
        and primary and statistics.mean(primary)>statistics.mean(by_group["FLOW_ONLY_CONTROL"])
        and statistics.mean(primary)>statistics.mean(by_group["UNCONDITIONAL_BASELINE"]))
    ready=(len(primary)>=MIN_PRIMARY_EVENTS and len(independent_primary_days)>=MIN_PRIMARY_DAYS)
    all_gates=(ready and statistics.mean(primary)>0 and lower is not None
               and lower>0 and largest_share is not None and largest_share<=0.20
               and baseline_ok)
    if audit_today<=LAST and len(days)<(audit_today-FIRST).days+1:
        state="IN_PROGRESS_MISSING_CHECKINS"
    elif audit_today<=LAST:
        state="IN_PROGRESS"
    elif not ready:
        state="INCONCLUSIVE_INSUFFICIENT_PRIMARY"
    elif all_gates:
        state="SCIENTIFIC_LIMITED_GO_NO_LIVE_GO"
    else:
        state="ECONOMIC_GATE_NOT_PASSED"
    return {
        "study":"BINANCE-005-FROZEN-004-30DAY",
        "audit_utc_day":str(audit_today),
        "frozen_days":f"{FIRST}..{LAST}",
        "reported_distinct_days":len(days),
        "source_valid_days":source_days,
        "source_blocked_or_missing_days":sorted(d for d,x in days.items() if x["status"]!="SOURCE_AND_FROZEN_LEDGER_PASS"),
        "duplicates_excluded":duplicates,
        "primary_days_with_matured_signals":len(independent_primary_days),
        "economic_groups":stats,
        "min_primary_events":MIN_PRIMARY_EVENTS,
        "min_primary_distinct_days":MIN_PRIMARY_DAYS,
        "cluster_bootstrap_lower_95_bps":lower,
        "max_single_day_positive_gain_concentration":largest_share,
        "baseline_relative_win_gate":baseline_ok,
        "economic_go_scientific_limited":bool(all_gates),
        "real_fills":0,
        "live_trading_authorized":False,
        "status":state,
        "note":"Source/economic-shadow; actual personal fees, Swiss account eligibility, fills not verified"
    }

def main():
    if len(sys.argv)<2:raise SystemExit("USAGE: rollup.py <extracted_artifact_dir_per_run> ...")
    entries=[]
    for p in sys.argv[1:]:
        entries.append(session(p))
    print(json.dumps(analyze(entries),indent=2,sort_keys=True))
if __name__=="__main__":main()
