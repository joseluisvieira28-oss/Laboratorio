from __future__ import annotations
import json, urllib.parse, urllib.request
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"research"/"local_data"/"cross_venue_diamond_replication_002_okx_schema_probe"
OUT.mkdir(parents=True,exist_ok=True)
BASE="https://www.okx.com/api/v5/public/market-data-history"
UA="CROSS-VENUE-DIAMOND-REPLICATION-002 schema-only/1.0"

def ms(x):
    return int(datetime.fromisoformat(x.replace("Z","+00:00")).timestamp()*1000)

def shape(v,depth=0):
    if depth>=3:
        return type(v).__name__
    if isinstance(v,dict):
        return {k:shape(v[k],depth+1) for k in sorted(v)}
    if isinstance(v,list):
        if not v: return {"type":"list","length":0}
        return {"type":"list","length":len(v),"item_shape":shape(v[0],depth+1)}
    if v is None: return "null"
    if isinstance(v,bool): return "bool"
    if isinstance(v,(int,float)): return "number"
    return "string"

def main():
    params={
      "module":"3","instType":"SWAP","dateAggrType":"monthly",
      "begin":ms("2025-01-01T00:00:00Z"),
      "end":ms("2025-02-01T00:00:00Z"),
      "instFamilyList":"AVAX-USDT",
    }
    req=urllib.request.Request(BASE+"?"+urllib.parse.urlencode(params),headers={"User-Agent":UA,"Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=20) as r:
        body=json.loads(r.read().decode("utf-8","replace"))
        rows=body.get("data") if isinstance(body,dict) else None
        receipt={
          "lab_id":"CROSS-VENUE-DIAMOND-REPLICATION-002",
          "stage":"OKX_HISTORICAL_RESPONSE_SCHEMA_ONLY",
          "candidate":"CED1D-0031-AVAX20-CONTINUATION-H1",
          "http_status":r.status,
          "provider_code":body.get("code") if isinstance(body,dict) else None,
          "provider_msg":body.get("msg") if isinstance(body,dict) else None,
          "data_row_count":len(rows) if isinstance(rows,list) else None,
          "response_shape":shape(body),
          "values_opened_or_persisted":False,
          "historical_payload_opened":False,
          "signal_calculation_performed":False,
          "return_calculation_performed":False,
          "pnl_calculation_performed":False,
          "2026_plus_accessed":False,
        }
    p=OUT/"CROSS_VENUE_DIAMOND_REPLICATION_002_OKX_SCHEMA_ONLY_RECEIPT_V0.1.json"
    p.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"http_status":receipt["http_status"],"provider_code":receipt["provider_code"],"data_row_count":receipt["data_row_count"],"response_shape":receipt["response_shape"]},sort_keys=True))
    return 0
if __name__=="__main__": raise SystemExit(main())
