#!/usr/bin/env python3
"""Offline PMD-001 V0.7 boundary parser re-adjudication.

Consumes only persisted full-block evidence from frozen V0.6 Cross-Date run.
No RPC and no economic outcomes.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
from pathlib import Path

from chain_boundary_semantics_v07 import (
    is_actual_pool_creation_migration_v07,
    migration_variant_v07,
)
from source_rebuild_helius_v01 import bonding_curve_pda, sha256_json
from intrablock_boundary_probe_v05 import tx_signature

ART_RE = re.compile(r"PMD-001-chain-exact-v06-row-(\d+)$")
EXPECTED = set(range(20))


def artifact_index(p: Path):
    for q in [p, *p.parents]:
        m = ART_RE.match(q.name)
        if m:
            return int(m.group(1))
    return None


def scan_artifact(artifact_dir: Path) -> dict:
    summary_path = artifact_dir / "source_rebuild_summary.jsonl"
    parts = [json.loads(x) for x in summary_path.read_text(encoding="utf-8").splitlines() if x.strip()]
    if len(parts) != 1:
        raise RuntimeError(f"expected one summary row in {artifact_dir}, found {len(parts)}")
    old = parts[0]
    mint = old["mint"]
    pool = old["pool_address"]
    pda = old.get("bonding_curve_pda") or bonding_curve_pda(mint)
    blocks = sorted((artifact_dir / "blocks" / mint).glob("slot_*.json.gz"))
    candidates = []
    block_errors = 0
    for fp in blocks:
        with gzip.open(fp, "rt", encoding="utf-8") as f:
            evidence = json.load(f)
        block = evidence.get("block")
        if not isinstance(block, dict) or block.get("_rpc_error"):
            block_errors += 1
            continue
        slot = int(evidence.get("slot") if evidence.get("slot") is not None else fp.stem.split("_")[-1].split(".")[0])
        btime = block.get("blockTime")
        for tx_index, item in enumerate(block.get("transactions") or []):
            if not isinstance(item, dict):
                continue
            if not is_actual_pool_creation_migration_v07(item, mint, pda, pool):
                continue
            candidates.append({
                "signature": tx_signature(item),
                "slot": slot,
                "block_time": btime,
                "transaction_index": tx_index,
                "variant": migration_variant_v07(item, mint, pda, pool),
                "transaction_sha256": sha256_json(item),
            })
    uniq = {(x["signature"], x["slot"], x["transaction_index"]) for x in candidates}
    boundary = candidates[0] if len(uniq) == 1 else None
    return {
        "crossdate_manifest_index": artifact_index(artifact_dir),
        "mint": mint,
        "t0": old.get("t0"),
        "pool_address": pool,
        "v06_source_complete": bool(old.get("source_complete")),
        "persisted_block_files": len(blocks),
        "persisted_block_errors": block_errors,
        "v07_qualifying_boundaries": len(uniq),
        "v07_boundary_signature": boundary.get("signature") if boundary else None,
        "v07_boundary_slot": boundary.get("slot") if boundary else None,
        "v07_boundary_transaction_index": boundary.get("transaction_index") if boundary else None,
        "v07_boundary_block_time": boundary.get("block_time") if boundary else None,
        "v07_boundary_variant": boundary.get("variant") if boundary else None,
        "parser_boundary_resolved": len(uniq) == 1 and block_errors == 0,
        "outcomes_opened": False,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-root", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    root = Path(args.input_root)
    artifact_dirs = sorted([p for p in root.iterdir() if p.is_dir() and ART_RE.match(p.name)], key=lambda p: artifact_index(p))
    rows = [scan_artifact(p) for p in artifact_dirs]
    indices = {r["crossdate_manifest_index"] for r in rows}
    resolved = sum(bool(r["parser_boundary_resolved"]) for r in rows)
    v1 = sum(r.get("v07_boundary_variant") == "migrate" for r in rows)
    v2 = sum(r.get("v07_boundary_variant") == "migrate_v2" for r in rows)
    old_failed_resolved = sum((not r["v06_source_complete"]) and r["parser_boundary_resolved"] for r in rows)
    reconciliation = len(rows) == 20 and indices == EXPECTED and all(r["outcomes_opened"] is False for r in rows)
    verdict = "V07_OFFLINE_BOUNDARY_COVERAGE_20_OF_20" if reconciliation and resolved == 20 else "V07_OFFLINE_BOUNDARY_COVERAGE_INCOMPLETE"

    out = Path(args.out_dir); out.mkdir(parents=True, exist_ok=True)
    canon = "".join(json.dumps(r, sort_keys=True, separators=(",", ":")) + "\n" for r in rows)
    (out / "v07_offline_boundary_rows.jsonl").write_text(canon, encoding="utf-8")
    receipt = {
        "lab": "PMD-001",
        "stage": "V07_OFFLINE_BOUNDARY_READJUDICATION",
        "economic_outcomes_opened": False,
        "source_run_id": 35132853202,
        "rows": len(rows),
        "indices_reconciled": indices == EXPECTED,
        "boundaries_resolved": resolved,
        "legacy_migrate_boundaries": v1,
        "migrate_v2_boundaries": v2,
        "v06_failed_rows_resolved_by_v07_parser": old_failed_resolved,
        "rows_sha256": hashlib.sha256(canon.encode()).hexdigest(),
        "scientific_source_gate_authority": False,
        "verdict": verdict,
    }
    (out / "v07_offline_boundary_receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if verdict == "V07_OFFLINE_BOUNDARY_COVERAGE_20_OF_20" else 2

if __name__ == "__main__":
    raise SystemExit(main())
