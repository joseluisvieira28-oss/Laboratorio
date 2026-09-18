#!/usr/bin/env python3
"""Derive the frozen R1 borrower sample from canonical Source Census shard receipts.

Outcome-blind transport remediation only. This replaces only the redundant Borrow
network traversal in r1_scaled_ledger_audit_v01.py. The selection rule is identical:
keccak256(raw 20-byte borrower address), then address, first 16.
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
SAMPLE_SIZE = 16


def main() -> int:
    outdir = Path("r1_audit_sample_output")
    outdir.mkdir(parents=True, exist_ok=True)
    dst = outdir / "AAVE_LIQUIDATION_OVERHANG_001_R1_AUDIT_SAMPLE_V0_2.json"
    receipt = {
        "lab_id": LAB_ID,
        "phase": "R1_AUDIT_SAMPLE_FROM_CANONICAL_CENSUS_OUTCOME_BLIND",
        "classification": None,
        "failure": None,
        "source_census_run_id": 35214027573,
        "sample_rule": "first 16 by (keccak256(raw 20-byte address), address)",
        "safety": {
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
        got_ranges = [(int(x["from_block"]), int(x["to_block"])) for x in rows]
        if got_ranges != EXPECTED_RANGES:
            raise RuntimeError(f"canonical census ranges mismatch: {got_ranges}")
        borrowers: set[str] = set()
        shard_meta = []
        for x in rows:
            if x.get("lab_id") != LAB_ID or x.get("classification") != "SHARD_PASS":
                raise RuntimeError("non-canonical census shard")
            vals = ((x.get("participants_by_event") or {}).get("Borrow") or [])
            for a in vals:
                a = str(a).lower()
                if not (a.startswith("0x") and len(a) == 42):
                    raise RuntimeError("invalid Borrow participant address")
                borrowers.add(a)
            shard_meta.append({
                "shard_id": x.get("shard_id"),
                "from_block": int(x["from_block"]),
                "to_block": int(x["to_block"]),
                "borrow_participant_count": len(vals),
                "structural_sha256": x.get("structural_sha256"),
            })
        if len(borrowers) != EXPECTED_UNIQUE_BORROWERS:
            raise RuntimeError(
                f"unique borrower count mismatch {len(borrowers)} != {EXPECTED_UNIQUE_BORROWERS}"
            )
        ranked = sorted(
            borrowers,
            key=lambda a: (keccak(bytes.fromhex(a[2:])), a),
        )
        sample = ranked[:SAMPLE_SIZE]
        receipt.update({
            "classification": "R1_AUDIT_SAMPLE_FREEZE_PASS",
            "unique_borrower_count": len(borrowers),
            "sample_borrowers": sample,
            "sample_sha256": hashlib.sha256("\n".join(sample).encode()).hexdigest(),
            "canonical_census_shards": shard_meta,
        })
    except Exception as exc:
        receipt["classification"] = "RECONSTRUCTION_ACQUISITION_TECHNICAL_FAILURE"
        receipt["failure"] = f"{type(exc).__name__}: {str(exc)[:1200]}"

    dst.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "classification": receipt["classification"],
        "unique_borrowers": receipt.get("unique_borrower_count"),
        "sample_size": len(receipt.get("sample_borrowers", [])),
        "sample_sha256": receipt.get("sample_sha256"),
        "health_factor_computed": False,
        "overhang_computed": False,
        "returns_opened": False,
        "pnl_opened": False,
    }, sort_keys=True))
    return 0 if receipt["classification"] == "R1_AUDIT_SAMPLE_FREEZE_PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
