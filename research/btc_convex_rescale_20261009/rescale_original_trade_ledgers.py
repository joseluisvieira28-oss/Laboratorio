#!/usr/bin/env python3
"""BTC Convex Parent V5 fixed-fraction sizing diagnostic (already exposed 2021-25 ledgers).
Research-only; no exchange, accounts, protected outcomes, or live orders.
"""
from __future__ import annotations
import argparse, hashlib, json, math, os, sys
from pathlib import Path
from datetime import datetime, timezone

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"historical_only_convex_20261009"))
import historical_ledger_audit as archive

INITIAL=10000.0
ENTRY_FEE=0.001
INITIAL_STOP=0.04
REFERENCE_FRACTION=0.95/(1+ENTRY_FEE)
BUDGETS={
  "ORIGINAL_95pct_allocation":REFERENCE_FRACTION,
  "0.25pct_nominal_initial_stop_risk":0.0025/INITIAL_STOP,
  "0.50pct_nominal_initial_stop_risk":0.005/INITIAL_STOP,
  "1.00pct_nominal_initial_stop_risk":0.01/INITIAL_STOP,
}
SURCHARGE_BPS=10
OUT=HERE/"FIXED_FRACTION_RESCALE_RECEIPT_V01.json"

def scalar(x,key):
    r=float(x)
    if not math.isfinite(r): raise ValueError(f"NONFINITE:{key}")
    return r

def core(trades,fraction,top_missing=None,plus_fee_bps=0):
    if not 0<fraction<=1:raise ValueError("INVALID_NOTIONAL_FRACTION")
    top_missing=set(top_missing or ())
    eq=INITIAL
    peak=eq
    maxdd=0.0
    win_sum=0.0;loss_sum=0.0;wins=[];losses=[]
    worst=0.0
    completed=0
    years={str(y):[] for y in range(2021,2026)}
    loss_streak=0;max_loss_streak=0
    last_exit=0
    for i,t in enumerate(trades):
        start=int(t["entry_t"]);end=int(t["exit_t"])
        if start<last_exit or end<start:raise ValueError(f"OUT_OF_ORDER_TRADE:{i}")
        last_exit=end
        notional=scalar(t["qty"],"qty")*scalar(t["entry"],"entry")
        if notional<=0:raise ValueError(f"INVALID_NOTIONAL:{i}")
        rawret=scalar(t["net_pnl"],"net_pnl")/notional
        realized_ret=0.0 if i in top_missing else rawret-(plus_fee_bps/10000.0)
        pnl=eq*fraction*realized_ret
        if eq+pnl<=0:raise ValueError(f"EXHAUSTED_EQUITY:{i}")
        worst=min(worst,pnl/eq)
        eq+=pnl
        peak=max(peak,eq)
        maxdd=min(maxdd,eq/peak-1)
        y=str(datetime.fromtimestamp(end/1000,timezone.utc).year)
        if y not in years:raise ValueError("BAD_YEAR")
        years[y].append(pnl)
        completed+=1
        if pnl>0:
            wins.append(pnl);win_sum+=pnl;loss_streak=0
        elif pnl<0:
            losses.append(-pnl);loss_sum-=pnl;loss_streak+=1
        else:loss_streak=0
        max_loss_streak=max(max_loss_streak,loss_streak)
    # Reconstitute successive close-to-close annual returns without guessing intratrade prices.
    byyear={};state=INITIAL
    for y in range(2021,2026):
        arr=years[str(y)];final=state+sum(arr)
        byyear[str(y)]=round(100*(final/state-1),6)
        state=final
    if abs(eq-state)>max(1e-5,1e-8*eq):raise ValueError("YEARLY_RECONCILIATION_FAILED")
    net=eq/INITIAL-1
    return {
      "ending_equity_usdt":round(eq,6),
      "net_return_pct":round(100*net,6),
      "cagr_pct":round(100*((eq/INITIAL)**0.2-1),6),
      "closed_trade_dd_pct":round(100*maxdd,6),
      "intratrade_mtm_dd":"NOT_RECOMPUTED_FROM_LEDGER",
      "worst_closed_trade_fraction_of_pretrade_equity_pct":round(100*worst,6),
      "nominal_4pct_stop_loss_before_costs_pct":round(100*fraction*.04,6),
      "winning_trades":len(wins),"losing_trades":len(losses),
      "zero_trades":completed-len(wins)-len(losses),
      "trades":completed,
      "realized_usdt_pf":round(win_sum/loss_sum,6) if loss_sum>0 else None,
      "avg_winning_dollar_over_avg_abs_losing_dollar":round((win_sum/len(wins))/(loss_sum/len(losses)),6) if wins and losses else None,
      "closed_trade_annual_pct":byyear,
      "max_consecutive_losing_trades":max_loss_streak,
    }

