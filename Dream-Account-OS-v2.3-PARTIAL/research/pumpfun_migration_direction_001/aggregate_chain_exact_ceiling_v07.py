#!/usr/bin/env python3
"""Aggregate all four mandatory PMD-001 Chain-Exact Ceiling V0.7 shards."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

EXPECTED_ROWS = 1012
EXPECTED_INDICES = set(range(EXPECTED_ROWS))
MIN_VIABLE = 1000


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-root", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    root = Path(args.input_root)
    details_files = sorted(root.rglob("chain_exact_ceiling_details.jsonl"))
    receipt_files = sorted(root.rglob("chain_exact_ceiling_shard_receipt.json"))
    rows: list[dict] = []
    shard_receipts: list[dict] = []
    malformed = 0
    for p in details_files:
        try:
            rows.extend(read_jsonl(p))
        except Exception:
            malformed += 1
    for p in receipt_files:
        try:
            shard_receipts.append(json.loads(p.read_text(encoding="utf-8")))
        except Exception:
            malformed += 1

    indices = [r.get("frozen_manifest_index") for r in rows]
    mints = [r.get("mint") for r in rows]
    valid_indices = [int(x) for x in indices if isinstance(x, int)]
    outcomes_closed = all(r.get("outcomes_opened") is False for r in rows)
    stage_ok = all(r.get("stage") == "CHAIN_EXACT_CEILING_V07_SHARD" for r in rows)
    parser_ok = all(r.get("boundary_parser_version") == "V07_MIGRATE_AND_MIGRATE_V2" for r in rows)
    shard_receipts_ok = (
        len(shard_receipts) == 4
        and all(r.get("stage") == "CHAIN_EXACT_CEILING_V07_SHARD" for r in shard_receipts)
        and all(r.get("boundary_parser_version") == "V07_MIGRATE_AND_MIGRATE_V2" for r in shard_receipts)
        and all(r.get("economic_outcomes_opened") is False for r in shard_receipts)
        and all(r.get("scientific_verdict_authority") is False for r in shard_receipts)
    )
    reconciliation_ok = (
        len(details_files) == 4 and len(rows) == EXPECTED_ROWS and len(valid_indices) == EXPECTED_ROWS
        and set(valid_indices) == EXPECTED_INDICES and len(set(valid_indices)) == EXPECTED_ROWS
        and len(set(mints)) == EXPECTED_ROWS and None not in mints
        and malformed == 0 and outcomes_closed and stage_ok and parser_ok and shard_receipts_ok
    )

    resolved = sum(bool(r.get("source_resolved")) for r in rows)
    with_success = sum(bool(r.get("ceiling_has_successful_preboundary_signature")) for r in rows)
    unresolved = EXPECTED_ROWS - resolved if len(rows) == EXPECTED_ROWS else None

    if not reconciliation_ok or resolved != EXPECTED_ROWS:
        verdict = "CHAIN_EXACT_CEILING_V07_UNRESOLVED"
    elif with_success >= MIN_VIABLE:
        verdict = "CHAIN_EXACT_CEILING_V07_VIABLE"
    else:
        verdict = "CHAIN_EXACT_CEILING_V07_INSUFFICIENT"

    sorted_rows = sorted(rows, key=lambda r: int(r.get("frozen_manifest_index", -1)))
    canon = "".join(json.dumps(r, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n" for r in sorted_rows)
    out = Path(args.out_dir); out.mkdir(parents=True, exist_ok=True)
    (out / "chain_exact_ceiling_v07_rows.jsonl").write_text(canon, encoding="utf-8")
    receipt = {
        "lab": "PMD-001",
        "stage": "CHAIN_EXACT_CEILING_V07",
        "economic_outcomes_opened": False,
        "expected_rows": EXPECTED_ROWS,
        "rows": len(rows),
        "details_files": len(details_files),
        "shard_receipts": len(shard_receipts),
        "malformed_inputs": malformed,
        "unique_indices": len(set(valid_indices)),
        "unique_mints": len(set(mints)),
        "full_index_set_reconciled": set(valid_indices) == EXPECTED_INDICES,
        "outcome_wall_intact": outcomes_closed,
        "parser_version_ok": parser_ok,
        "source_resolved_rows": resolved,
        "unresolved_rows": unresolved,
        "rows_with_successful_preboundary_signature": with_success,
        "minimum_viable": MIN_VIABLE,
        "rows_sha256": hashlib.sha256(canon.encode()).hexdigest(),
        "verdict": verdict,
    }
    (out / "chain_exact_ceiling_v07_receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if verdict == "CHAIN_EXACT_CEILING_V07_VIABLE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
