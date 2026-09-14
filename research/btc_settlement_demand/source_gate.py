#!/usr/bin/env python3
import hashlib, json, math, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

FAMILY_ID="BTC-SETTLEMENT-DEMAND-001"; SOURCE_GATE_ID="BSD-TXCOUNT-002"
AUTHORITY_COMMIT="6e23b0df54db10e96294403c3d7c33460168bb4a"
DRIVE_AUTHORITY_ID="1zSEtz0CWJAyV9CEF5JQHEF7QrJmf8dFV"
ENDPOINT="https://api.blockchain.info/charts/n-transactions"
START="2017-01-01"; TIMESPAN="2921days"
WINDOW_START=datetime(2017,1,1,tzinfo=timezone.utc); WINDOW_END=datetime(2024,12,31,23,59,59,tzinfo=timezone.utc)
MIN_UNIQUE_DAYS=2500; MIN_YEARS=7
OUT=Path("btc_settlement_demand_source_gate_out"); OUT.mkdir(parents=True,exist_ok=True)
flags={"price_values_opened":False,"signal_series_computed":False,"returns_computed":False,"pnl_computed":False,"performance_statistics_computed":False,"access_2025":False,"access_2026":False,"live_trading":False,"exchange_mutation":False}

def sha(b): return hashlib.sha256(b).hexdigest()
def wj(p,o): p.write_text(json.dumps(o,indent=2,sort_keys=True),encoding="utf-8")
def fail(status,reason,extra=None,code=2):
    r={"family_id":FAMILY_ID,"source_gate_id":SOURCE_GATE_ID,"phase":"SOURCE_DATA_GATE_ONLY","status":status,"reason":reason,"authority_commit":AUTHORITY_COMMIT,"drive_authority_id":DRIVE_AUTHORITY_ID,"endpoint":ENDPOINT,"source_start":"2017-01-01T00:00:00Z","source_end":"2024-12-31T23:59:59Z",**flags}
    if extra: r.update(extra)
    wj(OUT/"source_gate_result.json",r); print(json.dumps(r,indent=2,sort_keys=True)); raise SystemExit(code)

params={"start":START,"timespan":TIMESPAN,"format":"json","sampled":"false"}
url=ENDPOINT+"?"+urllib.parse.urlencode(params)
wj(OUT/"request_contract.json",{"url":url,"metric":"n-transactions","expected_name":"Confirmed Transactions Per Day","expected_unit":"Transactions","expected_period":"day",**flags})
req=urllib.request.Request(url,headers={"Accept":"application/json","User-Agent":"crypto-lab-source-gate/1.0"})
try:
    with urllib.request.urlopen(req,timeout=60) as resp:
        raw=resp.read(); headers=dict(resp.headers.items()); http_status=resp.status
except urllib.error.HTTPError as e:
    raw=e.read(); (OUT/"http_error.bin").write_bytes(raw)
    status="SOURCE_AUTH_BLOCKED" if e.code in (401,402,403) else "TECHNICAL_FAILURE"
    fail(status,f"HTTP {e.code} from Blockchain.com Charts API",{"http_status":e.code,"error_body_sha256":sha(raw)},2 if status=="SOURCE_AUTH_BLOCKED" else 6)
