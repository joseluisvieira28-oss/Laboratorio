#!/usr/bin/env python3
"""Independent historical TRADE-LEDGER recomputation (2021-2025).
Only preserved canonical Actions artifacts are consumed. No market, account or trading endpoints.
Positive local findings cannot become independent untouched OOS after original results were opened.
"""
from __future__ import annotations
import argparse, hashlib, json, math, os, sys
from datetime import datetime, timezone
from pathlib import Path

EXPECTED={
  "first":("CROSS_ASSET_COST_VALIDATION_V0.1.json","CROSS_ASSET_COST_VALIDATION_V0.1",("ETHUSDT","SOLUSDT","BNBUSDT")),
  "expansion":("EXPANSION_COST_VALIDATION_V0.1.json","EXPANSION_COST_VALIDATION_V0.1",("XRPUSDT","DOGEUSDT","ADAUSDT","LINKUSDT","AVAXUSDT")),
  "h2":("H2_THIRD_BASKET_VALIDATION_V0.1.json","H2_THIRD_BASKET_VALIDATION_V0.1",("LTCUSDT","BCHUSDT","TRXUSDT","DOTUSDT","UNIUSDT"))
}
ARTIFACT_IDS={"first":10775714534,"expansion":10778258822,"h2":10791006099}
PERIOD=["2021-01-01T00:00:00Z","2025-12-31T23:00:00Z"]
HERE=Path(__file__).resolve().parent
OUTPUT=HERE/"HISTORICAL_LEDGER_REPRO_RESULT_V01.json"

def near(a,b,where):
    if a is None or b is None:
        if a is not b:raise ValueError("NULL_MISMATCH:"+where)
        return
    if not math.isclose(float(a),float(b),rel_tol=1e-8,abs_tol=1e-5):
        raise ValueError(f"RECOMPUTE_MISMATCH:{where}:{a}:{b}")

def num(v,name):
    x=float(v)
    if not math.isfinite(x):
        raise ValueError("NOT_FINITE:"+name)
    return x

