#!/usr/bin/env python3
"""PMD-001 post-migration timestamp resolution diagnostic.

No post-migration price value is selected or read into analysis; only price NULLness,
source timestamps, pair identity, DEX id and incomplete-data flags are used.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
from huggingface_hub import hf_hub_download
import duckdb

REPO_ID="Slinky21/Pumpfun_Memecoin_Corpus"
FILES=["migrations.parquet","tokens.parquet","postgard_snapshots.parquet"]
SENTINELS="'synthetic_graduation_queue','backfilled_from_pumpswap_trade'"

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--data-dir",default="pmd_postres"); ap.add_argument("--out",default="pmd_post_resolution_v01.json"); a=ap.parse_args()
    d=Path(a.data_dir); d.mkdir(parents=True,exist_ok=True)
    p={f:hf_hub_download(repo_id=REPO_ID,repo_type="dataset",filename=f,local_dir=str(d)) for f in FILES}
    q=duckdb.connect(":memory:")
    def ep(f): return str(Path(p[f]).resolve()).replace("'","''")
    q.execute(f"CREATE VIEW m AS SELECT * FROM read_parquet('{ep('migrations.parquet')}')")
    q.execute(f"CREATE VIEW t AS SELECT mint,is_mayhem_mode FROM read_parquet('{ep('tokens.parquet')}')")
    q.execute(f"""CREATE VIEW p AS SELECT mint,snapshot_time,pair_address,dex_id,incomplete_data,(price_native IS NOT NULL) has_price FROM read_parquet('{ep('postgard_snapshots.parquet')}')""")
    q.execute(f"""CREATE TEMP VIEW b AS SELECT m.mint,m.migrated_at t0,m.pool_address FROM m JOIN t USING(mint)
      WHERE m.pool_address IS NOT NULL AND m.pool_address NOT IN ({SENTINELS})
      AND COALESCE(t.is_mayhem_mode,FALSE)=FALSE AND CAST(m.migrated_at AS DATE)<>DATE '2026-07-03'""")
    q.execute("""CREATE TEMP VIEW firsts AS
      SELECT b.mint,b.t0,b.pool_address,
        min(p.snapshot_time) FILTER(WHERE p.pair_address=b.pool_address AND NOT p.incomplete_data AND p.has_price AND p.snapshot_time>=b.t0) first_ts,
        min(p.snapshot_time) FILTER(WHERE p.pair_address=b.pool_address AND NOT p.incomplete_data AND p.has_price AND p.snapshot_time>=b.t0+INTERVAL 15 SECOND) first15_ts
      FROM b LEFT JOIN p USING(mint) GROUP BY 1,2,3""")
    q.execute("""CREATE TEMP VIEW timing AS
      SELECT f.*,
        date_diff('millisecond',f.t0,f.first_ts)/1000.0 first_lag_s,
        date_diff('millisecond',f.t0,f.first15_ts)/1000.0 first15_lag_from_t0_s,
        (SELECT min(p.snapshot_time) FROM p WHERE p.mint=f.mint AND p.pair_address=f.pool_address AND NOT p.incomplete_data AND p.has_price
          AND f.first_ts IS NOT NULL AND p.snapshot_time>=f.first_ts+INTERVAL 300 SECOND) exit_ts,
        (SELECT min(p.snapshot_time) FROM p WHERE p.mint=f.mint AND p.pair_address=f.pool_address AND NOT p.incomplete_data AND p.has_price
          AND f.first15_ts IS NOT NULL AND p.snapshot_time>=f.first15_ts+INTERVAL 300 SECOND) exit15_ts
      FROM firsts f""")
    q.execute("""CREATE TEMP VIEW timing2 AS SELECT *,
      CASE WHEN exit_ts IS NULL OR first_ts IS NULL THEN NULL ELSE date_diff('millisecond',first_ts+INTERVAL 300 SECOND,exit_ts)/1000.0 END exit_target_lag_s,
      CASE WHEN exit15_ts IS NULL OR first15_ts IS NULL THEN NULL ELSE date_diff('millisecond',first15_ts+INTERVAL 300 SECOND,exit15_ts)/1000.0 END exit15_target_lag_s
      FROM timing""")
    out={"lab":"PMD-001","stage":"POST_SOURCE_RESOLUTION_DIAGNOSTIC_V01","outcomes_opened":False}
    out["base_rows"]=q.execute("SELECT count(*) FROM b").fetchone()[0]
    out["first_valid_post_rows"]=q.execute("SELECT count(*) FROM timing2 WHERE first_ts IS NOT NULL").fetchone()[0]
    out["first_lag_quantiles_s"]=q.execute("SELECT quantile_cont(first_lag_s,[0,0.1,0.25,0.5,0.75,0.9,0.95,0.99,1]) FROM timing2 WHERE first_lag_s IS NOT NULL").fetchone()[0]
    out["exit_target_lag_quantiles_s"]=q.execute("SELECT quantile_cont(exit_target_lag_s,[0,0.1,0.25,0.5,0.75,0.9,0.95,0.99,1]) FROM timing2 WHERE exit_target_lag_s IS NOT NULL").fetchone()[0]
    entry_caps=[30,60,120,180,300,600,900]
    exit_caps=[30,60,120,180,300,600,900]
    out["entry_availability"]={str(c):q.execute("SELECT count(*) FROM timing2 WHERE first_lag_s BETWEEN 0 AND ?",[c]).fetchone()[0] for c in entry_caps}
    matrix={}
    for ec in entry_caps:
        matrix[str(ec)]={}
        for xc in exit_caps:
            matrix[str(ec)][str(xc)]=q.execute("SELECT count(*) FROM timing2 WHERE first_lag_s BETWEEN 0 AND ? AND exit_target_lag_s BETWEEN 0 AND ?",[ec,xc]).fetchone()[0]
    out["entry_exit_availability_matrix"]=matrix

    # Preserve the economic execution guard: no entry earlier than T0+15s.
    caps_from_t0=[60,90,120,150,180,300]
    out["entry15_availability"]={str(c):q.execute("SELECT count(*) FROM timing2 WHERE first15_lag_from_t0_s BETWEEN 15 AND ?",[c]).fetchone()[0] for c in caps_from_t0}
    out["entry15_exit120_availability"]={str(c):q.execute("SELECT count(*) FROM timing2 WHERE first15_lag_from_t0_s BETWEEN 15 AND ? AND exit15_target_lag_s BETWEEN 0 AND 120",[c]).fetchone()[0] for c in caps_from_t0}
    out["entry15_exit120_dates"]={str(c):q.execute("SELECT count(DISTINCT CAST(t0 AS DATE)) FROM timing2 WHERE first15_lag_from_t0_s BETWEEN 15 AND ? AND exit15_target_lag_s BETWEEN 0 AND 120",[c]).fetchone()[0] for c in caps_from_t0}
    out["entry15_lag_quantiles_s"]=q.execute("SELECT quantile_cont(first15_lag_from_t0_s,[0,0.1,0.25,0.5,0.75,0.9,0.95,0.99,1]) FROM timing2 WHERE first15_lag_from_t0_s IS NOT NULL").fetchone()[0]
    out["exit15_target_lag_quantiles_s"]=q.execute("SELECT quantile_cont(exit15_target_lag_s,[0,0.1,0.25,0.5,0.75,0.9,0.95,0.99,1]) FROM timing2 WHERE exit15_target_lag_s IS NOT NULL").fetchone()[0]
    out["dex_exact_pool_counts"]=q.execute("SELECT p.dex_id,count(*) FROM b JOIN p USING(mint) WHERE p.pair_address=b.pool_address GROUP BY 1 ORDER BY 2 DESC").fetchall()
    Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True,default=str)+"\n")
    print(json.dumps(out,indent=2,sort_keys=True,default=str))
    return 0
if __name__=='__main__': raise SystemExit(main())
