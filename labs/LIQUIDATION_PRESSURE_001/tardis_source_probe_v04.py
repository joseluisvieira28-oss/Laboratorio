#!/usr/bin/env python3
"""Outcome-blind Tardis liquidation source feasibility probe V0.4.

Only URL date segmentation differs from V0.3, per recorded erratum.
"""
from __future__ import annotations
import csv,gzip,hashlib,io,json
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parent
AUTH_PATH=ROOT/"TARDIS_SOURCE_PROBE_AUTHORITY_V0.4.json"
OUT=Path("artifacts/liquidation_pressure_tardis_source_probe_v04")
OUT.mkdir(parents=True,exist_ok=True)
VALID_SIDES={"buy","sell","unknown",""}
class RouteInsufficient(RuntimeError): pass
class AcquisitionFailure(RuntimeError): pass
def sha256_bytes(b): return hashlib.sha256(b).hexdigest()
def stable_sha(o): return sha256_bytes(json.dumps(o,sort_keys=True,separators=(",",":")).encode())

def fetch_sample(a,date):
    y,m,d=date.split("-"); symbol=a["source"]["dataset_symbol"]
    url=f"{a['source']['base_url']}/{y}/{m}/{d}/{symbol}.csv.gz"
    try: r=requests.get(url,timeout=(20,120))
    except requests.RequestException as e: raise AcquisitionFailure(f"{date}: request failed: {e}") from e
    if r.status_code!=200: raise AcquisitionFailure(f"{date}: HTTP {r.status_code}")
    if not r.content: raise RouteInsufficient(f"{date}: empty payload")
    try: raw=gzip.decompress(r.content).decode("utf-8")
    except Exception as e: raise RouteInsufficient(f"{date}: invalid gzip/csv payload: {e}") from e
    reader=csv.DictReader(io.StringIO(raw)); fields=reader.fieldnames or []
    missing=[c for c in a["required_columns"] if c not in fields]
    if missing: raise RouteInsufficient(f"{date}: missing required columns {missing}")
    n=bad=badside=0; first=last=None
    for row in reader:
        n+=1
        if (row.get("symbol") or "").upper()!=a["target_symbol"]:
            raise RouteInsufficient(f"{date}: unexpected symbol {(row.get('symbol') or '')!r}")
        ts=(row.get("timestamp") or "").strip(); price=(row.get("price") or "").strip(); amount=(row.get("amount") or "").strip()
        side=(row.get("side") or "").strip().lower()
        if not ts or not price or not amount: bad+=1
        if side not in VALID_SIDES: badside+=1
        if ts:
            try:
                t=int(ts); first=t if first is None else min(first,t); last=t if last is None else max(last,t)
            except ValueError: bad+=1
    if n==0: raise RouteInsufficient(f"{date}: zero BTCUSDT liquidation rows")
    if bad: raise RouteInsufficient(f"{date}: {bad} invalid required rows")
    if badside: raise RouteInsufficient(f"{date}: {badside} invalid side rows")
    return {"date":date,"url":url,"http_status":r.status_code,"compressed_bytes":len(r.content),
            "compressed_sha256":sha256_bytes(r.content),"btc_liquidation_rows":n,
            "first_timestamp_us":first,"last_timestamp_us":last,"schema":fields,"outcomes_opened":False}

def main():
    a=json.loads(AUTH_PATH.read_text())
    rec={"lab_id":a["lab_id"],"probe_id":a["probe_id"],"authority_sha256":sha256_bytes(AUTH_PATH.read_bytes()),
         "classification":None,"dates":[],"failure":None,"safety":a["safety"],"parent_v03_run":a["parent_v03_run"]}
    try:
        assert a["status"]=="FROZEN_SOURCE_ONLY_OUTCOME_BLIND"
        assert a["source"]["dataset_symbol"]=="BTCUSDT"
        assert all(int(d[:4])<2025 for d in a["sample_dates"])
        assert all(v is False for k,v in a["safety"].items() if k.endswith("_authorized"))
        rec["dates"]=[fetch_sample(a,d) for d in a["sample_dates"]]
        rec["classification"]="HISTORICAL_LIQUIDATION_SOURCE_ROUTE_FEASIBLE"
    except RouteInsufficient as e:
        rec["classification"]="SOURCE_ROUTE_SCHEMA_INSUFFICIENT"; rec["failure"]=f"{type(e).__name__}: {e}"
    except AcquisitionFailure as e:
        rec["classification"]="SOURCE_ACQUISITION_TECHNICAL_FAILURE"; rec["failure"]=f"{type(e).__name__}: {e}"
    except Exception as e:
        rec["classification"]="PROVENANCE_FAILURE"; rec["failure"]=f"{type(e).__name__}: {e}"
    rec["receipt_sha256"]=stable_sha({k:v for k,v in rec.items() if k!="receipt_sha256"})
    (OUT/"LIQUIDATION_PRESSURE_001_TARDIS_SOURCE_PROBE_RECEIPT_V0_4.json").write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"classification":rec["classification"],"dates_completed":len(rec["dates"]),
      "date_summaries":[{"date":x["date"],"btc_rows":x["btc_liquidation_rows"],"bytes":x["compressed_bytes"]} for x in rec["dates"]],
      "failure":rec["failure"],"receipt_sha256":rec["receipt_sha256"],"safety":rec["safety"]},sort_keys=True))
    return 0 if rec["classification"] in {"HISTORICAL_LIQUIDATION_SOURCE_ROUTE_FEASIBLE","SOURCE_ROUTE_SCHEMA_INSUFFICIENT"} else 2
if __name__=="__main__": raise SystemExit(main())
