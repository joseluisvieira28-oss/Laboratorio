#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path

import duckdb

BASE="https://data.ethpandaops.io/xatu/mainnet/databases/default/canonical_beacon_validators"
MAX_OFFSET=384

CONTROLS=[
 {"date":"2025-02-24","epoch":347738,"unix":1740355415,"pending_queued":0,"active_exiting":5,"net_queue":-5},
 {"date":"2025-03-02","epoch":349088,"unix":1740873815,"pending_queued":0,"active_exiting":0,"net_queue":0},
 {"date":"2025-10-17","epoch":400613,"unix":1760659415,"pending_queued":48,"active_exiting":55209,"net_queue":-55161},
]
MISSING=[
 {"date":"2025-02-25","epoch":347963},
 {"date":"2025-02-26","epoch":348188},
 {"date":"2025-02-27","epoch":348413},
 {"date":"2025-02-28","epoch":348638},
 {"date":"2025-03-01","epoch":348863},
 {"date":"2025-10-18","epoch":400838},
 {"date":"2025-10-19","epoch":401063},
]

def url_for(ds:str)->str:
    d=date.fromisoformat(ds)
    return f"{BASE}/{d.year}/{d.month}/{d.day}/0.parquet"

def midnight_unix(ds:str)->int:
    d=date.fromisoformat(ds)
    return int(datetime(d.year,d.month,d.day,tzinfo=timezone.utc).timestamp())

con=duckdb.connect(database=":memory:")
con.execute("INSTALL httpfs")
con.execute("LOAD httpfs")
con.execute("SET enable_http_metadata_cache=true")
con.execute("SET http_retries=5")
con.execute("SET http_timeout=60000")

def esc(s:str)->str:
    return s.replace("'","''")

def reconstruct(ds:str):
    url=url_for(ds)
    u=esc(url)
    # Independent reader: derive actual timestamp from values, not Parquet metadata.
    qmin=f"""
      SELECT min(CAST(epoch(epoch_start_date_time) AS BIGINT)) AS t
      FROM read_parquet('{u}')
    """
    row=con.execute(qmin).fetchone()
    if row is None or row[0] is None:
        raise RuntimeError(f"{ds}: no actual timestamp values")
    T=int(row[0])
    start=midnight_unix(ds)
    if not (start <= T <= start+MAX_OFFSET):
        raise RuntimeError(f"{ds}: selected timestamp outside +384s: {T}")

    q=f"""
      SELECT
        count(*)::BIGINT AS n,
        count(DISTINCT "index")::BIGINT AS uniq,
        count(*) FILTER (WHERE "index" IS NULL)::BIGINT AS null_indices,
        count(DISTINCT epoch)::BIGINT AS epoch_count,
        min(epoch)::BIGINT AS selected_epoch,
        count(*) FILTER (WHERE status='pending_queued')::BIGINT AS pending_queued,
        count(*) FILTER (WHERE status='active_exiting')::BIGINT AS active_exiting
      FROM read_parquet('{u}')
      WHERE CAST(epoch(epoch_start_date_time) AS BIGINT) = {T}
    """
    n,uniq,nulls,epn,epoch,pending,exiting=map(int,con.execute(q).fetchone())
    if n<=0: raise RuntimeError(f"{ds}: zero rows at T")
    if nulls!=0: raise RuntimeError(f"{ds}: null validator index")
    if uniq!=n: raise RuntimeError(f"{ds}: duplicate validator index n={n} uniq={uniq}")
    if epn!=1: raise RuntimeError(f"{ds}: distinct epoch count {epn}")
    return {
      "date":ds,
      "url":url,
      "selected_unix_time":T,
      "selected_time_utc":datetime.fromtimestamp(T,tz=timezone.utc).isoformat(),
      "selected_epoch":epoch,
      "validator_rows":n,
      "unique_validator_indices":uniq,
      "pending_queued_count":pending,
      "active_exiting_count":exiting,
      "net_queue_count":pending-exiting,
      "reader":"duckdb",
      "duckdb_version":duckdb.__version__,
      "timestamp_locator":"DUCKDB_COLUMN_VALUE_MIN"
    }

