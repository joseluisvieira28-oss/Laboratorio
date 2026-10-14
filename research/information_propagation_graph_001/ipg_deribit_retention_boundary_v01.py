#!/usr/bin/env python3
import hashlib,json,urllib.request
from collections import Counter
from datetime import datetime,timezone,timedelta
from pathlib import Path

URL="https://www.deribit.com/api/v2"
OUT=Path("artifacts/ipg_deribit_retention_boundary_v01.json")

def call(method,params):
    data=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    req=urllib.request.Request(URL,data=data,headers={"Content-Type":"application/json","User-Agent":"CryptoLab-IPG-001-Retention/0.1"},method="POST")
    with urllib.request.urlopen(req,timeout=45) as r: raw=r.read()
    x=json.loads(raw.decode())
    if x.get("error"): raise RuntimeError(x["error"])
    return x.get("result"),raw

def walk(v):
    if isinstance(v,dict):
        yield v
        for z in v.values(): yield from walk(z)
    elif isinstance(v,list):
        for z in v: yield from walk(z)

def timestamps(v):
    vals=[]
    for d in walk(v):
        x=d.get("timestamp")
        if isinstance(x,(int,float)) and x>1e11: vals.append(int(x))
    if isinstance(v,list):
        for row in v:
            if isinstance(row,list) and row and isinstance(row[0],(int,float)) and row[0]>1e11: vals.append(int(row[0]))
    return sorted(set(vals))

def check(name,method,params):
    try:
        result,raw=call(method,params)
        ts=timestamps(result)
        if isinstance(result,list): count=len(result)
        elif isinstance(result,dict) and isinstance(result.get("trades"),list): count=len(result["trades"])
        elif isinstance(result,dict) and isinstance(result.get("data"),list): count=len(result["data"])
        else: count=None
        fields=sorted({k for d in walk(result) for k in d.keys()})[:100]
        return {"name":name,"pass_call":True,"row_count":count,"min_ts":min(ts) if ts else None,
                "max_ts":max(ts) if ts else None,"field_names":fields,
                "raw_sha256":hashlib.sha256(raw).hexdigest(),"raw_bytes":len(raw)}
    except Exception as e:
        return {"name":name,"pass_call":False,"error":f"{type(e).__name__}:{str(e)[:700]}"}

inst,raw=call("public/get_instruments",{"currency":"BTC","kind":"option","expired":True})
valid=[x for x in inst if isinstance(x,dict) and isinstance(x.get("expiration_timestamp"),(int,float)) and isinstance(x.get("instrument_name"),str)]
valid.sort(key=lambda x:(int(x["expiration_timestamp"]),x["instrument_name"]))
months=Counter(datetime.fromtimestamp(int(x["expiration_timestamp"])/1000,tz=timezone.utc).strftime("%Y-%m") for x in valid)

receipt={"lab_id":"INFORMATION-PROPAGATION-GRAPH-001","stage":"DERIBIT_RETENTION_BOUNDARY_REMEDIATION_V0.1",
 "expired_option_count":len(valid),"inventory_sha256":hashlib.sha256(raw).hexdigest(),
 "expiration_month_histogram":dict(sorted(months.items())),
 "min_expiration_ts":int(valid[0]["expiration_timestamp"]) if valid else None,
 "max_expiration_ts":int(valid[-1]["expiration_timestamp"]) if valid else None,
 "checks":[],"price_values_persisted":False,"predictive_analysis_performed":False,
 "target_price_outcomes_opened":False,"mutation":False,"pnl_opened":False}

if valid:
    earliest=int(valid[0]["expiration_timestamp"])
    cohort=sorted([x for x in valid if int(x["expiration_timestamp"])==earliest],key=lambda x:x["instrument_name"])
    selected=cohort[0]
    expiry=datetime.fromtimestamp(earliest/1000,tz=timezone.utc)
    day=(expiry-timedelta(days=1)).date()
    start=int(datetime(day.year,day.month,day.day,tzinfo=timezone.utc).timestamp()*1000)
    end=start+86400000-1
    name=selected["instrument_name"]
    receipt["selected_option"]={"instrument_name":name,"expiration_timestamp":earliest,"creation_timestamp":selected.get("creation_timestamp")}
    receipt["fixture_start_ms"]=start;receipt["fixture_end_ms"]=end
    receipt["checks"].append(check("option_trades","public/get_last_trades_by_instrument_and_time",{"instrument_name":name,"start_timestamp":start,"end_timestamp":end,"count":1000,"sorting":"asc"}))
    receipt["checks"].append(check("option_mark_history","public/get_mark_price_history",{"instrument_name":name,"start_timestamp":start,"end_timestamp":end}))
    receipt["checks"].append(check("perp_mark_history","public/get_mark_price_history",{"instrument_name":"BTC-PERPETUAL","start_timestamp":start,"end_timestamp":end}))
    receipt["checks"].append(check("perp_funding_history","public/get_funding_rate_history",{"instrument_name":"BTC-PERPETUAL","start_timestamp":start,"end_timestamp":end}))
    dvol=None
    for resolution in (60,300,3600):
        z=check(f"dvol_{resolution}","public/get_volatility_index_data",{"currency":"BTC","start_timestamp":start,"end_timestamp":end,"resolution":resolution})
        if z.get("pass_call") and (z.get("row_count") or 0)>0:
            dvol=z;break
        if dvol is None:dvol=z
    receipt["checks"].append(dvol)

option_rows=sum((x.get("row_count") or 0) for x in receipt["checks"] if x["name"].startswith("option_"))
other_rows=sum((x.get("row_count") or 0) for x in receipt["checks"] if not x["name"].startswith("option_"))
if option_rows>0 and other_rows>0: cls="RETENTION_BOUNDARY_SURFACE_PASS"
elif option_rows>0 or other_rows>0: cls="RETENTION_BOUNDARY_PARTIAL"
else: cls="RETENTION_BOUNDARY_BLOCKED"
receipt["classification"]=cls
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2))
