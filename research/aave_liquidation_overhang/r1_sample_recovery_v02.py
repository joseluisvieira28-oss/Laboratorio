#!/usr/bin/env python3
"""Recover the frozen R1 borrower sample from canonical source-census receipts.

Outcome-blind. Reads only the already-preserved structural Borrow participant
identities from canonical run 35214027573 and applies the exact frozen sample rule.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from eth_hash.auto import keccak

LAB_ID = "AAVE-LIQUIDATION-OVERHANG-001"
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
EXPECTED_UNIQUE_BORROWERS = 30_691
EXPECTED_BORROW_LOGS = 204_952
SAMPLE_SIZE = 16


def main() -> int:
    outdir = Path("r1_sample_recovery_output")
    outdir.mkdir(parents=True, exist_ok=True)
    dst = outdir / "AAVE_LIQUIDATION_OVERHANG_001_R1_SAMPLE_RECOVERY_V0_2.json"
    receipt = {
        "lab_id": LAB_ID,
        "phase": "R1_SAMPLE_RECOVERY_FROM_CANONICAL_SOURCE_CENSUS_OUTCOME_BLIND",
        "classification": None,
        "failure": None,
        "canonical_source_census_run_id": 35214027573,
        "sample_rule": "first 16 unique Borrow.onBehalfOf addresses sorted by (keccak256(raw20), address)",
        "safety": {
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
    try:
        files = sorted(Path("downloaded_census_shards").rglob("shard_*.json"))
        if len(files) != 8:
            raise RuntimeError(f"expected 8 canonical census shard receipts, found {len(files)}")
        rows = [json.loads(p.read_text(encoding="utf-8")) for p in files]
        rows.sort(key=lambda x: int(x["from_block"]))
        ranges = [(int(x["from_block"]), int(x["to_block"])) for x in rows]
        if ranges != EXPECTED_RANGES:
            raise RuntimeError(f"canonical census shard ranges mismatch: {ranges}")

        borrowers: set[str] = set()
        borrow_logs = 0
        for row in rows:
            if row.get("lab_id") != LAB_ID or row.get("classification") != "SHARD_PASS":
                raise RuntimeError("non-canonical or non-pass census shard")
            safety = row.get("safety") or {}
            forbidden = [
                "economic_values_decoded", "health_factor_computed", "overhang_computed",
                "future_liquidation_outcome_computed", "market_prices_opened",
                "returns_opened", "pnl_opened", "accessed_2025_or_2026",
                "live_trading", "exchange_mutation",
            ]
            if any(bool(safety.get(k)) for k in forbidden):
                raise RuntimeError("source-census safety receipt violation")
            vals = ((row.get("participants_by_event") or {}).get("Borrow") or [])
            borrowers.update(str(x).lower() for x in vals)
            borrow_logs += int((row.get("event_counts") or {}).get("Borrow", 0))

        if borrow_logs != EXPECTED_BORROW_LOGS:
            raise RuntimeError(f"Borrow log count mismatch: {borrow_logs} != {EXPECTED_BORROW_LOGS}")
        if len(borrowers) != EXPECTED_UNIQUE_BORROWERS:
            raise RuntimeError(f"unique borrower count mismatch: {len(borrowers)} != {EXPECTED_UNIQUE_BORROWERS}")
        for a in borrowers:
            if not a.startswith("0x") or len(a) != 42:
                raise RuntimeError(f"invalid borrower identity: {a}")

        ranked = sorted(borrowers, key=lambda a: (keccak(bytes.fromhex(a[2:])), a))
        sample = ranked[:SAMPLE_SIZE]
        if len(sample) != SAMPLE_SIZE:
            raise RuntimeError("insufficient sample after canonical recovery")

        receipt.update({
            "classification": "R1_SAMPLE_RECOVERY_PASS",
            "unique_borrower_count": len(borrowers),
            "borrow_log_count": borrow_logs,
            "sample_borrowers": sample,
            "sample_sha256": hashlib.sha256("\n".join(sample).encode()).hexdigest(),
            "source_shard_ranges": EXPECTED_RANGES,
        })
    except Exception as exc:
        receipt["classification"] = "RECONSTRUCTION_ACQUISITION_TECHNICAL_FAILURE"
        receipt["failure"] = f"{type(exc).__name__}: {str(exc)[:1200]}"

    dst.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "classification": receipt["classification"],
        "unique_borrowers": receipt.get("unique_borrower_count"),
        "sample_size": len(receipt.get("sample_borrowers") or []),
        "sample_sha256": receipt.get("sample_sha256"),
        "health_factor_computed": False,
        "overhang_computed": False,
        "returns_opened": False,
        "pnl_opened": False,
    }, sort_keys=True))
    return 0 if receipt["classification"] == "R1_SAMPLE_RECOVERY_PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
