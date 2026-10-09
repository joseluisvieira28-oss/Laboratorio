#!/usr/bin/env python3
"""Frozen retrospective economics. All original losses preserved.
Original Binance Parent BASE already includes fees, adverse slippage and funding.
Additional bps are SYNTHETIC stress, not venue observations.
"""
import argparse, json, hashlib, math, os, runpy, sys, traceback
from pathlib import Path
from datetime import datetime,timezone
HERE=Path(__file__).resolve().parent
RISK_SOURCE=HERE.parent/"convex_risk_v01"/"convex_risk_replay_v01.py"
BPS=(0,5,10,20,30,40,60,80)
RISK=(0.0025,0.005)
CAPITALS=(10000,25000,100000)
INCOME=(12000,24000)
BASE_ARCHIVE="CROSS_ASSET_COST_VALIDATION_V0.1.json"
SYMBOLS=("ETHUSDT","SOLUSDT","BNBUSDT")
PREVIOUS_BASE={0.0025:34.59609,0.005:20.080257}
PREVIOUS_STRESS={0.0025:33.684714,0.005:16.949956}
def closest(a,b,what,tol=.005):
 if not math.isclose(float(a),float(b),rel_tol=0,abs_tol=tol):
  raise ValueError("FROZEN_BASELINE_MISMATCH:"+what+":"+str(a)+":"+str(b))
def capital_summary(ret_pct):
 growth=1+ret_pct/100
 if growth<=0:return {"status":"EQUITY_EXHAUSTION","income_target_required_capital_usdt":None}
 cagr=(growth**(.2)-1)*100
 return {"cagr_pct":round(cagr,6),
   "ending_equity_by_initial_usdt":{
    str(c):round(c*growth,4) for c in CAPITALS},
   "annualized_GEOMETRIC_RETURN_PER_10000_usdt":round(10000*cagr/100,4),
   "constant_CAGR_target_capital_not_forecast_usdt":{
    str(amount):round(amount/(cagr/100),2) if cagr>0 else None for amount in INCOME},
   "income_target_note":"NOT monthly payout, forecast, withdrawal schedule, leverage licence, inflation/tax adjusted or capital-safe."}
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--archive-root",required=True)
 args=p.parse_args()
 out=HERE/"FINAL_COST_ELASTICITY_MATERIALITY_RECEIPT_V01.json"
 try:
  files=list(Path(args.archive_root).rglob(BASE_ARCHIVE))
  if len(files)!=1:raise ValueError("ORIGINAL_FIRST_BASKET_ARCHIVE_ABSENT_OR_DUPLICATE")
  raw=files[0].read_bytes();doc=json.loads(raw)
  if doc.get("experiment")!="CROSS_ASSET_COST_VALIDATION_V0.1":raise ValueError("WRONG_ECONOMIC_LEDGER")
  if doc.get("period")!=["2021-01-01T00:00:00Z","2025-12-31T23:00:00Z"]:
   raise ValueError("ORIGINAL_TIME_RANGE_DIFFERS")
  if set(doc.get("symbols",{}))!=set(SYMBOLS):raise ValueError("ORIGINAL_FIRST_ASSETS_CHANGED")
  ns=runpy.run_path(str(RISK_SOURCE),run_name="frozen_replay_as_lib")
  ev_for=ns["events_for"];replay=ns["replay"]
  layer={
   name:{sym:doc["symbols"][sym]["results"]["PARENT"][name]["trades"] for sym in SYMBOLS}
   for name in ("BASE","STRESS")
  }
  results={"BASE_EXTRA_BPS":{},"ORIGINAL_STRESS":{}}
  for risk in RISK:
   main_key=f"{risk:.4f}"
   base=replay(ev_for(SYMBOLS,layer["BASE"],layer["BASE"],0,False),risk)
   stress=replay(ev_for(SYMBOLS,layer["BASE"],layer["STRESS"],0,False),risk)
   closest(base["net_return_pct"],PREVIOUS_BASE[risk],main_key+"_BASE")
   closest(stress["net_return_pct"],PREVIOUS_STRESS[risk],main_key+"_STRESS")
   results["ORIGINAL_STRESS"][main_key]={"portfolio":stress,
     "materiality":capital_summary(stress["net_return_pct"])}
   results["BASE_EXTRA_BPS"][main_key]={}
   for bps in BPS:
    new=replay(ev_for(SYMBOLS,layer["BASE"],layer["BASE"],bps,False),risk)
    if bps>0 and new["net_return_pct"]>base["net_return_pct"]+.00001:
      raise ValueError("ADVERSE_COST_INCREASED_RETURN")
    results["BASE_EXTRA_BPS"][main_key][str(bps)]={
      "portfolio":new,"materiality":capital_summary(new["net_return_pct"])}
  outp={
    "status":"ORIGINAL_LEDGERS_RECONCILED__RETROSPECTIVE_COST_MATERIALITY_READY",
    "original_canonical_action_run":35918769969,
    "original_canonical_artifact":10775714534,
    "original_archive_sha256":hashlib.sha256(raw).hexdigest(),
    "already_known_2021_2025":True,"not_new_independent_oos":True,
    "financial_materiality_policy_cagr_threshold_pct":10,
    "original_base_roundtrip_fee_and_slip_bps":24,
    "original_fee_and_funding_ALREADY_INCLUDED":True,
    "extra_cost_adverse_bps_each_roundtrip":BPS,
    "risk_per_trade":RISK,
    "hypothetical_capitals":CAPITALS,
    "hypothetical_constant_cagr_income_targets":INCOME,
    "result":results,
    "hypothetical_notional_size_uses_previous_shared_portfolio_model":True,
    "liquidation_intrabar_mtm_not_recalculated":True,
    "past_forward_2026_not_reopened":True,
    "live_go":False,
    "declared_limitation":"Not point-in-time historical quotes or actual order book fills; no CHF FX/taxes; cannot infer practical income."
  }
  out.write_text(json.dumps(outp,sort_keys=True,indent=2)+"\n")
  print("FINAL_ECONOMIC_RECEIPT",json.dumps({
    "status":outp["status"],"base":{key:{
      bps:{"five_y_pct":z["portfolio"]["net_return_pct"],"cagr_pct":z["materiality"]["cagr_pct"],
           "realized_only_dd_pct":z["portfolio"]["realized_only_dd_pct"],
           "trades":z["portfolio"]["trades"]} for bps,z in value.items()
     } for key,value in results["BASE_EXTRA_BPS"].items()},
    "stress":{key:{"five_y_pct":s["portfolio"]["net_return_pct"],
      "cagr_pct":s["materiality"]["cagr_pct"]} for key,s in results["ORIGINAL_STRESS"].items()}
  },sort_keys=True),flush=True)
 except Exception as e:
  out.write_text(json.dumps({"status":"FINAL_ECONOMICS_FAIL_CLOSED","reason":repr(e),
   "economic_credit":"ZERO","live_go":False},indent=2)+"\n")
  traceback.print_exc();sys.exit(2)
if __name__=="__main__":main()
