#!/usr/bin/env python3
from __future__ import annotations
import json, shutil, subprocess, sys
from pathlib import Path
from datetime import datetime, timezone

HERE=Path("research/dual_lst_rv_001")
ART=Path("artifacts/dual_lst_rv_001")
MAN=ART/"DUAL_LST_CONTINUATION_MANIFEST_V0.1.json"
MAN.parent.mkdir(parents=True,exist_ok=True)

m={
 "lab_id":"DUAL-LST-RV-001",
 "stage":"SINGLE_RUN_CONTINUATION_V0.1",
 "started_at_utc":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
 "classification":"RUNNING","completed_stages":[],
 "future_returns_opened":False,"market_returns_opened":False,"pnl_opened":False,
 "oos_opened":False,"protected_holdout_opened":False,"mutation":False,"promotion_credit":0
}

def save():
 m["updated_at_utc"]=datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
 MAN.write_text(json.dumps(m,indent=2,sort_keys=True)+"\n")

def run(cmd):
 print("+"," ".join(cmd),flush=True)
 return subprocess.run(cmd,check=False).returncode

def load(p): return json.loads(Path(p).read_text())

def cp(src,dst):
 src,dst=Path(src),Path(dst)
 if src.exists():
  dst.parent.mkdir(parents=True,exist_ok=True)
  shutil.copyfile(src,dst); return True
 return False

def terminal(cls,code=0,blocker=None):
 m["classification"]=cls
 if blocker:m["blocker"]=blocker
 save()
 terminal_set={
  "SOURCE_BLOCKED","PREDICTOR_CENSUS_BLOCKED","PREDICTOR_STATE_CALIBRATION_BLOCKED",
  "DUAL_LST_PREDICTOR_SOURCE_BLOCKED","DUAL_LST_PREDICTOR_INSUFFICIENT_SAMPLE",
  "MECHANISM_DISCOVERY_SOURCE_BLOCKED","MECHANISM_DISCOVERY_INSUFFICIENT_SAMPLE",
  "MECHANISM_DISCOVERY_FAIL"
 }
 if cls in terminal_set:
  rec={
   "lab_id":"DUAL-LST-RV-001","stage":"CLOSEOUT_V0.1",
   "closed_at_utc":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
   "final_classification":cls,"terminal":True,
   "completed_stages":m.get("completed_stages",[]),
   "future_returns_opened":m.get("future_returns_opened",False),
   "market_returns_opened":False,"pnl_opened":False,
   "oos_opened":False,"protected_holdout_opened":False,
   "mutation":False,"promotion_credit":0,"rescue_allowed":False
  }
  (HERE/"CLOSEOUT_RECEIPT_V0.1.json").write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
  (HERE/"CLOSEOUT_V0.1.md").write_text(
   "# DUAL-LST-RV-001 — CLOSEOUT V0.1\n\n"
   f"Final classification: **{cls}**\n\n"
   "This classification is terminal for the exact frozen lab.\n"
   "No threshold, pool, horizon, tail, numeraire or synthetic-market rescue is authorized.\n"
   f"Future convergence outcomes opened: {str(m.get('future_returns_opened',False)).lower()}\n"
   "Market-return PnL, OOS and protected holdout remain closed.\n"
  )
 raise SystemExit(code)

save()

# Gate 1: authoritative source V0.1B
rc=run(["node",str(HERE/"dual_lst_source_probe_v01b.mjs")])
src_art=ART/"DUAL_LST_RV_001_SOURCE_GATE_RECEIPT_V0.1B.json"
src_dst=HERE/"DUAL_LST_RV_001_SOURCE_GATE_RECEIPT_V0.1B.json"
cp(src_art,src_dst)
if not src_dst.exists(): terminal("SOURCE_BLOCKED",2,"source_receipt_missing")
sx=load(src_dst)
m["source_classification"]=sx.get("classification")
if rc!=0 or sx.get("classification")!="SOURCE_PASS": terminal("SOURCE_BLOCKED",2)
m["completed_stages"].append("SOURCE_PASS_V0.1B");save()

# Gate 2: exact 556 predictor census
rc=run(["node",str(HERE/"dual_lst_predictor_census_v01.mjs")])
rec_art=ART/"census"/"DUAL_LST_PREDICTOR_CENSUS_RECEIPT_V0.1.json"
rows_art=ART/"census"/"DUAL_LST_PREDICTOR_CENSUS_ROWS_V0.1.json"
rec_dst=HERE/"DUAL_LST_PREDICTOR_CENSUS_RECEIPT_V0.1.json"
rows_dst=HERE/"DUAL_LST_PREDICTOR_CENSUS_ROWS_V0.1.json"
cp(rec_art,rec_dst);cp(rows_art,rows_dst)
if not rec_dst.exists() or not rows_dst.exists(): terminal("PREDICTOR_CENSUS_BLOCKED",2,"census_evidence_missing")
cx=load(rec_dst)
m["census_classification"]=cx.get("classification")
m["census_valid_count"]=cx.get("valid_count")
m["census_invalid_count"]=cx.get("invalid_count")
m["selected_pool"]=cx.get("selected_pool")
if rc!=0 or cx.get("classification")!="PREDICTOR_CENSUS_PASS": terminal("PREDICTOR_CENSUS_BLOCKED",2)
m["completed_stages"].append("PREDICTOR_CENSUS_PASS");save()

