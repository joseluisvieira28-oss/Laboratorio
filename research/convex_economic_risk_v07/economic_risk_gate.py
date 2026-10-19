"""CONVEX V07: locked-original-ledger economic/risk pre-screen, not tuning alpha.

Pure stdlib, no market access, private exchange calls, margin, orders, 2026 or
strategy replay. 2023-25 model outcomes are already known: descriptive ONLY.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

SOURCE_RUN = 38432883246
EXPECTED = {"SOLUSDT": ("1h", 84), "BNBUSDT": ("4h", 28)}
SCENARIOS_BPS = (0, 6, 12, 20, 40)
SIZE_FACTORS = ("0.25", "0.50", "1.00")
YEARS = ("2023", "2024", "2025")
BASE_FEES_BPS_SIDE = 8
MAX_MODEL_LOW_DD = -10.0
MIN_TRADES = 60
TOP3_MAX_FRACTION_OF_NET = .60

def number(value, field):
    if isinstance(value, bool):
        raise ValueError("BOOLEAN_NUMERIC_" + field)
    try:
        x = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("INVALID_NUMBER_" + field) from exc
    if not math.isfinite(x):
        raise ValueError("NONFINITE_NUMBER_" + field)
    return x

def audit_ledger(records, cost_label, expected_count, symbol):
    if len(records) != expected_count:
        raise ValueError("ORIGINAL_TRADE_COUNT_MISMATCH")
    if cost_label not in ("BASE", "STRESS"):
        raise ValueError("UNREGISTERED_COST_MODEL")
    trades = []
    last_open = -1
    seen_starts = set()
    for row in records:
        t = int(row["open_t"])
        end = int(row["close_t"])
        if t <= last_open or t in seen_starts or end <= t:
            raise ValueError("TRADE_TIME_NONCHRONOLOGICAL_OR_DUPLICATED")
        last_open = t
        seen_starts.add(t)
        year = str(datetime.fromtimestamp((end-1)/1000, timezone.utc).year)
        if year not in YEARS or not (1672531200000 <= t < 1767225600000):
            raise ValueError("TRADE_OUTSIDE_FROZEN_SOURCE_2023_25")
        entry = number(row["entry_price"], "ENTRY")
        exit_px = number(row["exit_price"], "EXIT")
        qty = number(row["qty"], "QUANTITY")
        net = number(row["net_pnl"], "NET_PNL")
        price = number(row["price_pnl"], "PRICE_PNL")
        entry_fee = number(row["entry_fees"], "ENTRY_FEE")
        exit_fee = number(row["exit_fee"], "EXIT_FEE")
        funding = number(row["funding"], "FUNDING")
        if (entry <= 0 or exit_px <= 0 or qty <= 0 or entry_fee < 0
                or exit_fee < 0 or not row.get("exit_reason")):
            raise ValueError("INVALID_ENTRY_EXIT_FEE_OR_REASON")
        if not math.isclose(price, qty * (exit_px-entry), abs_tol=1e-6, rel_tol=1e-8):
            raise ValueError("TRADE_PRICE_DECOMPOSITION_FAILED")
        if not math.isclose(net, price - entry_fee - exit_fee + funding,
                            abs_tol=1e-6, rel_tol=1e-8):
            raise ValueError("NET_FEE_FUNDING_DECOMPOSITION_FAILED")
        trades.append({"open_t": t, "close_t": end, "year": year, "entry_notional": qty*entry,
                       "net": net, "funding": funding, "entry_fee": entry_fee, "exit_fee":exit_fee,
                       "reason":row["exit_reason"]})
    return trades

def evaluate(trades, original_model, symbol, cost_label):
    if not trades or int(original_model.get("closed_trades",-1)) != len(trades):
        raise ValueError("ORIGINAL_MODEL_COUNT_DISAGREEMENT")
    pnl = sum(t["net"] for t in trades)
    annual = {y: sum(x["net"] for x in trades if x["year"] == y) for y in YEARS}
    annual_count = {y: sum(x["year"] == y for x in trades) for y in YEARS}
    declared_years = original_model.get("annual_closed_trade_pnl_usdt",{})
    for year in YEARS:
        if not math.isclose(annual[year], number(declared_years.get(year,0),"PUBLISHED_YEAR"),
                            rel_tol=1e-8, abs_tol=1e-5):
            raise ValueError("ORIGINAL_MODEL_ANNUAL_CLOSED_PNL_DISAGREEMENT_"+year)
    top3 = sorted((t["net"] for t in trades if t["net"]>0), reverse=True)[:3]
    gross_plus = sum(t["net"] for t in trades if t["net"]>0)
    gross_minus = -sum(t["net"] for t in trades if t["net"]<=0)
    streak = max_streak = 0
    for trade in trades:
        streak = 0 if trade["net"] > 0 else streak+1
        max_streak=max(max_streak,streak)
    if int(original_model.get("max_loss_streak",-1)) != max_streak:
        raise ValueError("ORIGINAL_LOSS_STREAK_DISAGREEMENT")
    implied_pf = gross_plus/gross_minus if gross_minus else None
    orig_pf=original_model.get("profit_factor")
    if implied_pf is not None and not math.isclose(implied_pf,number(orig_pf,"PF"),rel_tol=1e-8,abs_tol=1e-7):
        raise ValueError("ORIGINAL_MODEL_PF_DISAGREEMENT")
    entry_sum = sum(t["entry_notional"] for t in trades)
    if entry_sum<=0:raise ValueError("INVALID_SUM_NOTIONAL")
    dd = number(original_model.get("max_5m_low_stress_dd_pct"),"MODELED_LOW_DD")
    economics=[]
    for extra in SCENARIOS_BPS:
        adjusted = [t["net"] - extra/10000 * t["entry_notional"] for t in trades]
        years = {y:sum(v for v,t in zip(adjusted,trades) if t["year"]==y) for y in YEARS}
        economics.append({
            "extra_round_trip_bps":extra,
            "original_fees_already_included": True,
            "adjusted_closed_total_USDT":sum(adjusted),
            "adjusted_annual_closed_USDT":years,
            "not_portfolio_replay_or_real_fill": True,
        })
    # Risk scaling modifies the cashflow magnitudes alone; account path unchanged.
    risk_ladder=[]
    for factor in SIZE_FACTORS:
        k=float(factor)
        risk_ladder.append({
            "modeled_original_qty_factor":factor,
            "static_nominal_equity_fraction_if_original_20pct":k*.20,
            "static_scaled_original_closed_net_USDT":pnl*k,
            "static_scaled_worst_calendar_year_USDT":min(annual.values())*k,
            "static_scaled_extra40bp_adjusted_closed_net_USDT":economics[-1]["adjusted_closed_total_USDT"]*k,
            "not_a_recalculated_account_or_execution":True,
        })
    return {
        "symbol":symbol, "cost_model":cost_label,"original_closed_trades":len(trades),
        "original_closed_net_USDT":pnl,"cashflow_year_USDT":annual,"trade_year_counts":annual_count,
        "original_total_closed_entry_notional_USDT":entry_sum,
        "original_marginal_break_even_extra_round_trip_bps":pnl/entry_sum*10000,
        "total_original_paid_closed_entry_and_exit_fees_USDT":sum(x["entry_fee"]+x["exit_fee"] for x in trades),
        "total_original_closed_funding_USDT":sum(x["funding"] for x in trades),
        "profit_factor":implied_pf, "max_nonpositive_streak":max_streak,
        "positive_winner_cashflow_gross_USDT":gross_plus,
        "negative_loser_cashflow_abs_USDT":gross_minus,
        "top_three_winner_cashflows_USDT":sum(top3),
        "top_three_winner_share_of_net_closed_profits":sum(top3)/pnl if pnl>0 else None,
        "max_5minute_low_mark_model_drawdown_pct":dd,
        "extra_friction_scenarios":economics,
        "three_static_risk_size_tiers":risk_ladder,
        "independent_out_of_sample":False,"broker_fills_proven":False,
        "no_real_trading":True,
    }

def gate(base,stress):
    reasons=[]
    if base["original_closed_trades"]<MIN_TRADES:
        reasons.append("LESS_THAN_60_CLOSED_TRADES")
    losses=[y for y,v in base["cashflow_year_USDT"].items() if v < 0]
    if losses:
        reasons.append("NEGATIVE_CALENDAR_YEAR_"+",".join(losses))
    if (base["extra_friction_scenarios"][-1]["adjusted_closed_total_USDT"] <= 0
        or stress["extra_friction_scenarios"][-1]["adjusted_closed_total_USDT"] <= 0):
        reasons.append("ADDITIONAL_40BPS_ERASES_MODEL_CLOSED_CASHFLOWS")
    concentration=base["top_three_winner_share_of_net_closed_profits"]
    if concentration is None or concentration>=TOP3_MAX_FRACTION_OF_NET:
        reasons.append("TOP_THREE_WINNERS_GE_60PCT_OF_NET_CLOSED_PROFIT")
    if base["max_5minute_low_mark_model_drawdown_pct"] < MAX_MODEL_LOW_DD:
        reasons.append("MODELED_LOW_DRAWDOWN_WORSE_THAN_10PCT")
    return {
        "risk_triage":"HISTORICAL_RISK_TRIAGE_REJECTED" if reasons else "HISTORICAL_RISK_TRIAGE_CANDIDATE_ONLY",
        "reasons":reasons,"risk_science_gate_is_not_statistical_alpha_proof":True,
        "actual_live_or_shadow_promotion_authorized":False,
    }

def process(root):
    evaluations=[]
    for symbol,(tf,count) in EXPECTED.items():
        files=list((root/symbol).rglob("RESULT.json"))
        if len(files)!=1:
            raise ValueError("CANONICAL_RESULT_NOT_UNIQUE:"+symbol+":"+str(len(files)))
        f=files[0]
        d=json.loads(f.read_text(encoding="utf-8"))
        if d.get("symbol")!=symbol or d.get("status")!="COMMON_2023_25_8ALT_COMPLETED_NO_OOS_CREDIT":
            raise ValueError("NOT_CANONICAL_SOURCE_RESULT")
        if d.get("source_counts")!={"5m":333216,"1h":27768,"funding":3288} or len(d.get("source_manifest",[]))!=112:
            raise ValueError("NOT_CANONICAL_SOURCE_MANIFEST")
        if d.get("independent_OOS") is not False or d.get("actual_venue_fills") is not False:
            raise ValueError("ORIGINAL_SOURCE_NOT_RESEARCH_ONLY")
        model=d.get("model",{})
        results={}
        hashes={"RESULT_json":hashlib.sha256(f.read_bytes()).hexdigest()}
        for cost in ("BASE","STRESS"):
            key=tf+"_"+cost
            original=model.get(key)
            if not isinstance(original,dict):
                raise ValueError("ORIGINAL_MODEL_MISSING_"+key)
            csvpath=f.parent/(key+"_TRADES.csv")
            if not csvpath.is_file():raise ValueError("ORIGINAL_LEDGER_CSV_MISSING_"+key)
            hashes[key+"_TRADES_csv"]=hashlib.sha256(csvpath.read_bytes()).hexdigest()
            with csvpath.open(encoding="utf8",newline="") as handle:
                records=list(csv.DictReader(handle))
            trades=audit_ledger(records,cost,count,symbol)
            results[cost]=evaluate(trades,original,symbol,cost)
        evaluations.append({
            "symbol":symbol,"original_artifact_source_run":SOURCE_RUN,
            "source_SHA256":hashes,
            "BASE":results["BASE"],"STRESS":results["STRESS"],
            "frozen_historical_gate":gate(results["BASE"],results["STRESS"]),
        })
    return {
        "status":"V07_RETROSPECTIVE_ECONOMIC_RISK_GATE_COMPLETE_NOT_OOS",
        "as_of":"2026-10-19","original_inputs":SOURCE_RUN,
        "asset_count":len(evaluations),
        "candidates":evaluations,
        "no_signal_tuning_performed":True,
        "source_2026_protected_holdout_opened":False,
        "native_broker_stop_verified":False,
        "full_okx_futures_execution_verified":False,
        "not_aggregate_account_return":True,
        "conclusion":"NO_HISTORICAL_RISK_TRIAGE_SURVIVORS" if all(
            x["frozen_historical_gate"]["risk_triage"]=="HISTORICAL_RISK_TRIAGE_REJECTED"
            for x in evaluations) else "AT_LEAST_ONE_HISTORICAL_TRIAGE_CANDIDATE_NOT_OOS",
        "trading_authority":"NONE",
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--original-artifacts",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    x=p.parse_args()
    result=process(x.original_artifacts)
    x.out.mkdir(parents=True,exist_ok=True)
    (x.out/"CONVEX_V07_ORIGINAL_BASE_STRESS_TWO_CANDIDATES_FULL_ECONOMIC_GATE.json").write_text(
        json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf8")
    for row in result["candidates"]:
        b=row["BASE"];s=row["STRESS"]
        print("V07_VERDICT",json.dumps({
            "symbol":row["symbol"],"closed_trades":b["original_closed_trades"],
            "original_closed_USDT":b["original_closed_net_USDT"],
            "annual_base_USDT":b["cashflow_year_USDT"],
            "original_marked_low_dd_pct":b["max_5minute_low_mark_model_drawdown_pct"],
            "top_three_winner_share_of_net":b["top_three_winner_share_of_net_closed_profits"],
            "BASE_plus40bp_closed_USDT":b["extra_friction_scenarios"][-1]["adjusted_closed_total_USDT"],
            "STRESS_plus40bp_closed_USDT":s["extra_friction_scenarios"][-1]["adjusted_closed_total_USDT"],
            "marginal_break_even_extra_cost_bps":b["original_marginal_break_even_extra_round_trip_bps"],
            "frozen_gate":row["frozen_historical_gate"],
        },sort_keys=True))
    print("V07_FINAL",result["conclusion"],"NO_LIVE_GO")
if __name__=="__main__":
    main()
