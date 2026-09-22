#!/usr/bin/env python3
import json, urllib.parse, urllib.request, urllib.error, xml.etree.ElementTree as ET
from pathlib import Path

BASE="https://drift-historical-data-v2.s3.eu-west-1.amazonaws.com/"
PREFIX="program/dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH/"
params=urllib.parse.urlencode({"list-type":"2","prefix":PREFIX,"delimiter":"/","max-keys":"1000"})
url=BASE+"?"+params
receipt={
 "schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001",
 "bucket":BASE,"prefix":PREFIX,"request_url_redacted":BASE+"?list-type=2&prefix=<FROZEN_PROGRAM_PREFIX>&delimiter=/&max-keys=1000",
 "unsigned":True,"credentials_used":False,"requester_pays":False,"object_bodies_downloaded":False,
 "event_rows":False,"prices":False,"returns":False,"pnl":False,"direction":False,
 "protected_market_outcomes_2025_2026":False,"live_trading":False,"orders":False,
 "wallets":False,"exchange_mutation":False,"paid_source":False,"merge_main":False
}
try:
    req=urllib.request.Request(url,headers={"User-Agent":"crypto-lab-dls-source-metadata/0.1"})
    with urllib.request.urlopen(req,timeout=45) as resp:
        raw=resp.read()
        receipt["http_status"]=resp.status
        root=ET.fromstring(raw)
        ns={"s3":"http://s3.amazonaws.com/doc/2006-03-01/"}
        def texts(path):
            vals=[]
            for e in root.findall(path,ns):
                if e.text: vals.append(e.text)
            return vals
        prefixes=texts("s3:CommonPrefixes/s3:Prefix")
        keys=texts("s3:Contents/s3:Key")
        truncated=(root.findtext("{http://s3.amazonaws.com/doc/2006-03-01/}IsTruncated") or "").lower()=="true"
        receipt["common_prefixes"]=prefixes
        receipt["object_keys"]=keys
        receipt["is_truncated"]=truncated
        hay=[x.lower() for x in prefixes+keys]
        liq=[x for x in prefixes+keys if "liquidat" in x.lower()]
        receipt["liquidation_like_entries"]=liq
        if liq:
            receipt["classification"]="DRIFT_HISTORICAL_S3_LIQUIDATION_KEYSPACE_PASS"
        elif truncated:
            receipt["classification"]="DRIFT_HISTORICAL_S3_KEYSPACE_PARTIAL"
        else:
            receipt["classification"]="DRIFT_HISTORICAL_S3_KEYSPACE_NO_LIQUIDATION_ROUTE"
except urllib.error.HTTPError as e:
    receipt.update(classification="DRIFT_HISTORICAL_S3_KEYSPACE_BLOCKED",http_status=e.code,reason="http_error")
except Exception as e:
    receipt.update(classification="DRIFT_HISTORICAL_S3_KEYSPACE_BLOCKED",reason=type(e).__name__)

Path("labs/DEFI_LIQUIDATION_SHOCK_001/DRIFT_HISTORICAL_S3_KEYSPACE_RECEIPT_V0.1.json").write_text(
    json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps(receipt,indent=2,sort_keys=True))
