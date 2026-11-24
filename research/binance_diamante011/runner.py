#!/usr/bin/env python3
"""BINANCE011 -- new frozen 30m source session, real lossless gzip tee, SAME 004 signal.
No exchange trading orders, private access, paid data or old experiment writes.
"""
from __future__ import annotations
import argparse
import asyncio
import datetime as dt
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"research"/"binance_diamante010"))
import runner as r10
from lossless_journal import (
    SegmentedJournal,verify_segments,sha_file,RAW_MAX,ARCHIVE_MAX,MAX_SEGMENTS,CHUNK_MAX_RAW
)

OUT=Path("binance011-evidence")
RELEASE=Path("binance011-release")
EXPECTED_DAY="2026-11-24"
EXPECTED_BRANCH="research/binance-diamante-011-segmented-source-20261124"
EXPERIMENT="BINANCE011_FROZEN_004_30MIN_LOSSLESS_JOURNAL_V01"
FRAMES=420000

def guard(check_day=True):
    base=r10.guard() # includes original 003/004 Git blob SHA checks.
    if r10.blob_sha((ROOT/"research/binance_diamante010/runner.py").read_bytes())!="4c58e496c048e8a4d032cfcd022995fa20ba21b7":
        raise RuntimeError("PINNED_010_TIMING_WRAPPER_CHANGED")
    marker=ROOT/"research/binance_diamante011/requests/2026-11-24.txt"
    if not marker.exists() or marker.read_text().strip()!="BINANCE011_ONE_SOURCE_CAPTURE_DAY_UTC=2026-11-24":
        raise RuntimeError("011_SINGLE_DAY_MARKER_MISSING_OR_CHANGED")
    if os.getenv("GITHUB_HEAD_REF") and os.getenv("GITHUB_HEAD_REF")!=EXPECTED_BRANCH:
        raise RuntimeError("UNEXPECTED_GITHUB_PR_SOURCE_BRANCH")
    if os.getenv("GITHUB_RUN_ATTEMPT") and os.getenv("GITHUB_RUN_ATTEMPT")!="1":
        raise RuntimeError("RERUN_NOT_AUTHORIZED")
    if check_day and dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")!=EXPECTED_DAY:
        raise RuntimeError("WRONG_FROZEN_011_UTC_DAY")
    if (r10.SECONDS,r10.WINDOWS,r10.DECISION_SECONDS)!=(1800,60,1680):
        raise RuntimeError("CHANGED_010_SAMPLE_HORIZON")
    if (RAW_MAX,ARCHIVE_MAX,MAX_SEGMENTS,CHUNK_MAX_RAW,FRAMES)!=(520000000,160000000,50,16000000,420000):
        raise RuntimeError("CHANGED_011_STORAGE_BUDGET")
    return {"study":EXPERIMENT,"status":"FROZEN_SOURCE_AND_SCIENCE_GUARD_PASS_ONLY",
            "original_010_guard":base,
            "new_utc_capture_day":EXPECTED_DAY,
            "full_source_duration_seconds":1800,
            "decision_horizon_seconds":1680,
            "uncompressed_original_hard_cap":RAW_MAX,
            "compressed_chunk_cap":CHUNK_MAX_RAW,
            "compressed_total_hard_cap":ARCHIVE_MAX,
            "frame_cap":FRAMES,
            "actual_orders":0,"real_fills":0,"live_go":False}

def setup():
    r10.OUT=OUT
    capture,study=r10.setup() # same 60-window no-lookahead 004 engine.
    capture.Journal=SegmentedJournal
    capture.MAX_FRAMES=FRAMES
    capture.MAX_JOURNAL_BYTES=RAW_MAX
    if capture.SECONDS_POST_SYNC!=1800:
        raise RuntimeError("WRONG_CAPTURE_DURATION")
    if study.CAPTURE_NS!=1800*10**9 or study.LATEST_DECISION_NS!=1680*10**9:
        raise RuntimeError("ORIGINAL_EXTENDED_STUDY_CLOCK_CHANGED")
    return capture,study

