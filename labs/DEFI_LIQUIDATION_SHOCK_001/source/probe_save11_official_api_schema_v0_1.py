#!/usr/bin/env python3
import json, urllib.request, urllib.error
from pathlib import Path

BASE="https://api.solend.fi/history-v2/liquidation-attempts"
QUERIES=[
  ("bare",""),
  ("limit","?limit=1"),
  ("page_limit","?page=1&limit=1"),
  ("offset_limit","?offset=0&limit=1"),
  ("frozen_time_bounds","?start=1721417452&end=1721433600&limit=1"),
]
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/SAVE11_OFFICIAL_API_SOURCE_PROBE_RECEIPT_V0.1.json")

def shape(v,depth=0):
    if depth>5: return {"type":type(v).__name__}
    if isinstance(v,dict):
        return {"type":"object","keys":{str(k):shape(x,depth+1) for k,x in sorted(v.items())}}
    if isinstance(v,list):
        return {"type":"array","length":len(v),"item_schema":shape(v[0],depth+1) if v else None}
    if v is None: return {"type":"null"}
    if isinstance(v,bool): return {"type":"boolean"}
    if isinstance(v,(int,float)): return {"type":"number"}
    if isinstance(v,str): return {"type":"string"}
    return {"type":type(v).__name__}

rows=[]
success=0
validation=0
transport=0
for label,q in QUERIES:
    url=BASE+q
    rec={"label":label,"url":url}
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"crypto-lab-dls-source-schema/0.1","Accept":"application/json"})
        with urllib.request.urlopen(req,timeout=45) as resp:
            raw=resp.read()
            rec["http_status"]=int(resp.status)
            rec["content_type"]=resp.headers.get("Content-Type")
            rec["response_bytes"]=len(raw)
            try:
                obj=json.loads(raw)
                rec["json_schema"]=shape(obj)
                rec["json_parse"]=True
                success+=1
            except Exception as e:
                rec["json_parse"]=False
                rec["parse_error"]=type(e).__name__
    except urllib.error.HTTPError as e:
        raw=e.read()
        rec["http_status"]=int(e.code)
        rec["content_type"]=e.headers.get("Content-Type") if e.headers else None
        rec["response_bytes"]=len(raw)
        try:
            obj=json.loads(raw)
            rec["json_schema"]=shape(obj)
            # Validation error values are intentionally not persisted.
            rec["json_parse"]=True
        except Exception:
            rec["json_parse"]=False
        if e.code in (400,401,403,404,405,422): validation+=1
    except Exception as e:
        rec["http_status"]=None
        rec["transport_error"]=type(e).__name__
        transport+=1
    rows.append(rec)

if success:
    cls="SAVE11_OFFICIAL_API_SCHEMA_ROUTE_PASS"
elif validation:
    cls="SAVE11_OFFICIAL_API_SCHEMA_ROUTE_VALIDATION_BLOCKED"
else:
    cls="SAVE11_OFFICIAL_API_SCHEMA_ROUTE_TRANSPORT_BLOCKED"

receipt={
 "schema_version":"0.1",
 "lab_id":"DEFI-LIQUIDATION-SHOCK-001",
 "classification":cls,
 "provider":"Save/Solend official API",
 "route":"/history-v2/liquidation-attempts",
 "successful_json_2xx":success,
 "validation_block_count":validation,
 "transport_error_count":transport,
 "rows":rows,
 "economic_values_persisted":False,
 "firewalls":{"prices":False,"amounts":False,"usd_values":False,"returns":False,"pnl":False,"direction":False,
              "live_trading":False,"orders":False,"wallets":False,"exchange_mutation":False,
              "paid_source":False,"account_creation":False,"merge_main":False}
}
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps(receipt,indent=2,sort_keys=True))