except Exception as e: fail("TECHNICAL_FAILURE",f"Transport failure: {type(e).__name__}: {e}",code=6)
(OUT/"raw_n_transactions.json").write_bytes(raw); wj(OUT/"response_headers.json",headers); raw_sha=sha(raw)
try: payload=json.loads(raw)
except Exception as e: fail("DATA_FAILURE",f"Invalid JSON response: {e}",{"raw_sha256":raw_sha},3)
if not isinstance(payload,dict): fail("DATA_FAILURE","Top-level response is not an object",{"raw_sha256":raw_sha},3)
expected={"name":"Confirmed Transactions Per Day","unit":"Transactions","period":"day"}
semantics={k:payload.get(k) for k in expected}
if semantics!=expected: fail("PROVENANCE_FAILURE","Unexpected chart semantics",{"semantics":semantics,"expected":expected,"raw_sha256":raw_sha},5)
values=payload.get("values")
if not isinstance(values,list): fail("DATA_FAILURE","Response missing values[]",{"raw_sha256":raw_sha},3)
seen={}; duplicates=[]; years=set(); invalid=negative=0; first_ts=last_ts=None
for i,row in enumerate(values):
    if not isinstance(row,dict) or set(row.keys())!={"x","y"}: fail("PROVENANCE_FAILURE",f"Unexpected values[] schema at row {i}",{"keys":sorted(row.keys()) if isinstance(row,dict) else None},5)
    try: x=int(row["x"]); y=float(row["y"]); dt=datetime.fromtimestamp(x,tz=timezone.utc)
    except Exception: invalid+=1; continue
    if dt.year>=2025:
        flags["access_2025"]=dt.year==2025; flags["access_2026"]=dt.year>=2026
        fail("PROVENANCE_FAILURE","Protected-period observation returned",{"first_protected_timestamp":dt.isoformat()},5)
    if dt<WINDOW_START or dt>WINDOW_END: fail("PROVENANCE_FAILURE","Observation outside frozen window",{"timestamp":dt.isoformat()},5)
    if not math.isfinite(y): invalid+=1; continue
    if y<0: negative+=1
    dk=dt.date().isoformat(); duplicates.append(dk) if dk in seen else None; seen[dk]=seen.get(dk,0)+1; years.add(dt.year)
    first_ts=dt.isoformat().replace("+00:00","Z") if first_ts is None else first_ts
    last_ts=dt.isoformat().replace("+00:00","Z")
unique=len(seen); expected_days=(WINDOW_END.date()-WINDOW_START.date()).days+1; missing_dates=expected_days-unique
manifest={"family_id":FAMILY_ID,"source_gate_id":SOURCE_GATE_ID,"raw_sha256":raw_sha,"raw_bytes":len(raw),"http_status":http_status,"row_count":len(values),"unique_days":unique,"duplicate_dates_count":len(duplicates),"duplicate_dates":sorted(set(duplicates))[:100],"invalid_rows":invalid,"negative_values":negative,"distinct_years":sorted(years),"distinct_year_count":len(years),"first_timestamp":first_ts,"last_timestamp":last_ts,"expected_calendar_days":expected_days,"missing_dates_count":missing_dates,"semantics":semantics,**flags}
wj(OUT/"source_manifest.json",manifest); manifest_sha=sha((OUT/"source_manifest.json").read_bytes())
if duplicates or invalid or negative: fail("DATA_FAILURE","Duplicate/invalid/negative source observations",{**manifest,"source_manifest_sha256":manifest_sha},3)
if unique<MIN_UNIQUE_DAYS or len(years)<MIN_YEARS: fail("INSUFFICIENT_SAMPLE","Frozen minimum sample not met",{**manifest,"source_manifest_sha256":manifest_sha},4)
result={"family_id":FAMILY_ID,"source_gate_id":SOURCE_GATE_ID,"phase":"SOURCE_DATA_GATE_ONLY","status":"SOURCE_DATA_PASS","reason":"Confirmed Bitcoin transaction-count source passed provenance and sample gates","authority_commit":AUTHORITY_COMMIT,"drive_authority_id":DRIVE_AUTHORITY_ID,"endpoint":ENDPOINT,"metric":"n-transactions","source_start":"2017-01-01T00:00:00Z","source_end":"2024-12-31T23:59:59Z","row_count":len(values),"unique_days":unique,"distinct_year_count":len(years),"distinct_years":sorted(years),"first_timestamp":first_ts,"last_timestamp":last_ts,"missing_dates_count":missing_dates,"raw_sha256":raw_sha,"source_manifest_sha256":manifest_sha,**flags}
wj(OUT/"source_gate_result.json",result); print(json.dumps(result,indent=2,sort_keys=True))
