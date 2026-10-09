#!/usr/bin/env python3
"""Read-only preflight of last authoritative XALT-004 durable artifact.
Strictly checks past source status and frozen future-boundary restart behavior.
Does not issue market queries, simulate fills, or trade.
"""
import argparse,hashlib,json,sys
from datetime import datetime,timezone
from pathlib import Path

EXPECTED_RUN=37733563875
EXPECTED_ARTIFACT_ID=11548718087
EXPECTED_ZIP_SHA="16debf506b5f2f090ab0eefd19529fcf82547cb36e9ff4d6973c2956582ae93d"
EXPECTED_COMPLETE=4
EXPECTED_PENDING_EXIT=2
HORIZON_MS=3_600_000
DELAY_MS=60_000
FEE_BPS=16.0
SOURCE_FREEZE=Path("research/liquidation_cascade/LICP_FWD_XALT_004_PRE_OUTCOME_FREEZE_V0_1.md")
SOURCE_TRIGGER=Path("research/liquidation_cascade/LICP_001_TRIGGER_CONFIG_V0_1.json")

class Blocked(ValueError):pass

def check_state(data,now_ms):
    if data.get("schema")!="licp_fwd_xalt_004.state.v1" or not isinstance(data.get("records"),list):
        raise Blocked("STATE_SCHEMA_MISMATCH")
    records=data["records"]
    ids=[v.get("episode_id") for v in records]
    if any(not x for x in ids) or len(ids)!=len(set(ids)):
        raise Blocked("DUPLICATE_EPISODE_ID")
    complete=[];pending=[]
    for r in records:
        if r.get("pressure")!="SELL" or "entry_due_wall_ms" not in r or "event_wall_ms" not in r:
            raise Blocked("EPISODE_SCIENCE_IDENTITY")
        if int(r["entry_due_wall_ms"])-int(r["event_wall_ms"])!=DELAY_MS:
            raise Blocked("ENTRY_DELAY_MUTATED")
        entry,exit=r.get("entry"),r.get("exit")
        if entry and exit:
            if "net_taker_bps" not in r or "gross_bps" not in r:
                raise Blocked("COMPLETED_METRICS_MISSING")
            if abs((float(r["gross_bps"])-float(r["net_taker_bps"]))-FEE_BPS)>1e-6:
                raise Blocked("FROZEN_FEE_MISMATCH")
            if int(exit["wall_ms"])-int(entry["wall_ms"])<HORIZON_MS:
                raise Blocked("EXIT_BEFORE_HORIZON")
            complete.append(r)
        elif entry and not exit:
            due=int(entry["wall_ms"])+HORIZON_MS
            if due>=now_ms:
                raise Blocked("OUTSTANDING_EXIT_NOT_YET_DUE")
            pending.append(r)
        else:
            raise Blocked("UNEXPECTED_EPISODE_STATE")
    if len(complete)!=EXPECTED_COMPLETE or len(pending)!=EXPECTED_PENDING_EXIT:
        raise Blocked("BASELINE_COUNTS_CHANGED")
    # This is source status only, never fabricate or compute pending exits.
    return {"classification":"PRE_OBSERVATION_TRANSPORT_PASS",
        "scientific_state":"FORWARD_INSUFFICIENT",
        "reference_run_id":EXPECTED_RUN,"artifact_id":EXPECTED_ARTIFACT_ID,
        "state_sha256":hashlib.sha256(json.dumps(data,sort_keys=True,separators=(",",":")).encode()).hexdigest(),
        "completed":len(complete),"elapsed_exit_missing_on_restart":len(pending),
        "valid_primary_dates":len({datetime.fromtimestamp(int(x["event_wall_ms"])/1000,timezone.utc).date().isoformat() for x in complete}),
        "existing_outcome_marks_changed":False,"future_results_opened":False,
        "trading_authority":"NONE"}

def main():
    a=argparse.ArgumentParser();a.add_argument("--artifact-zip",required=True)
    a.add_argument("--state-json",required=True)
    a.add_argument("--receipt",required=True)
    opts=a.parse_args()
    if not SOURCE_FREEZE.exists() or "PRE-OUTCOME TRANSFER FREEZE" not in SOURCE_FREEZE.read_text():
        raise Blocked("FROZEN_XALT_AUTHORITY_MISSING")
    if json.loads(SOURCE_TRIGGER.read_text()).get("status")!="FROZEN":
        raise Blocked("TRIGGER_NOT_FROZEN")
    z=Path(opts.artifact_zip).read_bytes()
    if hashlib.sha256(z).hexdigest()!=EXPECTED_ZIP_SHA:
        raise Blocked("OFFICIAL_GITHUB_ARTIFACT_ZIP_SHA_MISMATCH")
    s=json.loads(Path(opts.state_json).read_text())
    status=check_state(s,int(datetime.now(timezone.utc).timestamp()*1000))
    p=Path(opts.receipt);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(status,sort_keys=True,indent=2)+"\n")
    print(json.dumps(status,sort_keys=True,indent=2))
if __name__=="__main__":
    try:main()
    except (Blocked,ValueError,KeyError,TypeError,OSError) as e:
        print("PRE_OBSERVATION_SOURCE_BLOCKED",str(e),file=sys.stderr)
        raise SystemExit(2)
