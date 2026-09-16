#!/usr/bin/env python3
"""PMD-001 V0.2 exact-population public RPC probe.

Outcome-blind source reconstruction probe. Reproduces the V0.1 post-source
execution ceiling using only identity/timestamp/nullness metadata, enforces the
published source hashes, freezes the exact manifest, then tests public Solana
RPC coverage for a deterministic evenly-spaced sample.

No post-migration price value, return, PnL or direction label is read.
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

import duckdb
from huggingface_hub import hf_hub_download

REPO_ID = "Slinky21/Pumpfun_Memecoin_Corpus"
EXPECTED_SHA256 = {
    "migrations.parquet": "ef5d5141fd94acbcd121bed50e39e525cf7777d25338fc9852a67fd8a085105d",
    "postgard_snapshots.parquet": "34a63b8333a41b3cc84d05461febe725cf37842fa0e21d6ea00472dcdcfa1e72",
    "tokens.parquet": "c005d86d424013e5c78701161b025f3d8c3d472afb61466e0ad6fd5afe9e8ea6",
}
EXPECTED_EXECUTABLE_CEILING = 1012
RPC_URL = os.environ.get("PMD_SOLANA_RPC_URL", "https://api.mainnet.solana.com")
PROBE_N = 50
WINDOW_SECONDS = 300
SIG_LIMIT = 1000
MAX_SIGNATURE_PAGES = 5
FULL_TX_CHECKS_PER_MINT = 1


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, obj: Any) -> str:
    raw = (json.dumps(obj, indent=2, sort_keys=True, default=str) + "\n").encode()
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> str:
    raw = b"".join((json.dumps(r, sort_keys=True, default=str) + "\n").encode() for r in rows)
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def rpc(method: str, params: list[Any], retries: int = 7) -> dict[str, Any]:
    payload = json.dumps({"jsonrpc":"2.0","id":"pmd001-v02-exact","method":method,"params":params}).encode()
    for attempt in range(retries):
        req = Request(RPC_URL, data=payload, headers={"Content-Type":"application/json"}, method="POST")
        try:
            with urlopen(req, timeout=45) as resp:
                raw = resp.read()
            obj = json.loads(raw)
            if obj.get("error"):
                code = obj["error"].get("code") if isinstance(obj["error"], dict) else None
                if code == 429 and attempt + 1 < retries:
                    time.sleep(min(2 ** attempt, 10)); continue
                raise RuntimeError(f"RPC_ERROR {obj['error']}")
            return obj
        except HTTPError as exc:
            if exc.code == 429 and attempt + 1 < retries:
                time.sleep(min(2 ** attempt, 10)); continue
            raise
        except URLError:
            if attempt + 1 < retries:
                time.sleep(min(2 ** attempt, 10)); continue
            raise
    raise RuntimeError("RPC_RETRY_EXHAUSTED")


def download_and_verify(data_dir: Path) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    for name, expected in EXPECTED_SHA256.items():
        path = Path(hf_hub_download(repo_id=REPO_ID, repo_type="dataset", filename=name, local_dir=str(data_dir)))
        actual = sha256_path(path)
        if actual != expected:
            raise RuntimeError(f"SOURCE_HASH_MISMATCH {name} expected={expected} actual={actual}")
        paths[name] = path
    return paths


def sql_path(path: Path) -> str:
    return str(path.resolve()).replace("'", "''")


def build_exact_manifest(paths: dict[str, Path]) -> list[dict[str, Any]]:
    con = duckdb.connect(database=":memory:")
    mig = sql_path(paths["migrations.parquet"]); tok = sql_path(paths["tokens.parquet"]); post = sql_path(paths["postgard_snapshots.parquet"])
    con.execute(f"CREATE VIEW migrations AS SELECT mint,migrated_at,pool_address FROM read_parquet('{mig}')")
    con.execute(f"CREATE VIEW tokens AS SELECT mint,is_mayhem_mode,bonding_curve_key,top10_pct_suspect FROM read_parquet('{tok}')")
    # Nullness only: no price value is selected or exposed.
    con.execute(f"""CREATE VIEW post_meta AS
        SELECT mint,snapshot_time,pair_address,incomplete_data,(price_native IS NOT NULL) AS has_native_price
        FROM read_parquet('{post}')""")
    con.execute("""
      CREATE TEMP VIEW base AS
      SELECT m.mint,m.migrated_at AS t0,m.pool_address,t.bonding_curve_key,t.top10_pct_suspect
      FROM migrations m JOIN tokens t USING(mint)
      WHERE m.pool_address IS NOT NULL
        AND m.pool_address NOT IN ('synthetic_graduation_queue','backfilled_from_pumpswap_trade')
        AND CAST(m.migrated_at AS DATE) <> DATE '2026-07-03'
        AND COALESCE(t.is_mayhem_mode,FALSE)=FALSE
        AND t.bonding_curve_key IS NOT NULL
    """)
    con.execute("""
      CREATE TEMP VIEW post_cov AS
      SELECT b.*,
             min(p.snapshot_time) FILTER (
               WHERE p.pair_address=b.pool_address AND NOT p.incomplete_data AND p.has_native_price
                 AND p.snapshot_time >= b.t0 + INTERVAL 15 SECOND
                 AND p.snapshot_time <= b.t0 + INTERVAL 60 SECOND
             ) AS entry_ts
      FROM base b LEFT JOIN post_meta p USING(mint)
      GROUP BY b.mint,b.t0,b.pool_address,b.bonding_curve_key,b.top10_pct_suspect
    """)
    con.execute("""
      CREATE TEMP VIEW exact_exec AS
      SELECT c.*,
             EXISTS(
               SELECT 1 FROM post_meta p
               WHERE p.mint=c.mint AND p.pair_address=c.pool_address
                 AND c.entry_ts IS NOT NULL AND NOT p.incomplete_data AND p.has_native_price
                 AND p.snapshot_time >= c.entry_ts + INTERVAL 300 SECOND
                 AND p.snapshot_time <= c.entry_ts + INTERVAL 330 SECOND
             ) AS has_exit
      FROM post_cov c
    """)
    rows = con.execute("""
      SELECT mint,t0,pool_address,bonding_curve_key,COALESCE(top10_pct_suspect,FALSE) AS top10_pct_suspect,entry_ts
      FROM exact_exec WHERE entry_ts IS NOT NULL AND has_exit
      ORDER BY t0,mint
    """).fetchall()
    if len(rows) != EXPECTED_EXECUTABLE_CEILING:
        raise RuntimeError(f"EXECUTABLE_CEILING_MISMATCH {len(rows)}/{EXPECTED_EXECUTABLE_CEILING}")
    out = []
    for mint,t0,pool,curve,suspect,entry_ts in rows:
        out.append({
            "mint": mint,
            "t0": str(t0),
            "t0_epoch": int(t0.timestamp()),
            "migration_date": str(t0.date()),
            "pool_address": pool,
            "bonding_curve_key": curve,
            "top10_pct_suspect": bool(suspect),
            "entry_timestamp_metadata": str(entry_ts),
            "post_2026_07_04_curve_regime": str(t0.date()) >= "2026-07-04",
        })
    return out


def even_sample(rows: list[dict[str, Any]], n: int) -> list[dict[str, Any]]:
    idxs = [round(i * (len(rows)-1)/(n-1)) for i in range(n)]
    if len(set(idxs)) != n:
        raise RuntimeError("DETERMINISTIC_SAMPLE_INDEX_COLLISION")
    return [dict(rows[i], manifest_index=i) for i in idxs]


def main() -> int:
    root = Path("artifacts/pmd001_exact_population_public_rpc_probe_v02")
    data_dir = root / "source_data"; raw_dir = root / "raw_rpc"
    data_dir.mkdir(parents=True, exist_ok=True); raw_dir.mkdir(parents=True, exist_ok=True)
    try:
        paths = download_and_verify(data_dir)
        manifest = build_exact_manifest(paths)
    except Exception as exc:
        receipt = {"lab":"PMD-001","stage":"EXACT_POPULATION_PUBLIC_RPC_PROBE_V02","classification":"EXACT_POPULATION_BUILD_FAILURE","detail":repr(exc),"outcomes_opened":False,"forbidden_outcome_file_acquired":False}
        write_json(root/"receipt.json", receipt); print(json.dumps(receipt,indent=2,sort_keys=True)); return 2

    manifest_sha = write_jsonl(root/"exact_executable_manifest_1012.jsonl", manifest)
    sample = even_sample(manifest, PROBE_N)
    sample_sha = write_jsonl(root/"deterministic_probe_sample_50.jsonl", sample)

    audit = []
    provider_errors = 0; with_window = 0; full_verified = 0; pagination_caps = 0
    for rank,row in enumerate(sample,1):
        before = None; pages = 0; all_sigs = []; err = None
        try:
            while pages < MAX_SIGNATURE_PAGES:
                cfg: dict[str, Any] = {"commitment":"finalized","limit":SIG_LIMIT}
                if before: cfg["before"] = before
                obj = rpc("getSignaturesForAddress", [row["bonding_curve_key"], cfg])
                pages += 1
                # Raw signature responses are intentionally not persisted at scale here;
                # the full backfill will persist/hashes every accepted raw response.
                batch = obj.get("result") or []
                if not isinstance(batch,list): raise RuntimeError("SIGNATURE_RESULT_SHAPE_FAILURE")
                all_sigs.extend(batch)
                if not batch: break
                times=[int(x["blockTime"]) for x in batch if isinstance(x,dict) and x.get("blockTime") is not None]
                if times and min(times) < row["t0_epoch"]-WINDOW_SECONDS: break
                before = batch[-1].get("signature") if isinstance(batch[-1],dict) else None
                if not before: break
                time.sleep(0.30)
            if pages >= MAX_SIGNATURE_PAGES and before:
                oldest = min([int(x["blockTime"]) for x in all_sigs if isinstance(x,dict) and x.get("blockTime") is not None], default=None)
                if oldest is not None and oldest >= row["t0_epoch"]-WINDOW_SECONDS:
                    pagination_caps += 1
                    err = "PAGINATION_CAP_BEFORE_WINDOW_BOUNDARY"
        except Exception as exc:
            err = repr(exc); provider_errors += 1

        window=[x for x in all_sigs if isinstance(x,dict) and x.get("blockTime") is not None and row["t0_epoch"]-WINDOW_SECONDS <= int(x["blockTime"]) < row["t0_epoch"] and x.get("err") is None and x.get("signature")]
        if window: with_window += 1
        checked=0
        if err is None and window:
            for x in window[:FULL_TX_CHECKS_PER_MINT]:
                try:
                    tx=rpc("getTransaction",[x["signature"],{"commitment":"finalized","encoding":"json","maxSupportedTransactionVersion":0}])
                    result=tx.get("result")
                    if not isinstance(result,dict): raise RuntimeError("GET_TRANSACTION_NULL_OR_BAD_SHAPE")
                    bt=result.get("blockTime")
                    if bt is not None and int(bt) >= row["t0_epoch"]: raise RuntimeError("LEAKAGE_WALL_POST_T0_TRANSACTION")
                    # Persist one full raw tx per positive sample case as proof.
                    write_json(raw_dir/f"{rank:03d}_tx.json",tx)
                    checked += 1; full_verified += 1; time.sleep(0.30)
                except Exception as exc:
                    err=repr(exc); provider_errors += 1; break
        audit.append({
            "probe_rank":rank,"manifest_index":row["manifest_index"],"mint":row["mint"],"migration_date":row["migration_date"],"t0_epoch":row["t0_epoch"],
            "signature_pages":pages,"signatures_total":len(all_sigs),"signatures_pre_t0_300s":len(window),"full_transactions_verified":checked,"error":err,
        })
        time.sleep(0.30)

    audit_sha=write_jsonl(root/"probe_audit_50.jsonl",audit)
    coverage=with_window/PROBE_N
    # Probe verdict is deliberately descriptive: it does not infer full-population PASS.
    if provider_errors or pagination_caps:
        classification="EXACT_POPULATION_PUBLIC_RPC_PROBE_TECHNICAL_LIMIT"
        rc=2
    elif with_window == PROBE_N:
        classification="EXACT_POPULATION_PUBLIC_RPC_PROBE_FULL_SAMPLE_COVERAGE"
        rc=0
    else:
        classification="EXACT_POPULATION_PUBLIC_RPC_PROBE_PARTIAL_SAMPLE_COVERAGE"
        rc=0
    receipt={
        "lab":"PMD-001","stage":"EXACT_POPULATION_PUBLIC_RPC_PROBE_V02","exact_executable_population":len(manifest),"distinct_migration_dates":len({r['migration_date'] for r in manifest}),
        "manifest_sha256":manifest_sha,"probe_n":PROBE_N,"sample_sha256":sample_sha,"probe_with_pre_t0_300s_activity":with_window,"probe_coverage_fraction":coverage,
        "full_transactions_verified":full_verified,"provider_errors":provider_errors,"pagination_caps":pagination_caps,"probe_audit_sha256":audit_sha,
        "classification":classification,"outcomes_opened":False,"forbidden_outcome_file_acquired":False,
    }
    write_json(root/"receipt.json",receipt); print(json.dumps(receipt,indent=2,sort_keys=True)); return rc

if __name__ == "__main__": raise SystemExit(main())
