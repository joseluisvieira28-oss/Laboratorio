#!/usr/bin/env python3
import hashlib, json, urllib.parse, urllib.request
from pathlib import Path

base="https://lab.ethpandaops.io/api/v1/mainnet/dim_validator_status"
params={"validator_index_gte":0,"epoch_lte":401063,"page_size":3,"order_by":"validator_index,epoch"}
url=base+"?"+urllib.parse.urlencode(params)
receipt={
  "lab_id":"ETH-STAKING-FLOW-001",
  "stage":"V3_STAGEA_CBT_RESPONSE_ENVELOPE_V0_1_9",
  "url":url,
  "signal_evaluated":False,"market_prices_opened":False,"returns_opened":False,"pnl_opened":False,
  "source_after_2026_08_31_opened":False,
}
try:
    req=urllib.request.Request(url,headers={"User-Agent":"crypto-lab-cbt-envelope-v019/1.0","Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=45) as r:
        raw=r.read(); receipt["http_status"]=r.status; receipt["content_type"]=r.headers.get("content-type")
    receipt["raw_bytes"]=len(raw); receipt["raw_sha256"]=hashlib.sha256(raw).hexdigest()
    obj=json.loads(raw)
    if isinstance(obj,dict):
        receipt["json_root_type"]="object"
        receipt["top_level_keys"]=sorted(obj.keys())
        rows=obj.get("dim_validator_status",obj.get("items"))
        receipt["row_container_type"]=type(rows).__name__ if rows is not None else None
        if isinstance(rows,list):
            receipt["row_count"]=len(rows)
            receipt["first_row_keys"]=sorted(rows[0].keys()) if rows and isinstance(rows[0],dict) else []
        tok=obj.get("next_page_token")
        receipt["next_page_token_present"]=bool(tok)
        receipt["next_page_token_type"]=type(tok).__name__ if tok is not None else None
    elif isinstance(obj,list):
        receipt["json_root_type"]="list"
        receipt["row_count"]=len(obj)
        receipt["first_row_keys"]=sorted(obj[0].keys()) if obj and isinstance(obj[0],dict) else []
        receipt["next_page_token_present"]=False
        receipt["next_page_token_type"]=None
    else:
        receipt["json_root_type"]=type(obj).__name__
    official={"updated_date_time","version","validator_index","pubkey","status","epoch","epoch_start_date_time","activation_epoch","activation_eligibility_epoch","exit_epoch","withdrawable_epoch","slashed"}
    keys=set(receipt.get("first_row_keys",[]))
    receipt["official_row_schema_compatible"]=bool(keys) and keys.issuperset(official)
    if receipt.get("json_root_type")=="object" and receipt.get("row_container_type")=="list" and receipt["official_row_schema_compatible"]:
        receipt["classification"]="CBT_ENVELOPE_DOCUMENTED_WRAPPER_PASS"
    elif receipt.get("json_root_type")=="list" and receipt["official_row_schema_compatible"]:
        receipt["classification"]="CBT_ENVELOPE_BARE_LIST_FOUND_PAGINATION_UNRESOLVED"
    else:
        receipt["classification"]="SOURCE_ACQUISITION_TECHNICAL_FAILURE"
except Exception as e:
    receipt["classification"]="SOURCE_ACQUISITION_TECHNICAL_FAILURE"
    receipt["error"]=f"{type(e).__name__}:{str(e)[:500]}"

Path("artifacts").mkdir(exist_ok=True)
Path("artifacts/ETH_STAKING_FLOW_001_CBT_ENVELOPE_V0_1_9.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,sort_keys=True))
raise SystemExit(0 if receipt["classification"]!="SOURCE_ACQUISITION_TECHNICAL_FAILURE" else 2)
