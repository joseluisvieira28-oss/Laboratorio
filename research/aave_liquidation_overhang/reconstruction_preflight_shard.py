#!/usr/bin/env python3
"""AAVE-LIQUIDATION-OVERHANG-001 reconstruction R0 fixed shard.

Transport-only sharding of the already-authorized reconstruction preflight.
Decodes only historical Aave protocol values needed for reconstruction provenance.
No health factor, overhang, future liquidation outcome, market return or PnL.
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter
from pathlib import Path

import reconstruction_preflight as rp

LAB_ID = rp.LAB_ID
MAX_TS = rp.MAX_TS


def main() -> int:
    shard_id = os.environ["SHARD_ID"]
    start = int(os.environ["SHARD_FROM_BLOCK"])
    end = int(os.environ["SHARD_TO_BLOCK"])
    if start < 16_490_000 or end > 21_525_890 or start > end:
        raise SystemExit("invalid frozen shard")

    # Reuse the frozen R0 source logic on a deterministic sub-envelope only.
    rp.FROM_BLOCK = start
    rp.TO_BLOCK = end
    stats = Counter()
    failure = None
    try:
        rare_counts, reserves, provider_transitions, rare_hash = rp.collect_rare_source(stats)
        borrow_total, borrow_modes, borrow_examples = rp.audit_borrow_modes(stats)
        classification = "RECONSTRUCTION_R0_SHARD_PASS"
    except Exception as exc:
        classification = "RECONSTRUCTION_ACQUISITION_TECHNICAL_FAILURE"
        failure = f"{type(exc).__name__}: {str(exc)[:800]}"
        rare_counts = Counter()
        reserves = {}
        provider_transitions = {}
        rare_hash = None
        borrow_total = 0
        borrow_modes = {}
        borrow_examples = {}

    receipt = {
        "lab_id": LAB_ID,
        "phase": "RECONSTRUCTION_R0_SHARD_OUTCOME_BLIND",
        "classification": classification,
        "shard_id": shard_id,
        "from_block": start,
        "to_block": end,
        "hard_timestamp_ceiling": MAX_TS,
        "config_provider_event_counts": dict(sorted(rare_counts.items())),
        "reserves": reserves,
        "provider_transitions": provider_transitions,
        "rare_source_sha256": rare_hash,
        "borrow_event_count": borrow_total,
        "borrow_interest_rate_mode_counts": borrow_modes,
        "borrow_mode_examples": borrow_examples,
        "transport_stats": dict(stats),
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
    out = Path("reconstruction_shards")
    out.mkdir(parents=True, exist_ok=True)
    (out / f"shard_{shard_id}.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "lab_id": LAB_ID,
        "shard_id": shard_id,
        "classification": classification,
        "borrow_event_count": borrow_total,
        "borrow_modes": borrow_modes,
        "reserve_initializations": int(rare_counts.get("ReserveInitialized", 0)),
        "health_factor_computed": False,
        "overhang_computed": False,
        "returns_opened": False,
        "pnl_opened": False,
    }, sort_keys=True))
    return 0 if classification == "RECONSTRUCTION_R0_SHARD_PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
