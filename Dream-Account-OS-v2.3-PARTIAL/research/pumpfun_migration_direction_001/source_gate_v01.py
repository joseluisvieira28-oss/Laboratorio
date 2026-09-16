#!/usr/bin/env python3
"""PMD-001 pre-outcome source/schema gate.

This script MUST NOT compute returns, outcome labels, feature/outcome correlations,
or any trading result. It downloads only the four files required to establish the
source schema and migration/pre/post snapshot coverage. postgard_outcomes.parquet
is intentionally forbidden.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq
from huggingface_hub import hf_hub_download

REPO_ID = "Slinky21/Pumpfun_Memecoin_Corpus"
FILES = {
    "migrations.parquet": "ef5d5141fd94acbcd121bed50e39e525cf7777d25338fc9852a67fd8a085105d",
    "tokens.parquet": "c005d86d424013e5c78701161b025f3d8c3d472afb61466e0ad6fd5afe9e8ea6",
    "snapshots.parquet": "41b6a221dca6ea01d68fac2129c3c5cd3966a27839f267e0f6aa4e980b6fc7d8",
    "postgard_snapshots.parquet": "34a63b8333a41b3cc84d05461febe725cf37842fa0e21d6ea00472dcdcfa1e72",
}
FORBIDDEN = {"postgard_outcomes.parquet"}
SENTINELS = {"synthetic_graduation_queue", "backfilled_from_pumpswap_trade"}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def schema_info(path: Path) -> dict[str, Any]:
    pf = pq.ParquetFile(path)
    schema = pf.schema_arrow
    return {
        "rows": pf.metadata.num_rows,
        "row_groups": pf.metadata.num_row_groups,
        "columns": [field.name for field in schema],
        "types": {field.name: str(field.type) for field in schema},
    }


def read_selected(path: Path, columns: list[str]):
    available = set(pq.ParquetFile(path).schema_arrow.names)
    chosen = [c for c in columns if c in available]
    if not chosen:
        return None, []
    return pq.read_table(path, columns=chosen), chosen


def candidate_columns(columns: list[str], needles: list[str]) -> list[str]:
    return [c for c in columns if any(n in c.lower() for n in needles)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="pmd_source_data")
    ap.add_argument("--receipt", default="pmd_source_gate_v01_receipt.json")
    args = ap.parse_args()

    data_dir = Path(args.data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    receipt: dict[str, Any] = {
        "lab": "PMD-001",
        "stage": "PRE_OUTCOME_SOURCE_SCHEMA_GATE_V01",
        "repo_id": REPO_ID,
        "outcomes_opened": False,
        "forbidden_files": sorted(FORBIDDEN),
        "files": {},
        "checks": [],
    }

    all_hashes_ok = True
    schemas: dict[str, dict[str, Any]] = {}
    for filename, expected_sha in FILES.items():
        if filename in FORBIDDEN:
            raise RuntimeError(f"Forbidden outcome file requested: {filename}")
        cached = hf_hub_download(
            repo_id=REPO_ID,
            repo_type="dataset",
            filename=filename,
            local_dir=str(data_dir),
        )
        path = Path(cached)
        actual_sha = sha256_file(path)
        ok = actual_sha == expected_sha
        all_hashes_ok &= ok
        info = schema_info(path)
        schemas[filename] = info
        receipt["files"][filename] = {
            "sha256_expected": expected_sha,
            "sha256_actual": actual_sha,
            "sha256_match": ok,
            "size_bytes": path.stat().st_size,
            **info,
        }

    receipt["checks"].append({"name": "all_published_sha256_match", "pass": all_hashes_ok})

    mig_cols = schemas["migrations.parquet"]["columns"]
    token_cols = schemas["tokens.parquet"]["columns"]
    snap_cols = schemas["snapshots.parquet"]["columns"]
    post_cols = schemas["postgard_snapshots.parquet"]["columns"]

    receipt["semantic_candidates"] = {
        "migration_time": candidate_columns(mig_cols, ["migrat", "time", "timestamp", "created_at"]),
        "migration_pool": candidate_columns(mig_cols, ["pool"]),
        "migration_mint": candidate_columns(mig_cols, ["mint"]),
        "mayhem": candidate_columns(token_cols, ["mayhem"]),
        "token_mint": candidate_columns(token_cols, ["mint"]),
        "pre_time": candidate_columns(snap_cols, ["time", "timestamp", "snapshot", "bucket"]),
        "pre_flow": candidate_columns(snap_cols, ["buy", "sell", "pressure", "velocity", "trade", "volume", "curve"]),
        "pre_concentration": candidate_columns(snap_cols, ["holder", "top1", "top5", "top10", "gini", "hhi"]),
        "post_time": candidate_columns(post_cols, ["time", "timestamp", "snapshot", "bucket"]),
        "post_price": candidate_columns(post_cols, ["price"]),
        "post_pool": candidate_columns(post_cols, ["pool"]),
        "post_mint": candidate_columns(post_cols, ["mint"]),
    }

    # Source-only migration integrity summaries. No post-migration price values are read.
    mig_path = data_dir / "migrations.parquet"
    mig_table, chosen = read_selected(mig_path, ["mint", "migrated_at", "pool_address"])
    if mig_table is not None:
        import pyarrow.compute as pc

        summary: dict[str, Any] = {"columns_read": chosen, "rows": mig_table.num_rows}
        if "mint" in chosen:
            mints = mig_table["mint"]
            summary["unique_mints"] = len(pc.unique(mints))
            summary["null_mints"] = int(pc.sum(pc.cast(pc.is_null(mints), "int64")).as_py() or 0)
        if "pool_address" in chosen:
            pools = mig_table["pool_address"].to_pylist()
            summary["sentinel_pool_rows"] = sum(v in SENTINELS for v in pools if v is not None)
            summary["null_pool_rows"] = sum(v is None for v in pools)
            summary["real_pool_candidate_rows"] = sum(v is not None and v not in SENTINELS for v in pools)
        if "migrated_at" in chosen:
            vals = [v for v in mig_table["migrated_at"].to_pylist() if v is not None]
            if vals:
                summary["migrated_at_min"] = str(min(vals))
                summary["migrated_at_max"] = str(max(vals))
        receipt["migration_source_summary"] = summary

    # Fail closed if the key semantic families cannot even be located.
    required_candidates = {
        "migration_time": receipt["semantic_candidates"]["migration_time"],
        "migration_mint": receipt["semantic_candidates"]["migration_mint"],
        "post_time": receipt["semantic_candidates"]["post_time"],
        "post_price": receipt["semantic_candidates"]["post_price"],
        "post_mint": receipt["semantic_candidates"]["post_mint"],
        "pre_time": receipt["semantic_candidates"]["pre_time"],
    }
    semantic_gate = all(bool(v) for v in required_candidates.values())
    receipt["checks"].append({"name": "minimum_semantic_schema_located", "pass": semantic_gate})

    receipt["verdict"] = (
        "SOURCE_SCHEMA_GATE_PASS_READY_FOR_FORMULA_FREEZE"
        if all_hashes_ok and semantic_gate
        else "SOURCE_SCHEMA_GATE_FAIL_CLOSED"
    )

    out = Path(args.receipt)
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True, default=str))
    return 0 if receipt["verdict"].endswith("FORMULA_FREEZE") else 2


if __name__ == "__main__":
    raise SystemExit(main())
