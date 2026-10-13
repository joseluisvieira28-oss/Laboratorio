#!/usr/bin/env python3
"""BTC CONVEX 1H closed-trade accounting forensics: 2021-25 prior run ONLY.
No network, no exchange, no price-data changes, no recalculated strategy/fees.
Expected artifact: immutable Actions 38426153613 / 11828479302.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

EXPECTED = {
    "1h_BASE": {"closed": 77, "marked_return": 15.074361072241294,
                "cash": 11521.632749461698, "fees": 278.22355543339734,
                "funding": -1154.2604487567478},
    "1h_STRESS": {"closed": 78, "marked_return": 13.607362113910892,
                  "cash": 11375.43101484286, "fees": 280.43153046393576,
                  "funding": -1149.3581925737353},
}
STUDY_SOURCE = {"run_id":38426153613, "artifact_id":11828479302,
                "artifact_name":"BTC-CONVEX-5M-CANONICAL-4TF-V02-DESCRIPTIVE-NO-OOS"}
FIELDS = {"open_t","close_t","entry_price","exit_price","qty",
          "entry_fees","exit_fee","funding","net_pnl",
          "price_pnl","exit_reason","exit_year","notional_return_pct"}
COST_MULTIPLIERS = {
    "AS_RECORDED":1.0, "FEE_HALF_ACCOUNTING_ONLY":0.5,
    "FEE_ZERO_ACCOUNTING_ONLY":0.0, "FUNDING_ZERO_ACCOUNTING_ONLY":1.0,
    "BOTH_ZERO_ACCOUNTING_ONLY":0.0
}

def locate(dir_, name):
    matches=list(dir_.rglob(name))
    if len(matches)!=1:
        raise ValueError(f"SOURCE_MISSING_OR_AMBIGUOUS:{name}:{len(matches)}")
    return matches[0]

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def close(a,b,*,abs_tol=0.000005,rel_tol=1e-9):
    return math.isclose(a,b,abs_tol=abs_tol,rel_tol=rel_tol)

def read_source(folder):
    p=locate(folder,"MATRIX_RESULTS.json")
    raw=json.loads(p.read_text(encoding="utf-8-sig"))
    if raw.get("status")!="HISTORICAL_5M_CANONICAL_COMPLETED_NO_OOS_CREDIT":
        raise ValueError("ARTIFACT_SOURCE_OR_SCOPE_NOT_PASS")
    if raw.get("alpha_credit")!="NONE_ALREADY_KNOWN_HISTORY":
        raise ValueError("ARTIFACT_INDEPENDENCE_CLAIM_INVALID")
    if raw.get("source_counts")!={"5m":543456,"1h":45288,"funding":5478}:
        raise ValueError("ARTIFACT_SOURCE_COUNTS_MISMATCH")
    if raw.get("signal_source_parity",{}).get("one_hour_2021_25_disagreements")!=0:
        raise ValueError("ARTIFACT_SOURCE_ENTRY_SIGNAL_DIVERGENCE")
    if raw.get("one_hour_parity",{}).get("official_1h_bar_mismatch_count")!=7:
        raise ValueError("ARTIFACT_SOURCE_DISCREPANCY_NOT_PRESERVED")
    if "models" not in raw:raise ValueError("SOURCE_MODELS_MISSING")
    files={"MATRIX_RESULTS.json":sha256(p)}
    out={}
    for label,exp in EXPECTED.items():
        m=raw["models"].get(label)
        if m is None:raise ValueError(f"MISSING_MODEL:{label}")
        for k,e,g in [("closed",exp["closed"],m.get("closed_trades")),
                       ("cash",exp["cash"],m.get("cash_equity_usdt")),
                       ("fees",exp["fees"],m.get("fees_usdt")),
                       ("funding",exp["funding"],m.get("funding_usdt")),
                       ("marked_return",exp["marked_return"],m.get("marked_return_pct"))]:
            if not isinstance(g,(int,float)) or not close(float(g),float(e)):
                raise ValueError(f"MODEL_FINGERPRINT_MISMATCH:{label}:{k}:{e}:{g}")
        trade_file=locate(folder,label+"_TRADES.csv")
        files[label+"_TRADES.csv"]=sha256(trade_file)
        with trade_file.open(newline="",encoding="utf-8-sig") as f:
            reader=csv.DictReader(f)
            if not FIELDS.issubset(reader.fieldnames or []):
                raise ValueError("TRADE_LEDGER_FIELDS_MISSING")
            rows=list(reader)
        if len(rows)!=exp["closed"]:
            raise ValueError(f"LEDGER_COUNT_MISMATCH:{label}")
        out[label]=(m,rows)
    # Deliberately do not take old 15m/30m/4h alpha outcomes into account.
    return raw, out, files

def analyze_arm(m, raw_rows):
    trades=[]
    sums=defaultdict(float)
    annual=defaultdict(lambda:defaultdict(float))
    funders=[]
    fee_rows=[]
    before=0
    signal_venue_errors=0
    for i,r in enumerate(raw_rows):
        tr={k:float(r[k]) for k in
            ("entry_price","exit_price","qty","entry_fees","exit_fee","funding",
             "net_pnl","price_pnl","notional_return_pct")}
        for x in tr.values():
            if not math.isfinite(x):raise ValueError("NONFINITE_LEDGER")
        opened=int(r["open_t"]);closed=int(r["close_t"])
        if opened<=0 or closed<=opened or (i and opened<before):
            raise ValueError(f"TRADE_TIME_OVERLAP_OR_INVALID:{i}")
        if not (1609459200000<=opened<1767225600000 and closed<=1767225600000):
            raise ValueError("TRADE_TIMESTAMP_OUT_OF_FROZEN_WINDOW")
        if tr["entry_price"]<=0 or tr["exit_price"]<=0 or tr["qty"]<=0:
            raise ValueError("NONPOSITIVE_MARKET_PRICE_OR_QUANTITY")
        if tr["entry_fees"]<0 or tr["exit_fee"]<0:
            raise ValueError("NEGATIVE_FEE")
        net_check=tr["price_pnl"]-tr["entry_fees"]-tr["exit_fee"]+tr["funding"]
        if not close(net_check,tr["net_pnl"],abs_tol=1e-7):
            raise ValueError(f"LEDGER_ARITHMETIC_FAILED:{i}")
        qty_price=tr["qty"]*tr["entry_price"]
        if not close(tr["notional_return_pct"],tr["net_pnl"]/qty_price*100,abs_tol=1e-6):
            raise ValueError("NOTIONAL_RETURN_IDENTITY_FAIL")
        if not close(tr["entry_fees"],qty_price*0.0008,abs_tol=1e-6):
            raise ValueError("ENTRY_FEE_ASSUMPTION_MISMATCH")
        if not close(tr["exit_fee"],tr["qty"]*tr["exit_price"]*0.0008,abs_tol=1e-6):
            raise ValueError("EXIT_FEE_ASSUMPTION_MISMATCH")
        tr["year"]=str(int(r["exit_year"]))
        if tr["year"]!=str(datetime.fromtimestamp((closed-1)/1000,tz=timezone.utc).year):
            raise ValueError("YEAR_ATTRIBUTION_BAD")
        if tr["year"] not in ("2021","2022","2023","2024","2025"):
            raise ValueError("OUTSIDE_YEAR")
        tr["exit_reason"]=r["exit_reason"]
        tr["entry_notional"]=qty_price
        tr["exit_notional"]=tr["qty"]*tr["exit_price"]
        tr["fee_total"]=tr["entry_fees"]+tr["exit_fee"]
        tr["days_held"]=(closed-opened)/86400000.
        for k in ("price_pnl","net_pnl","funding","fee_total"):
            sums[k]+=tr[k]
            annual[tr["year"]][k]+=tr[k]
        funders.append(tr)
        trades.append(tr)
        before=closed

    fees_residual=m["fees_usdt"]-sums["fee_total"]
    funding_residual=m["funding_usdt"]-sums["funding"]
    open_cash_residual=m["cash_equity_usdt"]-m["initial_equity"]-sums["net_pnl"]
    if abs(open_cash_residual-(funding_residual-fees_residual))>0.00001:
        raise ValueError("ACCOUNT_LEDGER_VERSUS_OPEN_POSITION_RESIDUAL_RECONCILIATION_FAIL")
    if not m.get("end_position_open") or fees_residual<=0:
        raise ValueError("EXPECTED_OUTSTANDING_POSITION_NOT_RECONCILED")
    marked_open_unrealized=m["terminal_marked_equity_usdt"]-m["cash_equity_usdt"]
    if not close(m["terminal_marked_equity_usdt"]/m["initial_equity"]*100-100,m["marked_return_pct"],abs_tol=0.00001):
        raise ValueError("TERMINAL_MARK_RETURN_INVARIANT_FAIL")

    net_winners=sorted((t for t in trades if t["net_pnl"]>0),
                       key=lambda t:t["net_pnl"],reverse=True)
    net_losers=sorted((t for t in trades if t["net_pnl"]<0),
                      key=lambda t:t["net_pnl"])
    gross_wins=sum(t["net_pnl"] for t in net_winners)
    top={}
    for count in (1,3,5,10):
        amount=sum(t["net_pnl"] for t in net_winners[:count])
        top[str(count)]={
            "winner_pnl_usdt":amount,
            "share_gross_positive_pct":100*amount/gross_wins if gross_wins else None,
            "remaining_closed_static_pnl_usdt":sums["net_pnl"]-amount,
            "not_rebalanced":True}
    top_losses={str(n):sum(t["net_pnl"] for t in net_losers[:n]) for n in (1,3,5)}
    static_cost={}
    for label in ("AS_RECORDED","FEE_HALF_ACCOUNTING_ONLY",
                  "FEE_ZERO_ACCOUNTING_ONLY","FUNDING_ZERO_ACCOUNTING_ONLY",
                  "BOTH_ZERO_ACCOUNTING_ONLY",
                  "EXTRA_2BPS_SIDE_ACCOUNTING_ONLY",
                  "EXTRA_5BPS_SIDE_ACCOUNTING_ONLY",
                  "EXTRA_10BPS_SIDE_ACCOUNTING_ONLY"):
        fee_multiplier={"AS_RECORDED":1,"FEE_HALF_ACCOUNTING_ONLY":0.5,
            "FEE_ZERO_ACCOUNTING_ONLY":0,"FUNDING_ZERO_ACCOUNTING_ONLY":1,
            "BOTH_ZERO_ACCOUNTING_ONLY":0}.get(label,1)
        funding_multiplier=(0 if label in ("FUNDING_ZERO_ACCOUNTING_ONLY","BOTH_ZERO_ACCOUNTING_ONLY") else 1)
        bps={"EXTRA_2BPS_SIDE_ACCOUNTING_ONLY":2,
             "EXTRA_5BPS_SIDE_ACCOUNTING_ONLY":5,
             "EXTRA_10BPS_SIDE_ACCOUNTING_ONLY":10}.get(label,0)
        extra=sum((t["entry_notional"]+t["exit_notional"])*bps/10000
                  for t in trades)
        pnl=sums["price_pnl"]-fee_multiplier*sums["fee_total"]+funding_multiplier*sums["funding"]-extra
        static_cost[label]={
            "closed_unchanged_ledger_pnl_usdt":pnl,
            "delta_vs_original_closed_pnl_usdt":pnl-sums["net_pnl"],
            "note":"NOT dynamic rebalance, portfolio forward return, or executable cost guarantee"}
    holding={
        "median_days":sorted(t["days_held"] for t in trades)[len(trades)//2],
        "max_days":max(t["days_held"] for t in trades),
        "over_7_days":sum(t["days_held"]>7 for t in trades),
        "over_30_days":sum(t["days_held"]>30 for t in trades),
        "funding_cost_trades":sum(t["funding"]<0 for t in trades),
        "funding_credit_trades":sum(t["funding"]>0 for t in trades),
        "largest_single_trade_funding_cost_usdt":min(t["funding"] for t in trades),
        "largest_single_trade_funding_credit_usdt":max(t["funding"] for t in trades)}
    return {"closed_trade_count":len(trades),"closed_wins":len(net_winners),
            "closed_net_usdt":sums["net_pnl"],"closed_price_pnl_usdt":sums["price_pnl"],
            "closed_fee_usdt":sums["fee_total"],"closed_funding_usdt":sums["funding"],
            "cash_equity_usdt":m["cash_equity_usdt"],
            "terminal_marked_equity_usdt":m["terminal_marked_equity_usdt"],
            "open_position_residual":{
              "total_fees_minus_closed_fees_usdt":fees_residual,
              "total_funding_minus_closed_funding_usdt":funding_residual,
              "cash_ledger_minus_closed_trade_net_usdt":open_cash_residual,
              "terminal_unrealized_mark_pnl_usdt":marked_open_unrealized,
              "verified_cashflow_identity":True},
            "annual_closed_trade_components":{k:dict(v) for k,v in sorted(annual.items())},
            "top_winners":top,"top_losers":top_losses,
            "holding_and_funding":holding,
            "cost_sensitivity_on_fixed_closed_trades":static_cost,
            "return_classification":"historical descriptive; known outcomes; unchanged exits; NOT OOS"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source-dir",type=Path,required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    a=p.parse_args()
    a.output_dir.mkdir(parents=True,exist_ok=True)
    report={"status":"SOURCE_BLOCKED","study":"BTC-CONVEX-1H-ECONOMIC-FORENSICS-001",
            "source_ref":STUDY_SOURCE,"method":"STATIC_ALREADY_OBSERVED_2021_2025_ACCOUNTING_ONLY",
            "live_execution_proof":False,"independent_OOS_proof":False}
    try:
        _,data,checksums=read_source(a.source_dir)
        report["artifacts_sha256"]=checksums
        report["arms"]={label:analyze_arm(*data[label]) for label in EXPECTED}
        report["status"]="LEDGER_FORENSICS_PASS_NO_ALPHA_CREDIT"
    except Exception as e:
        report["block_reason"]=f"{type(e).__name__}:{e}"
    dest=a.output_dir/"FORENSICS_RESULT.json"
    dest.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("FORENSICS_SUMMARY",json.dumps(report,sort_keys=True))
    print("WROTE",dest)
    if report["status"]!="LEDGER_FORENSICS_PASS_NO_ALPHA_CREDIT":
        raise SystemExit(2)

if __name__=="__main__":main()
