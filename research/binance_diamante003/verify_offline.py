#!/usr/bin/env python3
"""Standalone offline verifier of BINANCE-003 original public source journal."""
from __future__ import annotations
import hashlib
import json
import sys
from pathlib import Path
from book_core import SYMBOLS, replay

EVIDENCE=Path("binance003-evidence")

def main():
    result={"audit":"BINANCE-003_INDEPENDENT_OFFLINE_REPLAY","status":"REPLAY_BLOCKED","no_network":True}
    try:
        manifest=EVIDENCE/"manifest.json"
        sig=EVIDENCE/"manifest.sha256"
        journal=EVIDENCE/"journal.jsonl"
        expected=sig.read_text().split()[0]
        if hashlib.sha256(manifest.read_bytes()).hexdigest()!=expected:
            raise ValueError("MANIFEST_SHA256_MISMATCH")
        m=json.loads(manifest.read_text())
        if hashlib.sha256(journal.read_bytes()).hexdigest()!=m["journal_sha256"]:
            raise ValueError("JOURNAL_RAW_SHA256_MISMATCH")
        r=replay(journal)
        if r["last_chain_hash"]!=m["journal_chain_head"] or r["events"]!=m["journal_events"]:
            raise ValueError("JOURNAL_CHAIN_OR_EVENT_COUNT_MISMATCH")
        if set(m["symbols"])!=set(SYMBOLS):
            raise ValueError("WRONG_SCOPE")
        for symbol in SYMBOLS:
            if r["books"][symbol]!=m["symbols"][symbol]:
                raise ValueError("REPLAYER_STATE_DIFFERS_FOR_"+symbol)
        if (m["status"]!="SOURCE_REPLAY_PASS_ONLY" or
            not m["replay_matches_original_state"]):
            raise ValueError("SOURCE_NOT_SCIENTIFICALLY_ACCEPTED")
        for symbol in SYMBOLS:
            s=m["symbols"][symbol]
            if s["status"]!="SYNCED" or s["depth_applied"]<10 or s["aggtrades"]<1:
                raise ValueError("INSUFFICIENT_STREAM_"+symbol)
        result.update({
            "status":"INDEPENDENT_REPLAY_PASS_SOURCE_ONLY",
            "source_frames":m["ws_frames_captured"],
            "events_replayed":r["events"],
            "sha256_journal":m["journal_sha256"],
            "final_chain":r["last_chain_hash"],
            "symbols":{s:{
                "depth_applied":r["books"][s]["depth_applied"],
                "aggregated_trades":r["books"][s]["aggtrades"],
                "last_update_id":r["books"][s]["last_update_id"]
            } for s in SYMBOLS}
        })
    except Exception as exc:
        result["status"]="REPLAY_BLOCKED"
        result["error"]=str(exc)[:300]
    EVIDENCE.mkdir(parents=True,exist_ok=True)
    dest=EVIDENCE/"independent_replay.json"
    dest.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0 if result["status"]=="INDEPENDENT_REPLAY_PASS_SOURCE_ONLY" else 2

if __name__=="__main__":
    sys.exit(main())