def sizing(trades,fraction,selected_top3=None):
    return {
      "BASE":core(trades["BASE"],fraction),
      "STRESS":core(trades["STRESS"],fraction),
      "STRESS_PLUS_ADVERSE_10BPS_RT":core(trades["STRESS"],fraction,plus_fee_bps=SURCHARGE_BPS),
      "BASE_MISSED_THREE_TOP_WINNERS":core(trades["BASE"],fraction,top_missing=selected_top3),
    }

def test():
    t=[
       {"entry_t":1609459200000,"exit_t":1609462800000,"qty":1,"entry":100,"net_pnl":-4},
       {"entry_t":1609466400000,"exit_t":1609470000000,"qty":1,"entry":100,"net_pnl":12}
    ]
    a=core(t,.125)
    exp=INITIAL*(1-.125*.04)*(1+.125*.12)
    assert abs(a["ending_equity_usdt"]-exp)<1e-5
    assert a["nominal_4pct_stop_loss_before_costs_pct"]==0.5
    assert core(t,.125,top_missing={1})["net_return_pct"]<0
    assert core(t,.125,plus_fee_bps=10)["net_return_pct"]<a["net_return_pct"]
    try:core([t[1],t[0]],.125)
    except ValueError as exc:assert "OUT_OF_ORDER_TRADE" in str(exc)
    else:raise AssertionError("FAIL_OPEN_ORDER")
    print("SYNTHETIC_FIXED_FRACTION_TESTS:5/PASS")

