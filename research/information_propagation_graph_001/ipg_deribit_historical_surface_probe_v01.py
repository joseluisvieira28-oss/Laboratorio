#!/usr/bin/env python3
import hashlib,json,urllib.request
from datetime import datetime,timezone
from pathlib import Path

URL="https://www.deribit.com/api/v2"
OUT=Path("artifacts/ipg_deribit_historical_surface_probe_v01.json")
START=int(datetime(2024,6,1,tzinfo=timezone.utc).timestamp()*1000)
END=int(datetime(2024,6,2,tzinfo=timezone.utc).timestamp()*1000)-1
JUNE_START=START
JULY_START=int(datetime(2024,7,1,tzinfo=timezone.utc).timestamp()*1000)

def call(method,params):
    payload=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    req=urllib.request.Request(URL,data=payload,headers={"Content-Type":"application/json","User-Agent":"CryptoLab-IPG-001-Deribit-Hist/0.1"},method="POST")
    with urllib.request.urlopen(req,timeout=45) as r:
        raw=r.read()
    x=json.loads(raw.decode())
    if x.get("error"):raise RuntimeError(x["error"])
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
        for k in ("timestamp","tick","time","t"):
            x=d.get(k)
            if isinstance(x,(int,float)) and x>1e11: vals.append(int(x))
    if isinstance(v,list):
        for row in v:
            if isinstance(row,list) and row and isinstance(row[0],(int,float)) and row[0]>1e11:
                vals.append(int(row[0]))
    return sorted(set(vals))

def meta(name,fn):
    try:
        result,raw=fn()
        ts=timestamps(result)
        keys=sorted({k for d in walk(result) for k in d.keys()})[:100]
        count=len(result) if isinstance(result,list) else (
            len(result.get("trades",[])) if isinstance(result,dict) and isinstance(result.get("trades"),list) else
            len(result.get("data",[])) if isinstance(result,dict) and isinstance(result.get("data"),list) else None)
        spacings=[b-a for a,b in zip(ts,ts[1:]) if b>a]
        return {"name":name,"pass":True,"count":count,"min_ts":min(ts) if ts else None,"max_ts":max(ts) if ts else None,
                "min_positive_spacing_ms":min(spacings) if spacings else None,"field_names":keys,
                "raw_sha256":hashlib.sha256(raw).hexdigest(),"raw_bytes":len(raw)}
    except Exception as e:
        return {"name":name,"pass":False,"error":f"{type(e).__name__}:{str(e)[:700]}"}

receipt={"lab_id":"INFORMATION-PROPAGATION-GRAPH-001","stage":"DERIBIT_HISTORICAL_SURFACE_SOURCE_PROBE_V0.1",
 "fixture_start_ms":START,"fixture_end_ms":END,"checks":[],
 "target_price_outcomes_opened":False,"predictive_analysis_performed":False,"price_values_persisted":False,
 "mutation":False,"pnl_opened":False}

# expired option inventory
try:
    inst,raw=call("public/get_instruments",{"currency":"BTC","kind":"option","expired":True})
    june=[x for x in inst if isinstance(x,dict) and JUNE_START<=int(x.get("expiration_timestamp",0))<JULY_START]
    june.sort(key=lambda x:str(x.get("instrument_name","")))
    receipt["expired_btc_options_total"]=len(inst)
    receipt["june_2024_expired_options"]=len(june)
    receipt["instrument_inventory_sha256"]=hashlib.sha256(raw).hexdigest()
    selected=june[0] if june else None
    receipt["selected_option"]={k:selected.get(k) for k in ("instrument_name","expiration_timestamp","creation_timestamp","strike","option_type")} if selected else None
except Exception as e:
    selected=None
    receipt["instrument_inventory_error"]=f"{type(e).__name__}:{str(e)[:700]}"

if selected:
    name=selected["instrument_name"]
    active_start=max(START,int(selected.get("creation_timestamp") or START))
    active_end=min(END,int(selected.get("expiration_timestamp") or END)-1)
    receipt["checks"].append(meta("option_mark_price_history",lambda:call("public/get_mark_price_history",{"instrument_name":name,"start_timestamp":active_start,"end_timestamp":active_end})))
    receipt["checks"].append(meta("option_trades_by_time",lambda:call("public/get_last_trades_by_instrument_and_time",{"instrument_name":name,"start_timestamp":active_start,"end_timestamp":active_end,"count":1000,"sorting":"asc"})))

receipt["checks"].append(meta("btc_perp_mark_price_history",lambda:call("public/get_mark_price_history",{"instrument_name":"BTC-PERPETUAL","start_timestamp":START,"end_timestamp":END})))
receipt["checks"].append(meta("btc_perp_funding_history",lambda:call("public/get_funding_rate_history",{"instrument_name":"BTC-PERPETUAL","start_timestamp":START,"end_timestamp":END})))

# Try documented volatility endpoint with common numeric resolution first; record exact failure if schema differs.
def dvol():
    attempts=[]
    for resolution in (60,300,3600):
        try:return call("public/get_volatility_index_data",{"currency":"BTC","start_timestamp":START,"end_timestamp":END,"resolution":resolution})
        except Exception as e:attempts.append(f"{resolution}:{type(e).__name__}:{str(e)[:160]}")
    raise RuntimeError(" | ".join(attempts))
receipt["checks"].append(meta("btc_dvol_history",dvol))

passed=[x["name"] for x in receipt["checks"] if x.get("pass")]
option_ok=any(x.get("pass") for x in receipt["checks"] if x["name"].startswith("option_"))
perp_ok=any(x.get("pass") for x in receipt["checks"] if x["name"].startswith("btc_perp_"))
dvol_ok=any(x.get("pass") for x in receipt["checks"] if x["name"]=="btc_dvol_history")
if option_ok and perp_ok and dvol_ok: cls="DERIBIT_HISTORICAL_SURFACE_PASS"
elif passed: cls="DERIBIT_HISTORICAL_SURFACE_PARTIAL"
else: cls="DERIBIT_HISTORICAL_SURFACE_BLOCKED"
receipt["classification"]=cls
receipt["passing_methods"]=passed
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2))
