"""Decompose ALREADY FINISHED FAST-CONVEX model ledger into prices, fees and funding.

Not dynamic fee-free backtest, not proof that zero/half fees executable or profitable.
No price source, exchange API, orders or live datasets touched.
"""
from __future__ import annotations
import argparse,hashlib,json,math
from pathlib import Path

ASSETS=("ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT","DOGEUSDT","ADAUSDT","LINKUSDT","AVAXUSDT")
TF=("5m","15m","30m","1h")
HORIZONS=("FAST8H","FAST24H")
COSTS=("BASE","STRESS")
CASES=128
INITIAL=10000.

def investigate(root):
    paths=list(root.rglob("FAST_RESULT.json"))
    seen={}
    for path in paths:
        d=json.loads(path.read_text(encoding="utf8"))
        sym=d.get("symbol")
        if sym not in ASSETS or sym in seen:
            raise ValueError("DUPLICATE_OR_INVALID_SYMBOL")
        seen[sym]=(path,d)
    if set(seen)!=set(ASSETS):
        raise ValueError("EIGHT_ORIGINAL_SOURCE_RECEIPTS_REQUIRED")
    rows=[]
    source_hash={}
    for sym in ASSETS:
        path,d=seen[sym]
        if d.get("status")!="FAST_CONVEX_FULL_HISTORICAL_DIAGNOSTIC_ONLY":
            raise ValueError("SOURCE_NOT_PASSED")
        if d.get("source_counts")!={"5m":333216,"1h":27768,"funding":3288}:
            raise ValueError("SOURCE_PROVENANCE_MISMATCH")
        source_hash[sym]=hashlib.sha256(path.read_bytes()).hexdigest()
        if len(d["models"])!=16:raise ValueError("MISSING_SYMBOL_ARMS")
        for timeframe in TF:
            for cap in HORIZONS:
                for cost in COSTS:
                    key=f"{timeframe}_{cap}_{cost}"
                    m=d["models"][key]
                    equity=m["terminal_marked_equity_usdt"]
                    fees=m["fees_total_usdt"]
                    funding=m["funding_total_usdt"]
                    if not all(math.isfinite(z) for z in (equity,fees,funding)) or fees<0:
                        raise ValueError("BAD_CASHFLOW_COMPONENT")
                    net=equity-INITIAL
                    if not math.isclose(net/INITIAL*100,m["marked_return_pct"],abs_tol=1e-8):
                        raise ValueError("SOURCE_NET_IDENTITY_BROKEN")
                    scenarios={
                        "original_after_cost_usdt":net,
                        "modeled_price_pnl_after_slip_before_fee_funding_usdt":net+fees-funding,
                        "static_fee_half_usdt":net+fees/2,
                        "static_fee_zero_usdt":net+fees,
                        "static_no_funding_usdt":net-funding,
                        "static_fee_and_funding_zero_usdt":net+fees-funding,
                    }
                    rows.append({"symbol":sym,"timeframe":timeframe,"horizon":cap,
                        "cost":cost,"closed_trades":m["closed_trades"],
                        "original_fee_usdt":fees,"original_funding_usdt":funding,
                        "terminal_equity_usdt":equity,
                        "static_only_not_dynamic_rebalance":True,**scenarios})
    if len(rows)!=CASES:raise ValueError("ALL_128_CASES_NOT_PRESENT")
    summary={k:{"positive":sum(row[k]>0 for row in rows),
                "negative":sum(row[k]<0 for row in rows),
                "zero":sum(row[k]==0 for row in rows)}
             for k in ("original_after_cost_usdt",
                     "modeled_price_pnl_after_slip_before_fee_funding_usdt",
                     "static_fee_half_usdt",
                     "static_fee_zero_usdt",
                     "static_no_funding_usdt",
                     "static_fee_and_funding_zero_usdt")}
    examples={key:next(x for x in rows if x["symbol"]==sym and x["timeframe"]==tf
                       and x["horizon"]==cap and x["cost"]=="BASE")
              for key,sym,tf,cap in (
                  ("SOL_5M_FAST8H","SOLUSDT","5m","FAST8H"),
                  ("ADA_1H_FAST24H","ADAUSDT","1h","FAST24H"),
                  ("BNB_1H_FAST8H","BNBUSDT","1h","FAST8H"),
                  ("SOL_1H_FAST24H","SOLUSDT","1h","FAST24H"))}
    return {"status":"STATIC_LEDGER_ACCOUNTING_RECONCILED_NO_ALPHA_CREDIT",
            "immutable_original_source_run":38446416504,
            "original_result_sha256_by_symbol":source_hash,
            "all_128_rows":rows,
            "sign_counts":summary,
            "key_examples":examples,
            "only_price_component_after_original_slippage":True,
            "no_dynamic_account_portfolio_recomputation":True,
            "actual_account_fee_or_maker_fill_rate_proven":False,
            "2026_OOS_opened":False,"trading_authority":"NONE"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source-dir",required=True,type=Path)
    p.add_argument("--output-dir",required=True,type=Path)
    a=p.parse_args()
    a.output_dir.mkdir(parents=True,exist_ok=True)
    result=investigate(a.source_dir)
    (a.output_dir/"STATIC_FEE_FUNDING_DIAGNOSTIC_128.json").write_text(
        json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print("STATIC_FEE_FINAL",json.dumps({k:v for k,v in result.items()
         if k in ("status","sign_counts","key_examples")},sort_keys=True),flush=True)
if __name__=="__main__":
    main()
