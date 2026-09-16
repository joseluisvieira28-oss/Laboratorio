#!/usr/bin/env python3
"""PMD-001 V0.2 public Solana RPC fallback probe.

Outcome-blind. Queries only bonding-curve account history and selected full
transactions strictly before T0. No post-migration price/outcome source is read.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import time
from typing import Any
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

import pyarrow.parquet as pq
from huggingface_hub import hf_hub_download

REPO_ID = "Slinky21/Pumpfun_Memecoin_Corpus"
RPC_URL = os.environ.get("PMD_SOLANA_RPC_URL", "https://api.mainnet.solana.com")
SENTINELS = {"synthetic_graduation_queue", "backfilled_from_pumpswap_trade"}
OUTAGE_DATE = "2026-07-03"
WINDOW_SECONDS = 300
PROBE_N = 3
MAX_SIGNATURE_PAGES = 3
SIG_LIMIT = 1000
FULL_TX_CHECKS_PER_MINT = 5


def sha256_bytes(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def write_json(path: Path, obj: Any) -> str:
    raw = (json.dumps(obj, indent=2, sort_keys=True, default=str) + "\n").encode()
    path.write_bytes(raw)
    return sha256_bytes(raw)


def rpc(method: str, params: list[Any], retries: int = 6) -> dict[str, Any]:
    payload = json.dumps({"jsonrpc": "2.0", "id": "pmd001-public-probe", "method": method, "params": params}).encode()
    for attempt in range(retries):
        req = Request(RPC_URL, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urlopen(req, timeout=45) as resp:
                raw = resp.read()
            obj = json.loads(raw)
            if obj.get("error"):
                code = obj["error"].get("code") if isinstance(obj["error"], dict) else None
                if code == 429 and attempt + 1 < retries:
                    time.sleep(min(2 ** attempt, 8)); continue
                raise RuntimeError(f"RPC_ERROR {obj['error']}")
            return obj
        except HTTPError as exc:
            if exc.code == 429 and attempt + 1 < retries:
                time.sleep(min(2 ** attempt, 8)); continue
            raise
        except URLError:
            if attempt + 1 < retries:
                time.sleep(min(2 ** attempt, 8)); continue
            raise
    raise RuntimeError("RPC_RETRY_EXHAUSTED")


def load_candidates(data_dir: Path) -> list[dict[str, Any]]:
    migrations = Path(hf_hub_download(repo_id=REPO_ID, repo_type="dataset", filename="migrations.parquet", local_dir=str(data_dir)))
    tokens = Path(hf_hub_download(repo_id=REPO_ID, repo_type="dataset", filename="tokens.parquet", local_dir=str(data_dir)))
    mrows = pq.read_table(migrations, columns=["mint", "migrated_at", "pool_address"]).to_pylist()
    trows = pq.read_table(tokens, columns=["mint", "is_mayhem_mode", "bonding_curve_key"]).to_pylist()
    by_mint = {r["mint"]: r for r in trows if r.get("mint")}
    out = []
    for m in mrows:
        t = by_mint.get(m.get("mint"))
        ts = m.get("migrated_at"); pool = m.get("pool_address")
        if not t or ts is None or not pool or pool in SENTINELS:
            continue
        if bool(t.get("is_mayhem_mode")) or ts.date().isoformat() == OUTAGE_DATE or not t.get("bonding_curve_key"):
            continue
        out.append({
            "mint": m["mint"],
            "t0_epoch": int(ts.timestamp()),
            "bonding_curve_key": t["bonding_curve_key"],
        })
    out.sort(key=lambda r: (r["t0_epoch"], r["mint"]))
    return out


def even_sample(rows: list[dict[str, Any]], n: int) -> list[dict[str, Any]]:
    if len(rows) <= n:
        return rows
    idxs = [round(i * (len(rows) - 1) / (n - 1)) for i in range(n)]
    return [rows[i] for i in idxs]


def main() -> int:
    root = Path("artifacts/pmd001_public_rpc_probe_v02")
    raw_dir = root / "raw_rpc"; data_dir = root / "source_data"
    raw_dir.mkdir(parents=True, exist_ok=True); data_dir.mkdir(parents=True, exist_ok=True)
    candidates = load_candidates(data_dir)
    sample = even_sample(candidates, PROBE_N)
    rows = []
    provider_errors = 0
    any_window = 0
    full_tx_verified = 0

    for rank, row in enumerate(sample, 1):
        before = None
        sigs: list[dict[str, Any]] = []
        pages = 0
        err = None
        try:
            while pages < MAX_SIGNATURE_PAGES:
                cfg: dict[str, Any] = {"commitment": "finalized", "limit": SIG_LIMIT}
                if before:
                    cfg["before"] = before
                obj = rpc("getSignaturesForAddress", [row["bonding_curve_key"], cfg])
                pages += 1
                write_json(raw_dir / f"{rank:02d}_signatures_{pages:02d}.json", obj)
                batch = obj.get("result") or []
                if not isinstance(batch, list):
                    raise RuntimeError("SIGNATURE_RESULT_SHAPE_FAILURE")
                sigs.extend(batch)
                if not batch:
                    break
                times = [int(x["blockTime"]) for x in batch if isinstance(x, dict) and x.get("blockTime") is not None]
                if times and min(times) < row["t0_epoch"] - WINDOW_SECONDS:
                    break
                before = batch[-1].get("signature") if isinstance(batch[-1], dict) else None
                if not before:
                    break
                time.sleep(0.30)
        except Exception as exc:
            err = repr(exc); provider_errors += 1

        window_sigs = [
            x for x in sigs
            if isinstance(x, dict) and x.get("blockTime") is not None
            and row["t0_epoch"] - WINDOW_SECONDS <= int(x["blockTime"]) < row["t0_epoch"]
            and x.get("err") is None and x.get("signature")
        ]
        if window_sigs:
            any_window += 1

        checked = 0
        if err is None:
            for x in window_sigs[:FULL_TX_CHECKS_PER_MINT]:
                try:
                    txobj = rpc("getTransaction", [x["signature"], {"commitment": "finalized", "encoding": "json", "maxSupportedTransactionVersion": 0}])
                    write_json(raw_dir / f"{rank:02d}_tx_{checked+1:02d}.json", txobj)
                    result = txobj.get("result")
                    if not isinstance(result, dict):
                        raise RuntimeError("GET_TRANSACTION_NULL_OR_BAD_SHAPE")
                    bt = result.get("blockTime")
                    if bt is not None and int(bt) >= row["t0_epoch"]:
                        raise RuntimeError("LEAKAGE_WALL_POST_T0_TRANSACTION")
                    checked += 1; full_tx_verified += 1
                    time.sleep(0.30)
                except Exception as exc:
                    err = repr(exc); provider_errors += 1; break

        rows.append({
            "probe_rank": rank,
            "mint": row["mint"],
            "t0_epoch": row["t0_epoch"],
            "bonding_curve_key": row["bonding_curve_key"],
            "signature_pages": pages,
            "signatures_total_returned": len(sigs),
            "signatures_in_pre_t0_300s": len(window_sigs),
            "full_transactions_verified": checked,
            "error": err,
        })

    manifest_sha = write_json(root / "probe_manifest.json", rows)
    classification = "SOURCE_REBUILD_PUBLIC_RPC_PROBE_PASS" if provider_errors == 0 and any_window == len(sample) and full_tx_verified > 0 else "SOURCE_REBUILD_PUBLIC_RPC_PROBE_FAIL"
    receipt = {
        "lab": "PMD-001",
        "stage": "SOURCE_REBUILD_PUBLIC_RPC_PROBE_V02",
        "rpc_url": RPC_URL,
        "candidate_rows_before_execution_ceiling": len(candidates),
        "probe_n": len(sample),
        "records_with_pre_t0_300s_signatures": any_window,
        "full_transactions_verified": full_tx_verified,
        "provider_errors": provider_errors,
        "manifest_sha256": manifest_sha,
        "classification": classification,
        "outcomes_opened": False,
        "forbidden_outcome_file_acquired": False,
    }
    write_json(root / "receipt.json", receipt)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if classification.endswith("_PASS") else 2


if __name__ == "__main__":
    raise SystemExit(main())
