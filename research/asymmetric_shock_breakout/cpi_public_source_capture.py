#!/usr/bin/env python3
"""Future CPI public-only book collector. Do not open economic outcomes."""
import argparse
import datetime as dt
import hashlib
import json
import time
from pathlib import Path
from public_bbo_probe import SYMBOLS, check
from contract_meta_probe import public_get, HOST

START_MS=1791980940000  # 2026-10-14 12:29:00 UTC
T0_MS=1791981000000     # 2026-10-14 12:30:00 UTC
INTERVAL_MS=5000
SLOTS=49
MAX_DRIFT_MS=2000
MAX_GAP_MS=10000

def canonical(obj):
    return json.dumps(obj,sort_keys=True,separators=(",",":"),allow_nan=False).encode()

def summarize(records,clock_ok):
    output={"status":"SOURCE_COVERAGE_BLOCKED","expected_per_symbol":SLOTS,"symbols":{}}
    for symbol in SYMBOLS:
        rows=[r for r in records if r["symbol"]==symbol]
        valid=[r for r in rows if r["status"]=="VALID"]
        version_ok=all(a["version"]<=b["version"] for a,b in zip(valid,valid[1:]))
        gaps=[b["slot_ms"]-a["slot_ms"] for a,b in zip(valid,valid[1:])]
        phases={("PRE" if r["slot_ms"]<T0_MS else "POST") for r in valid}
        distinct_slots=len({r["slot_index"] for r in rows})==len(rows)==SLOTS
        passed=(len(valid)>=47 and {"PRE","POST"}<=phases and version_ok
                and distinct_slots and (not gaps or max(gaps)<=MAX_GAP_MS))
        output["symbols"][symbol]={"valid":len(valid),"observed":len(rows),
                                  "versions_nondecreasing":version_ok,
                                  "max_valid_slot_gap_ms":max(gaps) if gaps else None,
                                  "pre_post_covered":len(phases)==2,
                                  "unique_complete_slots":distinct_slots,
                                  "source_pass":passed}
    if clock_ok and all(v["source_pass"] for v in output["symbols"].values()):
        output["status"]="SOURCE_ONLY_COVERAGE_PASS"
    if not clock_ok:output["status"]="BLOCKED_CLOCK"
    return output

def collect():
    now=int(time.time()*1000)
    header={"schema":"asym.cpi_public_bbo_source.v01",
            "schedule_utc":"2026-10-14T12:30:00Z",
            "start_ms":START_MS,"interval_ms":INTERVAL_MS,"slots":SLOTS,
            "trading_authority":"NONE","live_trading":False,
            "economic_outcomes_unlocked":False,"initiated_ms":now}
    if now>START_MS:
        return {**header,"state":"MISSED_PROSPECTIVE_SOURCE_WINDOW","records":[]}
    try:
        server_ts=public_get("/api/v1/contract/ping")
        drift=int(time.time()*1000)-server_ts
        clock_ok=abs(drift)<=MAX_DRIFT_MS
    except Exception as exc:
        return {**header,"state":"BLOCKED_CLOCK","reason":type(exc).__name__,"records":[]}
    if not clock_ok:
        return {**header,"state":"BLOCKED_CLOCK","clock_offset_ms":drift,"records":[]}
    records=[]
    for i in range(SLOTS):
        target=START_MS+i*INTERVAL_MS
        wait=(target-int(time.time()*1000))/1000
        if wait>0:time.sleep(wait)
        for symbol in SYMBOLS:
            request_ms=int(time.time()*1000)
            entry={"slot_index":i,"slot_ms":target,"symbol":symbol,
                   "request_timestamp_ms":request_ms,"status":"MISSING"}
            if request_ms>target+INTERVAL_MS:
                entry["reason"]="LATE_SLOT_START"
                records.append(entry)
                continue
            try:
                obj=public_get("/api/v1/contract/depth/"+symbol,{"limit":10})
                # public_get returns only 'data', validation expects full envelope.
                observed_ms=int(time.time()*1000)
                details=check({"success":True,"code":0,"data":obj},observed_ms)
                entry.update({"status":"VALID","observed_timestamp_ms":observed_ms,
                    "raw_source_data":obj,
                    "source_data_sha256":hashlib.sha256(canonical(obj)).hexdigest(),
                    "version":details["version"],"source_timestamp_ms":details["exchange_timestamp_ms"],
                    "request_to_observation_ms":observed_ms-request_ms})
            except Exception as exc:
                entry["reason"]=type(exc).__name__+":"+str(exc)[:80]
            records.append(entry)
    verdict=summarize(records,True)
    return {**header,"state":verdict["status"],"clock_offset_ms":drift,
            "source_adjudication":verdict,"records":records,
            "completed_ms":int(time.time()*1000)}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True)
    a=p.parse_args()
    result=collect()
    path=Path(a.out)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n")
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    # PRICE DATA SEALED: print only source counts and outcome-blind status.
    print(json.dumps({"state":result["state"],"sha256":digest,
        "symbols":result.get("source_adjudication",{}).get("symbols",{}),
        "trading_authority":"NONE","economic_outcomes_unlocked":False},sort_keys=True))

if __name__=="__main__":main()
