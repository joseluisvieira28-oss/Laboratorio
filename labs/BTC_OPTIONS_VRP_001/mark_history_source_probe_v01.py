#!/usr/bin/env python3
import hashlib,json,sys
from datetime import datetime,timedelta,timezone
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parent
AUTH=json.loads((ROOT/"MARK_HISTORY_SOURCE_AUTHORITY_V0.1.json").read_text())
OUT=Path("artifacts/btc_options_vrp_mark_history_probe_v01");OUT.mkdir(parents=True,exist_ok=True)

def ms(z): return int(z.timestamp()*1000)
def h(b): return hashlib.sha256(b).hexdigest()

def extract_rows(obj):
    r=(obj or {}).get("result")
    if isinstance(r,list): return r
    if isinstance(r,dict):
        for k in ("data","prices","records","history"):
            if isinstance(r.get(k),list): return r[k]
    return []

def point_ts(x):
    if isinstance(x,(list,tuple)) and x:
        return x[0] if isinstance(x[0],(int,float)) else None
    if isinstance(x,dict):
        for k in ("timestamp","time","date"):
            v=x.get(k)
            if isinstance(v,(int,float)): return v
    return None

receipt={"lab_id":AUTH["lab_id"],"probe_id":AUTH["probe_id"],"classification":None,"legs":[],"error":None,
         "safety":{"mark_price_values_retained":False,"returns_opened":False,"strategy_pnl_opened":False,
                   "access_2025":False,"access_2026":False,"api_key_used":False,"paid_subscription_used":False,
                   "live_trading":False,"exchange_mutation":False,"merge_to_main":False}}
try:
    assert AUTH["status"]=="FROZEN_SOURCE_ONLY_OUTCOME_BLIND"
    assert all(v is False for k,v in AUTH["safety"].items() if k.endswith("_authorized"))
    for case in AUTH["cases"]:
        start=datetime.fromisoformat(case["date"]).replace(tzinfo=timezone.utc)
        end=start+timedelta(days=AUTH["window"]["end_offset_days"])
        if start.year>=2025 or end.year>=2025: raise RuntimeError("protected-period access blocked")
        for right in ("call","put"):
            inst=case[right]
            params={"instrument_name":inst,"start_timestamp":ms(start),"end_timestamp":ms(end)}
            r=requests.get(AUTH["source"]["url"],params=params,timeout=(20,60),
                           headers={"User-Agent":"SRC-Crypto-Lab-VRP-MarkHistory/0.1"})
            raw=r.content;dig=h(raw)
            if r.status_code!=200: raise RuntimeError(f"HTTP {r.status_code} {inst} sha256={dig}")
            obj=r.json(); err=obj.get("error") if isinstance(obj,dict) else None
            if err: raise RuntimeError(f"API error {inst} sha256={dig} error={err}")
            rows=extract_rows(obj)
            tss=[int(point_ts(x)) for x in rows if point_ts(x) is not None]
            first=min(tss) if tss else None;last=max(tss) if tss else None
            span=(last-first)/3600000 if first is not None and last is not None else 0.0
            passed=(len(tss)>=AUTH["pass_rule"]["minimum_points_per_leg"] and span>=AUTH["pass_rule"]["minimum_span_hours_per_leg"])
            receipt["legs"].append({"year":start.year,"instrument_name":inst,"http_status":r.status_code,
                                     "payload_sha256":dig,"point_count":len(tss),
                                     "first_timestamp":first,"last_timestamp":last,
                                     "span_hours":span,"pass":passed})
    all_pass=all(x["pass"] for x in receipt["legs"]) and len(receipt["legs"])==8 and len({x["year"] for x in receipt["legs"]})==4
    receipt["classification"]=AUTH["classifications"]["pass"] if all_pass else AUTH["classifications"]["insufficient"]
except Exception as e:
    receipt["classification"]=AUTH["classifications"]["provenance_failure"] if "protected-period" in repr(e) else AUTH["classifications"]["technical_failure"]
    receipt["error"]=repr(e)
p=OUT/"MARK_HISTORY_SOURCE_PROBE_RECEIPT_V0.1.json";p.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({"classification":receipt["classification"],"legs":[{"year":x["year"],"instrument":x["instrument_name"],"n":x["point_count"],"span_h":x["span_hours"],"pass":x["pass"]} for x in receipt["legs"]],"error":receipt["error"],"safety":receipt["safety"]},sort_keys=True))
sys.exit(0 if receipt["classification"] in (AUTH["classifications"]["pass"],AUTH["classifications"]["insufficient"]) else 2)
