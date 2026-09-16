#!/usr/bin/env python3
"""PMD-001 full raw-trade coverage gate, outcome-blind.

Downloads all raw trade shards plus only metadata needed to reconstruct the frozen
source-eligible post-migration universe. It NEVER reads post-migration price values;
it reads only their non-nullness and timestamps to enforce availability.

No return, PnL, sign label, feature/outcome relationship or outcome file is opened.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb
from huggingface_hub import HfApi, hf_hub_download

REPO_ID = "Slinky21/Pumpfun_Memecoin_Corpus"
SENTINELS = "'synthetic_graduation_queue','backfilled_from_pumpswap_trade'"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="pmd_trade_coverage")
    ap.add_argument("--out", default="pmd_trade_coverage_gate_v01.json")
    args = ap.parse_args()
    d = Path(args.data_dir); d.mkdir(parents=True, exist_ok=True)

    api = HfApi()
    all_files = api.list_repo_files(REPO_ID, repo_type="dataset")
    shards = sorted(f for f in all_files if f.startswith("trades/") and f.endswith(".parquet"))
    if len(shards) != 18:
        raise RuntimeError(f"Expected 18 raw trade shards, found {len(shards)}")

    fixed = ["migrations.parquet", "tokens.parquet", "postgard_snapshots.parquet"]
    paths = {}
    for f in fixed + shards:
        paths[f] = Path(hf_hub_download(repo_id=REPO_ID, repo_type="dataset", filename=f, local_dir=str(d))).resolve()

    con = duckdb.connect(database=":memory:")
    def esc(p: Path) -> str: return str(p).replace("'", "''")
    mig = esc(paths["migrations.parquet"]); tok = esc(paths["tokens.parquet"]); post = esc(paths["postgard_snapshots.parquet"])
    trade_glob = esc(d.resolve() / "trades" / "*.parquet")

    con.execute(f"CREATE VIEW migrations AS SELECT * FROM read_parquet('{mig}')")
    con.execute(f"CREATE VIEW tokens AS SELECT mint,is_mayhem_mode FROM read_parquet('{tok}')")
    # Critical leakage wall: price value is never selected, only whether it is present.
    con.execute(f"""CREATE VIEW post_meta AS
      SELECT mint,snapshot_time,pair_address,dex_id,incomplete_data,(price_native IS NOT NULL) AS has_price
      FROM read_parquet('{post}')""")
    con.execute(f"""CREATE VIEW trades AS
      SELECT mint,event_time,user_wallet,is_buy,token_amount,curve_pct_depleted,
             v_tokens_bonding_curve,v_sol_bonding_curve,source,tx_signature
      FROM read_parquet('{trade_glob}', union_by_name=true)""")

    con.execute(f"""CREATE TEMP VIEW base AS
      SELECT m.mint,m.migrated_at AS t0,m.pool_address
      FROM migrations m JOIN tokens t USING(mint)
      WHERE m.pool_address IS NOT NULL
        AND m.pool_address NOT IN ({SENTINELS})
        AND COALESCE(t.is_mayhem_mode,FALSE)=FALSE
        AND CAST(m.migrated_at AS DATE)<>DATE '2026-07-03'""")

    # Frozen source-amendment execution universe: entry >= T0+15s and <=T0+90s;
    # first 5m target exit no more than 120s late. Values remain sealed.
    con.execute("""CREATE TEMP VIEW entry_meta AS
      SELECT b.mint,b.t0,b.pool_address,
        min(p.snapshot_time) FILTER (
          WHERE p.pair_address=b.pool_address AND p.dex_id='pumpswap'
            AND NOT p.incomplete_data AND p.has_price
            AND p.snapshot_time>=b.t0+INTERVAL 15 SECOND
            AND p.snapshot_time<=b.t0+INTERVAL 90 SECOND
        ) AS entry_ts
      FROM base b LEFT JOIN post_meta p USING(mint)
      GROUP BY 1,2,3""")
    con.execute("""CREATE TEMP VIEW executable AS
      SELECT e.*,
        (SELECT min(p.snapshot_time) FROM post_meta p
         WHERE p.mint=e.mint AND p.pair_address=e.pool_address AND p.dex_id='pumpswap'
           AND NOT p.incomplete_data AND p.has_price AND e.entry_ts IS NOT NULL
           AND p.snapshot_time>=e.entry_ts+INTERVAL 300 SECOND
           AND p.snapshot_time<=e.entry_ts+INTERVAL 420 SECOND) AS exit_ts
      FROM entry_meta e""")
    con.execute("CREATE TEMP VIEW exec1012 AS SELECT * FROM executable WHERE entry_ts IS NOT NULL AND exit_ts IS NOT NULL")

    # Raw trade source coverage strictly before T0. No post-T0 trade enters diagnostics.
    con.execute("""CREATE TEMP VIEW raw_cov AS
      SELECT e.mint,e.t0,e.entry_ts,e.exit_ts,
        count(t.tx_signature) FILTER(WHERE t.event_time<e.t0 AND t.event_time>=e.t0-INTERVAL 30 SECOND) n30,
        count(t.tx_signature) FILTER(WHERE t.event_time<e.t0 AND t.event_time>=e.t0-INTERVAL 60 SECOND) n60,
        count(t.tx_signature) FILTER(WHERE t.event_time<e.t0 AND t.event_time>=e.t0-INTERVAL 300 SECOND) n300,
        count(DISTINCT t.user_wallet) FILTER(WHERE t.event_time<e.t0 AND t.event_time>=e.t0-INTERVAL 30 SECOND) wallets30,
        count(DISTINCT t.user_wallet) FILTER(WHERE t.event_time<e.t0 AND t.event_time>=e.t0-INTERVAL 60 SECOND) wallets60,
        count(DISTINCT t.user_wallet) FILTER(WHERE t.event_time<e.t0 AND t.event_time>=e.t0-INTERVAL 300 SECOND) wallets300,
        max(t.event_time) FILTER(WHERE t.event_time<e.t0) last_pre_trade,
        min(t.event_time) FILTER(WHERE t.event_time<e.t0) first_pre_trade,
        count(t.tx_signature) FILTER(WHERE t.event_time>=e.t0) post_t0_rows_seen_but_forbidden
      FROM exec1012 e LEFT JOIN trades t USING(mint)
      GROUP BY 1,2,3,4""")
    con.execute("""CREATE TEMP VIEW cov2 AS
      SELECT *,
        CASE WHEN last_pre_trade IS NULL THEN NULL ELSE date_diff('millisecond',last_pre_trade,t0)/1000.0 END AS last_pre_lag_s
      FROM raw_cov""")

    out = {
      "lab":"PMD-001",
      "stage":"FULL_RAW_TRADE_COVERAGE_GATE_V01",
      "outcomes_opened":False,
      "raw_trade_shards":len(shards),
      "raw_trade_rows":con.execute("SELECT count(*) FROM trades").fetchone()[0],
      "raw_trade_distinct_mints":con.execute("SELECT count(DISTINCT mint) FROM trades").fetchone()[0],
      "source_executable_rows":con.execute("SELECT count(*) FROM exec1012").fetchone()[0],
      "source_executable_dates":con.execute("SELECT count(DISTINCT CAST(t0 AS DATE)) FROM exec1012").fetchone()[0],
    }
    out["raw_coverage"] = {
      "any_pre_trade": con.execute("SELECT count(*) FROM cov2 WHERE last_pre_trade IS NOT NULL").fetchone()[0],
      "any_30s": con.execute("SELECT count(*) FROM cov2 WHERE n30>0").fetchone()[0],
      "any_60s": con.execute("SELECT count(*) FROM cov2 WHERE n60>0").fetchone()[0],
      "any_300s": con.execute("SELECT count(*) FROM cov2 WHERE n300>0").fetchone()[0],
      "wallets_30s": con.execute("SELECT count(*) FROM cov2 WHERE wallets30>0").fetchone()[0],
      "wallets_60s": con.execute("SELECT count(*) FROM cov2 WHERE wallets60>0").fetchone()[0],
      "wallets_300s": con.execute("SELECT count(*) FROM cov2 WHERE wallets300>0").fetchone()[0],
    }
    out["last_pre_trade_lag_quantiles_s"] = con.execute(
      "SELECT quantile_cont(last_pre_lag_s,[0,0.01,0.05,0.1,0.25,0.5,0.75,0.9,0.95,0.99,1]) FROM cov2 WHERE last_pre_lag_s IS NOT NULL"
    ).fetchone()[0]
    out["n30_quantiles"] = con.execute("SELECT quantile_cont(n30,[0,0.1,0.25,0.5,0.75,0.9,0.99,1]) FROM cov2").fetchone()[0]
    out["n60_quantiles"] = con.execute("SELECT quantile_cont(n60,[0,0.1,0.25,0.5,0.75,0.9,0.99,1]) FROM cov2").fetchone()[0]
    out["n300_quantiles"] = con.execute("SELECT quantile_cont(n300,[0,0.1,0.25,0.5,0.75,0.9,0.99,1]) FROM cov2").fetchone()[0]
    out["wallets60_quantiles"] = con.execute("SELECT quantile_cont(wallets60,[0,0.1,0.25,0.5,0.75,0.9,0.99,1]) FROM cov2").fetchone()[0]
    out["coverage_by_date"] = [[str(d),int(n),int(n60),int(n300)] for d,n,n60,n300 in con.execute("""
      SELECT CAST(t0 AS DATE),count(*),count(*) FILTER(WHERE n60>0),count(*) FILTER(WHERE n300>0)
      FROM cov2 GROUP BY 1 ORDER BY 1""").fetchall()]

    # Pure source candidates for later freeze; not an outcome filter.
    n60 = out["raw_coverage"]["any_60s"]
    n300 = out["raw_coverage"]["any_300s"]
    out["sample_gate_if_require_60s_trade"] = {
      "n": n60,
      "validation_floor": int(n60*0.20),
      "holdout_remainder_floor": n60-int(n60*0.60)-int(n60*0.20),
      "pass": n60>=1000 and int(n60*0.20)>=200,
    }
    out["sample_gate_if_require_300s_trade"] = {
      "n": n300,
      "validation_floor": int(n300*0.20),
      "holdout_remainder_floor": n300-int(n300*0.60)-int(n300*0.20),
      "pass": n300>=1000 and int(n300*0.20)>=200,
    }
    out["verdict"] = "RAW_TRADE_COVERAGE_PROFILE_COMPLETE"
    Path(args.out).write_text(json.dumps(out,indent=2,sort_keys=True,default=str)+"\n",encoding="utf-8")
    print(json.dumps(out,indent=2,sort_keys=True,default=str))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
