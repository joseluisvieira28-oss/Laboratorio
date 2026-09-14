#!/usr/bin/env python3
import hashlib, json, math, time, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

FAMILY_ID="UTXO-DORMANCY-001"; SOURCE_GATE_ID="UD-CDD-001"
AUTHORITY_COMMIT="e7a12f8739a7bfbbacb78f92a476895e7be79903"
DRIVE_AUTHORITY_ID="1YUJXZVdggsfRoxyKexhniu9wKeRNuv_Z"
ENDPOINT="https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"
ASSET="btc"; METRIC="TxTfrValDayDst"; FREQUENCY="1d"
START_TIME="2017-01-01T00:00:00Z"; END_TIME="2024-12-31T23:59:59Z"
MIN_ROWS=2000; MIN_YEARS=6
OUT=Path("utxo_dormancy_source_gate_out"); OUT.mkdir(parents=True, exist_ok=True)
ALLOWED_ROW_KEYS={"asset","time",METRIC,f"{METRIC}-status",f"{METRIC}-status-time"}
flags={"price_values_opened":False,"signal_series_computed":False,"returns_computed":False,"pnl_computed":False,"performance_statistics_computed":False,"access_2025":False,"access_2026":False,"live_trading":False,"exchange_mutation":False}

def sha(b): return hashlib.sha256(b).hexdigest()
def wj(p,o): p.write_text(json.dumps(o,indent=2,sort_keys=True),encoding="utf-8")
def http_class(c): return "SOURCE_AUTH_BLOCKED" if c in (401,402,403) else "TECHNICAL_FAILURE"

def fail(status,reason,extra=None,code=2):
    r={"family_id":FAMILY_ID,"source_gate_id":SOURCE_GATE_ID,"phase":"SOURCE_DATA_GATE_ONLY","status":status,"reason":reason,"authority_commit":AUTHORITY_COMMIT,"drive_authority_id":DRIVE_AUTHORITY_ID,"source_endpoint":ENDPOINT,"asset":ASSET,"metric":METRIC,"frequency":FREQUENCY,"source_start":START_TIME,"source_end":END_TIME,**flags}
    if extra: r.update(extra)
    wj(OUT/"source_gate_result.json",r); print(json.dumps(r,indent=2,sort_keys=True)); raise SystemExit(code)

def url_for(token=None):
    p={"assets":ASSET,"metrics":METRIC,"frequency":FREQUENCY,"start_time":START_TIME,"end_time":END_TIME,"page_size":"10000","paging_from":"start"}
    if token: p["next_page_token"]=token
    return ENDPOINT+"?"+urllib.parse.urlencode(p)

def fetch(url,idx):
    req=urllib.request.Request(url,headers={"Accept":"application/json","User-Agent":"crypto-lab-source-gate/1.0"})
    try:
        with urllib.request.urlopen(req,timeout=45) as resp:
            raw=resp.read(); headers=dict(resp.headers.items()); code=resp.status
    except urllib.error.HTTPError as e:
        raw=e.read(); (OUT/f"page_{idx:03d}_http_error.bin").write_bytes(raw)
        fail(http_class(e.code),f"HTTP {e.code} from Coin Metrics Community API",{"http_status":e.code,"error_body_sha256":sha(raw)},2 if e.code in (401,402,403) else 6)
    except Exception as e: fail("TECHNICAL_FAILURE",f"Transport failure: {type(e).__name__}: {e}",code=6)
    (OUT/f"page_{idx:03d}.json").write_bytes(raw); wj(OUT/f"page_{idx:03d}_headers.json",headers); wj(OUT/f"page_{idx:03d}_request.json",{"url":url,"http_status":code})
    return raw

wj(OUT/"request_contract.json",{"endpoint":ENDPOINT,"assets":ASSET,"metrics":[METRIC],"frequency":FREQUENCY,"start_time":START_TIME,"end_time":END_TIME,"page_size":10000,"paging_from":"start","forbidden_market_metrics":["PriceUSD","ReferenceRate"],**flags})
rows=[]; page_hashes=[]; page=1; token=None; seen_tokens=set()
while True:
    if page>20: fail("TECHNICAL_FAILURE","Pagination exceeded 20 pages unexpectedly",code=6)
    u=url_for(token); raw=fetch(u,page); page_hashes.append({"page":page,"sha256":sha(raw),"bytes":len(raw)})
    try: payload=json.loads(raw)
    except Exception as e: fail("DATA_FAILURE",f"Invalid JSON response: {e}",{"page":page},3)
    if not isinstance(payload,dict) or not isinstance(payload.get("data"),list): fail("DATA_FAILURE","Response missing data[]",{"page":page},3)
    rows.extend(payload["data"]); nxt=payload.get("next_page_token")
    if not nxt: break
    if nxt in seen_tokens: fail("TECHNICAL_FAILURE","Repeated pagination token",{"page":page},6)
    seen_tokens.add(nxt); token=nxt; page+=1; time.sleep(0.7)
