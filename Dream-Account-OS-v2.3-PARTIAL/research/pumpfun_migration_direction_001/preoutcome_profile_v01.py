#!/usr/bin/env python3
"""PMD-001 outcome-blind coverage profiler.

Reads only source identity/timestamps/nullness and pre-migration aggregate fields.
It MUST NOT read post-migration price values or compute any return/label.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
from huggingface_hub import hf_hub_download
import duckdb

REPO_ID = "Slinky21/Pumpfun_Memecoin_Corpus"
FILES = ["migrations.parquet", "tokens.parquet", "snapshots.parquet", "postgard_snapshots.parquet"]
SENTINELS = ("synthetic_graduation_queue", "backfilled_from_pumpswap_trade")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="pmd_profile_data")
    ap.add_argument("--out", default="pmd_preoutcome_profile_v01.json")
    args = ap.parse_args()
    d = Path(args.data_dir); d.mkdir(parents=True, exist_ok=True)
    paths = {}
    for f in FILES:
        paths[f] = hf_hub_download(repo_id=REPO_ID, repo_type="dataset", filename=f, local_dir=str(d))

    con = duckdb.connect(database=":memory:")
    mig = str(Path(paths["migrations.parquet"]).resolve()).replace("'", "''")
    tok = str(Path(paths["tokens.parquet"]).resolve()).replace("'", "''")
    pre = str(Path(paths["snapshots.parquet"]).resolve()).replace("'", "''")
    post = str(Path(paths["postgard_snapshots.parquet"]).resolve()).replace("'", "''")

    con.execute(f"CREATE VIEW migrations AS SELECT * FROM read_parquet('{mig}')")
    con.execute(f"CREATE VIEW tokens AS SELECT * FROM read_parquet('{tok}')")
    con.execute(f"CREATE VIEW pre AS SELECT * FROM read_parquet('{pre}')")
    # Deliberately exclude every post-migration price/value field from the view.
    con.execute(f"""CREATE VIEW post_meta AS
        SELECT mint, snapshot_time, seconds_since_graduation, phase, pair_address, dex_id, incomplete_data,
               (price_native IS NOT NULL) AS has_native_price
        FROM read_parquet('{post}')""")

    out = {"lab":"PMD-001","stage":"PRE_OUTCOME_COVERAGE_PROFILE_V01","outcomes_opened":False}
    out["pre_bucket_seconds"] = con.execute("SELECT bucket_seconds, count(*) n FROM pre GROUP BY 1 ORDER BY 1").fetchall()
    out["pre_phase_counts"] = con.execute("SELECT phase, count(*) n FROM pre GROUP BY 1 ORDER BY 1").fetchall()
    out["post_phase_counts"] = con.execute("SELECT phase, count(*) n FROM post_meta GROUP BY 1 ORDER BY 1").fetchall()
    out["post_dex_counts"] = con.execute("SELECT dex_id, count(*) n FROM post_meta GROUP BY 1 ORDER BY 2 DESC LIMIT 20").fetchall()

    con.execute("""
      CREATE TEMP VIEW base AS
      SELECT m.mint, m.migrated_at AS t0, m.pool_address, m.seconds_to_graduation,
             t.is_mayhem_mode, t.top10_pct_suspect
      FROM migrations m
      JOIN tokens t USING(mint)
      WHERE m.pool_address IS NOT NULL
        AND m.pool_address NOT IN ('synthetic_graduation_queue','backfilled_from_pumpswap_trade')
        AND CAST(m.migrated_at AS DATE) <> DATE '2026-07-03'
        AND COALESCE(t.is_mayhem_mode, FALSE) = FALSE
    """)
    out["base_rows"] = con.execute("SELECT count(*) FROM base").fetchone()[0]
    out["base_distinct_mints"] = con.execute("SELECT count(DISTINCT mint) FROM base").fetchone()[0]
    out["base_distinct_dates"] = con.execute("SELECT count(DISTINCT CAST(t0 AS DATE)) FROM base").fetchone()[0]
    out["base_time_minmax"] = [str(x) for x in con.execute("SELECT min(t0), max(t0) FROM base").fetchone()]
    out["suspect_top10_rows_in_base"] = con.execute("SELECT count(*) FROM base WHERE COALESCE(top10_pct_suspect,FALSE)").fetchone()[0]

    # Cross-source pool identity check; uses addresses/timestamps/nullness only.
    con.execute("""
      CREATE TEMP VIEW post_cov AS
      SELECT b.mint, b.t0, b.pool_address,
             count(*) FILTER (WHERE p.pair_address = b.pool_address) AS exact_pool_rows,
             count(*) FILTER (WHERE p.pair_address <> b.pool_address) AS other_pool_rows,
             min(p.snapshot_time) FILTER (
               WHERE p.pair_address=b.pool_address AND NOT p.incomplete_data AND p.has_native_price
                 AND p.snapshot_time >= b.t0 + INTERVAL 15 SECOND
                 AND p.snapshot_time <= b.t0 + INTERVAL 60 SECOND
             ) AS entry_ts
      FROM base b LEFT JOIN post_meta p USING(mint)
      GROUP BY b.mint,b.t0,b.pool_address
    """)
    con.execute("""
      CREATE TEMP VIEW exec_cov AS
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
    out["post_exact_pool_any"] = con.execute("SELECT count(*) FROM exec_cov WHERE exact_pool_rows>0").fetchone()[0]
    out["entry_available"] = con.execute("SELECT count(*) FROM exec_cov WHERE entry_ts IS NOT NULL").fetchone()[0]
    out["entry_and_exit_available"] = con.execute("SELECT count(*) FROM exec_cov WHERE entry_ts IS NOT NULL AND has_exit").fetchone()[0]
    out["pair_mismatch_only"] = con.execute("SELECT count(*) FROM exec_cov WHERE exact_pool_rows=0 AND other_pool_rows>0").fetchone()[0]

    # Pre-migration coverage. No post-price fields are visible in this query.
    con.execute("""
      CREATE TEMP VIEW pre_cov AS
      SELECT b.mint, b.t0,
             count(*) FILTER (WHERE s.bucket_start < b.t0 AND s.bucket_start >= b.t0-INTERVAL 300 SECOND) AS n300,
             count(*) FILTER (WHERE s.bucket_start < b.t0 AND s.bucket_start >= b.t0-INTERVAL 60 SECOND) AS n60,
             count(*) FILTER (WHERE s.bucket_start < b.t0 AND s.bucket_start >= b.t0-INTERVAL 30 SECOND) AS n30,
             max(s.bucket_start) FILTER (WHERE s.bucket_start < b.t0) AS last_pre_ts
      FROM base b LEFT JOIN pre s USING(mint)
      GROUP BY b.mint,b.t0
    """)
    out["pre_any_300"] = con.execute("SELECT count(*) FROM pre_cov WHERE n300>0").fetchone()[0]
    out["pre_any_60"] = con.execute("SELECT count(*) FROM pre_cov WHERE n60>0").fetchone()[0]
    out["pre_any_30"] = con.execute("SELECT count(*) FROM pre_cov WHERE n30>0").fetchone()[0]
    out["pre_coverage_quantiles"] = con.execute("""
      SELECT quantile_cont(n300,0.0),quantile_cont(n300,0.1),quantile_cont(n300,0.5),
             quantile_cont(n300,0.9),quantile_cont(n300,1.0) FROM pre_cov
    """).fetchone()

    con.execute("""
      CREATE TEMP VIEW eligible_source AS
      SELECT b.mint,b.t0,b.pool_address,b.seconds_to_graduation,b.top10_pct_suspect,
             p.n300,p.n60,p.n30,e.entry_ts,e.has_exit
      FROM base b JOIN pre_cov p USING(mint,t0) JOIN exec_cov e USING(mint,t0)
      WHERE p.n300>0 AND e.entry_ts IS NOT NULL AND e.has_exit
    """)
    out["eligible_source_rows"] = con.execute("SELECT count(*) FROM eligible_source").fetchone()[0]
    out["eligible_source_distinct_dates"] = con.execute("SELECT count(DISTINCT CAST(t0 AS DATE)) FROM eligible_source").fetchone()[0]
    out["eligible_source_by_date"] = [[str(d), int(n)] for d,n in con.execute("SELECT CAST(t0 AS DATE),count(*) FROM eligible_source GROUP BY 1 ORDER BY 1").fetchall()]
    n=out["eligible_source_rows"]
    out["frozen_count_split_sizes"]={"discovery":int(n*0.60),"validation":int(n*0.20),"holdout":n-int(n*0.60)-int(n*0.20)}
    out["minimum_sample_gate_pass"] = (n>=1000 and int(n*0.20)>=200 and out["eligible_source_distinct_dates"]>=20)
    out["verdict"] = "COVERAGE_GATE_PASS" if out["minimum_sample_gate_pass"] else "COVERAGE_GATE_FAIL_CLOSED"
    Path(args.out).write_text(json.dumps(out,indent=2,sort_keys=True,default=str)+"\n",encoding="utf-8")
    print(json.dumps(out,indent=2,sort_keys=True,default=str))
    return 0 if out["minimum_sample_gate_pass"] else 2

if __name__ == "__main__": raise SystemExit(main())
