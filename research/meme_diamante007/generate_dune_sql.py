#!/usr/bin/env python3
"""Generate exact 36 frozen MEME006 price-trigger windows for Dune; never executes SQL."""
import datetime as dt
import hashlib
import json
import pathlib
import sys

EXPECTED_HASH="477b3a69edc4e2dd8a08c1d40a5a9d0e7584a0a43143791224c692b1ba4121a4"
POLICIES={"H_REVERSAL_PRICE_ONLY","H_MOMENTUM_PRICE_ONLY"}

def selected_from_report(blob,expected_hash=EXPECTED_HASH):
    if hashlib.sha256(blob).hexdigest()!=expected_hash:
        raise RuntimeError("SOURCE_INTEGRITY_BLOCKED: MEME006 HIST001 report hash changed")
    report=json.loads(blob)
    rows=[x for x in report.get("proxy_price_events",[])
          if x.get("policy") in POLICIES]
    if len(rows)!=36:
        raise RuntimeError("SOURCE_INTEGRITY_BLOCKED: expected exactly 36 price-only signals")
    seen=set()
    cohort={x["coin_id"]:x for x in report.get("cohort",[])}
    if len(cohort)!=6:raise RuntimeError("SOURCE_INTEGRITY_BLOCKED: expected 6 source coins")
    selected=[]
    for x in rows:
        coin=x["coin_id"]
        if coin not in cohort:raise RuntimeError("SOURCE_INTEGRITY_BLOCKED: unknown source coin")
        ts=int(x["observed_at"])
        at=dt.datetime.fromtimestamp(ts,dt.timezone.utc)
        if at.hour%2 or at.minute!=37 or at.second!=0:
            raise RuntimeError("SOURCE_INTEGRITY_BLOCKED: wrong HH:37 UTC timestamp")
        if not dt.datetime(2026,10,1,tzinfo=dt.timezone.utc)<=at<dt.datetime(2026,11,15,tzinfo=dt.timezone.utc):
            raise RuntimeError("SOURCE_INTEGRITY_BLOCKED: outside 45d window")
        key=(coin,ts,x["policy"])
        if key in seen:raise RuntimeError("SOURCE_INTEGRITY_BLOCKED: duplicate trigger")
        seen.add(key)
        selected.append(dict(coin_id=coin,observed_at=at.strftime("%Y-%m-%d %H:%M:%S"),
            mint=cohort[coin]["mint"],pool=cohort[coin]["pool"],policy=x["policy"],
            h1_pct=x["h1_pct"],h6_pct=x["h6_pct"]))
    return sorted(selected,key=lambda x:(x["observed_at"],x["coin_id"]))

def sql_quote(x):
    return x.replace("'","''")

def make_sql(rows):
    values=",\n".join(
      "  ('"+sql_quote(x["coin_id"])+"', '"+sql_quote(x["mint"])+"', '"+sql_quote(x["pool"])+"', '"+sql_quote(x["policy"])+"', TIMESTAMP '"+x["observed_at"]+"')"
      for x in rows)
    return """-- MEME007 query-ready ONLY; NOT executed. Data source Dune public dex_solana.trades.
-- Exactly the 36 historically frozen price-only trigger windows, no hindsight relabeling.
-- Buyer/seller data are event legs; multiple rows per economic transaction possible.
-- project_main_id may NOT be the DexScreener pool address; no pool match means UNKNOWN.
-- Request/execute via authenticated Dune editor/API ONLY with operator-approved billing.
WITH windows (coin_id, mint, target_pool, policy, observed_at) AS (
 VALUES
"""+values+"""
),
trades AS (
  SELECT w.coin_id, w.mint, w.target_pool, w.policy, w.observed_at,
    t.block_time, t.block_slot, t.project, t.project_main_id,
    t.trade_source, t.tx_id, t.trader_id,
    t.outer_instruction_index, t.inner_instruction_index, t.tx_index,
    t.token_bought_mint_address, t.token_sold_mint_address,
    t.token_bought_amount, t.token_sold_amount, t.amount_usd,
    CASE
      WHEN t.token_bought_mint_address=w.mint AND t.token_sold_mint_address<>w.mint
        THEN 'BUY'
      WHEN t.token_sold_mint_address=w.mint AND t.token_bought_mint_address<>w.mint
        THEN 'SELL'
      ELSE 'AMBIGUOUS'
    END AS raw_leg_side,
    CASE WHEN t.project_main_id=w.target_pool THEN true ELSE false END AS direct_pool_id_match
  FROM dex_solana.trades t
  JOIN windows w
    ON (t.token_bought_mint_address=w.mint OR t.token_sold_mint_address=w.mint)
   AND t.block_time >= w.observed_at - INTERVAL '1' HOUR
   AND t.block_time < w.observed_at
  WHERE t.block_time >= TIMESTAMP '2026-09-30 23:37:00'
    AND t.block_time < TIMESTAMP '2026-11-14 23:00:00'
)
SELECT *
FROM trades
ORDER BY observed_at, coin_id, block_time, tx_id, outer_instruction_index, inner_instruction_index;
"""

def main(argv):
    path=pathlib.Path(argv[1])
    rows=selected_from_report(path.read_bytes())
    out=pathlib.Path("meme007-dune-ready")
    out.mkdir(exist_ok=True)
    sql=make_sql(rows)
    p=out/"dune_exact_36_windows.sql"
    p.write_text(sql,encoding="utf8")
    data=json.dumps(rows,indent=2,sort_keys=True).encode()
    (out/"frozen_36_windows.json").write_bytes(data)
    metadata=dict(
      candidate_windows=len(rows),
      counts={p:sum(x["policy"]==p for x in rows) for p in sorted(POLICIES)},
      original_report_sha256=EXPECTED_HASH,
      sql_sha256=hashlib.sha256(sql.encode()).hexdigest(),
      rows_sha256=hashlib.sha256(data).hexdigest(),
      sql_executed=False,actual_trades_retrieved=0,
      warning="Do not treat unmatched project_main_id as zero swaps; verify venue pool mapping.")
    (out/"manifest.json").write_text(json.dumps(metadata,indent=2,sort_keys=True)+"\n")
    print("MEME007_DUNE_PREP="+json.dumps(metadata,sort_keys=True))

if __name__=="__main__":main(sys.argv)
