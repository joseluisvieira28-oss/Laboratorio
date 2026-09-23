#!/usr/bin/env python3
import hashlib, json, math, urllib.parse, urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path

BASE="https://api.solend.fi/history-v2/liquidation-attempts"
START=1721417452
END=1721433600
START_ISO="2024-07-19T19:30:52Z"
END_ISO="2024-07-20T00:00:00Z"
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/SAVE11_OFFICIAL_API_TIMESTAMP_DIAGNOSTIC_RECEIPT_V0.2.json")

variants=[
 ("bare",{}),
 ("start_end_seconds",{"start":str(START),"end":str(END)}),
 ("start_time_end_time",{"start_time":str(START),"end_time":str(END)}),
 ("startTimestamp_endTimestamp",{"startTimestamp":str(START),"endTimestamp":str(END)}),
 ("from_to",{"from":str(START),"to":str(END)}),
 ("start_end_iso",{"start":START_ISO,"end":END_ISO}),
]

def parse_iso(s):
    try:
        if not isinstance(s,str): return None
        return int(datetime.fromisoformat(s.replace("Z","+00:00")).timestamp())
    except Exception:
        return None

def walk(v, stats):
    if isinstance(v,dict):
        if {"signature","slot","success","timestamp"}.issubset(v.keys()):
            stats["candidate_records"]+=1
            t=v.get("timestamp")
            if isinstance(t,bool):
                stats["timestamp_types"]["boolean"]+=1
            elif isinstance(t,(int,float)) and math.isfinite(float(t)):
                stats["timestamp_types"]["number"]+=1
                x=float(t)
                stats["numeric_min"]=x if stats["numeric_min"] is None else min(stats["numeric_min"],x)
                stats["numeric_max"]=x if stats["numeric_max"] is None else max(stats["numeric_max"],x)
                if START <= x < END: stats["inside_as_seconds"]+=1
                if START <= math.floor(x/1000) < END: stats["inside_as_milliseconds"]+=1
                if START <= math.floor(x/1000000) < END: stats["inside_as_microseconds"]+=1
            elif isinstance(t,str):
                stats["timestamp_types"]["string"]+=1
                y=parse_iso(t)
                if y is not None:
                    stats["iso_parseable"]+=1
                    if START <= y < END: stats["inside_as_iso_string"]+=1
            elif t is None:
                stats["timestamp_types"]["null"]+=1
            else:
                stats["timestamp_types"]["other"]+=1
        for x in v.values(): walk(x,stats)
    elif isinstance(v,list):
        for x in v: walk(x,stats)

rows=[]
json_2xx_with_candidates=0
for label,params in variants:
    qs=urllib.parse.urlencode(params)
    url=BASE+("?" + qs if qs else "")
    rec={"label":label,"query_keys":sorted(params.keys())}
    try:
        req=urllib.request.Request(url,headers={"Accept":"application/json","User-Agent":"crypto-lab-dls-api-diag/0.2"})
        with urllib.request.urlopen(req,timeout=60) as resp:
            raw=resp.read()
            rec["http_status"]=int(resp.status)
            rec["response_bytes"]=len(raw)
            rec["response_sha256"]=hashlib.sha256(raw).hexdigest()
        obj=json.loads(raw)
        st={
          "candidate_records":0,
          "timestamp_types":{"number":0,"string":0,"boolean":0,"null":0,"other":0},
          "numeric_min":None,"numeric_max":None,
          "inside_as_seconds":0,"inside_as_milliseconds":0,"inside_as_microseconds":0,
          "iso_parseable":0,"inside_as_iso_string":0
        }
        walk(obj,st)
        rec.update(st)
        if 200 <= rec["http_status"] < 300 and st["candidate_records"]>0:
            json_2xx_with_candidates+=1
    except urllib.error.HTTPError as e:
        raw=e.read()
        rec["http_status"]=int(e.code)
        rec["response_bytes"]=len(raw)
        rec["response_sha256"]=hashlib.sha256(raw).hexdigest()
    except Exception as e:
        rec["http_status"]=None
        rec["transport_error"]=type(e).__name__
    rows.append(rec)

receipt={
 "schema_version":"0.2",
 "lab_id":"DEFI-LIQUIDATION-SHOCK-001",
 "classification":"SAVE11_OFFICIAL_API_TIMESTAMP_DIAGNOSTIC_COMPLETE" if json_2xx_with_candidates else "SAVE11_OFFICIAL_API_TIMESTAMP_DIAGNOSTIC_BLOCKED",
 "reference_window":{"start":START,"end":END},
 "json_2xx_variants_with_candidate_records":json_2xx_with_candidates,
 "variants":rows,
 "signatures_persisted":False,
 "economic_values_persisted":False,
 "authority":"TECHNICAL_DIAGNOSTIC_ONLY",
 "firewalls":{"prices":False,"amounts":False,"balances":False,"usd_values":False,"signatures_persisted":False,
              "returns":False,"pnl":False,"direction":False,"market_outcomes":False,"live_trading":False,
              "orders":False,"wallets":False,"exchange_mutation":False,"paid_source":False,
              "account_creation":False,"merge_main":False}
}
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps(receipt,indent=2,sort_keys=True))
