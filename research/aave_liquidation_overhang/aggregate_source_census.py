#!/usr/bin/env python3
"""Aggregate fixed disjoint AAVE-LIQUIDATION-OVERHANG-001 census shards.

This script does not contact any data source. It adjudicates source coverage only.
No economic values, outcomes, returns or PnL are opened.
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

LAB_ID = "AAVE-LIQUIDATION-OVERHANG-001"
GLOBAL_FROM = 16_490_000
GLOBAL_TO = 21_525_890
MAX_TS = 1_735_689_599
EXPECTED_RANGES = [
    (16_490_000, 17_119_486),
    (17_119_487, 17_748_973),
    (17_748_974, 18_378_460),
    (18_378_461, 19_007_946),
    (19_007_947, 19_637_432),
    (19_637_433, 20_266_918),
    (20_266_919, 20_896_404),
    (20_896_405, 21_525_890),
]
MIN_REQUIRED = ["Borrow", "Repay", "LiquidationCall", "ReserveDataUpdated", "ReserveInitialized"]


def main() -> int:
    root = Path("downloaded_shards")
    files = sorted(root.rglob("shard_*.json"))
    failure = None
    receipts = []
    try:
        if len(files) != len(EXPECTED_RANGES):
            raise RuntimeError(f"expected {len(EXPECTED_RANGES)} shard receipts, found {len(files)}")
        for p in files:
            receipts.append(json.loads(p.read_text(encoding="utf-8")))
        receipts.sort(key=lambda r: int(r["from_block"]))
        got_ranges = [(int(r["from_block"]), int(r["to_block"])) for r in receipts]
        if got_ranges != EXPECTED_RANGES:
            raise RuntimeError(f"shard range mismatch: {got_ranges}")
        if receipts[0]["from_block"] != GLOBAL_FROM or receipts[-1]["to_block"] != GLOBAL_TO:
            raise RuntimeError("global envelope mismatch")
        for i, r in enumerate(receipts):
            if r.get("lab_id") != LAB_ID:
                raise RuntimeError("lab id mismatch")
            if r.get("classification") != "SHARD_PASS":
                raise RuntimeError(f"non-pass shard {r.get('shard_id')}: {r.get('classification')}")
            if int(r.get("terminal_header_block", -1)) != int(r["to_block"]):
                raise RuntimeError(f"incomplete terminal block for {r.get('shard_id')}")
            if r.get("last_timestamp") is not None and int(r["last_timestamp"]) > MAX_TS:
                raise RuntimeError("protected-period timestamp breach")
            safety = r.get("safety") or {}
            forbidden_true = [
                "economic_values_decoded", "health_factor_computed", "overhang_computed",
                "future_liquidation_outcome_computed", "market_prices_opened", "returns_opened",
                "pnl_opened", "accessed_2025_or_2026", "live_trading", "exchange_mutation",
            ]
            if any(bool(safety.get(k)) for k in forbidden_true):
                raise RuntimeError(f"safety violation in shard {r.get('shard_id')}")
            if bool(safety.get("log_data_requested")):
                raise RuntimeError("log.data was requested")
            if i and int(receipts[i-1]["to_block"]) + 1 != int(r["from_block"]):
                raise RuntimeError("gap or overlap between shards")
    except Exception as exc:
        failure = f"{type(exc).__name__}: {str(exc)[:1000]}"

    counts = Counter()
    users_by_event: dict[str, set[str]] = defaultdict(set)
    all_users: set[str] = set()
    liq_users: set[str] = set()
    unique_log_ids = 0
    first_ts = last_ts = None
    aggregate_hasher = hashlib.sha256()
    transport = Counter()

    if failure is None:
        for r in receipts:
            counts.update({k: int(v) for k, v in (r.get("event_counts") or {}).items()})
            for k, vals in (r.get("participants_by_event") or {}).items():
                users_by_event[k].update(vals)
            all_users.update(r.get("all_position_users") or [])
            liq_users.update(r.get("liquidated_users") or [])
            unique_log_ids += int(r.get("unique_log_ids", 0))
            if r.get("first_timestamp") is not None:
                x = int(r["first_timestamp"]); first_ts = x if first_ts is None else min(first_ts, x)
            if r.get("last_timestamp") is not None:
                x = int(r["last_timestamp"]); last_ts = x if last_ts is None else max(last_ts, x)
            for k, v in (r.get("transport_stats") or {}).items():
                transport[k] += int(v)
            aggregate_hasher.update(
                f"{r['from_block']}|{r['to_block']}|{r['unique_log_ids']}|{r['structural_sha256']}\n".encode()
            )

        if any(counts[x] <= 0 for x in MIN_REQUIRED):
            missing = [x for x in MIN_REQUIRED if counts[x] <= 0]
            failure = f"missing required historical event families: {missing}"
        elif unique_log_ids <= 0 or not all_users:
            failure = "empty global structural population"
        elif first_ts is None or last_ts is None or last_ts > MAX_TS:
            failure = "invalid global timestamp coverage"

    if failure is None:
        classification = "SOURCE_CENSUS_PASS"
    elif "missing required historical event families" in failure or "empty global" in failure:
        classification = "INSUFFICIENT_SOURCE_COVERAGE"
    elif "safety violation" in failure or "timestamp breach" in failure or "range mismatch" in failure or "gap or overlap" in failure:
        classification = "PROVENANCE_FAILURE"
    else:
        classification = "SOURCE_ACQUISITION_TECHNICAL_FAILURE"

    receipt = {
        "lab_id": LAB_ID,
        "phase": "SOURCE_CENSUS_ONLY_OUTCOME_BLIND",
        "probe_version": "0.1-sharded-aggregate",
        "classification": classification,
        "source": "SQD ethereum-mainnet Portal",
        "frozen_from_block": GLOBAL_FROM,
        "frozen_to_block": GLOBAL_TO,
        "hard_timestamp_ceiling": MAX_TS,
        "shard_ranges": EXPECTED_RANGES,
        "shards_received": len(receipts),
        "event_counts": dict(sorted(counts.items())),
        "unique_participants_by_event": {k: len(v) for k, v in sorted(users_by_event.items())},
        "unique_position_users": len(all_users),
        "unique_liquidated_users": len(liq_users),
        "unique_log_ids": unique_log_ids,
        "first_matching_timestamp": first_ts,
        "last_matching_timestamp": last_ts,
        "aggregate_structural_sha256": aggregate_hasher.hexdigest(),
        "transport_stats": dict(sorted(transport.items())),
        "failure": failure,
        "safety": {
            "log_data_requested": False,
            "economic_values_decoded": False,
            "health_factor_computed": False,
            "overhang_computed": False,
            "future_liquidation_outcome_computed": False,
            "market_prices_opened": False,
            "returns_opened": False,
            "pnl_opened": False,
            "accessed_2025_or_2026": False,
            "live_trading": False,
            "exchange_mutation": False,
        },
    }
    out = Path("source_census_output")
    out.mkdir(parents=True, exist_ok=True)
    p = out / "AAVE_LIQUIDATION_OVERHANG_001_SOURCE_CENSUS_RECEIPT_V0_1.json"
    p.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "lab_id": LAB_ID, "classification": classification,
        "unique_log_ids": unique_log_ids, "unique_position_users": len(all_users),
        "unique_liquidated_users": len(liq_users),
        "events_present": sorted(k for k,v in counts.items() if v > 0),
        "protected_period_firewall": "PASS" if not (last_ts and last_ts > MAX_TS) else "FAIL",
        "economic_values_decoded": False, "returns_opened": False, "pnl_opened": False,
    }, sort_keys=True))
    return 0 if classification == "SOURCE_CENSUS_PASS" else 2

if __name__ == "__main__":
    sys.exit(main())
