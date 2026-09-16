#!/usr/bin/env python3
"""PMD-001 outcome-blind source-rebuild cohort manifest builder.

Reproduces the amended pre-feature executable ceiling using only source identity,
timestamps, nullness and Mayhem/regime metadata. It does NOT expose any
post-migration price value or outcome label.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import duckdb
from huggingface_hub import hf_hub_download

REPO_ID = "Slinky21/Pumpfun_Memecoin_Corpus"
FILES = {
    "migrations.parquet": "ef5d5141fd94acbcd121bed50e39e525cf7777d25338fc9852a67fd8a085105d",
    "tokens.parquet": "c005d86d424013e5c78701161b025f3d8c3d472afb61466e0ad6fd5afe9e8ea6",
    "postgard_snapshots.parquet": "34a63b8333a41b3cc84d05461febe725cf37842fa0e21d6ea00472dcdcfa1e72",
}
EXPECTED_ROWS = 1012
EXPECTED_DISTINCT_DATES = 20
SENTINELS = ("synthetic_graduation_queue", "backfilled_from_pumpswap_trade")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="pmd_source_rebuild_manifest_data")
    ap.add_argument("--out", default="pmd_source_rebuild_manifest_v01.jsonl")
    ap.add_argument("--receipt", default="pmd_source_rebuild_manifest_v01_receipt.json")
    args = ap.parse_args()

    d = Path(args.data_dir)
    d.mkdir(parents=True, exist_ok=True)
    paths = {}
    hashes = {}
    for filename, expected in FILES.items():
        p = Path(hf_hub_download(repo_id=REPO_ID, repo_type="dataset", filename=filename, local_dir=str(d)))
        actual = sha256_file(p)
        if actual != expected:
            raise RuntimeError(f"SHA256 mismatch for {filename}: {actual} != {expected}")
        paths[filename] = p
        hashes[filename] = actual

    con = duckdb.connect(database=":memory:")
    mig = str(paths["migrations.parquet"].resolve()).replace("'", "''")
    tok = str(paths["tokens.parquet"].resolve()).replace("'", "''")
    post = str(paths["postgard_snapshots.parquet"].resolve()).replace("'", "''")

    con.execute(f"CREATE VIEW migrations AS SELECT mint,migrated_at,pool_address,seconds_to_graduation FROM read_parquet('{mig}')")
    con.execute(f"CREATE VIEW tokens AS SELECT mint,is_mayhem_mode,top10_pct_suspect FROM read_parquet('{tok}')")
    # Critical leakage wall: no price values are projected into the SQL view.
    con.execute(f"""
        CREATE VIEW post_meta AS
        SELECT mint,snapshot_time,pair_address,dex_id,incomplete_data,
               (price_native IS NOT NULL) AS has_native_price
        FROM read_parquet('{post}')
    """)

    dup = con.execute("SELECT mint,count(*) n FROM migrations GROUP BY 1 HAVING count(*)>1 ORDER BY n DESC,mint").fetchall()
    if dup:
        raise RuntimeError(f"duplicate migration mints fail closed: {len(dup)}")

    con.execute("""
        CREATE TEMP VIEW base AS
        SELECT m.mint,m.migrated_at AS t0,m.pool_address,m.seconds_to_graduation,
               t.top10_pct_suspect
        FROM migrations m
        JOIN tokens t USING(mint)
        WHERE m.pool_address IS NOT NULL
          AND m.pool_address NOT IN ('synthetic_graduation_queue','backfilled_from_pumpswap_trade')
          AND CAST(m.migrated_at AS DATE) <> DATE '2026-07-03'
          AND COALESCE(t.is_mayhem_mode,FALSE)=FALSE
    """)

    con.execute("""
        CREATE TEMP VIEW entries AS
        SELECT b.*,
               min(p.snapshot_time) FILTER (
                   WHERE p.pair_address=b.pool_address
                     AND COALESCE(p.incomplete_data,FALSE)=FALSE
                     AND p.has_native_price
                     AND p.snapshot_time >= b.t0 + INTERVAL 15 SECOND
                     AND p.snapshot_time <= b.t0 + INTERVAL 90 SECOND
               ) AS entry_ts
        FROM base b
        LEFT JOIN post_meta p USING(mint)
        GROUP BY b.mint,b.t0,b.pool_address,b.seconds_to_graduation,b.top10_pct_suspect
    """)

    con.execute("""
        CREATE TEMP VIEW eligible AS
        SELECT e.*,
               min(p.snapshot_time) FILTER (
                   WHERE e.entry_ts IS NOT NULL
                     AND p.pair_address=e.pool_address
                     AND COALESCE(p.incomplete_data,FALSE)=FALSE
                     AND p.has_native_price
                     AND p.snapshot_time >= e.entry_ts + INTERVAL 300 SECOND
                     AND p.snapshot_time <= e.entry_ts + INTERVAL 420 SECOND
               ) AS exit_ts
        FROM entries e
        LEFT JOIN post_meta p USING(mint)
        GROUP BY e.mint,e.t0,e.pool_address,e.seconds_to_graduation,e.top10_pct_suspect,e.entry_ts
    """)

    rows = con.execute("""
        SELECT mint,t0,pool_address,seconds_to_graduation,top10_pct_suspect,entry_ts,exit_ts
        FROM eligible
        WHERE entry_ts IS NOT NULL AND exit_ts IS NOT NULL
        ORDER BY t0,mint
    """).fetchall()

    cols = ["mint","t0","pool_address","seconds_to_graduation","top10_pct_suspect","entry_ts","exit_ts"]
    out_path = Path(args.out)
    with out_path.open("w", encoding="utf-8") as f:
        for values in rows:
            obj = dict(zip(cols, values))
            # Preserve only timing/identity metadata; never price values.
            serial = {
                "lab": "PMD-001",
                "stage": "SOURCE_REBUILD_MANIFEST_V01",
                "outcomes_opened": False,
                "mint": obj["mint"],
                "t0": str(obj["t0"]),
                "pool_address": obj["pool_address"],
                "seconds_to_graduation": obj["seconds_to_graduation"],
                "top10_pct_suspect": bool(obj["top10_pct_suspect"]) if obj["top10_pct_suspect"] is not None else False,
                "entry_ts_meta_only": str(obj["entry_ts"]),
                "exit_ts_meta_only": str(obj["exit_ts"]),
                "regime_post_2026_07_04": str(obj["t0"]).startswith(("2026-07-05","2026-07-06","2026-07-07","2026-07-08","2026-07-09","2026-07-10","2026-07-11","2026-07-12","2026-07-13","2026-07-14")),
            }
            f.write(json.dumps(serial, sort_keys=True, default=str) + "\n")

    distinct_dates = con.execute("SELECT count(DISTINCT CAST(t0 AS DATE)) FROM eligible WHERE entry_ts IS NOT NULL AND exit_ts IS NOT NULL").fetchone()[0]
    out_hash = sha256_file(out_path)
    receipt = {
        "lab": "PMD-001",
        "stage": "SOURCE_REBUILD_MANIFEST_V01",
        "outcomes_opened": False,
        "source_hashes": hashes,
        "rows": len(rows),
        "distinct_dates": distinct_dates,
        "expected_rows": EXPECTED_ROWS,
        "expected_distinct_dates": EXPECTED_DISTINCT_DATES,
        "manifest_sha256": out_hash,
        "post_price_values_projected": False,
        "postgard_outcomes_opened": False,
        "pass": len(rows) == EXPECTED_ROWS and distinct_dates == EXPECTED_DISTINCT_DATES,
    }
    Path(args.receipt).write_text(json.dumps(receipt, indent=2, sort_keys=True, default=str)+"\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True, default=str))
    return 0 if receipt["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
