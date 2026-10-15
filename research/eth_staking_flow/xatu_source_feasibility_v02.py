#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
import requests
import duckdb

LAB_ID="ETH-STAKING-FLOW-001"
BASE="https://data.ethpandaops.io/xatu/mainnet/databases/default/canonical_beacon_validators"
DATES=["2023-04-12","2023-09-01","2024-06-15","2024-12-31"]
REQUIRED={"epoch","epoch_start_date_time","index","status"}
MAX_OFFSET_SECONDS=32*12

def url_for(ds:str)->str:
    d=datetime.strptime(ds,"%Y-%m-%d")
    return f"{BASE}/{d.year}/{d.month}/{d.day}.parquet"

def sqlq(con,sql:str):
    return con.execute(sql).fetchall()

def main()->int:
    out=Path("xatu_source_feas_v02_output"); out.mkdir(parents=True,exist_ok=True)
    dst=out/"ETH_STAKING_FLOW_001_XATU_SOURCE_FEASIBILITY_V0_2.json"
    receipt={
      "lab_id":LAB_ID,
      "phase":"XATU_PUBLIC_SOURCE_FEASIBILITY_V0_2_OUTCOME_BLIND",
      "classification":None,
      "probe_dates":DATES,
      "market_prices_opened":False,
      "returns_opened":False,
      "pnl_opened":False,
      "accessed_2025_or_2026":False,
      "live_trading":False,
      "exchange_mutation":False,
    }
    rows=[]
    try:
        con=duckdb.connect(database=":memory:")
        con.execute("INSTALL httpfs")
        con.execute("LOAD httpfs")
        for ds in DATES:
            if ds[:4] in {"2025","2026"}: raise RuntimeError("protected period date")
            url=url_for(ds)
            meta={"date":ds,"url":url}
            try:
                r=requests.get(url,headers={"Range":"bytes=0-0","User-Agent":f"{LAB_ID}/xatu-source-feas-v0.2"},stream=True,timeout=(15,45),allow_redirects=True)
                meta["http_status"]=r.status_code
                meta["content_length"]=r.headers.get("Content-Length")
                meta["content_range"]=r.headers.get("Content-Range")
                meta["etag"]=r.headers.get("ETag")
                r.close()
            except Exception as exc:
                meta["transport_error"]=f"{type(exc).__name__}: {str(exc)[:500]}"
                rows.append(meta)
                continue
            if meta["http_status"] not in (200,206):
                rows.append(meta); continue

            esc=url.replace("'","''")
            schema=sqlq(con,f"DESCRIBE SELECT * FROM read_parquet('{esc}')")
            cols=[str(x[0]) for x in schema]
            meta["schema_columns"]=cols
            meta["schema_types"]={str(x[0]):str(x[1]) for x in schema}
            meta["required_columns_present"]=sorted(REQUIRED.intersection(cols))
            meta["required_columns_missing"]=sorted(REQUIRED.difference(cols))
            if meta["required_columns_missing"]:
                rows.append(meta); continue

            start=datetime.strptime(ds,"%Y-%m-%d").replace(tzinfo=timezone.utc)
            end=start+timedelta(seconds=MAX_OFFSET_SECONDS)
            s0=start.strftime("%Y-%m-%d %H:%M:%S")
            s1=end.strftime("%Y-%m-%d %H:%M:%S")
            q=f"""
              SELECT
                MIN(epoch) AS min_epoch,
                MAX(epoch) AS max_epoch,
                MIN(epoch_start_date_time) AS min_epoch_time,
                MAX(epoch_start_date_time) AS max_epoch_time,
                COUNT(DISTINCT epoch) AS distinct_epochs,
                MIN(CASE WHEN epoch_start_date_time >= TIMESTAMP '{s0}'
                          AND epoch_start_date_time <= TIMESTAMP '{s1}'
                         THEN epoch_start_date_time END) AS first_window_time
              FROM read_parquet('{esc}')
            """
            agg=sqlq(con,q)[0]
            meta.update({
              "min_epoch":str(agg[0]) if agg[0] is not None else None,
              "max_epoch":str(agg[1]) if agg[1] is not None else None,
              "min_epoch_start_date_time":str(agg[2]) if agg[2] is not None else None,
              "max_epoch_start_date_time":str(agg[3]) if agg[3] is not None else None,
              "distinct_epoch_count":int(agg[4]) if agg[4] is not None else 0,
              "first_snapshot_in_32_slot_window":str(agg[5]) if agg[5] is not None else None,
            })
            if agg[5] is not None:
                ts=str(agg[5]).replace("'","''")
                statuses=[str(x[0]) for x in sqlq(con,f"""
                  SELECT DISTINCT status
                  FROM read_parquet('{esc}')
                  WHERE epoch_start_date_time = TIMESTAMP '{ts}'
                  ORDER BY status
                """)]
                meta["status_labels_at_first_window_snapshot"]=statuses
                meta["pending_queued_present_at_snapshot"]="pending_queued" in statuses
                meta["active_exiting_present_at_snapshot"]="active_exiting" in statuses
            rows.append(meta)
        receipt["probes"]=rows
        if any(x.get("transport_error") for x in rows):
            receipt["classification"]="XATU_SOURCE_ACQUISITION_TECHNICAL_FAILURE"
            receipt["failure"]="one or more transport errors"
        elif any(x.get("http_status") not in (200,206) for x in rows):
            receipt["classification"]="XATU_SOURCE_PATH_NOT_FOUND"
            receipt["failure"]="one or more deterministic parquet paths unavailable"
        elif any(x.get("required_columns_missing") for x in rows):
            receipt["classification"]="XATU_SCHEMA_INSUFFICIENT"
            receipt["failure"]="required validator snapshot columns missing"
        elif any(not x.get("first_snapshot_in_32_slot_window") for x in rows):
            receipt["classification"]="XATU_TEMPORAL_ALIGNMENT_FAIL"
            receipt["failure"]="one or more probe dates lacks a canonical epoch snapshot inside +32 slots"
        else:
            receipt["classification"]="XATU_SOURCE_FEASIBILITY_PASS"
            receipt["failure"]=None
    except Exception as exc:
        receipt["classification"]="XATU_SOURCE_ACQUISITION_TECHNICAL_FAILURE"
        receipt["failure"]=f"{type(exc).__name__}: {str(exc)[:1200]}"
        receipt["probes"]=rows
    dst.write_text(json.dumps(receipt,indent=2,sort_keys=True,default=str)+"\n",encoding="utf-8")
    print(json.dumps({"classification":receipt["classification"],"probe_count":len(rows),"dates":[{"date":x.get("date"),"http":x.get("http_status"),"snapshot":x.get("first_snapshot_in_32_slot_window")} for x in rows],"prices":False,"returns":False,"pnl":False},sort_keys=True))
    return 0 if receipt["classification"]=="XATU_SOURCE_FEASIBILITY_PASS" else 2

if __name__=="__main__": sys.exit(main())
