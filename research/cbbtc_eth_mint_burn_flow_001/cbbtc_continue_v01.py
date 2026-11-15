#!/usr/bin/env python3
from __future__ import annotations
import json, shutil, subprocess, sys
from pathlib import Path
from datetime import datetime, timezone

HERE=Path("research/cbbtc_eth_mint_burn_flow_001")
ART=Path("artifacts")
MAN=ART/"cbbtc_continuation_manifest_v01.json"

manifest={
  "lab_id":"CBBTC-ETH-MINT-BURN-FLOW-001",
  "stage":"CONTINUATION_ORCHESTRATOR_V0.1",
  "started_at_utc":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
  "classification":"RUNNING",
  "completed_stages":[],
  "market_returns_opened":False,
  "protected_2026_opened":False,
  "pnl_opened":False,
  "mutation":False,
  "promotion_credit":0
}

def save():
    MAN.parent.mkdir(parents=True,exist_ok=True)
    manifest["updated_at_utc"]=datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
    MAN.write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")

def load(p): return json.loads(Path(p).read_text())
def run(cmd):
    print("+"," ".join(cmd),flush=True)
    return subprocess.run(cmd,check=False).returncode
def cp(src,dst):
    src,dst=Path(src),Path(dst)
    if src.exists():
        dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(src,dst)
        return True
    return False
def stop(cls,code=0,blocker=None):
    manifest["classification"]=cls
    if blocker: manifest["blocker"]=blocker
    save()
    raise SystemExit(code)

save()

src=HERE/"SOURCE_GATE_RECEIPT_V0.1.json"
if not src.exists():
    stop("SOURCE_GATE_RECEIPT_MISSING",2)
sx=load(src)
if sx.get("classification")!="SOURCE_PASS":
    stop("SOURCE_NOT_PASS",2)
manifest["completed_stages"].append("SOURCE_PASS")
save()

# Gate 2 — exact outcome-blind census.
rc=run(["node",str(HERE/"cbbtc_eth_flow_census_v01.mjs")])
rec_art=ART/"census"/"CBBTC_ETH_FLOW_CENSUS_RECEIPT_V0.1.json"
led_art=ART/"census"/"CBBTC_ETH_FLOW_LEDGER_V0.1.json"
day_art=ART/"census"/"CBBTC_ETH_DAILY_FLOW_V0.1.json"
cp(rec_art,HERE/"FLOW_CENSUS_RECEIPT_V0.1.json")
cp(led_art,HERE/"FLOW_LEDGER_V0.1.json")
cp(day_art,HERE/"DAILY_FLOW_V0.1.json")
if not (HERE/"FLOW_CENSUS_RECEIPT_V0.1.json").exists():
    stop("PREDICTOR_FLOW_CENSUS_BLOCKED",2,"census_receipt_missing")
rec=load(HERE/"FLOW_CENSUS_RECEIPT_V0.1.json")
manifest["census_classification"]=rec.get("classification")
manifest["ledger_event_count"]=rec.get("ledger_event_count")
manifest["daily_row_count"]=rec.get("daily_row_count")
if rc!=0 or rec.get("classification")!="PREDICTOR_FLOW_CENSUS_PASS":
    stop("PREDICTOR_FLOW_CENSUS_BLOCKED",2)
manifest["completed_stages"].append("PREDICTOR_FLOW_CENSUS_PASS")
save()

# Gate 3 — q10/q90 calibration.
rc=run([sys.executable,str(HERE/"cbbtc_flow_state_calibration_v01.py")])
cal=HERE/"FLOW_STATE_CALIBRATION_RECEIPT_V0.1.json"
if rc!=0 or not cal.exists():
    stop("FLOW_STATE_CALIBRATION_BLOCKED",2)
cx=load(cal)
if cx.get("classification")!="FLOW_STATE_CALIBRATION_PASS":
    stop("FLOW_STATE_CALIBRATION_BLOCKED",2)
manifest["completed_stages"].append("FLOW_STATE_CALIBRATION_PASS")
manifest["q10"]=cx.get("quantile_rule",{}).get("q10")
manifest["q90"]=cx.get("quantile_rule",{}).get("q90")
save()

# Gate 4 — outcome-blind H2 sample.
rc=run([sys.executable,str(HERE/"cbbtc_discovery_flow_sample_gate_v01.py")])
sample=HERE/"DISCOVERY_FLOW_PREDICTOR_SAMPLE_RECEIPT_V0.1.json"
if not sample.exists():
    stop("FLOW_PREDICTOR_SOURCE_BLOCKED",2,"sample_receipt_missing")
sm=load(sample)
manifest["sample_classification"]=sm.get("classification")
manifest["transition_event_count"]=sm.get("transition_event_count")
manifest["negative_extreme_event_count"]=sm.get("negative_extreme_event_count")
manifest["positive_extreme_event_count"]=sm.get("positive_extreme_event_count")
if rc!=0 or sm.get("classification")=="FLOW_PREDICTOR_SOURCE_BLOCKED":
    stop("FLOW_PREDICTOR_SOURCE_BLOCKED",2)
manifest["completed_stages"].append(sm.get("classification"))
save()
if sm.get("classification")=="FLOW_PREDICTOR_INSUFFICIENT_SAMPLE":
    stop("FLOW_PREDICTOR_INSUFFICIENT_SAMPLE",0)
if sm.get("classification")!="FLOW_PREDICTOR_SAMPLE_PASS":
    stop("FLOW_PREDICTOR_GATE_UNKNOWN",2)

# Gate 5 — open only frozen H2-2025 BTC outcome.
manifest["market_returns_opened"]=True
save()
rc=run([sys.executable,str(HERE/"cbbtc_flow_discovery_v01.py")])
disc=HERE/"FLOW_DISCOVERY_RESULT_V0.1.json"
if rc!=0 or not disc.exists():
    stop("FLOW_DISCOVERY_BLOCKED",2)
dx=load(disc)
manifest["discovery_classification"]=dx.get("classification")
manifest["completed_stages"].append(dx.get("classification"))
stop(dx.get("classification","FLOW_DISCOVERY_UNKNOWN"),0)