# Gate 3: frozen q10/q90
rc=run([sys.executable,str(HERE/"dual_lst_state_calibration_v01.py")])
cal=HERE/"DUAL_LST_STATE_CALIBRATION_RECEIPT_V0.1.json"
if rc!=0 or not cal.exists(): terminal("PREDICTOR_STATE_CALIBRATION_BLOCKED",2)
calx=load(cal)
if calx.get("classification")!="PREDICTOR_STATE_CALIBRATION_PASS": terminal("PREDICTOR_STATE_CALIBRATION_BLOCKED",2)
m["q10"]=calx.get("quantile_rule",{}).get("q10")
m["q90"]=calx.get("quantile_rule",{}).get("q90")
m["completed_stages"].append("PREDICTOR_STATE_CALIBRATION_PASS");save()

# Gate 4: outcome-blind Discovery predictor sample
rc=run(["node",str(HERE/"dual_lst_discovery_predictor_sample_v01.mjs")])
sdir=ART/"discovery_predictor"
srec_art=sdir/"DUAL_LST_DISCOVERY_PREDICTOR_SAMPLE_RECEIPT_V0.1.json"
srows_art=sdir/"DUAL_LST_DISCOVERY_PREDICTOR_ROWS_V0.1.json"
srec=HERE/"DUAL_LST_DISCOVERY_PREDICTOR_SAMPLE_RECEIPT_V0.1.json"
srows=HERE/"DUAL_LST_DISCOVERY_PREDICTOR_ROWS_V0.1.json"
cp(srec_art,srec);cp(srows_art,srows)
if not srec.exists(): terminal("DUAL_LST_PREDICTOR_SOURCE_BLOCKED",2,"sample_receipt_missing")
sm=load(srec)
m["sample_classification"]=sm.get("classification")
m["transition_event_count"]=sm.get("transition_event_count")
m["cheap_event_count"]=sm.get("cheap_event_count")
m["rich_event_count"]=sm.get("rich_event_count")
if rc!=0 or sm.get("classification")=="DUAL_LST_PREDICTOR_SOURCE_BLOCKED": terminal("DUAL_LST_PREDICTOR_SOURCE_BLOCKED",2)
m["completed_stages"].append(sm.get("classification"));save()
if sm.get("classification")=="DUAL_LST_PREDICTOR_INSUFFICIENT_SAMPLE": terminal("DUAL_LST_PREDICTOR_INSUFFICIENT_SAMPLE",0)
if sm.get("classification")!="DUAL_LST_PREDICTOR_SAMPLE_PASS": terminal("DUAL_LST_PREDICTOR_GATE_UNKNOWN",2)

# Gate 5: future dislocation only after sample PASS
m["future_returns_opened"]=True;save()
rc=run(["node",str(HERE/"dual_lst_mechanism_discovery_source_v01.mjs")])
msrc_art=ART/"mechanism"/"DUAL_LST_MECHANISM_DISCOVERY_SOURCE_V0.1.json"
msrc=HERE/"DUAL_LST_MECHANISM_DISCOVERY_SOURCE_V0.1.json"
cp(msrc_art,msrc)
if rc!=0 or not msrc.exists(): terminal("MECHANISM_DISCOVERY_SOURCE_BLOCKED",2)
mx=load(msrc)
if mx.get("classification")!="MECHANISM_DISCOVERY_SOURCE_PASS": terminal("MECHANISM_DISCOVERY_SOURCE_BLOCKED",2)
m["completed_stages"].append("MECHANISM_DISCOVERY_SOURCE_PASS");save()

rc=run([sys.executable,str(HERE/"dual_lst_mechanism_discovery_analyze_v01.py")])
mres_art=ART/"mechanism"/"DUAL_LST_MECHANISM_DISCOVERY_RESULT_V0.1.json"
mres=HERE/"DUAL_LST_MECHANISM_DISCOVERY_RESULT_V0.1.json"
cp(mres_art,mres)
if rc!=0 or not mres.exists(): terminal("MECHANISM_DISCOVERY_ANALYSIS_BLOCKED",2)
rx=load(mres)
m["mechanism_classification"]=rx.get("classification")
m["completed_stages"].append(rx.get("classification"));save()

if rx.get("classification")=="MECHANISM_DISCOVERY_PASS":
 status={
  "lab_id":"DUAL-LST-RV-001","stage":"POST_DISCOVERY_STATUS_V0.1",
  "classification":"MECHANISM_DISCOVERY_PASS_PENDING_SEPARATE_OOS_AUTHORITY",
  "terminal":False,"future_returns_opened":True,"market_returns_opened":False,
  "pnl_opened":False,"oos_opened":False,"protected_holdout_opened":False,
  "mutation":False,"promotion_credit":0
 }
 (HERE/"POST_DISCOVERY_STATUS_V0.1.json").write_text(json.dumps(status,indent=2,sort_keys=True)+"\n")
 m["classification"]=status["classification"];save();raise SystemExit(0)

terminal(rx.get("classification","MECHANISM_DISCOVERY_UNKNOWN"),0)
