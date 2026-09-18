#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from datetime import datetime,timezone,timedelta
from pathlib import Path
import fsspec
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

LAB_ID="ETH-STAKING-FLOW-001"
MVE_ID="ESF-NETQUEUE-XATU-7D-003"
BASE="https://data.ethpandaops.io/xatu/mainnet/databases/default/canonical_beacon_validators"
DATES=["2023-04-12","2023-09-01","2024-06-15","2024-12-31"]
MAX_OFFSET=384
COLS=["epoch","epoch_start_date_time","index","status"]

def url_for(ds):
    d=datetime.strptime(ds,"%Y-%m-%d")
    return f"{BASE}/{d.year}/{d.month}/{d.day}/0.parquet"

def stat_int(x):
    if hasattr(x,"as_py"): x=x.as_py()
    if isinstance(x,datetime): return int(x.replace(tzinfo=timezone.utc).timestamp() if x.tzinfo is None else x.timestamp())
    return int(x)

def bool_count(arr,label):
    mask=pc.equal(arr,pa.scalar(label,type=arr.type))
    return int(pc.sum(pc.cast(mask,pa.int64())).as_py() or 0)

def main():
    out=Path("xatu_v03c_queue_preflight_output");out.mkdir(parents=True,exist_ok=True)
    dst=out/"ETH_STAKING_FLOW_001_XATU_QUEUE_COUNT_PREFLIGHT_V0_3C.json"
    probes=[];cls=None;failure=None
    try:
        for ds in DATES:
            url=url_for(ds);row={"date":ds,"url":url}
            try:
                with fsspec.open(url,"rb",block_size=4*1024*1024,cache_type="readahead") as f:
                    pf=pq.ParquetFile(f)
                    names=list(pf.schema_arrow.names)
                    miss=[c for c in COLS if c not in names]
                    if miss: raise RuntimeError(f"required columns missing: {miss}")
                    ts_idx=names.index("epoch_start_date_time")
                    rgstats=[]
                    for i in range(pf.metadata.num_row_groups):
                        st=pf.metadata.row_group(i).column(ts_idx).statistics
                        if st and st.has_min_max:
                            rgstats.append((i,stat_int(st.min),stat_int(st.max)))
                    if not rgstats: raise RuntimeError("no epoch_start_date_time row-group statistics")
                    T=min(x[1] for x in rgstats)
                    start=int(datetime.strptime(ds,"%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())
                    if not(start<=T<=start+MAX_OFFSET): raise RuntimeError(f"selected timestamp {T} outside +32-slot window")
                    selected=[i for i,mn,mx in rgstats if mn<=T<=mx]
                    if not selected: raise RuntimeError("no row group contains selected timestamp")
                    tab=pf.read_row_groups(selected,columns=COLS)
                    tsarr=tab["epoch_start_date_time"]
                    scalar=pa.scalar(T,type=tsarr.type)
                    filt=tab.filter(pc.equal(tsarr,scalar))
                    n=int(filt.num_rows)
                    if n<=0: raise RuntimeError("selected timestamp yielded zero rows")
                    if filt["index"].null_count: raise RuntimeError("null validator index")
                    unique_idx=int(pc.count_distinct(filt["index"]).as_py())
                    if unique_idx!=n: raise RuntimeError(f"duplicate validator index rows={n} unique={unique_idx}")
                    epochs=int(pc.count_distinct(filt["epoch"]).as_py())
                    if epochs!=1: raise RuntimeError(f"selected timestamp has {epochs} distinct epochs")
                    epoch_value=int(pc.min(filt["epoch"]).as_py())
                    pending=bool_count(filt["status"],"pending_queued")
                    exiting=bool_count(filt["status"],"active_exiting")
                    row.update({
                      "selected_unix_time":T,
                      "selected_time_utc":datetime.fromtimestamp(T,tz=timezone.utc).isoformat(),
                      "selected_row_groups":selected,
                      "selected_epoch":epoch_value,
                      "validator_rows":n,
                      "unique_validator_indices":unique_idx,
                      "pending_queued_count":pending,
                      "active_exiting_count":exiting,
                      "net_queue_count":pending-exiting,
                      "pass":True
                    })
            except Exception as exc:
                row["pass"]=False;row["error"]=f"{type(exc).__name__}: {str(exc)[:1000]}"
            probes.append(row)
        if any(not x.get("pass") for x in probes):
            cls="SOURCE_ACQUISITION_TECHNICAL_FAILURE";failure="one or more deterministic queue-count probes failed"
        else:
            cls="QUEUE_COUNT_ENGINE_PASS"
    except Exception as exc:
        cls="SOURCE_ACQUISITION_TECHNICAL_FAILURE";failure=f"{type(exc).__name__}: {str(exc)[:1200]}"
    receipt={"lab_id":LAB_ID,"mve_id":MVE_ID,"phase":"QUEUE_COUNT_ENGINE_PREFLIGHT_V0_3C",
             "classification":cls,"failure":failure,"probes":probes,
             "validator_level_rows_persisted":False,"market_prices_opened":False,
             "returns_opened":False,"pnl_opened":False,"signal_evaluated":False,
             "accessed_2025_or_2026":False,"live_trading":False,"exchange_mutation":False}
    dst.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"classification":cls,"probes":[{"date":x["date"],"pass":x.get("pass"),"time":x.get("selected_time_utc"),"epoch":x.get("selected_epoch"),"validators":x.get("validator_rows"),"pending":x.get("pending_queued_count"),"exiting":x.get("active_exiting_count"),"net":x.get("net_queue_count"),"error":x.get("error")} for x in probes],"prices":False,"returns":False,"pnl":False},sort_keys=True))
    return 0 if cls=="QUEUE_COUNT_ENGINE_PASS" else 2
if __name__=="__main__":sys.exit(main())