if not rows: fail("INSUFFICIENT_SAMPLE","No rows returned",{"row_count":0},4)
unexpected=sorted(set().union(*(set(r.keys()) for r in rows))-ALLOWED_ROW_KEYS)
if unexpected: fail("PROVENANCE_FAILURE","Unexpected fields in response; outcome-blind schema violated",{"unexpected_fields":unexpected},5)
seen={}; dups=[]; missing=invalid=negative=non_null=0; years=set(); first_ts=last_ts=None; statuses={}
lo=datetime(2017,1,1,tzinfo=timezone.utc); hi=datetime(2024,12,31,23,59,59,tzinfo=timezone.utc)
for i,r in enumerate(rows):
    if r.get("asset")!=ASSET: fail("PROVENANCE_FAILURE",f"Unexpected asset at row {i}",{"asset_seen":r.get("asset")},5)
    ts=r.get("time")
    if not isinstance(ts,str): fail("DATA_FAILURE",f"Missing timestamp at row {i}",code=3)
    try:
        dt=datetime.fromisoformat(ts.replace("Z","+00:00")); dt=(dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)
    except Exception: fail("DATA_FAILURE",f"Unparseable timestamp at row {i}",{"timestamp":ts},3)
    if dt.year>=2025:
        flags["access_2025"]=dt.year==2025; flags["access_2026"]=dt.year>=2026
        fail("PROVENANCE_FAILURE","Protected-period observation returned despite frozen end_time",{"first_protected_timestamp":ts},5)
    if dt<lo or dt>hi: fail("PROVENANCE_FAILURE","Observation outside frozen source window",{"timestamp":ts},5)
    dk=dt.date().isoformat(); dups.append(dk) if dk in seen else None; seen[dk]=seen.get(dk,0)+1; years.add(dt.year)
    first_ts=ts if first_ts is None or ts<first_ts else first_ts; last_ts=ts if last_ts is None or ts>last_ts else last_ts
    v=r.get(METRIC)
    if v is None or v=="": missing+=1; continue
    try: fv=float(v)
    except Exception: invalid+=1; continue
    if not math.isfinite(fv): invalid+=1; continue
    if fv<0: negative+=1
    non_null+=1; st=r.get(f"{METRIC}-status","unspecified"); statuses[st]=statuses.get(st,0)+1
unique_days=len(seen); expected=(hi.date()-lo.date()).days+1; missing_dates=expected-unique_days
manifest={"family_id":FAMILY_ID,"source_gate_id":SOURCE_GATE_ID,"authority_commit":AUTHORITY_COMMIT,"drive_authority_id":DRIVE_AUTHORITY_ID,"page_hashes":page_hashes,"pages":page,"row_count":len(rows),"unique_days":unique_days,"non_null_metric_rows":non_null,"missing_metric_rows":missing,"invalid_metric_rows":invalid,"negative_metric_rows":negative,"duplicate_dates_count":len(dups),"duplicate_dates":sorted(set(dups))[:100],"first_timestamp":first_ts,"last_timestamp":last_ts,"distinct_years":sorted(years),"distinct_year_count":len(years),"expected_calendar_days_in_window":expected,"missing_dates_count":missing_dates,"provider_status_counts":statuses,**flags}
wj(OUT/"source_manifest.json",manifest); manifest_sha=sha((OUT/"source_manifest.json").read_bytes())
if dups: fail("DATA_FAILURE","Duplicate UTC dates present",{**manifest,"source_manifest_sha256":manifest_sha},3)
if invalid or negative: fail("DATA_FAILURE","Invalid or negative metric values present",{**manifest,"source_manifest_sha256":manifest_sha},3)
if non_null<MIN_ROWS or len(years)<MIN_YEARS: fail("INSUFFICIENT_SAMPLE","Frozen minimum source sample not met",{**manifest,"source_manifest_sha256":manifest_sha},4)
result={"family_id":FAMILY_ID,"source_gate_id":SOURCE_GATE_ID,"phase":"SOURCE_DATA_GATE_ONLY","status":"SOURCE_DATA_PASS","reason":"Single frozen Coin Days Destroyed metric passed source/provenance/sample gates","authority_commit":AUTHORITY_COMMIT,"drive_authority_id":DRIVE_AUTHORITY_ID,"source_endpoint":ENDPOINT,"asset":ASSET,"metric":METRIC,"frequency":FREQUENCY,"source_start":START_TIME,"source_end":END_TIME,"row_count":len(rows),"unique_days":unique_days,"non_null_metric_rows":non_null,"first_timestamp":first_ts,"last_timestamp":last_ts,"distinct_year_count":len(years),"distinct_years":sorted(years),"missing_dates_count":missing_dates,"duplicate_dates_count":0,"provider_status_counts":statuses,"source_manifest_sha256":manifest_sha,"page_hashes":page_hashes,**flags}
wj(OUT/"source_gate_result.json",result); print(json.dumps(result,indent=2,sort_keys=True))
