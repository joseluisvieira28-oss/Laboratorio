#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
import fsspec
import pyarrow.parquet as pq

LAB_ID="ETH-STAKING-FLOW-001"
BASE="https://data.ethpandaops.io/xatu/mainnet/databases/default/canonical_beacon_validators"
DATES=["2023-04-12","2023-09-01","2024-06-15","2024-12-31"]
REQUIRED={"epoch","epoch_start_date_time","index","status"}
MAX_OFFSET_SECONDS=32*12

def url_for(ds):
    d=datetime.strptime(ds,"%Y-%m-%d")
    return f"{BASE}/{d.year}/{d.month}/{d.day}/0.parquet"

def as_dt(x):
    if x is None: return None
    if isinstance(x, datetime):
        if x.tzinfo is None: return x.replace(tzinfo=timezone.utc)
        return x.astimezone(timezone.utc)
    if hasattr(x,"as_py"): return as_dt(x.as_py())
    s=str(x)
    if s.endswith("Z"): s=s[:-1]+"+00:00"
    d=datetime.fromisoformat(s)
    if d.tzinfo is None: d=d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc)

def main():
    out=Path("xatu_parquet_metadata_v02c_output"); out.mkdir(parents=True,exist_ok=True)
    dst=out/"ETH_STAKING_FLOW_001_XATU_PARQUET_METADATA_V0_2C.json"
    probes=[]
    classification=None; failure=None
    try:
        for ds in DATES:
            if ds[:4] in {"2025","2026"}: raise RuntimeError("protected-period date")
            url=url_for(ds); row={"date":ds,"url":url}
            try:
                of=fsspec.open(url,mode="rb",block_size=4*1024*1024,cache_type="readahead")
                with of as f:
                    try: row["remote_size_bytes"]=int(f.size)
                    except Exception: row["remote_size_bytes"]=None
                    pf=pq.ParquetFile(f)
                    names=list(pf.schema_arrow.names)
                    row["schema_columns"]=names
                    row["schema_types"]={field.name:str(field.type) for field in pf.schema_arrow}
                    row["required_columns_missing"]=sorted(REQUIRED.difference(names))
                    md=pf.metadata
                    row["row_count"]=int(md.num_rows)
                    row["row_group_count"]=int(md.num_row_groups)
                    epoch_idx=names.index("epoch") if "epoch" in names else None
                    ts_idx=names.index("epoch_start_date_time") if "epoch_start_date_time" in names else None
                    epoch_mins=[]; epoch_maxs=[]; ts_mins=[]; ts_maxs=[]
                    if epoch_idx is not None or ts_idx is not None:
                        for i in range(md.num_row_groups):
                            rg=md.row_group(i)
                            if epoch_idx is not None:
                                st=rg.column(epoch_idx).statistics
                                if st and st.has_min_max:
                                    epoch_mins.append(int(st.min)); epoch_maxs.append(int(st.max))
                            if ts_idx is not None:
                                st=rg.column(ts_idx).statistics
                                if st and st.has_min_max:
                                    ts_mins.append(as_dt(st.min)); ts_maxs.append(as_dt(st.max))
                    row["epoch_stats_row_groups"]=len(epoch_mins)
                    row["timestamp_stats_row_groups"]=len(ts_mins)
                    row["min_epoch"]=min(epoch_mins) if epoch_mins else None
                    row["max_epoch"]=max(epoch_maxs) if epoch_maxs else None
                    row["min_epoch_start_date_time"]=min(ts_mins).isoformat() if ts_mins else None
                    row["max_epoch_start_date_time"]=max(ts_maxs).isoformat() if ts_maxs else None
                    start=datetime.strptime(ds,"%Y-%m-%d").replace(tzinfo=timezone.utc)
                    end=start+timedelta(seconds=MAX_OFFSET_SECONDS)
                    row["temporal_alignment_pass"]=bool(ts_mins and start <= min(ts_mins) <= end)
            except Exception as exc:
                row["technical_error"]=f"{type(exc).__name__}: {str(exc)[:800]}"
            probes.append(row)

        if any(x.get("technical_error") for x in probes):
            classification="XATU_SOURCE_ACQUISITION_TECHNICAL_FAILURE"; failure="one or more metadata range-read errors"
        elif any(x.get("required_columns_missing") for x in probes):
            classification="XATU_SCHEMA_INSUFFICIENT"; failure="required schema columns missing"
        elif any((x.get("row_count") or 0)<=0 or (x.get("row_group_count") or 0)<=0 for x in probes):
            classification="XATU_METADATA_INSUFFICIENT"; failure="empty parquet metadata"
        elif any((x.get("timestamp_stats_row_groups") or 0)<=0 for x in probes):
            classification="XATU_METADATA_INSUFFICIENT"; failure="timestamp min/max statistics unavailable"
        elif any(not x.get("temporal_alignment_pass") for x in probes):
            classification="XATU_TEMPORAL_ALIGNMENT_FAIL"; failure="earliest timestamp outside +32-slot window"
        else:
            classification="XATU_PARQUET_METADATA_PASS"
    except Exception as exc:
        classification="XATU_SOURCE_ACQUISITION_TECHNICAL_FAILURE"
        failure=f"{type(exc).__name__}: {str(exc)[:1200]}"
    receipt={
      "lab_id":LAB_ID,"phase":"XATU_PARQUET_METADATA_V0_2C_OUTCOME_BLIND",
      "classification":classification,"failure":failure,"probes":probes,
      "validator_values_opened":False,"status_values_opened":False,"queue_counts_computed":False,
      "market_prices_opened":False,"returns_opened":False,"pnl_opened":False,
      "accessed_2025_or_2026":False,"live_trading":False,"exchange_mutation":False
    }
    dst.write_text(json.dumps(receipt,indent=2,sort_keys=True,default=str)+"\n",encoding="utf-8")
    print(json.dumps({"classification":classification,"probes":[{"date":x.get("date"),"rows":x.get("row_count"),"rgs":x.get("row_group_count"),"min_time":x.get("min_epoch_start_date_time"),"aligned":x.get("temporal_alignment_pass"),"missing":x.get("required_columns_missing"),"error":x.get("technical_error")} for x in probes],"status_values_opened":False,"prices":False,"returns":False,"pnl":False},sort_keys=True))
    return 0 if classification=="XATU_PARQUET_METADATA_PASS" else 2
if __name__=="__main__": sys.exit(main())
