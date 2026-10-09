#!/usr/bin/env python3
"""Frozen historical-only counterfactual small-risk portfolio replay.
No market calls; no output-based strategy selection; source already opened, NOT fresh OOS.
"""
import argparse, hashlib, json, math, os, sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent
SOURCE_INFO={
 "FIRST":("CROSS_ASSET_COST_VALIDATION_V0.1.json","CROSS_ASSET_COST_VALIDATION_V0.1",("ETHUSDT","SOLUSDT","BNBUSDT")),
 "SECOND":("EXPANSION_COST_VALIDATION_V0.1.json","EXPANSION_COST_VALIDATION_V0.1",("XRPUSDT","DOGEUSDT","ADAUSDT","LINKUSDT","AVAXUSDT")),
 "THIRD":("H2_THIRD_BASKET_VALIDATION_V0.1.json","H2_THIRD_BASKET_VALIDATION_V0.1",("LTCUSDT","BCHUSDT","TRXUSDT","DOTUSDT","UNIUSDT")),
}
ARTIFACT_IDS={"FIRST":10775714534,"SECOND":10778258822,"THIRD":10791006099}
INITIAL_CAPITAL=10000.0
RISK_LEVELS=(0.0025,0.005)
PLANNED_STOP_DRAG=0.04+0.002+0.0004
MAX_CONCURRENT=3
MAX_TOTAL_PLANNED_RISK=0.01
STRESSES=("BASE","STRESS","BASE_PLUS_20BPS_ROUNDTRIP")
PORTFOLIOS={
 "FIRST":SOURCE_INFO["FIRST"][2],
 "SECOND":SOURCE_INFO["SECOND"][2],
 "THIRD":SOURCE_INFO["THIRD"][2],
 "ALL13":tuple(sorted(sum((list(x[2]) for x in SOURCE_INFO.values()),[]))),
}
DATE_MIN=int(datetime(2021,1,1,tzinfo=timezone.utc).timestamp()*1000)
DATE_MAX=int(datetime(2026,1,1,tzinfo=timezone.utc).timestamp()*1000)

def finite(x):
 v=float(x)
 if not math.isfinite(v):raise ValueError("NONFINITE_VALUE")
 return v

def verify_load(root):
 loaded={};source_hash={}
 for family,(filename,experiment,symbols) in SOURCE_INFO.items():
  hits=list(Path(root).rglob(filename))
  if len(hits)!=1:raise ValueError(f"ARCHIVE_MISSING_OR_DUPLICATE:{family}:{len(hits)}")
  p=hits[0];blob=p.read_bytes();d=json.loads(blob)
  if d.get("experiment")!=experiment or d.get("period")!=["2021-01-01T00:00:00Z","2025-12-31T23:00:00Z"]:
   raise ValueError("ARCHIVE_EXPERIMENT_OR_PERIOD_MISMATCH:"+family)
  if set(d.get("symbols",{}))!=set(symbols):
   raise ValueError("ARCHIVE_ASSET_UNIVERSE_MISMATCH:"+family)
  for sym in symbols:
   z=d["symbols"][sym]
   prv=z.get("provenance",{})
   if prv.get("bar_count_economic")!=43824 or not prv.get("manifest_sha256") or not prv.get("manifest_entries"):
    raise ValueError("ARCHIVE_PROVENANCE_MISSING:"+sym)
  loaded[family]=d;source_hash[family]=hashlib.sha256(blob).hexdigest()
 return loaded,source_hash

def get_raw_trades(docs):
 base={};stress={};descriptive={}
 for family,(_,_,symbols) in SOURCE_INFO.items():
  for sym in symbols:
   data=docs[family]["symbols"][sym]["results"]["PARENT"]
   base[sym]=data["BASE"]["trades"];stress[sym]=data["STRESS"]["trades"]
   for layer,trades in (("BASE",base[sym]),("STRESS",stress[sym])):
    seen=set();last_end=-1;last_entry=-1
    for t in trades:
     entry=int(t["entry_t"]);end=int(t["exit_t"])
     key=(entry,end)
     if not DATE_MIN<=entry<=end<DATE_MAX:raise ValueError("DATE_BOUNDARY_ERROR:"+sym)
     if entry<last_end or entry<=last_entry or key in seen:
      raise ValueError("SOURCE_OVERLAP_DUPLICATE:"+sym)
     last_entry=entry;last_end=end;seen.add(key)
     runit=finite(t["return_pct"])/100.0
     if finite(t["net_pnl"])*runit<0:raise ValueError("NET_PNL_RETURN_SIGN_DISAGREEMENT")
     for f in ("commission","funding","slippage_cost"):
      finite(t[f])
   descriptive[sym]={
     "original_parent_mtm_dd_pct":100*finite(data["BASE"]["max_mark_to_market_drawdown"]),
     "original_parent_pct_net":100*finite(data["BASE"]["net_return"]),
     "original_trade_count":len(base[sym]),
     "stress_trade_count":len(stress[sym]),
     "layer_paths_identical":len(base[sym])==len(stress[sym]) and all((b["entry_t"],b["exit_t"])==(t["entry_t"],t["exit_t"]) for b,t in zip(base[sym],stress[sym]))}
 return base,stress,descriptive