def write_json(name,obj):
    OUT.mkdir(exist_ok=True)
    p=OUT/name
    p.write_text(json.dumps(obj,sort_keys=True,indent=2,ensure_ascii=False)+"\n")
    (OUT/(name+".sha256")).write_text(sha_file(p)+"  "+name+"\n")

def one_shot_audit():
    src=json.loads((OUT/"source_manifest.json").read_text())
    verdict=json.loads((OUT/"forward_verdict.json").read_text())
    ledger=json.loads((OUT/"forward_ledger.json").read_text())
    replay=json.loads((OUT/"independent_replay_verdict.json").read_text())
    archive=json.loads((OUT/"segmented_archive_verification.json").read_text())
    if src["status"]!="SOURCE_CAPTURE_PASS_NO_ECONOMIC_INFERENCE" or not src["completed_source_window"]:
        raise RuntimeError("SOURCE_INCOMPLETE")
    if src["seconds_post_bridge_target"]!=1800:
        raise RuntimeError("SOURCE_DURATION_CHANGED")
    if not src["source_replay_exact"]:
        raise RuntimeError("ORIGINAL_JOURNAL_REPLAY_MISMATCH")
    if src.get("snapshot_count")!=3:
        raise RuntimeError("THREE_SNAPSHOTS_REQUIRED")
    if any(v.get("status")!="SYNCED" for v in src["source_books"].values()):
        raise RuntimeError("L2_BOOK_NOT_SYNCED")
    if archive["status"]!="LOSSLESS_SEGMENTED_COMPRESSION_SHA256_PASS":
        raise RuntimeError("ARCHIVE_BYTES_NOT_VERIFIED")
    if archive["raw_uncompressed_sha256"]!=src["journal_file_sha256"]:
        raise RuntimeError("LOSSLESS_SOURCE_SHA_MISMATCH")
    if replay["status"]!="RAW_SOURCE_AND_DETERMINISTIC_LEDGER_PASS_ONLY":
        raise RuntimeError("ORIGINAL_SCIENCE_REPLAY_FAILED")
    if verdict["source_clock_invalid_frames"]!=0:
        raise RuntimeError("EVENT_AGE_INVALID")
    if len(ledger["windows"])!=180 or verdict["windows_evaluated"]!=180:
        raise RuntimeError("EXPECTED_180_ORIGINAL_RULE_WINDOWS")
    if any(x["allowed_before_cutoff"]!=(x["end_t0_seconds"]<=1680) for x in ledger["windows"]):
        raise RuntimeError("DECISION_CUTOFF_NOT_LOCKED")
    if any(x["decision_t0_sec"]>1680 for x in ledger["events"]):
        raise RuntimeError("POST_FROZEN_CUTOFF_SIGNAL")
    if verdict["real_fills"]!=0 or verdict["economic_go"] is not False:
        raise RuntimeError("INVALID_NO_LIVE_GO_CLAIM")
    with (OUT/"journal.jsonl").open("rb") as fh:
        first=json.loads(fh.readline())
        last=first
        for line in fh:
            last=json.loads(line)
    first_day=dt.datetime.fromtimestamp(first["utc_ns"]/1e9,dt.timezone.utc).strftime("%Y-%m-%d")
    last_day=dt.datetime.fromtimestamp(last["utc_ns"]/1e9,dt.timezone.utc).strftime("%Y-%m-%d")
    if first_day!=EXPECTED_DAY or last_day!=EXPECTED_DAY:
        raise RuntimeError("SOURCE_NOT_EXACT_FROZEN_UTC_DAY")
    groups=verdict["groups"]
    result={
        "study":EXPERIMENT,
        "status":"SOURCE_AND_REPLAY_PASS_ONE_DAY_ECONOMIC_INCONCLUSIVE",
        "actual_orders":0,"real_fills":0,"live_trading_go":False,
        "economic_go":False,
        "independent_utc_days":1,
        "not_independent_of_same_day_005":True,
        "raw_source_utc_day":first_day,
        "source_journal_raw_sha256":src["journal_file_sha256"],
        "source_journal_chain_sha256":src["journal_chain_sha256"],
        "journal_ws_frames":src["ws_frames"],
        "journal_events":src["captured_journal_events"],
        "uncompressed_raw_bytes":archive["raw_byte_count"],
        "compressed_gzip_bytes":archive["compressed_byte_count"],
        "gzip_chunk_count":archive["gzip_chunks"],
        "compression_ratio":archive["compressed_vs_raw_ratio"],
        "all_original_byte_sha256_recovered":True,
        "original_004_offline_replay":replay["status"],
        "original_004_hypothetical_ledger_sha256":verdict["ledger_sha256"],
        "evaluated_windows":verdict["windows_evaluated"],
        "valid_windows":verdict["window_valid"],
        "sell_pressure_windows":verdict["sell_pressure_windows"],
        "bid_resilience_pressure_windows":verdict["bid_resilience_pressure_windows"],
        "groups":groups,
        "source_visibility_limited_to_top1000_plus_diffs":True,
        "published_original_uncompressed_market_bytes":False,
        "economic_note":"ONE NEW UTC DAY ONLY, cannot satisfy >=20 independent days or prove profits; static quotes, zero fills"
    }
    write_json("binance011_source_and_economic_verdict.json",result)
    print(json.dumps({
        "study":EXPERIMENT,"status":result["status"],
        "ws_frames":result["journal_ws_frames"],
        "valid_30s_symbol_windows":result["valid_windows"],
        "raw_bytes":result["uncompressed_raw_bytes"],
        "compressed_gzip_bytes":result["compressed_gzip_bytes"],
        "gzip_parts":result["gzip_chunk_count"],
        "raw_sha256":result["source_journal_raw_sha256"],
        "PRIMARY_matured":groups["PRIMARY"]["matured"],
        "PRIMARY_1000USDT_STRESS_mean_net_bps":groups["PRIMARY"]["hypothetical"]["1000_STRESS_5BPS"]["mean_net_bps"],
        "FLOW_ONLY_matured":groups["FLOW_ONLY_CONTROL"]["matured"],
        "BASELINE_matured":groups["UNCONDITIONAL_BASELINE"]["matured"],
        "economic_go":False,"actual_trades":0
    },sort_keys=True,indent=2))
    return 0

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("phase",choices=("guard","capture","verify-archive","study","replay","audit","package"))
    args=parser.parse_args()
    # Package may be run later after failure, but is still single same-day run;
    # guard code/time validity on every phase so no swapped experiment identity.
    g=guard()
    if args.phase=="guard":
        print(json.dumps(g,sort_keys=True,indent=2))
        return 0
    if args.phase=="package":
        result=verify_segments(OUT,remove_raw=True)
        RELEASE.mkdir(parents=True,exist_ok=True)
        # Explicit allowlist only; raw original journal NEVER enters public artifact.
        for src in sorted(OUT.iterdir()):
            if (src.is_file() and
                (src.name.endswith(".json") or src.name.endswith(".sha256")
                 or src.name.endswith(".jsonl.gz"))):
                shutil.copy2(src,RELEASE/src.name)
        if (RELEASE/"journal.jsonl").exists():
            raise RuntimeError("RAW_ORIGINAL_WOULD_BE_PUBLISHED")
        result["release_file_count"]=len(list(RELEASE.iterdir()))
        print(json.dumps(result,sort_keys=True,indent=2))
        return 0 if result["status"]=="LOSSLESS_SEGMENTED_COMPRESSION_SHA256_PASS" else 2
    if args.phase=="verify-archive":
        result=verify_segments(OUT,remove_raw=False)
        print(json.dumps(result,sort_keys=True,indent=2))
        return 0 if result["status"]=="LOSSLESS_SEGMENTED_COMPRESSION_SHA256_PASS" else 2
    capture,study=setup()
    if args.phase=="capture":
        write_json("binance011_code_guard.json",g)
        return asyncio.run(capture.collect())
    if args.phase=="study":
        return study.main()
    if args.phase=="replay":
        import verify_offline
        return verify_offline.check()
    if args.phase=="audit":
        return one_shot_audit()
    return 2

if __name__=="__main__":
    raise SystemExit(main())
