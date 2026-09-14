#!/usr/bin/env python3
"""Outcome-blind source/data gate for ETH-STAKING-FLOW-001."""
from __future__ import annotations
import csv, gzip, hashlib, json, os, pathlib, sys, time
from datetime import date, datetime, timedelta, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

OUT=pathlib.Path(os.environ.get("ESF_OUT","artifacts/eth_staking_flow_source_gate"))
RAW=OUT/"raw"
OUT.mkdir(parents=True,exist_ok=True); RAW.mkdir(parents=True,exist_ok=True)
GENESIS=1606824023
BASE="https://ethereum-beacon-api.publicnode.com"
START=date(2023,4,12); END=date(2024,12,31)
RUN_ID=os.environ.get("GITHUB_RUN_ID","LOCAL-"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))

def get(url, timeout=45):
    req=Request(url,headers={"User-Agent":"ETH-STAKING-FLOW-001-source-gate/0.1","Accept":"application/json"})
    try:
        with urlopen(req,timeout=timeout) as r:
            return r.status,dict(r.headers),r.read()
    except HTTPError as e:
        return e.code,dict(e.headers),e.read()
    except (URLError,TimeoutError,OSError) as e:
        return 0,{},str(e).encode()

def slot_for_day(d):
    ts=int(datetime(d.year,d.month,d.day,tzinfo=timezone.utc).timestamp())
    return (ts-GENESIS)//12

def sha(b): return hashlib.sha256(b).hexdigest()

manifest={"family_id":"ETH-STAKING-FLOW-001","mve_id":"ESF-NETQUEUE-7D-001","run_id":RUN_ID,
"generated_at_utc":datetime.now(timezone.utc).isoformat(),"source_base":BASE,
"requested_start":START.isoformat(),"requested_end":END.isoformat(),
"2025_accessed":False,"2026_accessed":False,"price_values_opened":False,
"returns_computed":False,"pnl_computed":False,"performance_statistics_computed":False,
"requests":[],"documentation_findings":{
"beaconchain_v1_queue_semantics":"current-only; no historical state parameter documented",
"beaconchain_v2_queue_auth":"Bearer token required; current network queue only",
"beacon_standard_route":"historical state_id plus validator status filter"}}

# Small explicit auth/provenance probes; response bytes retained.
probe_urls=[
("beaconchain_v1_current_no_key","https://beaconcha.in/api/v1/validators/queue?apikey="),
("beacon_standard_start_pending",f"{BASE}/eth/v1/beacon/states/{slot_for_day(START)}/validators?status=pending_queued"),
("beacon_standard_start_exiting",f"{BASE}/eth/v1/beacon/states/{slot_for_day(START)}/validators?status=active_exiting"),
("beacon_standard_end_pending",f"{BASE}/eth/v1/beacon/states/{slot_for_day(END)}/validators?status=pending_queued"),
("beacon_standard_end_exiting",f"{BASE}/eth/v1/beacon/states/{slot_for_day(END)}/validators?status=active_exiting")]
probe={}
for name,url in probe_urls:
    status,headers,body=get(url)
    p=RAW/(name+".json")
    p.write_bytes(body)
    probe[name]={"http_status":status,"bytes":len(body),"sha256":sha(body),"content_type":headers.get("Content-Type"),"url":url}
    manifest["requests"].append(probe[name])

archive_ok=all(probe[k]["http_status"]==200 for k in probe if k.startswith("beacon_standard_"))
rows=[]; terminal=None; blocker=None
if not archive_ok:
    statuses=[probe[k]["http_status"] for k in probe if k.startswith("beacon_standard_")]
    if any(s in (401,403) for s in statuses):
        terminal="SOURCE_AUTH_BLOCKED"; blocker="Historical Beacon state access requires authorization/paid archive access."
    elif all(s in (404,410) for s in statuses):
        terminal="PROVENANCE_FAILURE"; blocker="Public endpoint does not retain the required historical consensus states."
    elif any(s==0 or s>=500 for s in statuses):
        terminal="SOURCE_ACQUISITION_TECHNICAL_FAILURE"; blocker="Historical source could not be reached reliably."
    else:
        terminal="DATA_FAILURE"; blocker=f"Historical endpoint probe failed with statuses {statuses}."