def events_for(symbols,original_base,layer_trades,extra_bps,remove_top3):
 ev=[]
 for sym in symbols:
  b=original_base[sym];tr=layer_trades[sym]
  suppressed=set()
  if remove_top3:
   # Deliberately adversarial hindsight removal, never a tradable filter.
   biggest=sorted(range(len(b)),key=lambda i:(-finite(b[i]["net_pnl"]),i))
   suppressed={i for i in biggest[:3] if finite(b[i]["net_pnl"])>0}
  for i,t in enumerate(tr):
   if i in suppressed:continue
   unit_return=finite(t["return_pct"])/100.0-extra_bps/10000
   if not math.isfinite(unit_return):raise ValueError("INVALID_UNIT_RETURN")
   entry=int(t["entry_t"]);end=int(t["exit_t"])
   ident=(sym,entry,end,i)
   ev.append((entry,1,sym,ident,unit_return))
   ev.append((end,0,sym,ident,unit_return))
 # Exits before entries at matching millisecond; stable alphabetical symbol order.
 ev.sort(key=lambda a:(a[0],a[1],a[2],a[3][3]))
 return ev

def replay(events,risk):
 equity=INITIAL_CAPITAL;peak=equity;max_realized_dd=0.0
 opened={};closed=[];skipped=0;skip_log={"RISK_BUDGET":0,"CONCURRENT_LIMIT":0}
 reservations=0.0;gross_wins=gross_losses=0.0;win_count=loss_count=0
 losing_streak=max_losing_streak=0;calendar=defaultdict(float)
 for ts,etype,sym,ident,unit_return in events:
  if etype==0:
   if ident not in opened:continue
   order=opened.pop(ident);reservations-=order["planned_risk"]
   # The per-notional return is NET of original recorded funding, commission, slip.
   pnl=order["notional"]*unit_return;equity+=pnl
   if equity<=0:raise ValueError("EQUITY_EXHAUSTED_BY_GAP_OR_NEGATIVE_TAIL")
   closed.append((ident,pnl))
   calendar[str(datetime.fromtimestamp(ts/1000,timezone.utc).year)]+=pnl
   peak=max(peak,equity)
   max_realized_dd=min(max_realized_dd,equity/peak-1)
   if pnl>0:gross_wins+=pnl;win_count+=1;losing_streak=0
   elif pnl<0:gross_losses-=pnl;loss_count+=1;losing_streak+=1;max_losing_streak=max(max_losing_streak,losing_streak)
   else:losing_streak=0
  else:
   notional=equity*risk/PLANNED_STOP_DRAG
   notional=min(notional,equity*0.95)
   reserved=notional*PLANNED_STOP_DRAG
   if len(opened)>=MAX_CONCURRENT:
    skip_log["CONCURRENT_LIMIT"]+=1;skipped+=1;continue
   if reservations+reserved>equity*MAX_TOTAL_PLANNED_RISK+1e-8:
    skip_log["RISK_BUDGET"]+=1;skipped+=1;continue
   if ident in opened:raise ValueError("DUPLICATE_ENTRY")
   opened[ident]={"notional":notional,"planned_risk":reserved}
   reservations+=reserved
 if opened:raise ValueError("OPEN_TRADES_AT_PERIOD_BOUNDARY")
 if not closed:raise ValueError("NO_TRADES_EXECUTED")
 win_pnls=sorted((p for _,p in closed if p>0),reverse=True)
 result={
  "trades":len(closed),"skipped_concurrent_or_budget":skipped,"skip_reasons":skip_log,
  "end_capital_usdt":round(equity,6),"net_return_pct":round(100*(equity/INITIAL_CAPITAL-1),6),
  "realized_only_dd_pct":round(100*max_realized_dd,6),
  "win_rate_pct":round(100*win_count/len(closed),5),
  "profit_factor_scaled_usdt":round(gross_wins/gross_losses,6) if gross_losses else None,
  "avg_win_to_abs_avg_loss":round((gross_wins/win_count)/(gross_losses/loss_count),6) if win_count and loss_count else None,
  "best_winner_share_of_total_gross_winners":round(win_pnls[0]/gross_wins,6) if gross_wins else None,
  "top3_winner_share_of_total_gross_winners":round(sum(win_pnls[:3])/gross_wins,6) if gross_wins else None,
  "max_losing_streak_by_chronological_exit":max_losing_streak,
  "positive_years":sum(x>0 for x in calendar.values()),
  "year_net_usdt":{str(y):round(calendar.get(str(y),0),5) for y in range(2021,2026)}
 }
 if result["trades"]+skipped!=len(events)//2:
  raise ValueError("TRADE_ACCOUNTING_MISMATCH")
 return result