def trace(asset,mode,layer,r):
    tr=r["trades"]
    if not isinstance(tr,list) or not tr:
        raise ValueError(f"EMPTY_HISTORIC_TRADES:{asset}/{mode}/{layer}")
    gains=[];losses=[];allp=[];yr={y:0.0 for y in range(2021,2026)}
    funds=[];fees=[];slips=[]
    last_entry=-1;last_exit=-1;streak=0;max_streak=0
    start=int(datetime(2021,1,1,tzinfo=timezone.utc).timestamp()*1000)
    end=int(datetime(2026,1,1,tzinfo=timezone.utc).timestamp()*1000)
    for i,t in enumerate(tr):
        st=int(t["entry_t"]);en=int(t["exit_t"])
        if not (start<=st<end and start<=en<end and st<=en):
            raise ValueError(f"INVALID_TIMESTAMP:{asset}/{mode}/{layer}/{i}")
        if st<last_entry or st<last_exit or en<last_exit:
            raise ValueError(f"OVERLAP_OR_NONCHRONOLOGICAL:{asset}/{mode}/{layer}/{i}")
        last_entry,last_exit=st,en
        p=num(t["net_pnl"],"net_pnl")
        f=num(t["funding"],"funding")
        fee=num(t["commission"],"commission")
        slip=num(t["slippage_cost"],"slippage")
        if fee<0 or slip<-1e-6: raise ValueError("NEGATIVE_FEE_SLIP")
        allp.append(p); funds.append(f);fees.append(fee);slips.append(slip)
        yr[datetime.fromtimestamp(en/1000,timezone.utc).year]+=p
        if p>0:gains.append(p);streak=0
        elif p<0:losses.append(p);streak+=1;max_streak=max(max_streak,streak)
        else:streak=0
    total=sum(allp); grosswin=sum(gains);grossloss=-sum(losses)
    pf=grosswin/grossloss if grossloss>0 else None
    top=sorted(gains,reverse=True)
    near(len(tr),r["closed_trades"],"trade_count")
    near(len(gains),r["wins"],"wins")
    near(len(losses),r["losses"],"losses")
    near(total,r["net_pnl"],"total_net")
    near(10000+total,r["ending_equity"],"equity")
    near(total/10000,r["net_return"],"return")
    near(pf,r["profit_factor"],"pf")
    near(len(gains)/len(tr),r["win_rate"],"winrate")
    near(total-(top[0] if top else 0),r["net_without_top1"],"top1")
    near(total-sum(top[:3]),r["net_without_top3"],"top3")
    near(max_streak,r["max_losing_streak"],"max_loss_streak")
    near(sum(funds),r["funding_cashflow"],"funding_total")
    near(sum(fees),r["commission_paid"],"fees_total")
    near(sum(slips),r["slippage_cost"],"slippage_total")
    for y,p in yr.items():
        near(p,r["year_pnl"][str(y)],f"year_{y}")
    return {
      "trades":len(tr),"wins":len(gains),"losses":len(losses),
      "net_usdt":round(total,6),"net_pct":round(total/100,5),
      "pf":round(pf,6) if pf is not None else None,
      "win_rate_pct":round(100*len(gains)/len(tr),4),
      "avg_winner_usdt":round(grosswin/len(gains),5) if gains else None,
      "avg_loser_usdt":round(grossloss/len(losses),5) if losses else None,
      "payoff_winner_over_abs_loser":round((grosswin/len(gains))/(grossloss/len(losses)),5) if gains and losses else None,
      "worst_trade_usdt":round(min(allp),5),
      "best_trade_usdt":round(max(allp),5),
      "net_without_top3_usdt":round(total-sum(top[:3]),5),
      "top3_positive_profit_share":round(sum(top[:3])/grosswin,5) if grosswin else None,
      "max_losing_streak":max_streak,
      "positive_years":sum(v>0 for v in yr.values()),
      "yearly_net_usdt":{str(y):round(v,5) for y,v in yr.items()},
      "fees_usdt":round(sum(fees),5),
      "funding_usdt":round(sum(funds),5),
      "recorded_slippage_usdt":round(sum(slips),5),
      "mtm_max_dd_pct_FROM_ORIGINAL_BAR_SIM":round(100*num(r["max_mark_to_market_drawdown"],"dd"),5),
      "risk_r_multiple":"NOT_AVAILABLE_FROM_THIS_TRADE_LEDGER"
    }

def load(which,root):
    file,experiment,symbols=EXPECTED[which]
    hits=list(Path(root).rglob(file))
    if len(hits)!=1:
        raise ValueError(f"ARTIFACT_MISSING_OR_DUPLICATE:{which}:{file}:{len(hits)}")
    path=hits[0]
    raw=path.read_bytes(); doc=json.loads(raw)
    if doc.get("lab")!="BTC-CONVEX-TREND-CAPTURE-001":
        raise ValueError("LAB_ID_MISMATCH:"+which)
    if doc.get("experiment")!=experiment:raise ValueError("EXPERIMENT_ID_MISMATCH:"+which)
    if doc.get("period")!=PERIOD:raise ValueError("PERIOD_MISMATCH:"+which)
    if set(doc.get("symbols",{}))!=set(symbols):
        raise ValueError("UNIVERSE_MISMATCH:"+which)
    for s in symbols:
        p=doc["symbols"][s]["provenance"]
        if p["bar_count_economic"]!=43824 or not p.get("manifest_sha256") or not p.get("manifest_entries"):
            raise ValueError("BAD_HISTORIC_SOURCE_PROVENANCE:"+s)
    return doc,hashlib.sha256(raw).hexdigest()