else:
    d=START
    while d<=END:
        target=slot_for_day(d); selected=None; counts={}
        for offset in range(33):
            candidate=target+offset
            day_ok=True; local={}
            for status_name in ("pending_queued","active_exiting"):
                url=f"{BASE}/eth/v1/beacon/states/{candidate}/validators?status={status_name}"
                code,headers,body=get(url)
                rec={"date":d.isoformat(),"target_slot":target,"slot":candidate,"offset":offset,"status_filter":status_name,
                     "http_status":code,"bytes":len(body),"sha256":sha(body),"url":url}
                manifest["requests"].append(rec)
                if code!=200:
                    day_ok=False; break
                try:
                    obj=json.loads(body); local[status_name]=len(obj["data"])
                except Exception:
                    day_ok=False; break
                rawp=RAW/f"{d.isoformat()}_{candidate}_{status_name}.json.gz"
                with gzip.open(rawp,"wb") as f: f.write(body)
            if day_ok:
                selected=candidate; counts=local; break
        if selected is None:
            rows.append({"date":d.isoformat(),"target_slot":target,"selected_slot":"","slot_offset":"","pending_queued":"","active_exiting":"","net_queue_count":"","missing":1})
        else:
            rows.append({"date":d.isoformat(),"target_slot":target,"selected_slot":selected,"slot_offset":selected-target,
                         "pending_queued":counts["pending_queued"],"active_exiting":counts["active_exiting"],
                         "net_queue_count":counts["pending_queued"]-counts["active_exiting"],"missing":0})
        d+=timedelta(days=1)
        time.sleep(0.03)
    with (OUT/"daily_queue_counts.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
    missing=sum(int(r["missing"]) for r in rows)
    dates=[r["date"] for r in rows]
    duplicates=len(dates)-len(set(dates))
    if len(rows)<400: terminal="INSUFFICIENT_SAMPLE"; blocker=f"Only {len(rows)} requested daily observations."
    elif missing: terminal="DATA_FAILURE"; blocker=f"{missing} daily historical states missing."
    elif duplicates: terminal="DATA_FAILURE"; blocker=f"{duplicates} duplicate dates."
    else: terminal="SOURCE_DATA_PASS"; blocker=None

manifest["coverage"]={"requested_days":(END-START).days+1,"materialized_rows":len(rows),
"missing_days":sum(int(r["missing"]) for r in rows) if rows else None,
"duplicate_dates":len(rows)-len({r["date"] for r in rows}) if rows else None,
"timezone":"UTC","daily_target":"00:00:00 UTC","slot_fallback":"first canonical state within +32 slots"}
manifest["classification"]=terminal; manifest["blocker"]=blocker
(OUT/"source_manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True),encoding="utf-8")
files=[]
for p in sorted(OUT.rglob("*")):
    if p.is_file(): files.append({"path":str(p.relative_to(OUT)),"bytes":p.stat().st_size,"sha256":sha(p.read_bytes())})
receipt={"run_id":RUN_ID,"family_id":"ETH-STAKING-FLOW-001","mve_id":"ESF-NETQUEUE-7D-001",
"classification":terminal,"blocker":blocker,"coverage":manifest["coverage"],"files":files,
"2025_accessed":False,"2026_accessed":False,"price_values_opened":False,"returns_computed":False,
"pnl_computed":False,"performance_statistics_computed":False}
(OUT/"closeout_receipt.json").write_text(json.dumps(receipt,indent=2,sort_keys=True),encoding="utf-8")
print(json.dumps(receipt,indent=2))
sys.exit(0)
