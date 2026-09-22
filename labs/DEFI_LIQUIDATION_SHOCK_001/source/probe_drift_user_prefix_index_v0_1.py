#!/usr/bin/env python3
import hashlib, json, urllib.parse, urllib.request, urllib.error, xml.etree.ElementTree as ET
from pathlib import Path

BASE="https://drift-historical-data-v2.s3.eu-west-1.amazonaws.com/"
PREFIX="program/dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH/user/"
params=urllib.parse.urlencode({"list-type":"2","prefix":PREFIX,"delimiter":"/","max-keys":"1000"})
url=BASE+"?"+params

receipt={
  "schema_version":"0.1",
  "lab_id":"DEFI-LIQUIDATION-SHOCK-001",
  "bucket":BASE,
  "prefix":PREFIX,
  "unsigned":True,
  "object_bodies":False,
  "event_rows":False,
  "prices":False,
  "returns":False,
  "pnl":False,
  "direction":False,
  "protected_market_outcomes_2025_2026":False,
  "credentials":False,
  "account_creation":False,
  "paid_source":False,
  "live_trading":False,
  "orders":False,
  "wallets":False,
  "exchange_mutation":False,
  "merge_main":False
}

try:
    req=urllib.request.Request(url,headers={"User-Agent":"crypto-lab-dls-source-metadata/0.1"})
    with urllib.request.urlopen(req,timeout=45) as resp:
        raw=resp.read()
        receipt["http_status"]=resp.status
        root=ET.fromstring(raw)
        ns="{http://s3.amazonaws.com/doc/2006-03-01/}"
        is_truncated=(root.findtext(ns+"IsTruncated") or "").lower()=="true"
        key_count=int(root.findtext(ns+"KeyCount") or "0")
        next_token=root.findtext(ns+"NextContinuationToken")
        prefixes=[]
        for cp in root.findall(ns+"CommonPrefixes"):
            p=cp.findtext(ns+"Prefix")
            if p:
                prefixes.append(p)
        expected_prefix=PREFIX
        bad=[p for p in prefixes if not p.startswith(expected_prefix)]
        if bad:
            receipt.update(
                classification="DRIFT_USER_PREFIX_INDEX_SOURCE_ANOMALY_FAIL_CLOSED",
                reason="common_prefix_outside_frozen_namespace",
                bad_prefix_count=len(bad)
            )
        elif prefixes:
            sorted_prefixes=sorted(prefixes)
            digest=hashlib.sha256(("\n".join(sorted_prefixes)+"\n").encode()).hexdigest()
            receipt.update(
                classification="DRIFT_USER_PREFIX_INDEX_PASS",
                is_truncated=is_truncated,
                key_count=key_count,
                common_prefix_count=len(prefixes),
                common_prefixes_sha256=digest,
                first_prefix=sorted_prefixes[0],
                last_prefix=sorted_prefixes[-1],
                next_continuation_token_present=bool(next_token)
            )
        else:
            receipt.update(
                classification="DRIFT_USER_PREFIX_INDEX_EMPTY",
                is_truncated=is_truncated,
                key_count=key_count,
                common_prefix_count=0,
                next_continuation_token_present=bool(next_token)
            )
except urllib.error.HTTPError as e:
    receipt.update(classification="DRIFT_USER_PREFIX_INDEX_BLOCKED",http_status=e.code,reason="http_error")
except Exception as e:
    receipt.update(classification="DRIFT_USER_PREFIX_INDEX_BLOCKED",reason=type(e).__name__)

Path("labs/DEFI_LIQUIDATION_SHOCK_001/DRIFT_USER_PREFIX_INDEX_PROBE_RECEIPT_V0.1.json").write_text(
    json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps(receipt,indent=2,sort_keys=True))