def run(args):
    roots={"first":args.first,"expansion":args.expansion,"h2":args.h2}
    original={}
    sha={}
    for k,p in roots.items():
        doc,digest=archive.load(k,p)
        original[k]=doc;sha[k]=digest
    provenance=archive.audit(**roots)
    if provenance["global_historical_parent_classification"]!="HISTORICAL_GENERALIZATION_FAIL":
        raise ValueError("ORIGINAL_GLOBAL_GATE_CHANGED")
    out={
      "authority":"PRE_COMPUTATION_RESCALE_FREEZE_V01.md",
      "already_exposed_historical_outcomes":True,
      "real_market_fills_verified":False,
      "research_only":True,
      "source_archived_trade_ledger_sha256":sha,
      "original_artifact_ids":archive.ARTIFACT_IDS,
      "original_historical_classification":provenance["global_historical_parent_classification"],
      "parent_variants_fixed":BUDGETS,
      "model":"scaling_original_per_notional_trade_pnl_linearly_by_fixed_sleeve_fraction",
      "capital_per_asset_sleeve_usdt":INITIAL,
      "mtm_downside_after_resize":"UNVERIFIED_WO_BAR_PATH",
      "asset_results":{},
      "commit":os.environ.get("GITHUB_SHA","LOCAL"),
    }
    for group,doc in original.items():
        for symbol,node in doc["symbols"].items():
            ref=node["results"]["PARENT"]
            trades={layer:ref[layer]["trades"] for layer in ("BASE","STRESS")}
            if len(trades["BASE"])!=len(trades["STRESS"]):
                raise ValueError("TRADE_COUNT_DIFFERS_BETWEEN_COSTS:"+symbol)
            for a,b in zip(trades["BASE"],trades["STRESS"]):
                if int(a["entry_t"])!=int(b["entry_t"]) or int(a["exit_t"])!=int(b["exit_t"]):
                    raise ValueError("TRADE_PATH_DIFFERS_BETWEEN_COSTS:"+symbol)
            # Baseline historical replay must match actual reported ending original equity.
            for layer in ("BASE","STRESS"):
                reproduced=core(trades[layer],REFERENCE_FRACTION)["ending_equity_usdt"]
                expected=scalar(ref[layer]["ending_equity"],"original_equity")
                if abs(reproduced-expected)>max(0.05,1e-5*abs(expected)):
                    raise ValueError(f"PARENT_BASELINE_NOT_REPRODUCED:{symbol}:{layer}:{reproduced}:{expected}")
            scored=sorted(
                range(len(trades["BASE"])),
                key=lambda i:scalar(trades["BASE"][i]["net_pnl"],"net_pnl")/(scalar(trades["BASE"][i]["qty"],"qty")*scalar(trades["BASE"][i]["entry"],"entry")),
                reverse=True,
            )
            top3=scored[:3]
            out["asset_results"][symbol]={
              "basket":group,
              "prior_parent_market_1h_max_mtm_dd_pct":round(100*scalar(ref["BASE"]["max_mark_to_market_drawdown"],"MTM"),6),
              "original_base_closed_trades":len(trades["BASE"]),
              "top3_positive_trade_indices_zero_based":top3,
              "arms":{name:sizing(trades,fraction,top3) for name,fraction in BUDGETS.items()},
            }
    # Only first 3 constitute previously independently positive basket; no asset dropping allowed from generalization.
    k=("ETHUSDT","SOLUSDT","BNBUSDT")
    all13=tuple(out["asset_results"])
    score={}
    for arm,fraction in BUDGETS.items():
        local_base=sum(out["asset_results"][s]["arms"][arm]["BASE"]["ending_equity_usdt"]>INITIAL for s in k)
        local_stress=sum(out["asset_results"][s]["arms"][arm]["STRESS"]["ending_equity_usdt"]>INITIAL for s in k)
        local_missed_loss=sum(out["asset_results"][s]["arms"][arm]["BASE_MISSED_THREE_TOP_WINNERS"]["ending_equity_usdt"]<INITIAL for s in k)
        local_extra_loss=sum(out["asset_results"][s]["arms"][arm]["STRESS_PLUS_ADVERSE_10BPS_RT"]["ending_equity_usdt"]<INITIAL for s in k)
        first_worst_dd=min(out["asset_results"][s]["arms"][arm]["BASE"]["closed_trade_dd_pct"] for s in k)
        all13_base=sum(out["asset_results"][s]["arms"][arm]["BASE"]["ending_equity_usdt"]>INITIAL for s in all13)
        expansion=("XRPUSDT","DOGEUSDT","ADAUSDT","LINKUSDT","AVAXUSDT")
        exp_pos=sum(out["asset_results"][s]["arms"][arm]["BASE"]["ending_equity_usdt"]>INITIAL for s in expansion)
        score[arm]={
          "local_first3_base_positive":local_base,
          "local_first3_stress_positive":local_stress,
          "local_first3_missed_top3_negative":local_missed_loss,
          "local_first3_plus_extra_cost_negative":local_extra_loss,
          "local_worst_closed_trade_dd_pct":first_worst_dd,
          "expansion5_base_positive":exp_pos,
          "parent_13_base_positive":all13_base,
          "local_source_only_diagnostic":"SCOPE_LIMITED_HISTORICAL_POSITIVE" if local_base==3 and local_stress==3 else "SCOPE_LIMITED_HISTORICAL_NEGATIVE",
          "all_13_historical_generalization":"FAIL" if all13_base<13 or exp_pos<3 else "REQUIRES_EXISTING_FROZEN_GATES",
          "winner_tail_diagnostic":"TAIL_DEPENDENCE_FAIL" if local_missed_loss>=2 else "TAIL_DEPENDENCE_SURVIVES_DIAGNOSTIC",
          "return_risk_qualifier":"CLOSED_TRADE_ONLY; CANNOT CLAIM FULL_PRICE_PATH_MAX_DD",
        }
    out["sizing_gate"]="RISKSCALE_MATHEMATICALLY_REDUCES_EXPOSURE"
    out["arm_summary"]=score
    OUT.write_text(json.dumps(out,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    display={"run":out["commit"],"source":out["sizing_gate"],"arms":score,"first_basket":{}}
    for s in k:
        display["first_basket"][s]={arm:{name:{
          "net_return_pct":out["asset_results"][s]["arms"][arm][name]["net_return_pct"],
          "cagr_pct":out["asset_results"][s]["arms"][arm][name]["cagr_pct"],
          "closed_trade_dd_pct":out["asset_results"][s]["arms"][arm][name]["closed_trade_dd_pct"],
          "worst_closed_trade_pct":out["asset_results"][s]["arms"][arm][name]["worst_closed_trade_fraction_of_pretrade_equity_pct"]
        } for name in ("BASE","STRESS","STRESS_PLUS_ADVERSE_10BPS_RT","BASE_MISSED_THREE_TOP_WINNERS")} for arm in BUDGETS}
    print(json.dumps(display,ensure_ascii=False,indent=2))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--first")
    p.add_argument("--expansion")
    p.add_argument("--h2")
    a=p.parse_args()
    if a.self_test:return test()
    try:
        if not all([a.first,a.expansion,a.h2]):raise ValueError("MISSING_CANONICAL_SOURCE")
        run(a)
    except Exception as e:
        OUT.write_text(json.dumps({
         "verdict":"COMPUTATION_BLOCKED","reason":str(e),
         "profitability_credit":False,"live_go":False
        },indent=2)+"\n")
        print("RESIZE_FAIL_CLOSED",repr(e),file=sys.stderr)
        raise SystemExit(2)
if __name__=="__main__":main()
