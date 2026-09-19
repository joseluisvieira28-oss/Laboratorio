#!/usr/bin/env python3
"""R1 scaled-ledger audit V0.2 operational remediation.

Scientific audit semantics remain those of r1_scaled_ledger_audit_v01.py.
Only borrower-universe acquisition is replaced by the canonical Source Census
shard receipts from run 35214027573.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from eth_hash.auto import keccak

import r1_scaled_ledger_audit_v01 as v

EXPECTED_BORROWERS = 30_691
EXPECTED_SHARDS = 8


def select_borrowers_from_canonical_census(stats: Counter[str]) -> tuple[list[str], int]:
    files = sorted(Path("downloaded_source_census_shards").rglob("shard_*.json"))
    if len(files) != EXPECTED_SHARDS:
        raise RuntimeError(f"expected {EXPECTED_SHARDS} canonical census shard receipts, found {len(files)}")

    borrowers: set[str] = set()
    shard_ids: set[str] = set()
    for p in files:
        obj = json.loads(p.read_text(encoding="utf-8"))
        if obj.get("lab_id") != v.LAB_ID:
            raise RuntimeError(f"wrong lab id in {p}")
        if obj.get("classification") != "SHARD_PASS":
            raise RuntimeError(f"non-pass canonical census shard {p}: {obj.get('classification')}")
        safety = obj.get("safety") or {}
        forbidden = [
            "economic_values_decoded", "health_factor_computed", "overhang_computed",
            "future_liquidation_outcome_computed", "market_prices_opened",
            "returns_opened", "pnl_opened", "accessed_2025_or_2026",
            "live_trading", "exchange_mutation",
        ]
        if any(bool(safety.get(k)) for k in forbidden) or bool(safety.get("log_data_requested")):
            raise RuntimeError(f"canonical census safety receipt violation in {p}")
        shard_id = str(obj.get("shard_id"))
        if shard_id in shard_ids:
            raise RuntimeError(f"duplicate source census shard id {shard_id}")
        shard_ids.add(shard_id)
        vals = ((obj.get("participants_by_event") or {}).get("Borrow") or [])
        borrowers.update(str(x).lower() for x in vals)

    if len(borrowers) != EXPECTED_BORROWERS:
        raise RuntimeError(f"canonical borrower-universe mismatch: {len(borrowers)} != {EXPECTED_BORROWERS}")

    ranked = sorted(borrowers, key=lambda a: (keccak(bytes.fromhex(a[2:])), a))
    sample = ranked[:v.SAMPLE_SIZE]
    if len(sample) != v.SAMPLE_SIZE:
        raise RuntimeError("insufficient canonical borrower sample")

    stats["borrower_universe_reused_from_canonical_census_shards"] = EXPECTED_SHARDS
    stats["borrower_network_rescan_skipped"] = 1
    return sample, len(borrowers)


def main() -> int:
    v.select_borrowers = select_borrowers_from_canonical_census
    rc = v.main()

    src = Path("r1_scaled_ledger_audit_output/AAVE_LIQUIDATION_OVERHANG_001_R1_SCALED_LEDGER_AUDIT_V0_1.json")
    if src.exists():
        obj = json.loads(src.read_text(encoding="utf-8"))
        obj["operational_remediation_version"] = "V0.2_CANONICAL_SOURCE_CENSUS_REUSE"
        obj["borrower_universe_source_run_id"] = 35214027573
        obj["canonical_r0_run_id"] = 35218275356
        obj["scientific_audit_semantics_changed"] = False
        obj["borrower_network_rescan_performed"] = False
        dst = src.with_name("AAVE_LIQUIDATION_OVERHANG_001_R1_SCALED_LEDGER_AUDIT_V0_2.json")
        dst.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