def audit(first,expansion,h2):
    files={"first":first,"expansion":expansion,"h2":h2}
    result={
       "scope":"EXISTING_HISTORICAL_TRADE_LEDGER_INDEPENDENT_RECOMPUTATION_ONLY",
       "never_new_untouched_oos":True,
       "forward_wait_required_for_historical_decision":False,
       "actual_fill_proven":False,
       "live_trading_authority":False,
       "original_artifact_ids":ARTIFACT_IDS,
       "commit_sha":os.environ.get("GITHUB_SHA","LOCAL"),
       "source_json_sha256":{},
       "asset_metrics":{},
       "errors":[],
    }
    docs={}
    for which,root in files.items():
        doc,digest=load(which,root)
        docs[which]=doc;result["source_json_sha256"][which]=digest
        for asset,node in doc["symbols"].items():
            modes={"H2_RISING_REGIME","PARENT"} if which=="h2" else {"PARENT"}
            result["asset_metrics"][asset]={}
            for mode in modes:
                result["asset_metrics"][asset][mode]={}
                for layer in ("BASE","STRESS"):
                    result["asset_metrics"][asset][mode][layer]=trace(
                        asset,mode,layer,node["results"][mode][layer])
    def metrics(which,mode="PARENT",layer="BASE"):
        return [result["asset_metrics"][s][mode][layer] for s in EXPECTED[which][2]]
    fbase=metrics("first");fstress=metrics("first",layer="STRESS")
    eb=metrics("expansion");es=metrics("expansion",layer="STRESS")
    hbase=metrics("h2","H2_RISING_REGIME")
    first_gate=(sum(r["net_usdt"]>0 for r in fbase)>=2
       and sum((r["pf"] or 0)>1 for r in fbase)>=2
       and sum(r["net_usdt"] for r in fstress)>0
       and sum(r["net_without_top3_usdt"]>0 for r in fbase)>=1) # strengthened top3 instead of top1 is diagnostic
    original_first=(sum(r["net_usdt"]>0 for r in fbase)>=2
       and sum((r["pf"] or 0)>1 for r in fbase)>=2
       and sum(r["net_usdt"] for r in fstress)>0
       and sum(1 for s in EXPECTED["first"][2] if docs["first"]["symbols"][s]["results"]["PARENT"]["BASE"]["net_without_top1"]>0)>=1)
    local_retrospective=original_first and all(r["net_usdt"]>0 for r in fbase) and all(r["net_usdt"]>0 for r in fstress) and all(r["mtm_max_dd_pct_FROM_ORIGINAL_BAR_SIM"]>=-60 for r in fbase)
    expansion_gate=(sum(r["net_usdt"]>0 for r in eb)>=3
       and sum((r["pf"] or 0)>1 for r in eb)>=3
       and sum(r["net_usdt"] for r in es)>0
       and sum(docs["expansion"]["symbols"][s]["results"]["PARENT"]["BASE"]["net_without_top1"]>0 for s in EXPECTED["expansion"][2])>=2)
    # Recompute 3rd H2 original as a separate already-opened child, never rescue parent
    h2_stress=metrics("h2","H2_RISING_REGIME","STRESS")
    parent_h2_base=metrics("h2","PARENT")
    h2_gate=(sum(r["net_usdt"]>0 for r in hbase)>=3 and sum((r["pf"] or 0)>1 for r in hbase)>=3
       and sum(r["net_usdt"] for r in h2_stress)>0
       and sum(docs["h2"]["symbols"][s]["results"]["H2_RISING_REGIME"]["BASE"]["net_without_top1"]>0 for s in EXPECTED["h2"][2])>=2
       and sum(r["net_usdt"] for r in hbase)>sum(r["net_usdt"] for r in parent_h2_base))
    if (original_first and docs["first"].get("parent_cross_asset_gate")!="SURVIVES") or (expansion_gate and docs["expansion"].get("expansion_gate")!="SURVIVES") or (h2_gate and docs["h2"].get("h2_gate")!="SURVIVES"):
        raise ValueError("FROZEN_GATE_RECOMPUTE_DISAGREEMENT")
    result["historical_first_basket_original_gate"]="PASS" if original_first else "FAIL"
    result["historical_first_basket_stronger_top3_diagnostic"]="PASS" if first_gate else "FAIL"
    result["historical_local_classification"]="HISTORICAL_LOCAL_PASS" if local_retrospective else "HISTORICAL_LOCAL_FAIL"
    result["historical_expansion_classification"]="HISTORICAL_CROSS_SECTION_PASS" if expansion_gate else "HISTORICAL_CROSS_SECTION_FAIL"
    result["historical_h2_child_classification"]="H2_CHILD_PASS" if h2_gate else "H2_CHILD_FAIL"
    result["global_historical_parent_classification"]="HISTORICAL_GENERALIZATION_PASS" if local_retrospective and expansion_gate else "HISTORICAL_GENERALIZATION_FAIL"
    result["source_status"]="ARCHIVED_CANONICAL_TRADE_RECORDS_VERIFIED"
    result["asset_counts"]={
       "first_positive_base":sum(r["net_usdt"]>0 for r in fbase),
       "expansion_positive_base":sum(r["net_usdt"]>0 for r in eb),
       "h2_child_positive_base":sum(r["net_usdt"]>0 for r in hbase),
       "parent_third_positive_base":sum(r["net_usdt"]>0 for r in parent_h2_base),
    }
    result["critical_limitation"]="No raw 1h bar reprocessing; price-path MTM DD referenced from original bar simulator. Re-adjudicates already exposed archived historical trade ledgers, not a new out-of-sample result. No independent exchange fills."
    return result

