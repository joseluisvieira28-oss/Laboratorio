#!/usr/bin/env python3
import json, os, urllib.request, urllib.error
from pathlib import Path

LAB="DEFI-LIQUIDATION-SHOCK-001"
PROGRAM="MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA"
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/DLS_ROUTE_A2_GTFA_CAPABILITY_RECEIPT_V0.3.json")

key=os.environ.get("HELIUS_API_KEY","").strip()
if not key:
    raise SystemExit("HELIUS_API_KEY_ABSENT")

url="https://mainnet.helius-rpc.com/?api-key="+key
payload={
  "jsonrpc":"2.0","id":"dls-gtfa-probe","method":"getTransactionsForAddress",
  "params":[PROGRAM,{
    "transactionDetails":"full",
    "sortOrder":"asc",
    "limit":2,
    "filters":{
      "blockTime":{"gte":1735689600,"lte":1735693200},
      "status":"succeeded"
    }
  }]
}
req=urllib.request.Request(url,data=json.dumps(payload,separators=(",",":")).encode(),
                           headers={"Content-Type":"application/json","User-Agent":"CryptoLab-DLS-gTFA-Probe/0.3"})
classification="GTFA_TRANSPORT_CAPABILITY_BLOCKED"
error=None
schema={}
try:
    with urllib.request.urlopen(req,timeout=45) as r:
        raw=r.read()
    obj=json.loads(raw)
    if obj.get("error"):
        error={"code":obj["error"].get("code"),"message":str(obj["error"].get("message"))[:240]}
    else:
        res=obj.get("result")
        if isinstance(res,dict) and isinstance(res.get("data"),list):
            data=res["data"]
            schema={
              "result_keys":sorted(res.keys()),
              "data_count":len(data),
              "pagination_token_present":bool(res.get("paginationToken")),
              "first_record_keys":sorted(data[0].keys()) if data and isinstance(data[0],dict) else []
            }
            classification="GTFA_TRANSPORT_CAPABILITY_PASS"
        else:
            error={"reason":"unexpected_result_schema","result_type":type(res).__name__}
except urllib.error.HTTPError as e:
    body=e.read().decode("utf-8","replace")
    error={"http_status":e.code,"body_prefix":body[:240]}
except Exception as e:
    error={"type":type(e).__name__,"detail":str(e)[:240]}

receipt={
  "schema_version":"0.3",
  "lab_id":LAB,
  "classification":classification,
  "method":"getTransactionsForAddress",
  "probe_program":PROGRAM,
  "probe_window":{"gte":1735689600,"lte":1735693200},
  "limit":2,
  "response_schema":schema,
  "error":error,
  "secret_value_exposed":False,
  "transaction_payload_persisted":False,
  "protected_2025_market_prices_opened":False,
  "returns_opened":False,
  "pnl_opened":False,
  "protected_2026_opened":False,
  "science_changed":False,
  "trading_authority":"NONE"
}
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({k:receipt[k] for k in ["classification","method","response_schema","error","transaction_payload_persisted","trading_authority"]},indent=2,sort_keys=True))
if classification!="GTFA_TRANSPORT_CAPABILITY_PASS":
    raise SystemExit(2)
