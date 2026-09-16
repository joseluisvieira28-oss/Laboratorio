#!/usr/bin/env python3
"""PMD-001 graduation-vs-migration timestamp alignment audit, outcome-blind.

Purpose: determine whether raw bonding-curve trades align to `tokens.graduated_at`
(G0) rather than `migrations.migrated_at` (T0). This script never reads post-price
values, returns, labels, PnL, or outcome files.
"""
from __future__ import annotations

import argparse, json
from pathlib import Path
import duckdb
from huggingface_hub import HfApi, hf_hub_download

REPO_ID = "Slinky21/Pumpfun_Memecoin_Corpus"
SYSTEM_WALLET = "BwWK17cbHxwWBKZkUYvzxLcNQ1YVyaFezduWbtm2de6s"
SENTINELS = "'synthetic_graduation_queue','backfilled_from_pumpswap_trade'"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="pmd_grad_alignment")
    ap.add_argument("--out", default="pmd_graduation_alignment_v01.json")
    a = ap.parse_args()
    d = Path(a.data_dir); d.mkdir(parents=True, exist_ok=True)

    api = HfApi()
    files = api.list_repo_files(REPO_ID, repo_type="dataset")
    shards = sorted(f for f in files if f.startswith("trades/") and f.endswith(".parquet"))
    if len(shards) != 18:
        raise RuntimeError(f"Expected 18 trade shards, found {len(shards)}")
    needed = ["migrations.parquet", "tokens.parquet", "postgard_snapshots.parquet"] + shards
    paths = {f: Path(hf_hub_download(repo_id=REPO_ID, repo_type="dataset", filename=f, local_dir=str(d))).resolve() for f in needed}

    con = duckdb.connect(":memory:")
    esc = lambda p: str(p).replace("'", "''")
    con.execute(f"CREATE VIEW m AS SELECT * FROM read_parquet('{esc(paths['migrations.parquet'])}')")
    con.execute(f"""CREATE VIEW t AS
        SELECT mint,is_mayhem_mode,graduated_at,seconds_to_graduation,detected_at
        FROM read_parquet('{esc(paths['tokens.parquet'])}')""")
    con.execute(f"""CREATE VIEW p AS
        SELECT mint,snapshot_time,pair_address,dex_id,incomplete_data,(price_native IS NOT NULL) has_price
        FROM read_parquet('{esc(paths['postgard_snapshots.parquet'])}')""")
    con.execute(f"""CREATE VIEW tr AS
        SELECT mint,event_time,user_wallet,is_buy,tx_signature
        FROM read_parquet('{esc(d.resolve() / 'trades' / '*.parquet')}', union_by_name=true)""")

    con.execute(f"""CREATE TEMP VIEW base AS
        SELECT m.mint,m.migrated_at t0,m.pool_address,t.graduated_at g0,t.seconds_to_graduation,t.detected_at
        FROM m JOIN t USING(mint)
        WHERE m.pool_address IS NOT NULL AND m.pool_address NOT IN ({SENTINELS})
          AND COALESCE(t.is_mayhem_mode,FALSE)=FALSE
          AND CAST(m.migrated_at AS DATE)<>DATE '2026-07-03'""")
    con.execute("""CREATE TEMP VIEW ent AS
        SELECT b.*,
          min(p.snapshot_time) FILTER(WHERE p.pair_address=b.pool_address AND p.dex_id='pumpswap'
            AND NOT p.incomplete_data AND p.has_price
            AND p.snapshot_time>=b.t0+INTERVAL 15 SECOND AND p.snapshot_time<=b.t0+INTERVAL 90 SECOND) entry_ts
        FROM base b LEFT JOIN p USING(mint)
        GROUP BY ALL""")
    con.execute("""CREATE TEMP VIEW ex AS
        SELECT e.*,
          (SELECT min(p.snapshot_time) FROM p WHERE p.mint=e.mint AND p.pair_address=e.pool_address
            AND p.dex_id='pumpswap' AND NOT p.incomplete_data AND p.has_price AND e.entry_ts IS NOT NULL
            AND p.snapshot_time>=e.entry_ts+INTERVAL 300 SECOND
            AND p.snapshot_time<=e.entry_ts+INTERVAL 420 SECOND) exit_ts
        FROM ent e""")
    con.execute("CREATE TEMP VIEW u AS SELECT * FROM ex WHERE entry_ts IS NOT NULL AND exit_ts IS NOT NULL")

    # Compare raw-trade proximity to G0 vs T0. For feature-eligible 'human' rows, remove known System Program wallet.
    con.execute(f"""CREATE TEMP VIEW align AS
        SELECT u.mint,u.g0,u.t0,u.entry_ts,u.exit_ts,
          date_diff('millisecond',u.g0,u.t0)/1000.0 migration_after_grad_s,
          max(tr.event_time) FILTER(WHERE u.g0 IS NOT NULL AND tr.event_time<u.g0) last_any_before_g0,
          max(tr.event_time) FILTER(WHERE u.g0 IS NOT NULL AND tr.event_time<u.g0 AND tr.user_wallet<>'{SYSTEM_WALLET}') last_human_before_g0,
          count(tr.tx_signature) FILTER(WHERE u.g0 IS NOT NULL AND tr.event_time<u.g0 AND tr.event_time>=u.g0-INTERVAL 30 SECOND AND tr.user_wallet<>'{SYSTEM_WALLET}') human30_g0,
          count(tr.tx_signature) FILTER(WHERE u.g0 IS NOT NULL AND tr.event_time<u.g0 AND tr.event_time>=u.g0-INTERVAL 60 SECOND AND tr.user_wallet<>'{SYSTEM_WALLET}') human60_g0,
          count(tr.tx_signature) FILTER(WHERE u.g0 IS NOT NULL AND tr.event_time<u.g0 AND tr.event_time>=u.g0-INTERVAL 300 SECOND AND tr.user_wallet<>'{SYSTEM_WALLET}') human300_g0,
          count(DISTINCT tr.user_wallet) FILTER(WHERE u.g0 IS NOT NULL AND tr.event_time<u.g0 AND tr.event_time>=u.g0-INTERVAL 60 SECOND AND tr.user_wallet<>'{SYSTEM_WALLET}') wallets60_g0,
          max(tr.event_time) FILTER(WHERE tr.event_time<u.t0 AND tr.user_wallet<>'{SYSTEM_WALLET}') last_human_before_t0
        FROM u LEFT JOIN tr USING(mint)
        GROUP BY u.mint,u.g0,u.t0,u.entry_ts,u.exit_ts""")
    con.execute("""CREATE TEMP VIEW a2 AS SELECT *,
        CASE WHEN last_any_before_g0 IS NULL OR g0 IS NULL THEN NULL ELSE date_diff('millisecond',last_any_before_g0,g0)/1000.0 END any_g0_lag_s,
        CASE WHEN last_human_before_g0 IS NULL OR g0 IS NULL THEN NULL ELSE date_diff('millisecond',last_human_before_g0,g0)/1000.0 END human_g0_lag_s,
        CASE WHEN last_human_before_t0 IS NULL THEN NULL ELSE date_diff('millisecond',last_human_before_t0,t0)/1000.0 END human_t0_lag_s
      FROM align""")

    n = con.execute("SELECT count(*) FROM a2").fetchone()[0]
    out = {
      "lab":"PMD-001","stage":"GRADUATION_TIMESTAMP_ALIGNMENT_V01","outcomes_opened":False,
      "executable_universe_n":n,
      "g0_nonnull":con.execute("SELECT count(*) FROM a2 WHERE g0 IS NOT NULL").fetchone()[0],
      "g0_le_t0":con.execute("SELECT count(*) FROM a2 WHERE g0 IS NOT NULL AND g0<=t0").fetchone()[0],
      "g0_gt_t0":con.execute("SELECT count(*) FROM a2 WHERE g0 IS NOT NULL AND g0>t0").fetchone()[0],
      "migration_after_grad_quantiles_s":con.execute("SELECT quantile_cont(migration_after_grad_s,[0,.01,.05,.1,.25,.5,.75,.9,.95,.99,1]) FROM a2 WHERE migration_after_grad_s IS NOT NULL").fetchone()[0],
      "human_g0_coverage":{"30s":con.execute("SELECT count(*) FROM a2 WHERE human30_g0>0").fetchone()[0],"60s":con.execute("SELECT count(*) FROM a2 WHERE human60_g0>0").fetchone()[0],"300s":con.execute("SELECT count(*) FROM a2 WHERE human300_g0>0").fetchone()[0],"any":con.execute("SELECT count(*) FROM a2 WHERE last_human_before_g0 IS NOT NULL").fetchone()[0]},
      "human_g0_dates":{"60s":con.execute("SELECT count(DISTINCT CAST(g0 AS DATE)) FROM a2 WHERE human60_g0>0").fetchone()[0],"300s":con.execute("SELECT count(DISTINCT CAST(g0 AS DATE)) FROM a2 WHERE human300_g0>0").fetchone()[0]},
      "human_g0_lag_quantiles_s":con.execute("SELECT quantile_cont(human_g0_lag_s,[0,.01,.05,.1,.25,.5,.75,.9,.95,.99,1]) FROM a2 WHERE human_g0_lag_s IS NOT NULL").fetchone()[0],
      "human_t0_lag_quantiles_s":con.execute("SELECT quantile_cont(human_t0_lag_s,[0,.01,.05,.1,.25,.5,.75,.9,.95,.99,1]) FROM a2 WHERE human_t0_lag_s IS NOT NULL").fetchone()[0],
      "human60_g0_quantiles":con.execute("SELECT quantile_cont(human60_g0,[0,.1,.25,.5,.75,.9,.95,.99,1]) FROM a2").fetchone()[0],
      "wallets60_g0_quantiles":con.execute("SELECT quantile_cont(wallets60_g0,[0,.1,.25,.5,.75,.9,.95,.99,1]) FROM a2").fetchone()[0],
      "coverage_by_g0_date":[[str(d),int(total),int(n60),int(n300)] for d,total,n60,n300 in con.execute("SELECT CAST(g0 AS DATE),count(*),count(*) FILTER(WHERE human60_g0>0),count(*) FILTER(WHERE human300_g0>0) FROM a2 WHERE g0 IS NOT NULL GROUP BY 1 ORDER BY 1").fetchall()]
    }
    for key in ("60s","300s"):
        nn = out["human_g0_coverage"][key]
        out[f"sample_gate_if_require_human_{key}_at_g0"]={"n":nn,"discovery":int(nn*.60),"validation":int(nn*.20),"holdout":nn-int(nn*.60)-int(nn*.20),"pass":nn>=1000 and int(nn*.20)>=200 and (nn-int(nn*.60)-int(nn*.20))>=200}
    out["verdict"] = "G0_ALIGNMENT_SUPPORTS_FROZEN_SAMPLE_GATE" if out["sample_gate_if_require_human_60s_at_g0"]["pass"] else "G0_ALIGNMENT_INSUFFICIENT_FOR_FROZEN_SAMPLE_GATE"
    Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True,default=str)+"\n",encoding="utf-8")
    print(json.dumps(out,indent=2,sort_keys=True,default=str))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
