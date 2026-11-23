#!/usr/bin/env python3
"""Independent source hash/chain + deterministic economic-shadow replication.
Uses same pre-frozen economic rules; NOT independent predictive validation.
No network, orders, account or new market observations.
"""
from __future__ import annotations
import hashlib
import json
import sys
from pathlib import Path
from study import OUT,run_study

def check():
    status={"audit":"BINANCE004_OFFLINE_RAW_REPLAY","status":"REPLAY_BLOCKED",
            "no_network":True,"no_trades":True,
            "independent_prediction_sample":False}
    try:
        src=OUT/"source_manifest.json"
        raw=src.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=(OUT/"source_manifest.sha256").read_text().split()[0]:
            raise ValueError("SOURCE_MANIFEST_SHA_MISMATCH")
        source=json.loads(raw)
        if source["status"]!="SOURCE_CAPTURE_PASS_NO_ECONOMIC_INFERENCE":
            raise ValueError("SOURCE_CAPTURE_NOT_ACCEPTED")
        journal=OUT/"journal.jsonl"
        if hashlib.sha256(journal.read_bytes()).hexdigest()!=source["journal_file_sha256"]:
            raise ValueError("RAW_SOURCE_JOURNAL_CHANGED")
        receipt=OUT/"forward_verdict.json"
        if hashlib.sha256(receipt.read_bytes()).hexdigest()!=(OUT/"forward_verdict.sha256").read_text().split()[0]:
            raise ValueError("VERDICT_SHA_MISMATCH")
        v=json.loads(receipt.read_text())
        ledger=OUT/"forward_ledger.json"
        if hashlib.sha256(ledger.read_bytes()).hexdigest()!=v["ledger_sha256"]:
            raise ValueError("ORIGINAL_SHADOW_LEDGER_SHA_MISMATCH")
        # Independent process/reopen of immutable journal reproduces deterministic
        # shadow outputs. The hypothesis and statistics implementation remain the SAME.
        recomputed,rows=run_study(journal)
        recoded=json.dumps(rows,sort_keys=True,indent=2)+"\n"
        if hashlib.sha256(recoded.encode()).hexdigest()!=v["ledger_sha256"]:
            raise ValueError("SOURCE_REPLAY_SHADOW_LEDGER_MISMATCH")
        for k,x in recomputed.items():
            if k not in ("source_journal_sha256","ledger_sha256") and x!=v.get(k):
                raise ValueError("RECOMPUTED_VERDICT_FIELD_DIFF_"+k)
        if recomputed["t0_monotonic_ns"]!=source["ready_monotonic_ns"]:
            raise ValueError("FROZEN_T0_MISMATCH")
        status.update({
            "status":"RAW_SOURCE_AND_DETERMINISTIC_LEDGER_PASS_ONLY",
            "source_sha256":source["journal_file_sha256"],
            "ledger_sha256":v["ledger_sha256"],
            "journal_events":source["captured_journal_events"],
            "decision_event_count":len(rows["events"]),
            "candles_or_future_external_reads":0,
            "predictive_economic_go":False,
            "validation_note":"Same code reproducibility is not an independent holdout"
        })
    except Exception as exc:
        status["error"]=str(exc)[:240]
    OUT.mkdir(exist_ok=True)
    p=OUT/"independent_replay_verdict.json"
    p.write_text(json.dumps(status,sort_keys=True,indent=2)+"\n")
    print(json.dumps(status,sort_keys=True,indent=2))
    return 0 if status["status"]=="RAW_SOURCE_AND_DETERMINISTIC_LEDGER_PASS_ONLY" else 2

if __name__=="__main__":
    sys.exit(check())
