#!/usr/bin/env python3
"""BINANCE010 independent longer-session wrapper. Reuses immutable 004 code.
Only duration, 60-window loop bound, source byte caps and receipt path change.
No exchange order/private endpoint, no PnL reality claims.
"""
from __future__ import annotations
import argparse
import asyncio
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OLD=ROOT/"research"/"binance_diamante004"
sys.path.insert(0,str(OLD))

OUT=Path("binance010-evidence")
SECONDS=1800
WINDOWS=60
DECISION_SECONDS=1680
FRAME_CAP=250000
JOURNAL_CAP=220000000
STUDY="BINANCE010_FROZEN_004_RULE_30MIN_V01"
PINS={
    "research/binance_diamante004/PROTOCOL.md":"b1b8d2aa2b9dd4853e04671de0d96336ae895d1b",
    "research/binance_diamante004/capture_forward.py":"ef8a987e026656cd3a60d402761c21078dee3ca7",
    "research/binance_diamante004/study.py":"58cf6af9c0ba26da2ac9efa700c103b93c7580b5",
    "research/binance_diamante004/verify_offline.py":"33ca9731cbbb2d4f22db8d5309d4616bfe3ca616",
    "research/binance_diamante003/book_core.py":"9b2a92455d36dc251ec99a2754c07a7f91a9af91",
    "research/binance_diamante003/capture.py":"490ad52bef283dedb4036e8793f6892788803a0e",
}

def blob_sha(raw:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode("ascii")+bytes((0,))+raw).hexdigest()

def guard():
    import os
    if os.getenv("GITHUB_REPOSITORY_PRIVATE","").lower()=="true":
        raise RuntimeError("REPOSITORY_PRIVATE_BILLING_STOP")
    if os.getenv("GITHUB_REPOSITORY") and os.getenv("GITHUB_REPOSITORY")!="joseluisvieira28-oss/Laboratorio":
        raise RuntimeError("UNEXPECTED_REPO")
    if os.getenv("GITHUB_EVENT_NAME") and os.getenv("GITHUB_EVENT_NAME")!="pull_request":
        raise RuntimeError("UNEXPECTED_ACTION_EVENT_NO_RETRY")
    for path,sha in PINS.items():
        actual=blob_sha((ROOT/path).read_bytes())
        if actual!=sha:
            raise RuntimeError("ORIGINAL_004_SOURCE_CODE_DRIFT_"+path+"_"+actual)
    marker=ROOT/"research/binance_diamante010/requests/2026-11-23.txt"
    if not marker.is_file() or marker.read_text().strip()!="BINANCE010_ONE_ONLY_SOURCE_PILOT_UTC_DAY=2026-11-23":
        raise RuntimeError("MISSING_FROZEN_ONE_SHOT_MARKER")
    if SECONDS!=1800 or WINDOWS!=60 or DECISION_SECONDS!=1680:
        raise RuntimeError("FROZEN_DURATION_CHANGED")
    if not 0<DECISION_SECONDS+120<=SECONDS:
        raise RuntimeError("INSUFFICIENT_EXIT_BUFFER")
    return {"study":STUDY,"status":"FROZEN_ORIGINAL_SOURCE_BLOB_CHECK_PASS_ONLY",
            "original_pins":PINS,"source_host":"data-stream.binance.vision",
            "duration_post_sync_seconds":SECONDS,"windows_per_symbol":WINDOWS,
            "max_decision_seconds":DECISION_SECONDS,
            "journal_byte_cap":JOURNAL_CAP,"frame_cap":FRAME_CAP,
            "real_orders":0,"private_account_calls":0,"no_paid_api":True}

def setup():
    import capture_forward as cap
    import study
    cap.OUT=OUT
    cap.SECONDS_POST_SYNC=SECONDS
    cap.MAX_FRAMES=FRAME_CAP
    cap.MAX_JOURNAL_BYTES=JOURNAL_CAP
    study.OUT=OUT
    study.CAPTURE_NS=SECONDS*1_000_000_000
    study.LATEST_DECISION_NS=DECISION_SECONDS*1_000_000_000

    def extended_advance(self,arrival_ns):
        if self.t0_ns is None:return
        while (arrival_ns>=self.t0_ns+(self.idx+1)*study.WINDOW_NS
               and self.idx<WINDOWS):
            self._window_close(self.t0_ns+(self.idx+1)*study.WINDOW_NS)

    study.ProspectiveStudy._advance=extended_advance
    return cap,study

