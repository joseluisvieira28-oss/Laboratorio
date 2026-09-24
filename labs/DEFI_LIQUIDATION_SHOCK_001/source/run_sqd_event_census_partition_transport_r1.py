#!/usr/bin/env python3
import argparse
import datetime as dt
import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

RUNNER=Path("labs/DEFI_LIQUIDATION_SHOCK_001/source/run_sqd_event_census_partition_v0_4_2.py")

def jread(p):
    return json.loads(Path(p).read_text())

def sha256_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

ap=argparse.ArgumentParser()
ap.add_argument("--protocol",choices=["kamino","save11"],required=True)
ap.add_argument("--start",required=True)
ap.add_argument("--end",required=True)
ap.add_argument("--out",required=True)
ap.add_argument("--max-empty200-retries",type=int,default=8)
args=ap.parse_args()

out=Path(args.out)
out.mkdir(parents=True,exist_ok=True)
tmp=out/"_transport_r1_tmp"
if tmp.exists():
    shutil.rmtree(tmp)
tmp.mkdir(parents=True)

start=dt.date.fromisoformat(args.start)
end=dt.date.fromisoformat(args.end)
chunks=[]
partition_class="PARTITION_COMPLETE"

cur=start
while cur<end:
    nxt=cur+dt.timedelta(days=1)
    day=cur.isoformat()
    day_out=tmp/day
    final_receipt=out/f"{day}.json"
    passed=False
    last_detail=None

    for attempt in range(1,args.max_empty200_retries+1):
        if day_out.exists():
            shutil.rmtree(day_out)
        cmd=[
            sys.executable,str(RUNNER),
            "--protocol",args.protocol,
            "--start",day,
            "--end",nxt.isoformat(),
            "--out",str(day_out),
        ]
        rc=subprocess.call(cmd)
        mp=day_out/"MANIFEST.json"
        manifest=jread(mp) if mp.exists() else {}
        receipts=[p for p in day_out.glob("*.json") if p.name!="MANIFEST.json"]
        receipt=jread(receipts[0]) if receipts else {}
        cls=manifest.get("classification")
        detail=receipt.get("detail")
        last_detail=detail

        if rc==0 and cls=="PARTITION_COMPLETE":
            shutil.copy2(receipts[0],final_receipt)
            ch=(manifest.get("chunks") or [])[0]
            chunks.append({
                "day":day,
                "file":final_receipt.name,
                "classification":ch.get("classification"),
                "sha256":sha256_file(final_receipt),
                "successful_instruction_count":ch.get("successful_instruction_count",0),
                "failed_attempt_count":ch.get("failed_attempt_count",0),
                "anomaly_count":ch.get("anomaly_count",0),
                "transport_r1_attempt":attempt,
            })
            passed=True
            break

        if detail!="empty_200_response":
            if receipts:
                shutil.copy2(receipts[0],final_receipt)
            partition_class="PARTITION_BLOCKED_FAIL_CLOSED"
            break

        if attempt<args.max_empty200_retries:
            time.sleep(min(60,2**(attempt-1)))

    if not passed:
        if not final_receipt.exists():
            final_receipt.write_text(json.dumps({
                "schema_version":"0.4.2-transport-r1",
                "protocol":args.protocol,
                "day_start":day+"T00:00:00Z",
                "day_end":nxt.isoformat()+"T00:00:00Z",
                "classification":"SOURCE_CHUNK_BLOCKED",
                "stream_complete":False,
                "error":"TransportRetryExhausted",
                "detail":last_detail or "transport_wrapper_unknown_failure",
            },indent=2,sort_keys=True)+"\n")
        chunks.append({
            "day":day,
            "file":final_receipt.name,
            "classification":"SOURCE_CHUNK_BLOCKED",
            "sha256":sha256_file(final_receipt),
            "successful_instruction_count":0,
            "failed_attempt_count":0,
            "anomaly_count":0,
        })
        partition_class="PARTITION_BLOCKED_FAIL_CLOSED"
        break

    cur=nxt

manifest={
    "schema_version":"0.4.2-transport-r1",
    "protocol":args.protocol,
    "requested_start":args.start,
    "requested_end":args.end,
    "classification":partition_class,
    "chunks":chunks,
    "chunk_count":len(chunks),
    "successful_instruction_count":sum(x.get("successful_instruction_count",0) for x in chunks),
    "failed_attempt_count":sum(x.get("failed_attempt_count",0) for x in chunks),
    "anomaly_count":sum(x.get("anomaly_count",0) for x in chunks),
    "transport_hardening":{
        "scope":"transport_only",
        "frozen_runner":str(RUNNER),
        "retry_only_detail":"empty_200_response",
        "max_retries":args.max_empty200_retries,
        "scientific_population_changed":False,
        "decoder_changed":False,
        "success_semantics_changed":False,
        "utc_membership_changed":False,
        "slot_envelope_changed":False,
    },
    "firewall":{
        "prices":False,"returns":False,"pnl":False,"direction":False,
        "economic_outcomes":False,"protected_market_outcomes_2025_2026":False,
        "live_trading":False,"orders":False,"wallets":False,
        "exchange_mutation":False,"paid_source":False,"account_creation":False,
        "merge_main":False,
    },
}
(out/"MANIFEST.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
if tmp.exists():
    shutil.rmtree(tmp)
print(json.dumps({
    "protocol":args.protocol,
    "classification":partition_class,
    "chunk_count":len(chunks),
    "successful_instruction_count":manifest["successful_instruction_count"],
    "failed_attempt_count":manifest["failed_attempt_count"],
    "anomaly_count":manifest["anomaly_count"],
},indent=2))
if partition_class!="PARTITION_COMPLETE":
    raise SystemExit(2)
