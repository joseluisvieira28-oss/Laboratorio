#!/usr/bin/env python3
"""BTC-FEE-PRESSURE-001 V0.2 source-remediation gate. No market outcomes."""
from __future__ import annotations
import concurrent.futures, datetime as dt, hashlib, json, math, os, pathlib, struct, sys, time, urllib.error, urllib.request

LAB="BTC-FEE-PRESSURE-001"; GATE="BFP-SOURCE-REMEDIATION-V0.2"
BASE="https://mempool.space"
START_TS=1609459200
END_TS=1735689599
START_DAY=dt.date(2021,1,1); END_DAY=dt.date(2024,12,31)
OUT=pathlib.Path(os.environ.get("BFP_OUT","btc_fee_pressure_source_remediation_artifact"))
OUT.mkdir(parents=True,exist_ok=True)
HEADERS={"Accept":"application/json","User-Agent":"Laboratorio-Research-SourceGate/0.2"}
transport=[]; raw_index=[]

def get(url, retries=4):
    last=None
    for attempt in range(retries):
        try:
            req=urllib.request.Request(url,headers=HEADERS)
            with urllib.request.urlopen(req,timeout=45) as r:
                return r.status,dict(r.headers.items()),r.read()
        except urllib.error.HTTPError as e:
            body=e.read()
            if e.code==429 or e.code>=500:
                last=(e.code,dict(e.headers.items()),body)
                time.sleep(min(8,2**attempt))
                continue
            return e.code,dict(e.headers.items()),body
        except Exception as e:
            last=e; time.sleep(min(8,2**attempt))
    raise RuntimeError(repr(last))

def height_at(ts):
    status,headers,body=get(f"{BASE}/api/v1/mining/blocks/timestamp/{ts}")
    if status in (401,403): raise PermissionError(status)
    if status!=200: raise RuntimeError(f"height_http_{status}:{body[:200]!r}")
    obj=json.loads(body)
    if isinstance(obj,int): return obj,body,headers
    if isinstance(obj,dict) and isinstance(obj.get("height"),int): return obj["height"],body,headers
    raise ValueError(f"height_schema:{obj!r}")

