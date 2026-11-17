#!/usr/bin/env python3
"""DIGUI-010 point-in-time sampling coverage; NOT a predictive test."""
from huggingface_hub import hf_hub_download
from pathlib import Path
import duckdb,json,os,time
REV="13bec2bf3089d56d50c35e602616d1b993bb37f5"
P=hf_hub_download("Slinky21/Pumpfun_Memecoin_Corpus","postgard_snapshots.parquet",repo_type="dataset",revision=REV)
c=duckdb.connect()
a=c.execute("""SELECT COUNT(*) n,
COUNT(DISTINCT mint) mints,
MIN(seconds_since_graduation) min_sec,
MAX(seconds_since_graduation) max_sec,
COUNT(DISTINCT mint) FILTER(WHERE seconds_since_graduation BETWEEN 0 AND 60) p0_60,
COUNT(DISTINCT mint) FILTER(WHERE seconds_since_graduation BETWEEN 60 AND 150) p60_150,
COUNT(DISTINCT mint) FILTER(WHERE seconds_since_graduation BETWEEN 240 AND 360) p240_360,
COUNT(DISTINCT mint) FILTER(WHERE seconds_since_graduation BETWEEN 1800 AND 2400) p30m,
COUNT(DISTINCT mint) FILTER(WHERE seconds_since_graduation BETWEEN 3300 AND 3900) p60m,
COUNT(DISTINCT mint) FILTER(WHERE seconds_since_graduation BETWEEN 20*3600 AND 28*3600) p24h,
COUNT(DISTINCT mint) FILTER(WHERE seconds_since_graduation BETWEEN 60 AND 150 AND price_usd>0 AND liquidity_usd>0 AND NOT COALESCE(incomplete_data,TRUE)) valid_signal,
COUNT(DISTINCT mint) FILTER(WHERE seconds_since_graduation BETWEEN 3300 AND 3900 AND price_usd>0 AND liquidity_usd>0 AND NOT COALESCE(incomplete_data,TRUE)) valid_target,
AVG(CASE WHEN liquidity_usd IS NULL THEN 1.0 ELSE 0 END) null_liquidity,
AVG(CASE WHEN price_usd IS NULL THEN 1.0 ELSE 0 END) null_price,
AVG(CASE WHEN COALESCE(incomplete_data,TRUE) THEN 1.0 ELSE 0 END) incomplete_pct
FROM read_parquet(?)""",[P]).df().iloc[0].to_dict()
b=c.execute("""SELECT phase,dex_id,COUNT(*) n,
COUNT(DISTINCT mint) distinct_mints,
AVG(CASE WHEN liquidity_usd IS NULL THEN 1.0 ELSE 0 END) null_liquidity,
AVG(CASE WHEN COALESCE(incomplete_data,TRUE) THEN 1.0 ELSE 0 END) incomplete
FROM read_parquet(?) GROUP BY phase,dex_id ORDER BY n DESC LIMIT 15""",[P]).df().to_dict('records')
d=c.execute("""WITH s AS (SELECT mint,
BOOL_OR(seconds_since_graduation BETWEEN 60 AND 150 AND price_usd>0 AND liquidity_usd>0 AND NOT COALESCE(incomplete_data,TRUE)) sig,
BOOL_OR(seconds_since_graduation BETWEEN 3300 AND 3900 AND price_usd>0 AND liquidity_usd>0 AND NOT COALESCE(incomplete_data,TRUE)) follow
FROM read_parquet(?) GROUP BY mint)
SELECT count(*) all_mints,sum(sig::INT) valid_sig,sum(follow::INT) valid_follow,sum((sig AND follow)::INT) valid_both FROM s""",[P]).df().iloc[0].to_dict()
out={"by_window":a,"by_phase":b,"paired_1m_1h":d}
Path("digui010-evidence").mkdir(exist_ok=True)
Path("digui010-evidence/coverage.json").write_text(json.dumps(out,indent=2,default=str))
print("COVERAGE",json.dumps(out,default=str),flush=True)
