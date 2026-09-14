#!/usr/bin/env python3
"""BTC-FEE-PRESSURE-001 V0.2 chunked source-remediation gate. No outcomes."""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, os, pathlib, struct, sys, time
import urllib.error, urllib.request
from collections import defaultdict

LAB="BTC-FEE-PRESSURE-001"
GATE="BFP-SOURCE-REMEDIATION-V0.2-CHUNKED"
PRIMARY="https://mempool.space"
AUDIT="https://blockstream.info"
GLOBAL_START=1609459200
GLOBAL_END=1735689599
START_DAY=dt.date(2021,1,1)
END_DAY=dt.date(2024,12,31)
HEADERS={"Accept":"application/json","User-Agent":"Laboratorio-Research-SourceGate/0.2"}
FORBIDDEN=(b'"usd"',b'"price"',b'"market_price"')

def canonical_json(obj):
    return (json.dumps(obj,sort_keys=True,separators=(",",":"))+"\n").encode()

def sha256_file(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for part in iter(lambda:f.read(1024*1024),b""): h.update(part)
    return h.hexdigest()

def atomic_json(path,obj):
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_bytes(canonical_json(obj)); tmp.replace(path)

def get(url,retries=5):
    last=None
    for attempt in range(retries):
        try:
            req=urllib.request.Request(url,headers=HEADERS)
            with urllib.request.urlopen(req,timeout=45) as r:
                return r.status,dict(r.headers.items()),r.read()
        except urllib.error.HTTPError as e:
            body=e.read(); last=(e.code,dict(e.headers.items()),body)
            if e.code==429 or e.code>=500:
                time.sleep(min(16,2**attempt)); continue
            return last
        except Exception as e:
            last=e; time.sleep(min(16,2**attempt))
    raise RuntimeError(repr(last))

def safe_response(url):
    status,headers,body=get(url)
    if status in (401,403): raise PermissionError(f"http_{status}")
    if status!=200: raise RuntimeError(f"http_{status}:{url}:{body[:160]!r}")
    if any(x in body.lower() for x in FORBIDDEN):
        raise ValueError("forbidden_market_field")
    return status,headers,body

def height_at(ts):
    url=f"{PRIMARY}/api/v1/mining/blocks/timestamp/{ts}"
    status,headers,body=safe_response(url)
    obj=json.loads(body)
    if isinstance(obj,int): height=obj
    elif isinstance(obj,dict) and isinstance(obj.get("height"),int): height=obj["height"]
    else: raise ValueError(f"height_schema:{obj!r}")
    return height,url,status,headers,body

def append_frame(raw,meta,url,status,headers,body):
    with raw.open("ab") as f:
        ub=url.encode(); offset=f.tell()
        f.write(struct.pack(">II",len(ub),len(body))); f.write(ub); f.write(body)
        f.flush(); os.fsync(f.fileno())
    rec={"url":url,"status":status,"headers":headers,"offset":offset,
         "body_bytes":len(body),"body_sha256":hashlib.sha256(body).hexdigest()}
    with meta.open("ab") as f:
        f.write(canonical_json(rec)); f.flush(); os.fsync(f.fileno())

def classify_exception(exc):
    if isinstance(exc,PermissionError): return "SOURCE_AUTH_BLOCKED"
    if isinstance(exc,(urllib.error.URLError,TimeoutError,RuntimeError)): return "SOURCE_ACQUISITION_TECHNICAL_FAILURE"
    if isinstance(exc,ValueError) and str(exc)=="forbidden_market_field": return "PROVENANCE_FAILURE"
    return "DATA_FAILURE"

def acquire(args):
    out=pathlib.Path(args.out); out.mkdir(parents=True,exist_ok=True)
    start_ts=int(args.start_ts); end_ts=int(args.end_ts)
    if not(GLOBAL_START<=start_ts<=end_ts<=GLOBAL_END):
        raise SystemExit("FAIL_CLOSED_TIMESTAMP_BOUNDARY")
    identity={"chunk":args.chunk,"start_ts":start_ts,"end_ts":end_ts}
    identity_path=out/"chunk_identity.json"
    if identity_path.exists() and json.loads(identity_path.read_text())!=identity:
        raise SystemExit("FAIL_CLOSED_CHECKPOINT_IDENTITY")
    atomic_json(identity_path,identity)
    raw=out/"raw_responses.bin"; meta=out/"raw_index.jsonl"
    checkpoint_path=out/"checkpoint.json"; blocks_path=out/"blocks.jsonl"
    transport=[]; malformed=[]; status_name="IN_PROGRESS"; start_h=end_h=None
    request_count=0; resumed=False; deadline=time.monotonic()+int(args.max_seconds)
    seen={}
    if blocks_path.exists():
        for line in blocks_path.read_text().splitlines():
            if line:
                b=json.loads(line); seen[int(b["height"])]=b
    try:
        sh,surl,sstatus,sheaders,sbody=height_at(start_ts)
        eh,eurl,estatus,eheaders,ebody=height_at(end_ts)
        start_h,end_h=sh,eh
        if not(0<start_h<=end_h): raise ValueError("height_order")
        if not checkpoint_path.exists():
            append_frame(raw,meta,surl,sstatus,sheaders,sbody)
            append_frame(raw,meta,eurl,estatus,eheaders,ebody)
            next_height=end_h
        else:
            cp=json.loads(checkpoint_path.read_text())
            if cp.get("chunk")!=args.chunk or cp.get("start_height")!=start_h or cp.get("end_height")!=end_h:
                raise ValueError("checkpoint_boundary_mismatch")
            next_height=int(cp["next_height"]); resumed=True
        while next_height>=start_h:
            if time.monotonic()>=deadline:
                status_name="SOURCE_ACQUISITION_TECHNICAL_FAILURE"
                transport.append({"type":"internal_deadline","next_height":next_height})
                break
            url=f"{PRIMARY}/api/v1/blocks/{next_height}"
            rstatus,rheaders,body=safe_response(url); request_count+=1
            append_frame(raw,meta,url,rstatus,rheaders,body)
            arr=json.loads(body)
            if not isinstance(arr,list) or not arr: raise ValueError("blocks_schema")
            heights=[]
            new_rows=[]
            for item in arr:
                h=item.get("height"); block_hash=item.get("id"); stamp=item.get("timestamp")
                extras=item.get("extras")
                fees=extras.get("totalFees") if isinstance(extras,dict) else None
                if not isinstance(h,int) or not isinstance(block_hash,str) or len(block_hash)!=64:
                    malformed.append({"height":h,"reason":"identity"}); continue
                if not isinstance(stamp,int) or not isinstance(fees,int) or fees<0:
                    malformed.append({"height":h,"reason":"timestamp_or_totalFees"}); continue
                heights.append(h)
                if start_ts<=stamp<=end_ts:
                    row={"height":h,"id":block_hash,"timestamp":stamp,"totalFees_sats":fees}
                    old=seen.get(h)
                    if old and old!=row: raise ValueError("canonical_conflict")
                    if not old: seen[h]=row; new_rows.append(row)
            if not heights: raise ValueError("empty_height_page")
            if new_rows:
                with blocks_path.open("ab") as f:
                    for row in sorted(new_rows,key=lambda x:x["height"],reverse=True):
                        f.write(canonical_json(row))
                    f.flush(); os.fsync(f.fileno())
            candidate=min(heights)-1
            if candidate>=next_height: raise ValueError("pagination_no_progress")
            next_height=candidate
            atomic_json(checkpoint_path,{"chunk":args.chunk,"start_height":start_h,
                "end_height":end_h,"next_height":next_height,"blocks":len(seen),
                "request_count_this_attempt":request_count})
        else:
            status_name="COMPLETE"
        if malformed and status_name=="COMPLETE": status_name="DATA_FAILURE"
    except Exception as exc:
        status_name=classify_exception(exc)
        transport.append({"type":type(exc).__name__,"message":str(exc)})
    heights=sorted(seen)
    gaps=[h for a,b in zip(heights,heights[1:]) for h in range(a+1,b) if b>a+1]
    if gaps and status_name=="COMPLETE": status_name="PROVENANCE_FAILURE"
    manifest={"lab":LAB,"gate":GATE,"mode":"acquire","run_id":os.getenv("GITHUB_RUN_ID","local"),
      "run_attempt":os.getenv("GITHUB_RUN_ATTEMPT","local"),**identity,"status":status_name,
      "source":PRIMARY,"start_height":start_h,"end_height":end_h,"blocks":len(seen),
      "first_height":min(heights,default=None),"last_height":max(heights,default=None),
      "height_gap_count":len(gaps),"height_gap_sample":gaps[:100],
      "malformed_count":len(malformed),"malformed":malformed[:100],
      "transport_failures":transport,"requests_this_attempt":request_count,"resumed":resumed,
      "raw_sha256":sha256_file(raw) if raw.exists() else None,
      "raw_index_sha256":sha256_file(meta) if meta.exists() else None,
      "firewall":{"btc_price_values_opened":False,"eth_price_values_opened":False,
       "market_returns_computed":False,"pnl_computed":False,
       "performance_statistics_computed":False,"holdout_2025_accessed":False,
       "year_2026_accessed":False,"live_trading_authorized":False,
       "exchange_mutation_authorized":False,"discovery_authorized":False}}
    atomic_json(out/"chunk_manifest.json",manifest)
    print(json.dumps(manifest,sort_keys=True))
    return 0

def audit_block(out,row,label):
    h=row["height"]
    url1=f"{AUDIT}/api/block-height/{h}"
    s1,hd1,b1=safe_response(url1); append_frame(out/"raw_audit.bin",out/"audit_index.jsonl",url1,s1,hd1,b1)
    audit_hash=b1.decode().strip()
    if audit_hash!=row["id"]: raise ValueError(f"audit_hash_mismatch:{label}")
    url2=f"{AUDIT}/api/block/{audit_hash}"
    s2,hd2,b2=safe_response(url2); append_frame(out/"raw_audit.bin",out/"audit_index.jsonl",url2,s2,hd2,b2)
    obj=json.loads(b2)
    if obj.get("id")!=row["id"] or obj.get("height")!=h or obj.get("timestamp")!=row["timestamp"]:
        raise ValueError(f"audit_metadata_mismatch:{label}")
    return {"label":label,"height":h,"hash":row["id"],"timestamp":row["timestamp"]}

def finalize(args):
    root=pathlib.Path(args.chunks); out=pathlib.Path(args.out); out.mkdir(parents=True,exist_ok=True)
    manifests=[]; rows=[]; transport=[]; verdict=None
    for p in sorted(root.rglob("chunk_manifest.json")):
        manifests.append(json.loads(p.read_text()))
        bp=p.parent/"blocks.jsonl"
        if bp.exists():
            rows.extend(json.loads(x) for x in bp.read_text().splitlines() if x)
    expected=int(args.expected_chunks)
    statuses=[m.get("status") for m in manifests]
    if len(manifests)!=expected:
        verdict="SOURCE_ACQUISITION_TECHNICAL_FAILURE"
        transport.append({"type":"missing_chunk_manifests","expected":expected,"actual":len(manifests)})
    elif any(s=="SOURCE_AUTH_BLOCKED" for s in statuses): verdict="SOURCE_AUTH_BLOCKED"
    elif any(s=="PROVENANCE_FAILURE" for s in statuses): verdict="PROVENANCE_FAILURE"
    elif any(s=="DATA_FAILURE" for s in statuses): verdict="DATA_FAILURE"
    elif any(s!="COMPLETE" for s in statuses): verdict="SOURCE_ACQUISITION_TECHNICAL_FAILURE"
    by_height={}; duplicate_count=0; conflicts=[]
    for row in rows:
        h=int(row["height"])
        if h in by_height:
            duplicate_count+=1
            if by_height[h]!=row: conflicts.append(h)
        else: by_height[h]=row
    ordered=[by_height[h] for h in sorted(by_height)]
    gaps=[h for a,b in zip(sorted(by_height),sorted(by_height)[1:]) for h in range(a+1,b) if b>a+1]
    daily=defaultdict(int); malformed=[]
    for row in ordered:
        try:
            stamp=int(row["timestamp"])
            if not(GLOBAL_START<=stamp<=GLOBAL_END): raise ValueError("protected_or_outside_timestamp")
            day=dt.datetime.fromtimestamp(stamp,tz=dt.timezone.utc).date()
            fees=row["totalFees_sats"]
            if not isinstance(fees,int) or fees<0: raise ValueError("fees")
            daily[day.isoformat()]+=fees
        except Exception as exc: malformed.append({"height":row.get("height"),"reason":str(exc)})
    all_days=[]; d=START_DAY
    while d<=END_DAY: all_days.append(d.isoformat()); d+=dt.timedelta(days=1)
    missing_days=[d for d in all_days if d not in daily]
    audits=[]
    if verdict is None:
        if conflicts or gaps: verdict="PROVENANCE_FAILURE"
        elif malformed: verdict="DATA_FAILURE"
        elif len(daily)<1400: verdict="INSUFFICIENT_SAMPLE"
        elif missing_days or len(daily)!=1461: verdict="PROVENANCE_FAILURE"
        else:
            try:
                samples=[ordered[0],ordered[len(ordered)//2],ordered[-1]]
                audits=[audit_block(out,row,label) for row,label in zip(samples,("first","middle","last"))]
            except Exception as exc:
                verdict=classify_exception(exc)
                transport.append({"type":type(exc).__name__,"message":str(exc),"route":AUDIT})
    if verdict is None: verdict="SOURCE_DATA_PASS"
    csv=out/"daily_total_fees.csv"
    with csv.open("w",encoding="utf-8",newline="") as f:
        f.write("utc_date,total_fees_sats,total_fees_btc\n")
        for day in sorted(daily):
            sats=daily[day]; f.write(f"{day},{sats},{sats/100000000:.8f}\n")
    manifest={"lab":LAB,"gate":GATE,"mode":"finalize","run_id":os.getenv("GITHUB_RUN_ID","local"),
      "verdict":verdict,"primary_source":PRIMARY,"audit_source":AUDIT,
      "window_start":"2021-01-01T00:00:00Z","window_end":"2024-12-31T23:59:59Z",
      "expected_chunks":expected,"received_chunks":len(manifests),"chunk_statuses":statuses,
      "total_blocks":len(ordered),"duplicate_rows":duplicate_count,
      "canonical_conflicts":len(conflicts),"missing_height_count":len(gaps),
      "missing_height_sample":gaps[:100],"malformed_count":len(malformed),
      "daily_observations":len(daily),"first_day":min(daily,default=None),
      "last_day":max(daily,default=None),"missing_day_count":len(missing_days),
      "missing_days":missing_days,"audit_samples":audits,"transport_failures":transport,
      "daily_csv_sha256":sha256_file(csv),
      "firewall":{"btc_price_values_opened":False,"eth_price_values_opened":False,
       "market_returns_computed":False,"pnl_computed":False,
       "performance_statistics_computed":False,"holdout_2025_accessed":False,
       "year_2026_accessed":False,"live_trading_authorized":False,
       "exchange_mutation_authorized":False,"discovery_authorized":False}}
    mb=json.dumps(manifest,sort_keys=True,indent=2).encode()+b"\n"
    (out/"manifest.json").write_bytes(mb)
    (out/"manifest.sha256").write_text(hashlib.sha256(mb).hexdigest()+"  manifest.json\n")
    (out/"verdict.txt").write_text(verdict+"\n")
    atomic_json(out/"chunk_manifests.json",manifests)
    print(json.dumps(manifest,sort_keys=True))
    print("MANIFEST_SHA256",hashlib.sha256(mb).hexdigest())
    return 0

def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest="mode",required=True)
    ac=sub.add_parser("acquire"); ac.add_argument("--chunk",required=True)
    ac.add_argument("--start-ts",required=True); ac.add_argument("--end-ts",required=True)
    ac.add_argument("--out",required=True); ac.add_argument("--max-seconds",default="5400")
    fn=sub.add_parser("finalize"); fn.add_argument("--chunks",required=True)
    fn.add_argument("--out",required=True); fn.add_argument("--expected-chunks",default="16")
    args=ap.parse_args()
    return acquire(args) if args.mode=="acquire" else finalize(args)
if __name__=="__main__": sys.exit(main())
