#!/usr/bin/env python3
import hashlib
import json
import os
import time
from urllib.request import Request, urlopen

URL="https://wq-api.lido.fi/v2/request-time/calculate"
OUTDIR=os.path.join(os.path.dirname(__file__),"receipts")
os.makedirs(OUTDIR,exist_ok=True)

def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()

req=Request(
    URL,
    headers={
        "User-Agent":"CryptoLab-Lido-WQ-Source-Collector-V0.1",
        "Accept":"application/json",
    },
    method="GET",
)

with urlopen(req,timeout=90) as r:
    raw=r.read()
    status=r.status

if status != 200:
    raise RuntimeError(f"SOURCE_COLLECTION_FAIL http_status={status}")

try:
    payload=json.loads(raw.decode("utf-8"))
except Exception as e:
    raise RuntimeError(f"SOURCE_COLLECTION_FAIL invalid_json={e!r}")

if not isinstance(payload,dict):
    raise RuntimeError("SOURCE_SCHEMA_FAIL payload_not_object")

required={"status","requestInfo","nextCalculationAt"}
missing=sorted(required-set(payload.keys()))
if missing:
    raise RuntimeError(f"SOURCE_SCHEMA_FAIL missing={missing}")

snapshot={
    "lab_id":"LIDO-WITHDRAWAL-QUEUE-PRESSURE-001",
    "protocol":"LIDO_WQ_SOURCE_COLLECTION_PROTOCOL_V0.1",
    "collection_status":"SOURCE_OBSERVATION_PASS",
    "fetched_at_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
    "source_url":URL,
    "http_status":status,
    "raw_payload_sha256":sha256_bytes(raw),
    "top_level_keys":sorted(payload.keys()),
    "raw_payload":payload,
    "firewall":{
        "source_only":True,
        "market_price_fetched":False,
        "return_computed":False,
        "signal_defined":False,
        "direction_defined":False,
        "holding_period_defined":False,
        "pnl_computed":False,
        "live_trading":False,
        "orders":False,
        "exchange_mutation":False,
        "capital":False,
    },
}
pre=json.dumps(snapshot,sort_keys=True,separators=(",",":")).encode()
snapshot["snapshot_sha256_pre_self_field"]=sha256_bytes(pre)

out=os.path.join(OUTDIR,"LIDO_WQ_SOURCE_SNAPSHOT_V0.1.json")
with open(out,"w",encoding="utf-8") as f:
    json.dump(snapshot,f,sort_keys=True,indent=2)
    f.write("\n")

print(json.dumps({
    "collection_status":snapshot["collection_status"],
    "fetched_at_utc":snapshot["fetched_at_utc"],
    "http_status":status,
    "raw_payload_sha256":snapshot["raw_payload_sha256"],
    "snapshot_sha256_pre_self_field":snapshot["snapshot_sha256_pre_self_field"],
    "top_level_keys":snapshot["top_level_keys"],
},sort_keys=True,indent=2))
print(f"snapshot={out}")
