#!/usr/bin/env python3
"""Outcome-blind Tardis liquidation source feasibility probe V0.3.

Only the dataset symbol addressing differs from V0.2, per the recorded erratum.
"""
from __future__ import annotations
import csv, gzip, hashlib, io, json
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parent
AUTH_PATH=ROOT/"TARDIS_SOURCE_PROBE_AUTHORITY_V0.3.json"
OUT=Path("artifacts/liquidation_pressure_tardis_source_probe_v03")
OUT.mkdir(parents=True,exist_ok=True)
VALID_SIDES={"buy","sell","unknown",""}

class RouteInsufficient(RuntimeError): pass
class AcquisitionFailure(RuntimeError): pass

def sha256_bytes(data:bytes)->str: return hashlib.sha256(data).hexdigest()
def stable_sha(obj:object)->str:
    return sha256_bytes(json.dumps(obj,sort_keys=True,separators=(",",":")).encode())

def fetch_sample(auth:dict,date:str)->dict:
    symbol=auth["source"]["dataset_symbol"]
    url=f"{auth['source']['base_url']}/{date}/{symbol}.csv.gz"
    try:
        r=requests.get(url,timeout=(20,120))
    except requests.RequestException as exc:
        raise AcquisitionFailure(f"{date}: request failed: {exc}") from exc
    if r.status_code!=200:
        raise AcquisitionFailure(f"{date}: HTTP {r.status_code}")
    payload=r.content
    if not payload: raise RouteInsufficient(f"{date}: empty payload")
    try:
        raw=gzip.decompress(payload).decode("utf-8")
    except Exception as exc:
        raise RouteInsufficient(f"{date}: invalid gzip/csv payload: {exc}") from exc
    reader=csv.DictReader(io.StringIO(raw))
    fields=reader.fieldnames or []
    missing=[c for c in auth["required_columns"] if c not in fields]
    if missing: raise RouteInsufficient(f"{date}: missing required columns {missing}")
    total=bad_required=bad_side=0
    first_ts=last_ts=None
    for row in reader:
        total+=1
        if (row.get("symbol") or "").upper()!=auth["target_symbol"]:
            raise RouteInsufficient(f"{date}: unexpected symbol {(row.get('symbol') or '')!r}")
        ts=(row.get("timestamp") or "").strip()
        price=(row.get("price") or "").strip()
        amount=(row.get("amount") or "").strip()
        side=(row.get("side") or "").strip().lower()
        if not ts or not price or not amount: bad_required+=1
        if side not in VALID_SIDES: bad_side+=1
        if ts:
            try:
                t=int(ts); first_ts=t if first_ts is None else min(first_ts,t); last_ts=t if last_ts is None else max(last_ts,t)
            except ValueError: bad_required+=1
    if total==0: raise RouteInsufficient(f"{date}: zero BTCUSDT liquidation rows")
    if bad_required: raise RouteInsufficient(f"{date}: {bad_required} invalid required rows")
    if bad_side: raise RouteInsufficient(f"{date}: {bad_side} invalid side rows")
    return {
        "date":date,"url":url,"http_status":r.status_code,
        "compressed_bytes":len(payload),"compressed_sha256":sha256_bytes(payload),
        "btc_liquidation_rows":total,"first_timestamp_us":first_ts,"last_timestamp_us":last_ts,
        "schema":fields,"outcomes_opened":False
    }

def main()->int:
    auth=json.loads(AUTH_PATH.read_text())
    receipt={"lab_id":auth["lab_id"],"probe_id":auth["probe_id"],
             "authority_sha256":sha256_bytes(AUTH_PATH.read_bytes()),
             "classification":None,"dates":[],"failure":None,"safety":auth["safety"],
             "parent_v02_run":auth["parent_v02_run"]}
    try:
        assert auth["status"]=="FROZEN_SOURCE_ONLY_OUTCOME_BLIND"
        assert auth["source"]["dataset_symbol"]=="BTCUSDT"
        assert all(int(d[:4])<2025 for d in auth["sample_dates"])
        assert all(v is False for k,v in auth["safety"].items() if k.endswith("_authorized"))
        for d in auth["sample_dates"]: receipt["dates"].append(fetch_sample(auth,d))
        receipt["classification"]="HISTORICAL_LIQUIDATION_SOURCE_ROUTE_FEASIBLE"
    except RouteInsufficient as exc:
        receipt["classification"]="SOURCE_ROUTE_SCHEMA_INSUFFICIENT"; receipt["failure"]=f"{type(exc).__name__}: {exc}"
    except AcquisitionFailure as exc:
        receipt["classification"]="SOURCE_ACQUISITION_TECHNICAL_FAILURE"; receipt["failure"]=f"{type(exc).__name__}: {exc}"
    except Exception as exc:
        receipt["classification"]="PROVENANCE_FAILURE"; receipt["failure"]=f"{type(exc).__name__}: {exc}"
    receipt["receipt_sha256"]=stable_sha({k:v for k,v in receipt.items() if k!="receipt_sha256"})
    p=OUT/"LIQUIDATION_PRESSURE_001_TARDIS_SOURCE_PROBE_RECEIPT_V0_3.json"
    p.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
        "classification":receipt["classification"],"dates_completed":len(receipt["dates"]),
        "date_summaries":[{"date":x["date"],"btc_rows":x["btc_liquidation_rows"],"bytes":x["compressed_bytes"]} for x in receipt["dates"]],
        "failure":receipt["failure"],"receipt_sha256":receipt["receipt_sha256"],"safety":receipt["safety"]
    },sort_keys=True))
    return 0 if receipt["classification"] in {"HISTORICAL_LIQUIDATION_SOURCE_ROUTE_FEASIBLE","SOURCE_ROUTE_SCHEMA_INSUFFICIENT"} else 2

if __name__=="__main__": raise SystemExit(main())