verdict=None; start_h=end_h=None; all_blocks={}
try:
    start_h,start_body,start_headers=height_at(START_TS)
    end_h,end_body,end_headers=height_at(END_TS)
    if not(0<start_h<=end_h):
        raise ValueError("height_order")
    bounds=(OUT/"raw_boundaries.bin")
    with bounds.open("wb") as f:
        for url,body in [(f"{BASE}/api/v1/mining/blocks/timestamp/{START_TS}",start_body),(f"{BASE}/api/v1/mining/blocks/timestamp/{END_TS}",end_body)]:
            ub=url.encode(); f.write(struct.pack(">II",len(ub),len(body))); f.write(ub); f.write(body)
            raw_index.append({"url":url,"container":"raw_boundaries.bin","body_bytes":len(body),"sha256":hashlib.sha256(body).hexdigest()})
    probe_heights=[end_h,(start_h+end_h)//2,start_h]
    for h in probe_heights:
        url=f"{BASE}/api/v1/blocks/{h}"; status,headers,body=get(url)
        if status in (401,403): verdict="SOURCE_AUTH_BLOCKED"; break
        if status!=200: raise RuntimeError(f"probe_http_{status}")
        low=body.lower()
        if any(x in low for x in (b'"usd"',b'"price"',b'"market_price"')):
            verdict="PROVENANCE_FAILURE"; break
        arr=json.loads(body)
        if not isinstance(arr,list) or not arr: verdict="DATA_FAILURE"; break
        target=next((b for b in arr if b.get("height")==h),None)
        if not target or not isinstance(target.get("id"),str) or not isinstance(target.get("timestamp"),int):
            verdict="DATA_FAILURE"; break
        extras=target.get("extras")
        if not isinstance(extras,dict) or not isinstance(extras.get("totalFees"),(int,float)):
            verdict="DATA_FAILURE"; break
    if verdict is None:
        request_heights=list(range(end_h,start_h-1,-10))
        def fetch_batch(h):
            url=f"{BASE}/api/v1/blocks/{h}"
            status,headers,body=get(url)
            return h,url,status,headers,body
        results=[]
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
            for item in ex.map(fetch_batch,request_heights):
                results.append(item)
        raw_path=OUT/"raw_block_batches.bin"
        with raw_path.open("wb") as f:
            for h,url,status,headers,body in sorted(results,reverse=True):
                if status in (401,403): verdict="SOURCE_AUTH_BLOCKED"; break
                if status!=200:
                    transport.append({"height":h,"status":status}); verdict="SOURCE_ACQUISITION_TECHNICAL_FAILURE"; break
                if any(x in body.lower() for x in (b'"usd"',b'"price"',b'"market_price"')):
                    verdict="PROVENANCE_FAILURE"; break
                ub=url.encode(); offset=f.tell()
                f.write(struct.pack(">II",len(ub),len(body))); f.write(ub); f.write(body)
                raw_index.append({"url":url,"container":"raw_block_batches.bin","offset":offset,"body_bytes":len(body),"sha256":hashlib.sha256(body).hexdigest(),"status":status})
                arr=json.loads(body)
                if not isinstance(arr,list): verdict="DATA_FAILURE"; break
                for b in arr:
                    h2=b.get("height")
                    if isinstance(h2,int) and start_h<=h2<=end_h:
                        if h2 in all_blocks and all_blocks[h2].get("id")!=b.get("id"):
                            verdict="PROVENANCE_FAILURE"; break
                        all_blocks[h2]=b
                if verdict: break
except PermissionError:
    verdict="SOURCE_AUTH_BLOCKED"
except (urllib.error.URLError,TimeoutError,RuntimeError) as e:
    transport.append({"type":type(e).__name__,"message":str(e)}); verdict="SOURCE_ACQUISITION_TECHNICAL_FAILURE"
except Exception as e:
    transport.append({"type":type(e).__name__,"message":str(e)}); verdict="DATA_FAILURE"

missing_heights=[]; duplicates=[]; malformed=[]; outside=[]; daily={}
if start_h is not None and end_h is not None:
    missing_heights=[h for h in range(start_h,end_h+1) if h not in all_blocks]
for h,b in sorted(all_blocks.items()):
    try:
        if b.get("height")!=h or not isinstance(b.get("id"),str) or len(b["id"])!=64: raise ValueError("identity")
        stamp=dt.datetime.fromtimestamp(int(b["timestamp"]),tz=dt.timezone.utc)
        day=stamp.date()
        if not(START_DAY<=day<=END_DAY): outside.append({"height":h,"date":day.isoformat()}); continue
        extras=b.get("extras"); fees=float(extras["totalFees"])
        if not math.isfinite(fees) or fees<0: raise ValueError("fees")
        daily[day.isoformat()]=daily.get(day.isoformat(),0.0)+fees
    except Exception as e: malformed.append({"height":h,"reason":str(e)})
missing_days=[]; d=START_DAY
while d<=END_DAY:
    if d.isoformat() not in daily: missing_days.append(d.isoformat())
    d+=dt.timedelta(days=1)
if verdict is None:
    if outside or missing_heights: verdict="PROVENANCE_FAILURE"
    elif malformed: verdict="DATA_FAILURE"
    elif len(daily)<1400: verdict="INSUFFICIENT_SAMPLE"
    else: verdict="SOURCE_DATA_PASS"
for fn in ("raw_boundaries.bin","raw_block_batches.bin"):
    p=OUT/fn
    if p.exists(): raw_index.append({"container_file":fn,"bytes":p.stat().st_size,"sha256":hashlib.sha256(p.read_bytes()).hexdigest()})
manifest={"lab":LAB,"gate":GATE,"run_id":os.environ.get("GITHUB_RUN_ID","local"),"verdict":verdict,
"source":BASE,"start_timestamp":START_TS,"end_timestamp":END_TS,"start_height":start_h,"end_height":end_h,
"blocks":len(all_blocks),"missing_height_count":len(missing_heights),"missing_height_sample":missing_heights[:100],
"daily_observations":len(daily),"first_day":min(daily,default=None),"last_day":max(daily,default=None),
"missing_day_count":len(missing_days),"missing_days":missing_days,"malformed_count":len(malformed),
"malformed":malformed[:100],"outside_count":len(outside),"outside":outside[:100],"transport_failures":transport,
"raw_index":raw_index,"firewall":{"btc_price_values_opened":False,"eth_price_values_opened":False,
"returns_computed":False,"pnl_computed":False,"performance_statistics_computed":False,
"access_2025":False,"access_2026":False,"live_trading":False,"exchange_mutation":False,"discovery":False}}
mb=json.dumps(manifest,sort_keys=True,indent=2).encode()+b"\n"
(OUT/"manifest.json").write_bytes(mb)
(OUT/"manifest.sha256").write_text(hashlib.sha256(mb).hexdigest()+"  manifest.json\n")
(OUT/"verdict.txt").write_text(verdict+"\n")
print(json.dumps({k:manifest[k] for k in ("run_id","verdict","start_height","end_height","blocks","missing_height_count","daily_observations","first_day","last_day","missing_day_count","malformed_count","outside_count")},sort_keys=True))
print("MANIFEST_SHA256",hashlib.sha256(mb).hexdigest())
for x in raw_index:
    if "container_file" in x: print("RAW_CONTAINER",json.dumps(x,sort_keys=True))
sys.exit(0)