def complete_run(root):
 docs,source_hash=verify_load(root)
 base,stress,original=get_raw_trades(docs)
 out={"scientific_status":"HISTORICAL_RISK_SCENARIO_TEST_ONLY_NOT_NEW_OOS",
      "running_commit":os.environ.get("GITHUB_SHA","LOCAL"),
      "original_artifact_ids":ARTIFACT_IDS,"source_sha256":source_hash,
      "planning_stop_plus_base_friction_pct":round(100*PLANNED_STOP_DRAG,4),
      "original_parent_mtm_desc":original,
      "risk_levels":list(RISK_LEVELS),
      "risk_budget_cap_pct":100*MAX_TOTAL_PLANNED_RISK,"max_concurrent":MAX_CONCURRENT,
      "output":{}}
 for name,symbols in {**PORTFOLIOS,**{f"SOLO_{s}":(s,) for s in sorted(base)}}.items():
  out["output"][name]={}
  for risk in RISK_LEVELS:
   k=f"{100*risk:.2f}pct"
   out["output"][name][k]={}
   for stressname in STRESSES:
    trades=stress if stressname=="STRESS" else base
    plus=20 if stressname=="BASE_PLUS_20BPS_ROUNDTRIP" else 0
    out["output"][name][k][stressname]={}
    for suffix,remove in (("FULL",False),("DROP_TOP3_PER_ASSET",True)):
     if stressname=="STRESS" and remove:
      out["output"][name][k][stressname][suffix]={"status":"NOT_COMPARABLE_CROSS_LAYER_SIGNAL_PATH"}
      continue
     ev=events_for(symbols,base,trades,plus,remove)
     out["output"][name][k][stressname][suffix]=replay(ev,risk)
 out["verdict"]="SCENARIOS_COMPUTED_ONLY__HISTORICAL_PROFITABILITY_GENERALIZATION_UNCHANGED"
 return out

def self_test():
 sym="TEST"
 def t(i,a,b,p):
  # hard-wired nominal $1000, known deterministic PnL
  return {"entry_t":DATE_MIN+i*3600000,"exit_t":DATE_MIN+(i+1)*3600000,"qty":1.0,
          "entry":1000.0,"net_pnl":p,"return_pct":p/10.0,"funding":0,"commission":2,"slippage_cost":0.4}
 z=[t(0,0,1,50),t(2,2,3,-30),t(4,4,5,10),t(6,6,7,20)]
 for r in (0.0025,0.005):
  ev=events_for((sym,),{sym:z},{sym:z},0,False)
  full=replay(ev,r)
  assert full["trades"]==4 and full["end_capital_usdt"]>INITIAL_CAPITAL
  broken=replay(events_for((sym,),{sym:z},{sym:z},0,True),r)
  assert broken["trades"]==1 and broken["net_return_pct"]<0
  extra=replay(events_for((sym,),{sym:z},{sym:z},20,False),r)
  assert extra["net_return_pct"]<full["net_return_pct"]
 assert abs(PLANNED_STOP_DRAG-.0424)<1e-9
 # Exhaustion of concurrent slots. No double counting.
 ev=[]
 for i in range(4):
  z0=(f"X{i}",DATE_MIN,DATE_MIN+3600000,i)
  ev.extend([(DATE_MIN,1,f"X{i}",z0,0.05),(DATE_MIN+3600000,0,f"X{i}",z0,0.05)])
 ev.sort(key=lambda a:(a[0],a[1],a[2],a[3][3]))
 z=replay(ev,.0025)
 assert z["trades"]==3 and z["skipped_concurrent_or_budget"]==1
 print("RISK_REPLAY_SELFTEST_PASS 9 deterministic invariants")

def main():
 p=argparse.ArgumentParser()
 p.add_argument("--self-test",action="store_true")
 p.add_argument("--archive-root",default=None)
 p.add_argument("--output",default=str(HERE/"RISK_NORMALIZED_ALL_BASKETS_RESULT_V01.json"))
 a=p.parse_args()
 if a.self_test:return self_test()
 if not a.archive_root:raise SystemExit("ARCHIVE_ROOT_REQUIRED")
 dest=Path(a.output)
 try:
  r=complete_run(a.archive_root)
  dest.write_text(json.dumps(r,sort_keys=True,indent=2)+"\n")
  print("CANONICAL_HISTORICAL_RISK_REPLAY")
  for portfolio in ("FIRST","SECOND","THIRD","ALL13"):
   for risk in ("0.25pct","0.50pct"):
    x=r["output"][portfolio][risk]
    print(json.dumps({"portfolio":portfolio,"risk":risk,
      "base":x["BASE"]["FULL"],
      "stress":x["STRESS"]["FULL"],
      "extra20bps":x["BASE_PLUS_20BPS_ROUNDTRIP"]["FULL"],
      "lost_top3":x["BASE"]["DROP_TOP3_PER_ASSET"],
      "no_research_upgrade":True},sort_keys=True))
  print("RUN_SUMMARY",json.dumps({"source_archive_sha256":r["source_sha256"],
   "status":r["scientific_status"],"commit":r["running_commit"]}))
 except Exception as e:
  dest.write_text(json.dumps({"status":"FAIL_CLOSED",
   "reason":str(e),"scientific_credit":"ZERO",
   "original_artifact_ids":ARTIFACT_IDS},indent=2))
  raise

if __name__=="__main__":main()
