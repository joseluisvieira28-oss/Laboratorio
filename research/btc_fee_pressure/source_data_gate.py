#!/usr/bin/env python3
"""Outcome-blind source/data gate for BTC-FEE-PRESSURE-001."""
from __future__ import annotations
import datetime as dt, hashlib, json, math, os, pathlib, sys, urllib.error, urllib.parse, urllib.request

LAB="BTC-FEE-PRESSURE-001"; GATE="BFP-TOTALFEES-7D-001"
BASE="https://api.blockchain.info/charts/transaction-fees"
OUT=pathlib.Path(os.environ.get("BFP_OUT","btc_fee_pressure_source_gate_artifact"))
RAW=OUT/"raw"; RAW.mkdir(parents=True,exist_ok=True)
windows=[
 ("2021","2021-01-01","364days",dt.date(2021,1,1),dt.date(2021,12,31)),
 ("2022","2022-01-01","364days",dt.date(2022,1,1),dt.date(2022,12,31)),
 ("2023","2023-01-01","364days",dt.date(2023,1,1),dt.date(2023,12,31)),
 ("2024","2024-01-01","365days",dt.date(2024,1,1),dt.date(2024,12,31)),
]
raw_files=[]; transport=[]; rows=[]; schemas=[]; verdict=None
for label,start,span,lo,hi in windows:
    params={"start":start,"timespan":span,"rollingAverage":"1day","format":"json","sampled":"false"}
    url=BASE+"?"+urllib.parse.urlencode(params)
    req=urllib.request.Request(url,headers={"Accept":"application/json","User-Agent":"Laboratorio-Research-SourceGate/0.1"})
    try:
        with urllib.request.urlopen(req,timeout=90) as resp:
            body=resp.read(); status=resp.status; headers=dict(resp.headers.items())
    except urllib.error.HTTPError as e:
        body=e.read(); status=e.code; headers=dict(e.headers.items())
    except Exception as e:
        transport.append({"window":label,"type":type(e).__name__,"message":str(e)})
        verdict="SOURCE_ACQUISITION_TECHNICAL_FAILURE"; break
    p=RAW/f"transaction_fees_{label}.json"; p.write_bytes(body)
    raw_files.append({"path":str(p.relative_to(OUT)),"bytes":len(body),"sha256":hashlib.sha256(body).hexdigest(),
      "http_status":status,"request_url":url,"headers":{k:v for k,v in headers.items() if k.lower() in
      ("date","content-type","etag","last-modified","cache-control","x-ratelimit-limit","x-ratelimit-remaining")}})
    if status in (401,403):
        verdict="SOURCE_AUTH_BLOCKED"; break
    if status==429 or status>=500:
        transport.append({"window":label,"http_status":status}); verdict="SOURCE_ACQUISITION_TECHNICAL_FAILURE"; break
    if status!=200:
        transport.append({"window":label,"http_status":status}); verdict="DATA_FAILURE"; break
    try: payload=json.loads(body)
    except Exception as e:
        transport.append({"window":label,"decode":str(e)}); verdict="DATA_FAILURE"; break
    schemas.append({"window":label,"keys":sorted(payload.keys()),"status":payload.get("status"),
                    "name":payload.get("name"),"unit":payload.get("unit"),"period":payload.get("period")})
    meta=(" ".join(str(payload.get(k,"")) for k in ("name","unit","description"))).lower()
    if "usd" in meta or "market price" in meta:
        verdict="PROVENANCE_FAILURE"; break
    vals=payload.get("values")
    if not isinstance(vals,list):
        verdict="DATA_FAILURE"; break
    for item in vals:
        rows.append({"window":label,"item":item})

seen={}; duplicates=[]; malformed=[]; out_of_window=[]; clean=[]
global_lo=dt.date(2021,1,1); global_hi=dt.date(2024,12,31)
for i,wrapped in enumerate(rows):
    item=wrapped["item"]
    try:
        if not isinstance(item,dict) or set(item)!={"x","y"}: raise ValueError("schema")
        x=item["x"]; y=item["y"]
        if not isinstance(x,(int,float)) or int(x)!=x: raise ValueError("timestamp")
        stamp=dt.datetime.fromtimestamp(int(x),tz=dt.timezone.utc)
        if stamp.time()!=dt.time(0,0): raise ValueError("not_utc_midnight")
        day=stamp.date()
        if not(global_lo<=day<=global_hi):
            out_of_window.append({"index":i,"date":day.isoformat()}); continue
        key=day.isoformat()
        if key in seen: duplicates.append({"date":key,"indexes":[seen[key],i]})
        else: seen[key]=i
        value=float(y)
        if not math.isfinite(value) or value<0: raise ValueError("fee_value")
        clean.append((key,value))
    except Exception as e:
        malformed.append({"index":i,"reason":str(e)})
missing=[]; d=global_lo
while d<=global_hi:
    if d.isoformat() not in seen: missing.append(d.isoformat())
    d+=dt.timedelta(days=1)
if verdict is None:
    if out_of_window or duplicates: verdict="PROVENANCE_FAILURE"
    elif malformed: verdict="DATA_FAILURE"
    elif len(clean)<1400 or len({k[:4] for k,_ in clean})<4: verdict="INSUFFICIENT_SAMPLE"
    else: verdict="SOURCE_DATA_PASS"
manifest={"lab":LAB,"gate":GATE,"run_id":os.environ.get("GITHUB_RUN_ID","local"),"verdict":verdict,
"source":BASE,"windows":[{"year":a,"start":b,"timespan":c} for a,b,c,_,_ in windows],
"schemas":schemas,"raw_files":raw_files,"total_rows":len(rows),"clean_rows":len(clean),
"first_observation":min((k for k,_ in clean),default=None),"last_observation":max((k for k,_ in clean),default=None),
"missing_count":len(missing),"missing_dates":missing,"duplicate_count":len(duplicates),"duplicates":duplicates,
"malformed_count":len(malformed),"malformed":malformed,"out_of_window_count":len(out_of_window),
"out_of_window":out_of_window,"transport_failures":transport,
"firewall":{"btc_price_values_opened":False,"eth_price_values_opened":False,"market_returns_computed":False,
"pnl_computed":False,"performance_statistics_computed":False,
"holdout_2025_accessed":any(x.get("date","").startswith("2025") for x in out_of_window),
"year_2026_accessed":any(x.get("date","").startswith("2026") for x in out_of_window),
"live_trading_authorized":False,"exchange_mutation_authorized":False,"discovery_authorized":False}}
mb=json.dumps(manifest,sort_keys=True,indent=2).encode()+b"\n"
(OUT/"manifest.json").write_bytes(mb)
(OUT/"manifest.sha256").write_text(hashlib.sha256(mb).hexdigest()+"  manifest.json\n",encoding="utf-8")
(OUT/"verdict.txt").write_text(verdict+"\n",encoding="utf-8")
print(json.dumps({k:manifest[k] for k in ("lab","gate","run_id","verdict","total_rows","clean_rows","first_observation","last_observation","missing_count","duplicate_count","malformed_count","out_of_window_count")},sort_keys=True))
print("RAW_SHA256 "+json.dumps({f["path"]:f["sha256"] for f in raw_files},sort_keys=True))
print("MANIFEST_SHA256 "+hashlib.sha256(mb).hexdigest())
sys.exit(0)
