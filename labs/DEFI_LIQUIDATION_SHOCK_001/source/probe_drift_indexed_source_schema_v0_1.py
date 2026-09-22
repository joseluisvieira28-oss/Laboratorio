#!/usr/bin/env python3
import json, urllib.request, urllib.error
from pathlib import Path

URL="https://data.api.drift.trade/playground/json"
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/DRIFT_INDEXED_SOURCE_SCHEMA_PROBE_RECEIPT_V0.1.json")
req=urllib.request.Request(URL,headers={"accept":"application/json","User-Agent":"crypto-lab-dls-source-schema/0.1"})
receipt={
  "schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001","schema_url":URL,
  "schema_only":True,"event_rows_requested":False,"prices":False,"returns":False,"pnl":False,
  "direction":False,"protected_market_outcomes_2025_2026":False,"credentials_used":False,
  "account_created":False,"paid_source":False,"live_trading":False,"orders":False,
  "wallets":False,"exchange_mutation":False,"merge_main":False
}
try:
    with urllib.request.urlopen(req,timeout=45) as resp:
        raw=resp.read()
        receipt["http_status"]=resp.status
        spec=json.loads(raw)
        paths=spec.get("paths")
        if not isinstance(paths,dict):
            receipt["classification"]="DRIFT_INDEXED_SOURCE_SCHEMA_BLOCKED"
            receipt["reason"]="openapi_paths_missing"
        else:
            matches=[]
            for path,ops in paths.items():
                if not isinstance(ops,dict): continue
                for method,op in ops.items():
                    if method.lower() not in {"get","post","put","patch","delete"} or not isinstance(op,dict):
                        continue
                    hay=" ".join([path,str(op.get("summary") or ""),str(op.get("description") or "")]).lower()
                    if "liquidat" not in hay:
                        continue
                    params=[]
                    for p in op.get("parameters") or []:
                        if isinstance(p,dict):
                            sch=p.get("schema") if isinstance(p.get("schema"),dict) else {}
                            params.append({
                              "name":p.get("name"),"in":p.get("in"),"required":bool(p.get("required",False)),
                              "type":sch.get("type"),"format":sch.get("format")
                            })
                    matches.append({
                      "path":path,"method":method.upper(),"summary":op.get("summary"),
                      "parameters":params,"security":op.get("security")
                    })
            receipt["liquidation_routes"]=matches
            receipt["liquidation_route_count"]=len(matches)
            globalish=[]
            account_scoped=[]
            for m in matches:
                low=m["path"].lower()
                if any(x in low for x in ["{account","{user","user/","account/"]):
                    account_scoped.append(m["path"])
                else:
                    globalish.append(m["path"])
            receipt["global_candidate_paths"]=sorted(set(globalish))
            receipt["account_scoped_paths"]=sorted(set(account_scoped))
            if globalish:
                receipt["classification"]="DRIFT_INDEXED_SOURCE_SCHEMA_PASS"
            elif matches:
                receipt["classification"]="DRIFT_INDEXED_SOURCE_SCHEMA_PARTIAL_ACCOUNT_SCOPED"
            else:
                receipt["classification"]="DRIFT_INDEXED_SOURCE_SCHEMA_NO_ROUTE"
except urllib.error.HTTPError as e:
    receipt.update(classification="DRIFT_INDEXED_SOURCE_SCHEMA_BLOCKED",http_status=e.code,reason="http_error")
except Exception as e:
    receipt.update(classification="DRIFT_INDEXED_SOURCE_SCHEMA_BLOCKED",reason=type(e).__name__)

OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps(receipt,indent=2,sort_keys=True))
