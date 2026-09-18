#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from datetime import datetime,timezone,timedelta
from pathlib import Path
import fsspec
import pyarrow.parquet as pq

LAB_ID="ETH-STAKING-FLOW-001"
MVE_ID="ESF-NETQUEUE-XATU-7D-003"
BASE="https://data.ethpandaops.io/xatu/mainnet/databases/default/canonical_beacon_validators"
DATES=["2023-04-12","2023-09-01","2024-06-15","2024-12-31"]
REQUIRED={"epoch","epoch_start_date_time","index","status"}
MAX_OFFSET_SECONDS=384

def url_for(ds):
    d=datetime.strptime(ds,"%Y-%m-%d")
    return f"{BASE}/{d.year}/{d.month}/{d.day}/0.parquet"

def as_dt(x):
    if x is None:return None
    if hasattr(x,"as_py"): x=x.as_py()
    if isinstance(x,datetime):
        return (x.replace(tzinfo=timezone.utc) if x.tzinfo is None else x.astimezone(timezone.utc))
    if isinstance(x,(int,float)):
        return datetime.fromtimestamp(float(x),tz=timezone.utc)
    s=str(x)
    if s.isdigit() or (s.startswith("-") and s[1:].isdigit()):
        return datetime.fromtimestamp(int(s),tz=timezone.utc)
    if s.endswith("Z"):s=s[:-1]+"+00:00"
    d=datetime.fromisoformat(s)
    return d.replace(tzinfo=timezone.utc) if d.tzinfo is None else d.astimezone(timezone.utc)

def main():
    out=Path("xatu_v03a_metadata_output");out.mkdir(parents=True,exist_ok=True)
    dst=out/"ETH_STAKING_FLOW_001_XATU_V03A_METADATA_RECEIPT.json"
    probes=[];classification=None;failure=None
    try:
        for ds in DATES:
            url=url_for(ds);row={"date":ds,"url":url}
            try:
                with fsspec.open(url,"rb",block_size=4*1024*1024,cache_type="readahead") as f:
                    row["remote_size_bytes"]=int(f.size)
                    pf=pq.ParquetFile(f)
                    names=list(pf.schema_arrow.names)
                    row["schema_columns"]=names
                    row["schema_types"]={z.name:str(z.type) for z in pf.schema_arrow}
                    row["required_columns_missing"]=sorted(REQUIRED.difference(names))
                    md=pf.metadata
                    row["row_count"]=int(md.num_rows);row["row_group_count"]=int(md.num_row_groups)
                    if row["required_columns_missing"]:
                        probes.append(row);continue
                    ts_idx=names.index("epoch_start_date_time"); ep_idx=names.index("epoch")
                    tsmin=[];tsmax=[];epmin=[];epmax=[]
                    for i in range(md.num_row_groups):
                        rg=md.row_group(i)
                        st=rg.column(ts_idx).statistics
                        if st and st.has_min_max:
                            tsmin.append(as_dt(st.min));tsmax.append(as_dt(st.max))
                        se=rg.column(ep_idx).statistics
                        if se and se.has_min_max:
                            epmin.append(int(se.min));epmax.append(int(se.max))
                    row["timestamp_stats_row_groups"]=len(tsmin)
                    row["epoch_stats_row_groups"]=len(epmin)
                    row["min_epoch_start_date_time"]=min(tsmin).isoformat() if tsmin else None
                    row["max_epoch_start_date_time"]=max(tsmax).isoformat() if tsmax else None
                    row["min_epoch"]=min(epmin) if epmin else None
                    row["max_epoch"]=max(epmax) if epmax else None
                    start=datetime.strptime(ds,"%Y-%m-%d").replace(tzinfo=timezone.utc)
                    end=start+timedelta(seconds=MAX_OFFSET_SECONDS)
                    row["temporal_alignment_pass"]=bool(tsmin and start<=min(tsmin)<=end)
            except Exception as exc:
                row["technical_error"]=f"{type(exc).__name__}: {str(exc)[:800]}"
            probes.append(row)
        if any(x.get("technical_error") for x in probes):
            classification="SOURCE_ACQUISITION_TECHNICAL_FAILURE";failure="metadata range-read error"
        elif any(x.get("required_columns_missing") for x in probes):
            classification="DATA_FAILURE";failure="required schema missing"
        elif any((x.get("timestamp_stats_row_groups") or 0)<=0 for x in probes):
            classification="PROVENANCE_FAILURE";failure="timestamp statistics unavailable"
        elif any(not x.get("temporal_alignment_pass") for x in probes):
            classification="DATA_FAILURE";failure="hour-0 earliest epoch outside +32 slots"
        else:
            classification="SOURCE_FEASIBILITY_PASS"
    except Exception as exc:
        classification="SOURCE_ACQUISITION_TECHNICAL_FAILURE";failure=f"{type(exc).__name__}: {str(exc)[:1200]}"
    receipt={"lab_id":LAB_ID,"mve_id":MVE_ID,"phase":"XATU_V03A_METADATA_SOURCE_FEASIBILITY",
             "classification":classification,"failure":failure,"probes":probes,
             "queue_counts_computed":False,"status_values_opened":False,"market_prices_opened":False,
             "returns_opened":False,"pnl_opened":False,"accessed_2025_or_2026":False,
             "live_trading":False,"exchange_mutation":False}
    dst.write_text(json.dumps(receipt,indent=2,sort_keys=True,default=str)+"\n",encoding="utf-8")
    print(json.dumps({"classification":classification,"probes":[{"date":x.get("date"),"rows":x.get("row_count"),"rgs":x.get("row_group_count"),"min_time":x.get("min_epoch_start_date_time"),"aligned":x.get("temporal_alignment_pass"),"missing":x.get("required_columns_missing"),"err":x.get("technical_error")} for x in probes],"queue_counts":False,"prices":False,"returns":False,"pnl":False},sort_keys=True))
    return 0 if classification=="SOURCE_FEASIBILITY_PASS" else 2
if __name__=="__main__":sys.exit(main())
