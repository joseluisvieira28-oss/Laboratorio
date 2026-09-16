#!/usr/bin/env python3
"""PMD-001 V0.2 outcome-blind archival source probe.

This script never opens post-migration outcomes or prices. It downloads only
migrations.parquet and tokens.parquet to deterministically select source records,
then queries Helius archival getTransactionsForAddress for bonding-curve activity
strictly in [T0-300s, T0).

HELIUS_API_KEY must be supplied by environment. Raw provider responses are saved
and SHA-256 hashed. Missing credentials/data fail closed.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys
import time
from typing import Any
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

import pyarrow.parquet as pq
from huggingface_hub import hf_hub_download

REPO_ID = "Slinky21/Pumpfun_Memecoin_Corpus"
SENTINELS = {"synthetic_graduation_queue", "backfilled_from_pumpswap_trade"}
OUTAGE_DATE = "2026-07-03"
WINDOW_SECONDS = 300
PROBE_N = 12
FULL_LIMIT = 100
MAX_PAGES_PER_ADDRESS = 20


def sha256_bytes(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def write_json(path: Path, obj: Any) -> str:
    raw = (json.dumps(obj, indent=2, sort_keys=True, default=str) + "\n").encode()
    path.write_bytes(raw)
    return sha256_bytes(raw)


def fail(receipt: Path, classification: str, detail: str, extra: dict[str, Any] | None = None) -> int:
    out: dict[str, Any] = {
        "lab": "PMD-001",
        "stage": "SOURCE_REBUILD_PROBE_V02",
        "classification": classification,
        "detail": detail,
        "outcomes_opened": False,
        "forbidden_outcome_file_acquired": False,
    }
    if extra:
        out.update(extra)
    write_json(receipt, out)
    print(json.dumps(out, indent=2, sort_keys=True, default=str))
    return 2


def rpc_call(url: str, address: str, t0: int, pagination_token: str | None) -> dict[str, Any]:
    cfg: dict[str, Any] = {
        "transactionDetails": "full",
        "encoding": "json",
        "maxSupportedTransactionVersion": 0,
        "sortOrder": "asc",
        "limit": FULL_LIMIT,
        "commitment": "finalized",
        "filters": {
            "blockTime": {"gte": t0 - WINDOW_SECONDS, "lt": t0},
            "status": "succeeded",
        },
    }
    if pagination_token:
        cfg["paginationToken"] = pagination_token
    payload = json.dumps({
        "jsonrpc": "2.0",
        "id": "pmd001-v02-probe",
        "method": "getTransactionsForAddress",
        "params": [address, cfg],
    }).encode()
    req = Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(req, timeout=60) as resp:
        raw = resp.read()
    obj = json.loads(raw)
    if obj.get("error"):
        raise RuntimeError(f"RPC_ERROR {obj['error']}")
    if not isinstance(obj.get("result"), dict):
        raise RuntimeError("RPC_RESULT_SHAPE_FAILURE")
    return obj


def to_epoch_seconds(value: Any) -> int:
    # pyarrow commonly returns datetime with tz info.
    return int(value.timestamp())


def load_candidates(data_dir: Path) -> list[dict[str, Any]]:
    migrations = Path(hf_hub_download(
        repo_id=REPO_ID, repo_type="dataset", filename="migrations.parquet", local_dir=str(data_dir)
    ))
    tokens = Path(hf_hub_download(
        repo_id=REPO_ID, repo_type="dataset", filename="tokens.parquet", local_dir=str(data_dir)
    ))

    mtab = pq.read_table(migrations, columns=["mint", "migrated_at", "pool_address"])
    ttab = pq.read_table(tokens, columns=["mint", "is_mayhem_mode", "bonding_curve_key"])
    token_rows = {
        r["mint"]: r
        for r in ttab.to_pylist()
        if r.get("mint")
    }
    out: list[dict[str, Any]] = []
    for m in mtab.to_pylist():
        mint = m.get("mint")
        t0 = m.get("migrated_at")
        pool = m.get("pool_address")
        t = token_rows.get(mint)
        if not mint or t0 is None or not pool or pool in SENTINELS or t is None:
            continue
        if bool(t.get("is_mayhem_mode")):
            continue
        if t0.date().isoformat() == OUTAGE_DATE:
            continue
        curve = t.get("bonding_curve_key")
        if not curve:
            continue
        out.append({
            "mint": mint,
            "t0": t0,
            "t0_epoch": to_epoch_seconds(t0),
            "pool_address": pool,
            "bonding_curve_key": curve,
        })
    out.sort(key=lambda r: (r["t0_epoch"], r["mint"]))
    return out


def deterministic_even_sample(rows: list[dict[str, Any]], n: int) -> list[dict[str, Any]]:
    if len(rows) < n:
        return rows
    if n == 1:
        return [rows[0]]
    indexes = [round(i * (len(rows) - 1) / (n - 1)) for i in range(n)]
    # Preserve order and remove pathological duplicate rounded indices.
    seen: set[int] = set()
    picked = []
    for idx in indexes:
        if idx not in seen:
            picked.append(rows[idx]); seen.add(idx)
    return picked


def main() -> int:
    out_dir = Path(os.environ.get("PMD_V02_OUT_DIR", "artifacts/pmd001_source_rebuild_probe_v02"))
    raw_dir = out_dir / "raw_rpc"
    data_dir = out_dir / "source_data"
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)
    receipt = out_dir / "receipt.json"

    key = os.environ.get("HELIUS_API_KEY", "").strip()
    if not key:
        return fail(receipt, "SOURCE_REBUILD_BLOCKED_MISSING_HELIUS_API_KEY", "HELIUS_API_KEY is not available to the workflow.")
    rpc_url = f"https://mainnet.helius-rpc.com/?api-key={key}"

    try:
        candidates = load_candidates(data_dir)
    except Exception as exc:
        return fail(receipt, "SOURCE_REBUILD_PROBE_SOURCE_SELECTION_FAILURE", repr(exc))
    sample = deterministic_even_sample(candidates, PROBE_N)
    if len(sample) != PROBE_N:
        return fail(receipt, "SOURCE_REBUILD_PROBE_INSUFFICIENT_SOURCE_ROWS", f"sample={len(sample)}/{PROBE_N}", {"candidate_rows": len(candidates)})

    manifest_rows: list[dict[str, Any]] = []
    provider_errors = 0
    records_with_any_tx = 0
    total_txs = 0

    for rank, row in enumerate(sample, 1):
        pagination: str | None = None
        pages = 0
        tx_count = 0
        raw_hashes: list[str] = []
        error: str | None = None
        while pages < MAX_PAGES_PER_ADDRESS:
            pages += 1
            try:
                obj = rpc_call(rpc_url, row["bonding_curve_key"], row["t0_epoch"], pagination)
            except (HTTPError, URLError, TimeoutError, RuntimeError, ValueError) as exc:
                error = repr(exc)
                provider_errors += 1
                break
            raw_path = raw_dir / f"{rank:02d}_page_{pages:02d}.json"
            digest = write_json(raw_path, obj)
            raw_hashes.append(digest)
            result = obj["result"]
            data = result.get("data") or []
            if not isinstance(data, list):
                error = "RPC_DATA_SHAPE_FAILURE"; provider_errors += 1; break
            # Enforce the leakage wall again against provider timestamps.
            for tx in data:
                bt = tx.get("blockTime") if isinstance(tx, dict) else None
                if bt is not None and int(bt) >= row["t0_epoch"]:
                    error = f"POST_T0_TRANSACTION_RETURNED blockTime={bt} t0={row['t0_epoch']}"
                    provider_errors += 1
                    break
            if error:
                break
            tx_count += len(data)
            pagination = result.get("paginationToken")
            if not pagination or not data:
                break
            time.sleep(0.03)
        if pagination and pages >= MAX_PAGES_PER_ADDRESS and error is None:
            error = "PAGINATION_SAFETY_CAP_REACHED"
            provider_errors += 1
        if tx_count > 0:
            records_with_any_tx += 1
        total_txs += tx_count
        manifest_rows.append({
            "probe_rank": rank,
            "mint": row["mint"],
            "t0_epoch": row["t0_epoch"],
            "bonding_curve_key": row["bonding_curve_key"],
            "pages": pages,
            "transaction_count_pre_t0_300s": tx_count,
            "raw_page_sha256": raw_hashes,
            "error": error,
        })

    manifest_path = out_dir / "probe_manifest.json"
    manifest_sha = write_json(manifest_path, manifest_rows)
    out = {
        "lab": "PMD-001",
        "stage": "SOURCE_REBUILD_PROBE_V02",
        "candidate_rows_before_execution_ceiling": len(candidates),
        "probe_n": PROBE_N,
        "probe_records_with_any_pre_t0_transaction": records_with_any_tx,
        "total_pre_t0_transactions_returned": total_txs,
        "provider_errors": provider_errors,
        "manifest_sha256": manifest_sha,
        "outcomes_opened": False,
        "forbidden_outcome_file_acquired": False,
    }
    if provider_errors:
        out["classification"] = "SOURCE_REBUILD_PROBE_PROVIDER_FAILURE"
        rc = 2
    elif records_with_any_tx == 0:
        out["classification"] = "SOURCE_REBUILD_PROBE_ZERO_ACTIVITY_FAILURE"
        rc = 2
    else:
        out["classification"] = "SOURCE_REBUILD_PROBE_PASS_READY_FOR_FULL_BACKFILL"
        rc = 0
    write_json(receipt, out)
    print(json.dumps(out, indent=2, sort_keys=True))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
