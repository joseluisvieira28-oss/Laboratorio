#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
import requests, duckdb

LAB_ID="ETH-STAKING-FLOW-001"
BASE="https://data.ethpandaops.io/xatu/mainnet/databases/default/canonical_beacon_validators"
DATES=["2023-04-12","2023-09-01","2024-06-15","2024-12-31"]
REQUIRED={"epoch","epoch_start_date_time","index","status"}
MAX_OFFSET_SECONDS=32*12

def url_for(ds:str)->str:
    d=datetime.strptime(ds,"%Y-%m-%d")
    return f"{BASE}/{d.year}/{d.month}/{d.day}/0.parquet"

def main()->int:
    out=Path("xatu_source_feas_v02a_output"); out.mkdir(parents=True,exist_ok=True)
    dst=out/"ETH_STAKING_FLOW_001_XATU_SOURCE_FEASIBILITY_V0_2A.json"
    receipt={"lab_id":LAB_ID,"phase":"XATU_PUBLIC_SOURCE_FEASIBILITY_V0_2A_OUTCOME_BLIND",
             "classification":None,"probe_dates":DATES,"market_prices_opened":False,
             "returns_opened":False,"pnl_opened":False,"accessed_2025_or_2026":False,
             "live_trading":False,"exchange_mutation":False}
    probes=[]
    try:
        con=duckdb.connect(database=":memory:")
        con.execute("INSTALL httpfs")
        con.execute("LOAD httpfs")
        for ds in DATES:
            if ds[:4] in {"2025","2026"}: raise RuntimeError("protected period date")
            url=url_for(ds); p={"date":ds,"url":url}
            try:
                r=requests.get(url,headers={"Range":"bytes=0-0","User-Agent":f"{LAB_ID}/xatu-source-feas-v0.2a"},stream=True,timeout=(15,45),allow_redirects=True)
                p["http_status"]=r.status_code
                p["content_length"]=r.headers.get("Content-Length")
                p["content_range"]=r.headers.get("Content-Range")
                p["etag"]=r.headers.get("ETag")
                r.close()
            except Exception as exc:
                p["transport_error"]=f"{type(exc).__name__}: {str(exc)[:500]}"; probes.append(p); continue
            if p["http_status"] not in (200,206):
                probes.append(p); continue
            esc=url.replace("'","''")
            schema=con.execute(f"DESCRIBE SELECT * FROM read_parquet('{esc}')").fetchall()
            cols=[str(x[0]) for x in schema]
            p["schema_columns"]=cols
            p["schema_types"]={str(x[0]):str(x[1]) for x in schema}
            p["required_columns_present"]=sorted(REQUIRED.intersection(cols))
            p["required_columns_missing"]=sorted(REQUIRED.difference(cols))
            if p["required_columns_missing"]:
                probes.append(p); continue
            start=datetime.strptime(ds,"%Y-%m-%d").replace(tzinfo=timezone.utc)
            end=start+timedelta(seconds=MAX_OFFSET_SECONDS)
            s0=start.strftime("%Y-%m-%d %H:%M:%S")
            s1=end.strftime("%Y-%m-%d %H:%M:%S")
            agg=con.execute(f"""
              SELECT MIN(epoch),MAX(epoch),MIN(epoch_start_date_time),MAX(epoch_start_date_time),
                     COUNT(DISTINCT epoch),
                     MIN(CASE WHEN epoch_start_date_time >= TIMESTAMP '{s0}'
                               AND epoch_start_date_time <= TIMESTAMP '{s1}'
                              THEN epoch_start_date_time END)
              FROM read_parquet('{esc}')
            """).fetchone()
            p.update({"min_epoch":str(agg[0]) if agg[0] is not None else None,
                      "max_epoch":str(agg[1]) if agg[1] is not None else None,
                      "min_epoch_start_date_time":str(agg[2]) if agg[2] is not None else None,
                      "max_epoch_start_date_time":str(agg[3]) if agg[3] is not None else None,
                      "distinct_epoch_count":int(agg[4]) if agg[4] is not None else 0,
                      "first_snapshot_in_32_slot_window":str(agg[5]) if agg[5] is not None else None})
            if agg[5] is not None:
                ts=str(agg[5]).replace("'","''")
                statuses=[str(x[0]) for x in con.execute(f"""
                  SELECT DISTINCT status FROM read_parquet('{esc}')
                  WHERE epoch_start_date_time=TIMESTAMP '{ts}' ORDER BY status
                """).fetchall()]
                p["status_labels_at_first_window_snapshot"]=statuses
                p["pending_queued_present_at_snapshot"]="pending_queued" in statuses
                p["active_exiting_present_at_snapshot"]="active_exiting" in statuses
            probes.append(p)
        receipt["probes"]=probes
        if any(x.get("transport_error") for x in probes):
            receipt["classification"]="XATU_SOURCE_ACQUISITION_TECHNICAL_FAILURE"; receipt["failure"]="transport error"
        elif any(x.get("http_status") not in (200,206) for x in probes):
            receipt["classification"]="XATU_SOURCE_PATH_NOT_FOUND"; receipt["failure"]="hour-0 parquet path unavailable"
        elif any(x.get("required_columns_missing") for x in probes):
            receipt["classification"]="XATU_SCHEMA_INSUFFICIENT"; receipt["failure"]="required columns missing"
        elif any(not x.get("first_snapshot_in_32_slot_window") for x in probes):
            receipt["classification"]="XATU_TEMPORAL_ALIGNMENT_FAIL"; receipt["failure"]="no snapshot within +32 slots"
        else:
            receipt["classification"]="XATU_SOURCE_FEASIBILITY_PASS"; receipt["failure"]=None
    except Exception as exc:
        receipt["classification"]="XATU_SOURCE_ACQUISITION_TECHNICAL_FAILURE"
        receipt["failure"]=f"{type(exc).__name__}: {str(exc)[:1200]}"
        receipt["probes"]=probes
    dst.write_text(json.dumps(receipt,indent=2,sort_keys=True,default=str)+"\n",encoding="utf-8")
    print(json.dumps({"classification":receipt["classification"],
                      "dates":[{"date":x.get("date"),"http":x.get("http_status"),"epochs":x.get("distinct_epoch_count"),"snapshot":x.get("first_snapshot_in_32_slot_window"),"pending":x.get("pending_queued_present_at_snapshot"),"exiting":x.get("active_exiting_present_at_snapshot")} for x in probes],
                      "prices":False,"returns":False,"pnl":False},sort_keys=True))
    return 0 if receipt["classification"]=="XATU_SOURCE_FEASIBILITY_PASS" else 2

if __name__=="__main__": sys.exit(main())