receipt={
 "lab_id":"ETH-STAKING-FLOW-001",
 "stage":"V3_STAGEA_ALT_PARQUET_READER_V0_1_7",
 "classification":"SOURCE_ACQUISITION_TECHNICAL_FAILURE",
 "source_base":BASE,
 "reader":{"engine":"duckdb","version":duckdb.__version__},
 "controls":[],
 "recovered_missing_dates":[],
 "errors":[],
 "signal_evaluated":False,
 "market_prices_opened":False,
 "returns_opened":False,
 "pnl_opened":False,
 "source_after_2026_08_31_opened":False,
 "mutation":False
}

controls_pass=True
for c in CONTROLS:
    try:
        got=reconstruct(c["date"])
        expected={k:c[k] for k in ("epoch","unix","pending_queued","active_exiting","net_queue")}
        observed={
          "epoch":got["selected_epoch"],"unix":got["selected_unix_time"],
          "pending_queued":got["pending_queued_count"],"active_exiting":got["active_exiting_count"],
          "net_queue":got["net_queue_count"]
        }
        exact=observed==expected
        receipt["controls"].append({"date":c["date"],"exact":exact,"expected":expected,"observed":observed,
                                    "validator_rows":got["validator_rows"],"url":got["url"]})
        if not exact: controls_pass=False
    except Exception as e:
        controls_pass=False
        receipt["controls"].append({"date":c["date"],"exact":False,"error":repr(e),"url":url_for(c["date"])})

if not controls_pass:
    receipt["classification"]="SOURCE_PROVENANCE_FAILURE" if any(x.get("observed") for x in receipt["controls"] if not x["exact"]) else "SOURCE_ACQUISITION_TECHNICAL_FAILURE"
else:
    missing_ok=True
    for m in MISSING:
        try:
            got=reconstruct(m["date"])
            if got["selected_epoch"]!=m["epoch"]:
                raise RuntimeError(f"{m['date']}: epoch mismatch {got['selected_epoch']} != {m['epoch']}")
            receipt["recovered_missing_dates"].append(got)
        except Exception as e:
            missing_ok=False
            receipt["errors"].append({"date":m["date"],"error":repr(e),"url":url_for(m["date"])})
    if missing_ok and len(receipt["recovered_missing_dates"])==7:
        receipt["classification"]="ALTERNATE_PARQUET_READER_RECOVERY_PASS"
    else:
        receipt["classification"]="SOURCE_ACQUISITION_TECHNICAL_FAILURE"

canon=[
  {k:r[k] for k in ("date","selected_unix_time","selected_epoch","validator_rows","unique_validator_indices",
                     "pending_queued_count","active_exiting_count","net_queue_count")}
  for r in receipt["recovered_missing_dates"]
]
receipt["recovered_rows_sha256"]=hashlib.sha256((json.dumps(canon,sort_keys=True,separators=(",",":"))+"\n").encode()).hexdigest()

Path("artifacts").mkdir(exist_ok=True)
out=Path("artifacts/ETH_STAKING_FLOW_001_ALT_PARQUET_READER_RECOVERY_V0_1_7.json")
out.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({
 "classification":receipt["classification"],
 "reader":receipt["reader"],
 "control_exact_count":sum(1 for x in receipt["controls"] if x.get("exact")),
 "recovered_missing_date_count":len(receipt["recovered_missing_dates"]),
 "errors":len(receipt["errors"]),
 "signal":False,"market":False,"returns":False,"pnl":False
},indent=2,sort_keys=True))
raise SystemExit(0 if receipt["classification"]=="ALTERNATE_PARQUET_READER_RECOVERY_PASS" else 2)
