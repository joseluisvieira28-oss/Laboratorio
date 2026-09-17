#!/usr/bin/env python3
"""Aggregate fixed AAVE reconstruction R0 shards into one bootstrap receipt."""
from __future__ import annotations

import glob
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

LAB_ID = "AAVE-LIQUIDATION-OVERHANG-001"
EXPECTED = [
    ("01", 16490000, 17119486),
    ("02", 17119487, 17748973),
    ("03", 17748974, 18378460),
    ("04", 18378461, 19007946),
    ("05", 19007947, 19637432),
    ("06", 19637433, 20266918),
    ("07", 20266919, 20896404),
    ("08", 20896405, 21525890),
]


def main() -> int:
    paths = sorted(glob.glob("downloaded_reconstruction_shards/**/shard_*.json", recursive=True))
    receipts = []
    for p in paths:
        with open(p, "r", encoding="utf-8") as f:
            receipts.append(json.load(f))

    by_id = {str(x.get("shard_id")): x for x in receipts}
    failure = None
    if len(by_id) != len(EXPECTED):
        failure = f"expected {len(EXPECTED)} shard receipts, got {len(by_id)}"

    event_counts = Counter()
    borrow_modes = Counter()
    borrow_total = 0
    transport = Counter()
    reserves = {}
    provider_transitions = defaultdict(list)
    shard_hashes = {}
    shard_summary = []

    if failure is None:
        for sid, start, end in EXPECTED:
            r = by_id.get(sid)
            if r is None:
                failure = f"missing shard {sid}"; break
            if r.get("classification") != "RECONSTRUCTION_R0_SHARD_PASS":
                failure = f"shard {sid} failed: {r.get('classification')} {r.get('failure')}"; break
            if int(r.get("from_block")) != start or int(r.get("to_block")) != end:
                failure = f"shard {sid} boundary mismatch"; break
            if bool(r.get("safety", {}).get("accessed_2025_or_2026")):
                failure = f"shard {sid} protected-period violation"; break

            event_counts.update(r.get("config_provider_event_counts", {}))
            borrow_modes.update(r.get("borrow_interest_rate_mode_counts", {}))
            borrow_total += int(r.get("borrow_event_count", 0))
            transport.update(r.get("transport_stats", {}))
            shard_hashes[sid] = r.get("rare_source_sha256")

            for asset, info in (r.get("reserves") or {}).items():
                if asset in reserves and reserves[asset] != info:
                    # ReserveInitialized is expected once per proxy reserve identity; conflicting
                    # bootstrap identities are provenance failures, not silently overwritten.
                    failure = f"conflicting ReserveInitialized identity for {asset}"; break
                reserves[asset] = info
            if failure:
                break
            for name, rows in (r.get("provider_transitions") or {}).items():
                provider_transitions[name].extend(rows)
            shard_summary.append({
                "shard_id": sid,
                "from_block": start,
                "to_block": end,
                "borrow_event_count": int(r.get("borrow_event_count", 0)),
                "reserve_initializations": int((r.get("config_provider_event_counts") or {}).get("ReserveInitialized", 0)),
            })

    for name in list(provider_transitions):
        provider_transitions[name] = sorted(provider_transitions[name], key=lambda x: int(x.get("block", 0)))

    classification = "RECONSTRUCTION_R0_BOOTSTRAP_PASS" if failure is None else "RECONSTRUCTION_ACQUISITION_TECHNICAL_FAILURE"
    receipt = {
        "lab_id": LAB_ID,
        "phase": "RECONSTRUCTION_R0_BOOTSTRAP_AGGREGATE_OUTCOME_BLIND",
        "classification": classification,
        "frozen_from_block": 16490000,
        "frozen_to_block": 21525890,
        "exact_shard_coverage": shard_summary,
        "config_provider_event_counts": dict(sorted(event_counts.items())),
        "reserve_count": len(reserves),
        "reserves": reserves,
        "provider_transitions": dict(provider_transitions),
        "borrow_event_count": borrow_total,
        "borrow_interest_rate_mode_counts": dict(sorted(borrow_modes.items())),
        "transport_stats": dict(transport),
        "shard_rare_source_sha256": shard_hashes,
        "failure": failure,
        "safety": {
            "source_values_decoded": True,
            "health_factor_computed": False,
            "overhang_computed": False,
            "future_liquidation_outcome_computed": False,
            "market_return_prices_opened": False,
            "returns_opened": False,
            "pnl_opened": False,
            "accessed_2025_or_2026": False,
            "live_trading": False,
            "exchange_mutation": False,
        },
    }
    out = Path("reconstruction_bootstrap_output")
    out.mkdir(parents=True, exist_ok=True)
    (out / "AAVE_LIQUIDATION_OVERHANG_001_RECONSTRUCTION_R0_BOOTSTRAP_V0_1.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "classification": classification,
        "reserve_count": len(reserves),
        "borrow_event_count": borrow_total,
        "borrow_interest_rate_modes": dict(borrow_modes),
        "health_factor_computed": False,
        "overhang_computed": False,
    }, sort_keys=True))
    return 0 if classification == "RECONSTRUCTION_R0_BOOTSTRAP_PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
