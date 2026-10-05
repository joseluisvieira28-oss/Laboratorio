#!/usr/bin/env python3
import json,urllib.request

URL="https://www.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/cex/alpha/all/token/list"
req=urllib.request.Request(URL,headers={"User-Agent":"Mozilla/5.0 CryptoLabDualPrecursorAlphaSchema/1.0","Accept":"application/json"})
with urllib.request.urlopen(req,timeout=30) as r:
    status=r.status
    obj=json.load(r)

# Normalize likely response wrappers without assuming schema.
data=obj.get("data",obj) if isinstance(obj,dict) else obj
if isinstance(data,dict):
    # find first list-valued field
    list_fields={k:v for k,v in data.items() if isinstance(v,list)}
    rows=next(iter(list_fields.values()),[])
elif isinstance(data,list):
    rows=data
else:
    rows=[]

keys=sorted({k for x in rows if isinstance(x,dict) for k in x.keys()})
# Print metadata only. No prices or outcome-derived fields.
safe_names=[k for k in keys if any(z in k.lower() for z in ("symbol","name","token","chain","contract","address","time","date","status","id"))]
samples=[]
for x in rows[:5]:
    if isinstance(x,dict):
        samples.append({k:x.get(k) for k in safe_names if k in x})

time_like=[k for k in keys if any(z in k.lower() for z in ("time","date","created","online","launch","list"))]
identity_like=[k for k in keys if any(z in k.lower() for z in ("symbol","name","token","contract","address","id"))]
res={
 "http_status":status,
 "row_count":len(rows),
 "top_level_type":type(data).__name__,
 "all_row_keys":keys,
 "identity_like_fields":identity_like,
 "time_like_fields":time_like,
 "sample_metadata":samples,
 "source_reachable":status==200 and len(rows)>0,
 "historical_timestamp_fields_present":len(time_like)>0,
}
print("DUAL_PRECURSOR_ALPHA_SCHEMA_BEGIN")
print(json.dumps(res,indent=2,ensure_ascii=False,sort_keys=True))
print("DUAL_PRECURSOR_ALPHA_SCHEMA_END")
if not res["source_reachable"]:
    raise SystemExit(2)

# trigger after workflow YAML repair
