#!/usr/bin/env python3
import argparse
import concurrent.futures
import datetime as dt
import json
import os
from pathlib import Path

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

BUCKET = "hyperliquid-archive"
YEAR = 2024
ASSET = "BTC"
EXPECTED = 8784
CONFIRM = "I_AUTHORIZE_L2R_2024_BTC_HEAD_ONLY_REQUESTER_PAYS_INVENTORY"

def keys():
    d = dt.date(2024,1,1)
    end = dt.date(2024,12,31)
    while d <= end:
        ymd = d.strftime("%Y%m%d")
        for hour in range(24):
            yield f"market_data/{ymd}/{hour}/l2Book/{ASSET}.lz4"
        d += dt.timedelta(days=1)

def one(client, key):
    try:
        r = client.head_object(Bucket=BUCKET, Key=key, RequestPayer="requester")
        return {
            "key": key,
            "status": "PRESENT",
            "content_length": int(r.get("ContentLength", 0)),
            "etag": str(r.get("ETag", "")).strip('"'),
            "last_modified": r.get("LastModified").isoformat() if r.get("LastModified") else None,
        }
    except ClientError as e:
        meta=e.response.get("ResponseMetadata",{})
        err=e.response.get("Error",{})
        code=str(err.get("Code",""))
        http=int(meta.get("HTTPStatusCode",0) or 0)
        status="MISSING" if http==404 or code in {"404","NoSuchKey","NotFound"} else "ERROR"
        return {"key":key,"status":status,"http_status":http,"error_code":code}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--authorization-confirmation", default="")
    ap.add_argument("--out", default="L2_RESILIENCY_001_2024_BTC_SOURCE_INVENTORY_V0_1.json")
    ap.add_argument("--workers", type=int, default=16)
    args=ap.parse_args()

    frozen=list(keys())
    assert len(frozen)==EXPECTED
    assert all("/2024" in ("/"+k.split("/")[1]) for k in frozen)
    assert not any("/2025" in k or "/2026" in k for k in frozen)

    base={
        "schema_version":"0.1",
        "lab_id":"L2-RESILIENCY-001",
        "mode":"SOURCE_INVENTORY_HEAD_ONLY",
        "bucket":BUCKET,
        "asset":ASSET,
        "year":YEAR,
        "expected_keys":EXPECTED,
        "list_requests":0,
        "get_requests":0,
        "object_bodies_read":False,
        "decompression_performed":False,
        "sweep_events_computed":False,
        "replenishment_computed":False,
        "midpoint_response_computed":False,
        "returns_computed":False,
        "pnl_computed":False,
        "access_2025":False,
        "access_2026":False,
        "live_trading":False,
        "exchange_mutation":False,
    }

    if not args.execute or args.authorization_confirmation != CONFIRM:
        base.update({"classification":"BLOCKED_NO_EXECUTION_AUTHORIZATION","head_requests":0,"rows":[]})
        Path(args.out).write_text(json.dumps(base,indent=2)+"\n")
        return 3

    session=boto3.Session()
    if session.get_credentials() is None:
        base.update({"classification":"BLOCKED_NO_AWS_CREDENTIALS","head_requests":0,"rows":[]})
        Path(args.out).write_text(json.dumps(base,indent=2)+"\n")
        return 3

    client=session.client("s3")
    rows=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1,min(args.workers,32))) as ex:
        for row in ex.map(lambda k: one(client,k), frozen):
            rows.append(row)

    present=[r for r in rows if r["status"]=="PRESENT"]
    missing=[r for r in rows if r["status"]=="MISSING"]
    errors=[r for r in rows if r["status"]=="ERROR"]
    empty=[r for r in present if int(r.get("content_length",0))<=0]
    classification = "SOURCE_INVENTORY_PASS" if len(rows)==EXPECTED and not errors and not empty else "SOURCE_INVENTORY_FAIL_CLOSED"
    base.update({
        "classification":classification,
        "head_requests":len(rows),
        "present_keys":len(present),
        "missing_keys":len(missing),
        "error_keys":len(errors),
        "empty_present_keys":len(empty),
        "total_present_compressed_bytes":sum(int(r.get("content_length",0)) for r in present),
        "rows":rows,
    })
    Path(args.out).write_text(json.dumps(base,indent=2,sort_keys=True)+"\n")
    return 0 if classification=="SOURCE_INVENTORY_PASS" else 2

if __name__=="__main__":
    raise SystemExit(main())