def write_json(name,obj):
    OUT.mkdir(exist_ok=True)
    dest=OUT/name
    dest.write_text(json.dumps(obj,sort_keys=True,indent=2)+"\n")
    (OUT/(name+".sha256")).write_text(hashlib.sha256(dest.read_bytes()).hexdigest()+"  "+name+"\n")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("phase",choices=("guard","capture","study","replay","audit"))
    args=p.parse_args()
    check=guard()
    if args.phase=="guard":
        print(json.dumps(check,indent=2))
        return 0
    cap,study=setup()
    if args.phase=="capture":
        write_json("binance010_code_gate.json",check)
        status=asyncio.run(cap.collect())
        return status
    if args.phase=="study":
        return study.main()
    if args.phase=="replay":
        import verify_offline
        return verify_offline.check()
    if args.phase=="audit":
        manifest=OUT/"source_manifest.json"
        verdict=OUT/"forward_verdict.json"
        ledger=OUT/"forward_ledger.json"
        replay=OUT/"independent_replay_verdict.json"
        a=json.loads(manifest.read_text())
        v=json.loads(verdict.read_text())
        e=json.loads(ledger.read_text())
        rr=json.loads(replay.read_text())
        if a["seconds_post_bridge_target"]!=SECONDS:
            raise RuntimeError("CAPTURE_DURATION_NOT_FROZEN")
        if a["status"]!="SOURCE_CAPTURE_PASS_NO_ECONOMIC_INFERENCE":
            raise RuntimeError("SOURCE_NOT_VALID")
        if rr["status"]!="RAW_SOURCE_AND_DETERMINISTIC_LEDGER_PASS_ONLY":
            raise RuntimeError("REPLAY_NOT_VALID")
        if v["windows_evaluated"]!=WINDOWS*3 or len(e["windows"])!=WINDOWS*3:
            raise RuntimeError("STUDY_REPLAYED_ONLY_16_OF_60_WINDOWS")
        if v["source_clock_invalid_frames"]!=0:
            raise RuntimeError("INVALID_SOURCE_EVENT_AGE")
        if any(x["allowed_before_cutoff"]!=(x["end_t0_seconds"]<=DECISION_SECONDS) for x in e["windows"]):
            raise RuntimeError("WRONG_DECISION_CUTOFF")
        if any(x["decision_t0_sec"]>DECISION_SECONDS for x in e["events"]):
            raise RuntimeError("POST_CUTOFF_SIGNAL")
        if v["real_fills"]!=0 or v["economic_go"] is not False:
            raise RuntimeError("UNAUTHORIZED_ECONOMIC_OR_FILL_CLAIM")
        with (OUT/"journal.jsonl").open(encoding="utf-8") as f:
            first=json.loads(next(f))
            last=first
            for line in f:last=json.loads(line)
        date_first=dt.datetime.fromtimestamp(first["utc_ns"]/1e9,dt.timezone.utc).date()
        date_last=dt.datetime.fromtimestamp(last["utc_ns"]/1e9,dt.timezone.utc).date()
        if date_first!=date_last:
            raise RuntimeError("CROSS_UTC_DAY_NO_INDEPENDENT_DAY")
        source_date=str(date_first)
        primary=v["groups"]["PRIMARY"]
        flow=v["groups"]["FLOW_ONLY_CONTROL"]
        baseline=v["groups"]["UNCONDITIONAL_BASELINE"]
        result={
            "study":STUDY,
            "status":"ONE_DAY_SOURCE_AND_HYPOTHETICAL_REPLAY_PASS_ECONOMIC_INCONCLUSIVE",
            "primary_utc_day":source_date,
            "single_day_not_20_independent_days":True,
            "source_ws_frames":a["ws_frames"],
            "source_journal_records":a["captured_journal_events"],
            "source_journal_sha256":a["journal_file_sha256"],
            "forward_decision_ledger_sha256":v["ledger_sha256"],
            "source_status":a["status"],
            "offline_replay_status":rr["status"],
            "completed_30s_symbol_windows":v["windows_evaluated"],
            "valid_30s_symbol_windows":v["window_valid"],
            "sell_pressure_windows":v["sell_pressure_windows"],
            "resilient_sell_pressure_windows":v["bid_resilience_pressure_windows"],
            "primary":primary,
            "flow_only_control":flow,
            "unconditional_baseline":baseline,
            "actual_orders":0,
            "actual_fills":0,
            "estimated_fee_verified_with_account":False,
            "source_depth_visibility_risk":True,
            "live_trading_go":False,
            "economic_go":False,
            "prospective_005_frozen_and_unmodified":True,
            "note":"Hypothetical quote walks not executions; 1 UTC day pilot, cannot meet >=20-day criterion"
        }
        write_json("binance010_one_shot_verdict.json",result)
        compact={
            "study":STUDY,"status":result["status"],
            "source_utc_day":source_date,
            "symbol_30s_windows":v["windows_evaluated"],
            "source_records":a["captured_journal_events"],
            "source_sha256":a["journal_file_sha256"],
            "primary_matured":primary["matured"],
            "primary_1000USDT_stress_net_bps_mean":
                 primary["hypothetical"]["1000_STRESS_5BPS"]["mean_net_bps"],
            "primary_positive_after_stress":
                 primary["hypothetical"]["1000_STRESS_5BPS"]["positive_count"],
            "flow_only_matured":flow["matured"],
            "baseline_matured":baseline["matured"],
            "economic_go":False,"real_fills":0
        }
        print(json.dumps(compact,sort_keys=True,indent=2))
        return 0
    return 2

if __name__=="__main__":raise SystemExit(main())
