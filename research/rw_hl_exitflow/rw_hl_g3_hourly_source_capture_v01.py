#!/usr/bin/env python3
"""G3 hourly point-in-time Hyperliquid public source, no outcome access.

Uniqueness is by TRUE received UTC hour; GitHub trigger cannot assert an old
market hour. Fail closed on duplicates; source-only future forward receipts.
"""
from __future__ import annotations
from datetime import datetime,timezone
import hashlib,json,os
from pathlib import Path
import rw_hl_public_source_gate_v01 as public

ROOT=Path(__file__).resolve().parent
FREEZE=ROOT/"RW_HL_EXITFLOW_001_G3_HOURLY_SOURCE_PREACTIVATION_FREEZE_2026-10-09.md"
ARCHIVE=ROOT/"forward_source"/"hourly"
MIN_MARKETS=100
class Blocked(ValueError):pass

def parse_utc(ts):
    if not isinstance(ts,str) or not ts.endswith("Z"):
        raise Blocked("SOURCE_RECEIVE_TIMESTAMP_NO_UTC")
    try:
        val=datetime.fromisoformat(ts.replace("Z","+00:00"))
    except ValueError:raise Blocked("SOURCE_RECEIVE_TIMESTAMP_INVALID") from None
    if val.utcoffset().total_seconds()!=0:raise Blocked("TIMEZONE_NOT_UTC")
    return val

def safe_market(raw):
    parsed=public.parse_public_market(raw)
    if parsed["valid_public_markets"]<MIN_MARKETS:
        raise Blocked("G3_MIN_VALID_MARKETS_NOT_MET")
    markets=parsed["market_context"]
    names=[x["coin"] for x in markets]
    if len(names)!=len(set(names)):
        raise Blocked("DUPLICATE_COIN")
    for row in markets:
        if set(row)!={"coin","openInterest","markPx","funding","dayNtlVlm"}:
            raise Blocked("UNEXPECTED_NONMARKET_SOURCE_FIELD")
    return parsed

def build_receipt(raw,received_at,run_id):
    if "G3 HOURLY POINT-IN-TIME SOURCE" not in FREEZE.read_text():
        raise Blocked("G3_PREACTIVATION_FREEZE_MISSING")
    ts=parse_utc(received_at)
    market=safe_market(raw)
    slot=ts.strftime("%Y-%m-%dT%H:00:00Z")
    obj={"lab_id":"RW-HL-EXITFLOW-001","record_type":"PUBLIC_HL_HOURLY_SOURCE",
        "observed_at_utc":received_at,"source_hour_utc":slot,
        "github_run_id":str(run_id),
        "market_count":market["valid_public_markets"],
        "source":"HYPERLIQUID_PUBLIC_META_AND_ASSET_CTXS",
        "market_data":market,"economic_outcomes_opened":False,
        "trading_authority":"NONE","no_backfill":True}
    return obj

def write_immutable(receipt):
    ts=parse_utc(receipt["observed_at_utc"])
    root=ARCHIVE/ts.strftime("%Y-%m-%d")
    path=root/(ts.strftime("%H")+".json")
    if path.exists():raise Blocked("DUPLICATE_SOURCE_HOUR_KEEP_FIRST")
    root.mkdir(parents=True,exist_ok=True)
    body=public.canon(receipt)+b"\n"
    # Create exclusively; NEVER overwrite earlier source rows.
    try:
        with path.open("xb") as f:f.write(body)
    except FileExistsError:raise Blocked("DUPLICATE_SOURCE_HOUR_KEEP_FIRST") from None
    checksum=hashlib.sha256(body).hexdigest()
    return path,checksum

def execute():
    ts=datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00","Z")
    # The clock is the local receive start. API snapshot itself has no exact exchange timestamp.
    raw=public.public_info({"type":"metaAndAssetCtxs"})
    observed=datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00","Z")
    if (parse_utc(observed)-parse_utc(ts)).total_seconds()>45:
        raise Blocked("PUBLIC_SOURCE_OBSERVATION_TOO_SLOW")
    x=build_receipt(raw,observed,os.environ.get("GITHUB_RUN_ID","LOCAL"))
    file,digest=write_immutable(x)
    result={"lab_id":"RW-HL-EXITFLOW-001","state":"ONE_PROSPECTIVE_UTC_HOUR_SOURCE_SAVED",
        "file_path":str(file.relative_to(ROOT)),"source_sha256":digest,
        "source_hour_utc":x["source_hour_utc"],"market_count":x["market_count"],
        "coverage_for_14_days_ready":False,"economic_outcomes_opened":False,
        "trading_authority":"NONE"}
    print(json.dumps(result,sort_keys=True),flush=True)
    return result

if __name__=="__main__":
    try:execute()
    except (Blocked,public.Blocked,OSError,ValueError,KeyError,TypeError) as e:
        print(json.dumps({"state":"SOURCE_BLOCKED","reason":str(e),"economic_outcomes_opened":False,
           "trading_authority":"NONE"}))
        raise SystemExit(2)
