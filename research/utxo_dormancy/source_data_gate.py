#!/usr/bin/env python3
"""Outcome-blind Coin Metrics source/data gate for UTXO-DORMANCY-001."""
from __future__ import annotations
import datetime as dt, hashlib, json, math, os, pathlib, sys, urllib.error, urllib.parse, urllib.request

LAB="UTXO-DORMANCY-001"; GATE="UD-CDD-001"
BASE="https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"
START="2017-01-01T00:00:00Z"; END="2024-12-31T23:59:59Z"
OUT=pathlib.Path(os.environ.get("UD_OUT","utxo_dormancy_source_gate_artifact"))
RAW=OUT/"raw"; RAW.mkdir(parents=True,exist_ok=True)
params={"assets":"btc","metrics":"TxTfrValDayDst","frequency":"1d","start_time":START,
        "end_time":END,"paging_from":"start","page_size":"10000"}
url=BASE+"?"+urllib.parse.urlencode(params)
transport=[]; files=[]; rows=[]; page=0
try:
    while url:
        page+=1
        req=urllib.request.Request(url,headers={"Accept":"application/json","User-Agent":"Laboratorio-Research-SourceGate/0.1"})
        try:
            with urllib.request.urlopen(req,timeout=60) as resp:
                body=resp.read(); status=resp.status; headers=dict(resp.headers.items())
        except urllib.error.HTTPError as e:
            body=e.read(); status=e.code; headers=dict(e.headers.items())
        except Exception as e:
            transport.append({"page":page,"type":type(e).__name__,"message":str(e)})
            verdict="SOURCE_ACQUISITION_TECHNICAL_FAILURE"; break
        p=RAW/f"page_{page:04d}.json"; p.write_bytes(body)
        files.append({"path":str(p.relative_to(OUT)),"bytes":len(body),"sha256":hashlib.sha256(body).hexdigest(),
                      "http_status":status,"request_url":url,
                      "headers":{k:v for k,v in headers.items() if k.lower() in ("date","content-type","etag","last-modified","x-ratelimit-limit","x-ratelimit-remaining")}})
        if status in (401,403):
            verdict="SOURCE_AUTH_BLOCKED"; break
        if status!=200:
            transport.append({"page":page,"http_status":status}); verdict="SOURCE_ACQUISITION_TECHNICAL_FAILURE"; break
        try: payload=json.loads(body)
        except Exception:
            verdict="DATA_FAILURE"; break
        rows.extend(payload.get("data",[]))
        url=payload.get("next_page_url")
    else:
        verdict=None
except Exception as e:
    transport.append({"type":type(e).__name__,"message":str(e)})
    verdict="SOURCE_ACQUISITION_TECHNICAL_FAILURE"

duplicates=[]; malformed=[]; out_of_window=[]; seen={}; years=set()
start_d=dt.date(2017,1,1); end_d=dt.date(2024,12,31)
for i,r in enumerate(rows):
    try:
        if set(r)-{"asset","time","TxTfrValDayDst","TxTfrValDayDst-status","TxTfrValDayDst-status-time"}:
            pass
        if r.get("asset")!="btc": raise ValueError("asset")
        ts=r["time"]; day=dt.datetime.fromisoformat(ts.replace("Z","+00:00")).date()
        if not(start_d<=day<=end_d): out_of_window.append({"index":i,"time":ts})
        if day.isoformat() in seen: duplicates.append({"date":day.isoformat(),"indexes":[seen[day.isoformat()],i]})
        else: seen[day.isoformat()]=i
        v=float(r["TxTfrValDayDst"])
        if not math.isfinite(v) or v<0: raise ValueError("value")
        years.add(day.year)
    except Exception as e:
        malformed.append({"index":i,"reason":str(e)})
expected=[]; d=start_d
while d<=end_d:
    if d.isoformat() not in seen: expected.append(d.isoformat())
    d+=dt.timedelta(days=1)
if verdict is None:
    if out_of_window or duplicates or malformed: verdict="PROVENANCE_FAILURE" if out_of_window or duplicates else "DATA_FAILURE"
    elif len(rows)<2000 or len(years)<6: verdict="INSUFFICIENT_SAMPLE"
    else: verdict="SOURCE_DATA_PASS"
manifest={"lab":LAB,"gate":GATE,"run_id":os.environ.get("GITHUB_RUN_ID","local"),
"source":BASE,"request":params,"verdict":verdict,"pages":page,"total_rows":len(rows),
"first_observation":min(seen) if seen else None,"last_observation":max(seen) if seen else None,
"years":sorted(years),"missing_dates":expected,"missing_count":len(expected),
"duplicates":duplicates,"duplicate_count":len(duplicates),"malformed":malformed,
"malformed_count":len(malformed),"out_of_window":out_of_window,"transport_failures":transport,
"raw_files":files,"firewall":{"btc_price_values_opened":False,"eth_price_values_opened":False,
"market_returns_computed":False,"pnl_computed":False,"performance_statistics_computed":False,
"holdout_2025_accessed":False,"year_2026_accessed":False,"live_trading_authorized":False,
"exchange_mutation_authorized":False}}
mb=json.dumps(manifest,sort_keys=True,indent=2).encode()+b"\n"
(OUT/"manifest.json").write_bytes(mb)
(OUT/"manifest.sha256").write_text(hashlib.sha256(mb).hexdigest()+"  manifest.json\n",encoding="utf-8")
(OUT/"verdict.txt").write_text(verdict+"\n",encoding="utf-8")
print(json.dumps({k:manifest[k] for k in ("lab","gate","run_id","verdict","total_rows","first_observation","last_observation","missing_count","duplicate_count","malformed_count")},sort_keys=True))
sys.exit(0 if verdict in {"SOURCE_DATA_PASS","SOURCE_AUTH_BLOCKED","SOURCE_ACQUISITION_TECHNICAL_FAILURE","DATA_FAILURE","PROVENANCE_FAILURE","INSUFFICIENT_SAMPLE"} else 2)
