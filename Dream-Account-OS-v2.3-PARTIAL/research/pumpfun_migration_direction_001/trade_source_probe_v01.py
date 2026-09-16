#!/usr/bin/env python3
"""PMD-001 raw trade source probe, outcome-blind.

Discovers the raw trade shards, downloads the lexicographically last shard, verifies
its local SHA256, reports schema/timestamp coverage and nullness only. It never opens
post-migration prices, returns or labels.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import duckdb
from huggingface_hub import HfApi, hf_hub_download
import pyarrow.parquet as pq

REPO_ID = "Slinky21/Pumpfun_Memecoin_Corpus"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="pmd_trade_probe")
    ap.add_argument("--out", default="pmd_trade_source_probe_v01.json")
    args = ap.parse_args()

    d = Path(args.data_dir)
    d.mkdir(parents=True, exist_ok=True)

    api = HfApi()
    all_files = api.list_repo_files(REPO_ID, repo_type="dataset")
    shards = sorted(f for f in all_files if f.startswith("trades/") and f.endswith(".parquet"))
    if not shards:
        raise RuntimeError("No trades/*.parquet shards discovered")

    probe_name = shards[-1]
    local = Path(hf_hub_download(repo_id=REPO_ID, repo_type="dataset", filename=probe_name, local_dir=str(d)))
    pf = pq.ParquetFile(local)
    schema = pf.schema_arrow
    cols = schema.names

    time_candidates = [c for c in cols if any(k in c.lower() for k in ("time", "timestamp", "block"))]
    mint_candidates = [c for c in cols if "mint" in c.lower()]
    wallet_candidates = [c for c in cols if any(k in c.lower() for k in ("wallet", "user", "trader", "owner", "signer"))]
    side_candidates = [c for c in cols if any(k in c.lower() for k in ("buy", "sell", "side", "direction"))]
    amount_candidates = [c for c in cols if any(k in c.lower() for k in ("amount", "volume", "token", "sol"))]
    reserve_candidates = [c for c in cols if any(k in c.lower() for k in ("reserve", "curve", "bonding"))]

    out = {
        "lab": "PMD-001",
        "stage": "RAW_TRADE_SOURCE_PROBE_V01",
        "outcomes_opened": False,
        "repo_id": REPO_ID,
        "trade_shard_count": len(shards),
        "trade_shards": shards,
        "probe_shard": probe_name,
        "probe_size_bytes": local.stat().st_size,
        "probe_sha256": sha256_file(local),
        "probe_rows": pf.metadata.num_rows,
        "schema": {f.name: str(f.type) for f in schema},
        "semantic_candidates": {
            "time": time_candidates,
            "mint": mint_candidates,
            "wallet": wallet_candidates,
            "side": side_candidates,
            "amount": amount_candidates,
            "reserve_curve": reserve_candidates,
        },
    }

    con = duckdb.connect(":memory:")
    p = str(local.resolve()).replace("'", "''")
    con.execute(f"CREATE VIEW tr AS SELECT * FROM read_parquet('{p}')")

    if time_candidates:
        tc = time_candidates[0]
        out["probe_time_column_used"] = tc
        out["probe_time_minmax"] = [str(v) for v in con.execute(f'SELECT min("{tc}"), max("{tc}") FROM tr').fetchone()]
    if mint_candidates:
        mc = mint_candidates[0]
        out["probe_distinct_mints"] = con.execute(f'SELECT count(DISTINCT "{mc}") FROM tr').fetchone()[0]
        out["probe_null_mints"] = con.execute(f'SELECT count(*) FROM tr WHERE "{mc}" IS NULL').fetchone()[0]

    # Nullness audit for fields relevant to allowed feature families. No outcome data is present here.
    selected = []
    for group in (time_candidates[:2], mint_candidates[:2], wallet_candidates[:3], side_candidates[:3], amount_candidates[:6], reserve_candidates[:6]):
        for c in group:
            if c not in selected:
                selected.append(c)
    nullness = {}
    for c in selected:
        nullness[c] = con.execute(f'SELECT count(*) FROM tr WHERE "{c}" IS NULL').fetchone()[0]
    out["probe_null_counts"] = nullness

    required = {
        "time": bool(time_candidates),
        "mint": bool(mint_candidates),
        "wallet": bool(wallet_candidates),
        "side": bool(side_candidates),
    }
    out["minimum_trade_schema"] = required
    out["verdict"] = "RAW_TRADE_SCHEMA_PASS" if all(required.values()) else "RAW_TRADE_SCHEMA_FAIL_CLOSED"

    Path(args.out).write_text(json.dumps(out, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2, sort_keys=True, default=str))
    return 0 if all(required.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