def synthetic_test():
    d0={"closed_trades":2,"wins":1,"losses":1,"net_pnl":1.0,"ending_equity":10001,"net_return":0.0001,
       "profit_factor":1.5,"win_rate":.5,"net_without_top1":-2,"net_without_top3":-2,
       "max_losing_streak":1,"funding_cashflow":0,"commission_paid":2,"slippage_cost":1,
       "max_mark_to_market_drawdown":-.1,"year_pnl":{str(y):0 for y in range(2021,2026)},
       "trades":[
          {"entry_t":1640995200000,"exit_t":1640998800000,"net_pnl":3,"funding":0,"commission":1,"slippage_cost":.5},
          {"entry_t":1641002400000,"exit_t":1641006000000,"net_pnl":-2,"funding":0,"commission":1,"slippage_cost":.5}
       ]}
    d0["year_pnl"]["2022"]=1
    assert trace("TEST","PARENT","BASE",d0)["trades"]==2
    d1=json.loads(json.dumps(d0));d1["trades"][1]["entry_t"]=d1["trades"][0]["entry_t"]
    try:trace("TEST","PARENT","BASE",d1)
    except ValueError as e:assert "OVERLAP" in str(e)
    else:raise AssertionError("FAIL_CLOSED_OVERLAP_MISSING")
    d2=json.loads(json.dumps(d0));d2["net_pnl"]=2
    try:trace("TEST","PARENT","BASE",d2)
    except ValueError as e:assert "RECOMPUTE_MISMATCH" in str(e)
    else:raise AssertionError("FAIL_CLOSED_PNL_MISSING")
    print("HISTORICAL_LEDGER_SYNTHETIC_TESTS_PASS: 3")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--first");p.add_argument("--expansion");p.add_argument("--h2")
    a=p.parse_args()
    if a.self_test:return synthetic_test()
    if not all((a.first,a.expansion,a.h2)):raise SystemExit("MUST_SUPPLY_ALL_THREE_ORIGINAL_ARTIFACTS")
    try:
        report=audit(a.first,a.expansion,a.h2)
        OUTPUT.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n",encoding="utf-8")
        print(json.dumps({"verification":report["source_status"],
          "original_parent_local":report["historical_first_basket_original_gate"],
          "retrospective_local":report["historical_local_classification"],
          "expansion":report["historical_expansion_classification"],
          "h2":report["historical_h2_child_classification"],
          "global":report["global_historical_parent_classification"],
          "counts":report["asset_counts"],"run_sha":report["commit_sha"]},indent=2))
    except Exception as e:
        blocked={"status":"ARCHIVED_TRADE_LEDGER_AUDIT_BLOCKED","reason":str(e),
          "original_artifact_ids":ARTIFACT_IDS,
          "scientific_credit":"NONE","live_trading_authority":False}
        OUTPUT.write_text(json.dumps(blocked,sort_keys=True,indent=2)+"\n")
        print(json.dumps(blocked,indent=2),file=sys.stderr)
        raise SystemExit(2)

if __name__=="__main__":main()
