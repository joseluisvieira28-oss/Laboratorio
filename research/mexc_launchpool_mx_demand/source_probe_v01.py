import ccxt, json, os, re, time
from datetime import datetime, timezone

OUT="artifacts/mexc_launchpool_mx_demand_v01_source"
os.makedirs(OUT,exist_ok=True)
ex=ccxt.mexc({"enableRateLimit":True})

attempts=[]
param_sets=[
 {},
 {"pageNum":1,"pageSize":100},
 {"page":1,"pageSize":100},
 {"pageNum":1,"limit":100},
 {"page":1,"limit":100},
]
for params in param_sets:
    try:
        x=ex.spot_public_get_announcements(params)
        attempts.append({"params":params,"ok":True,"type":type(x).__name__,"response":x})
    except Exception as e:
        attempts.append({"params":params,"ok":False,"error":repr(e)})

with open(f"{OUT}/announcement_probe.json","w",encoding="utf-8") as f:
    json.dump(attempts,f,ensure_ascii=False,indent=2,default=str)

def flatten(obj):
    rows=[]
    if isinstance(obj,dict):
        # likely containers
        for k,v in obj.items():
            if isinstance(v,list):
                for item in v:
                    if isinstance(item,dict):
                        rows.append(item)
            elif isinstance(v,dict):
                rows.extend(flatten(v))
    return rows

allrows=[]
for a in attempts:
    if a.get("ok"):
        allrows.extend(flatten(a["response"]))

# de-duplicate raw dicts
uniq=[]
seen=set()
for r in allrows:
    s=json.dumps(r,sort_keys=True,ensure_ascii=False,default=str)
    if s not in seen:
        seen.add(s); uniq.append(r)

def textish(r):
    return " ".join(str(v) for v in r.values() if isinstance(v,(str,int,float)))

launch=[r for r in uniq if "launchpool" in textish(r).lower()]
mx=[r for r in launch if re.search(r"\bMX\b", textish(r), re.I)]

summary={
 "endpoint":"MEXC public announcements via CCXT spotPublicGetAnnouncements",
 "authenticated":False,
 "market_prices_opened":False,
 "probe_attempts":len(attempts),
 "raw_unique_rows":len(uniq),
 "launchpool_rows":len(launch),
 "launchpool_rows_with_MX_text":len(mx),
 "sample_keys":sorted(list(uniq[0].keys())) if uniq else [],
}
with open(f"{OUT}/source_probe_summary.json","w") as f: json.dump(summary,f,indent=2)
with open(f"{OUT}/launchpool_rows.json","w",encoding="utf-8") as f: json.dump(launch,f,ensure_ascii=False,indent=2,default=str)
with open(f"{OUT}/launchpool_mx_rows.json","w",encoding="utf-8") as f: json.dump(mx,f,ensure_ascii=False,indent=2,default=str)
print(json.dumps(summary,indent=2))
