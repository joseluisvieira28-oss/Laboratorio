#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,os,sys
from datetime import date,datetime,timezone,timedelta
from pathlib import Path
import fsspec
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

LAB_ID="ETH-STAKING-FLOW-001"
MVE_ID="ESF-NETQUEUE-XATU-7D-003"
REPLICATION_ID="ESF-V3-REPLICATION-2025-2026A"
BASE="https://data.ethpandaops.io/xatu/mainnet/databases/default/canonical_beacon_validators"
GLOBAL_START=date(2025,1,1); GLOBAL_END=date(2026,8,31)
COLS=["epoch","epoch_start_date_time","index","status"]
MAX_OFFSET=384

def url_for(d):
    return f"{BASE}/{d.year}/{d.month}/{d.day}/0.parquet"

def stat_int(x):
    if hasattr(x,"as_py"):x=x.as_py()
    if isinstance(x,datetime):return int((x.replace(tzinfo=timezone.utc) if x.tzinfo is None else x).timestamp())
    return int(x)

def status_count(arr,label):
    mask=pc.equal(arr,pa.scalar(label,type=arr.type))
    return int(pc.sum(pc.cast(mask,pa.int64())).as_py() or 0)

def reconstruct_day(d):
    url=url_for(d)
    with fsspec.open(url,"rb",block_size=4*1024*1024,cache_type="readahead") as f:
        pf=pq.ParquetFile(f)
        names=list(pf.schema_arrow.names)
        miss=[c for c in COLS if c not in names]
        if miss: raise RuntimeError(f"{d}: required columns missing {miss}")
        ts_idx=names.index("epoch_start_date_time")
        rgstats=[]
        for i in range(pf.metadata.num_row_groups):
            st=pf.metadata.row_group(i).column(ts_idx).statistics
            if st and st.has_min_max:
                rgstats.append((i,stat_int(st.min),stat_int(st.max)))
        if not rgstats: raise RuntimeError(f"{d}: no timestamp row-group stats")
        T=min(x[1] for x in rgstats)
        start=int(datetime(d.year,d.month,d.day,tzinfo=timezone.utc).timestamp())
        if not(start<=T<=start+MAX_OFFSET): raise RuntimeError(f"{d}: selected timestamp outside +32 slots: {T}")
        selected=[i for i,mn,mx in rgstats if mn<=T<=mx]
        if not selected: raise RuntimeError(f"{d}: no row group contains selected timestamp")
        tab=pf.read_row_groups(selected,columns=COLS)
        filt=tab.filter(pc.equal(tab["epoch_start_date_time"],pa.scalar(T,type=tab["epoch_start_date_time"].type)))
        n=int(filt.num_rows)
        if n<=0: raise RuntimeError(f"{d}: zero validator rows at selected timestamp")
        if filt["index"].null_count: raise RuntimeError(f"{d}: null validator index")
        uniq=int(pc.count_distinct(filt["index"]).as_py())
        if uniq!=n: raise RuntimeError(f"{d}: duplicate validator index rows={n} unique={uniq}")
        epn=int(pc.count_distinct(filt["epoch"]).as_py())
        if epn!=1: raise RuntimeError(f"{d}: selected timestamp has {epn} epochs")
        epoch=int(pc.min(filt["epoch"]).as_py())
        pending=status_count(filt["status"],"pending_queued")
        exiting=status_count(filt["status"],"active_exiting")
        return {
          "date":d.isoformat(),"url":url,
          "selected_unix_time":T,
          "selected_time_utc":datetime.fromtimestamp(T,tz=timezone.utc).isoformat(),
          "selected_epoch":epoch,
          "selected_row_groups":selected,
          "validator_rows":n,
          "unique_validator_indices":uniq,
          "pending_queued_count":pending,
          "active_exiting_count":exiting,
          "net_queue_count":pending-exiting
        }

def main():
    sid=os.environ["SHARD_ID"]
    start=date.fromisoformat(os.environ["SHARD_START"])
    end=date.fromisoformat(os.environ["SHARD_END"])
    if not(GLOBAL_START<=start<=end<=GLOBAL_END):raise SystemExit("invalid replication shard")
    out=Path("xatu_v3_replication_shards");out.mkdir(parents=True,exist_ok=True)
    dst=out/f"queue_rep_{sid}.json"
    rows=[];errors=[];d=start
    while d<=end:
        try: rows.append(reconstruct_day(d))
        except Exception as exc: errors.append({"date":d.isoformat(),"error":f"{type(exc).__name__}: {str(exc)[:1000]}"})
        d+=timedelta(days=1)
    cls="SHARD_PASS" if not errors and len(rows)==((end-start).days+1) else "SOURCE_ACQUISITION_TECHNICAL_FAILURE"
    h=hashlib.sha256()
    for r in rows:
        h.update(f"{r['date']}|{r['selected_unix_time']}|{r['selected_epoch']}|{r['validator_rows']}|{r['pending_queued_count']}|{r['active_exiting_count']}|{r['net_queue_count']}\n".encode())
    receipt={
      "lab_id":LAB_ID,"mve_id":MVE_ID,"replication_id":REPLICATION_ID,
      "phase":"V3_INDEPENDENT_REPLICATION_SOURCE_SHARD_V0_1",
      "classification":cls,"shard_id":sid,"start":start.isoformat(),"end":end.isoformat(),
      "expected_dates":(end-start).days+1,"observed_dates":len(rows),"errors":errors,
      "daily_source_records":rows,"shard_source_sha256":h.hexdigest(),
      "validator_level_rows_persisted":False,"signal_evaluated":False,
      "market_prices_opened":False,"returns_opened":False,"pnl_opened":False,
      "protected_2025_2026_source_opened_under_specific_v3_authority":True,
      "source_cutoff_2026":"2026-08-31","market_data_opened":False,
      "live_trading":False,"exchange_mutation":False
    }
    dst.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"shard":sid,"classification":cls,"observed":len(rows),"errors":len(errors),"signal":False,"market":False,"returns":False,"pnl":False},sort_keys=True))
    return 0 if cls=="SHARD_PASS" else 2

if __name__=="__main__":sys.exit(main())
