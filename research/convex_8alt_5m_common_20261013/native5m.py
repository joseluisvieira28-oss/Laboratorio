"""Native 5m CONVEX V5 on eight alts, immutable historical 2023-2025.
All signal, stop and accounting logic reuses V5 matrix.simulate unchanged,
except child-branch lower timeframe admission from 15m to 5m.
"""
from __future__ import annotations
import argparse, csv, json, math
from pathlib import Path
from research.convex_8alt_common_2023_25 import common_3yr as w
from research.convex_multialt_4tf_20261013 import multialt_matrix as old

ASSETS=("ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT","DOGEUSDT","ADAUSDT","LINKUSDT","AVAXUSDT")
TF=300_000
COSTS=(("BASE",2),("STRESS",5))

def analyze(symbol):
    if symbol not in ASSETS: raise ValueError("NOT_FROZEN_SYMBOL")
    w.apply_locked_3year_window()
    if old.base.FEE!=.0008 or old.base.STOP!=.04 or old.base.TRAIL!=.12 or old.base.ACTIVATE!=.05 or old.base.PCT_NOTIONAL!=.2:
        raise AssertionError("UNFROZEN_PARENT_SETTINGS")
    if (old.START,old.END,old.START_PRICE)!=(w.ECON_MS,w.END_MS,w.PRE_MS):
        raise AssertionError("UNFROZEN_DATE_WINDOW")
    five,one,funding,manifest=old.fetch_all(symbol)
    # Audit the independently published hourly source, but always calculate
    # the native 5m signals from the same complete canonical 5m market tape.
    hourly=old.base.resample(five,old.base.HOUR)
    hourly_audit=old.base.verify_one_hour_parity(hourly,one)
    original=old.src.load_parent()
    signals_canonical,_=original(hourly)
    signals_official,_=original([one[t] for t in sorted(one)])
    one_hour_disagreements=sum(a!=b for i,(a,b) in enumerate(zip(signals_canonical,signals_official))
                                if hourly[i]["t"]>=w.ECON_MS)
    five_bars=[five[t] for t in sorted(five)]
    results={};ledgers={}
    for name,slip in COSTS:
        model=old.base.simulate(TF,five_bars,five,funding,slip,include_trades=True)
        trades=model.pop("trades")
        if model["closed_trades"]!=len(trades) or model["tf_minutes"]!=5:
            raise ValueError("BAD_FIVE_MINUTE_MODEL_OR_LEDGER")
        results[name]=model
        ledgers[name]=trades
        print("NATIVE5M_MODEL",symbol,name,"net",round(model["marked_return_pct"],6),
              "trades",model["closed_trades"],"PF",model["profit_factor"],
              "drawdown",model["max_5m_low_stress_dd_pct"],flush=True)
    return {"models":results,"ledgers":ledgers,
            "source_manifest":manifest,
            "source_counts":{"5m":len(five),"1h":len(one),"funding":len(funding)},
            "official_1h_discrepancy":hourly_audit,
            "hourly_entry_signal_disagreement_count":one_hour_disagreements,
            "warmup_start_utc":"2022-11-01T00:00:00Z",
            "economic_start_utc":"2023-01-01T00:00:00Z",
            "economic_end_exclusive_utc":"2026-01-01T00:00:00Z"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--symbol",required=True,choices=ASSETS)
    p.add_argument("--output-dir",type=Path,required=True)
    a=p.parse_args()
    a.output_dir.mkdir(parents=True,exist_ok=True)
    doc={"symbol":a.symbol,"status":"SOURCE_OR_MODEL_BLOCKED",
         "freeze":"PRE_OUTCOME_FREEZE.md",
         "scenarios":["BASE","STRESS"],
         "timeframe":"5m",
         "source":"OFFICIAL_BINANCE_USD_M_5M_CANONICAL",
         "parent_rules_changed":False,
         "signal_on_closed_5m":True,
         "entry_second_next_5m_open":True,
         "fee_bps_side":8,
         "slippage_base_bps_side":2,
         "slippage_stress_bps_side":5,
         "funding_mark":"5m_market_open_proxy_not_official_mark",
         "independent_oos":False,
         "actual_exchange_fills":False,
         "trading_authority":"NONE"}
    try:
        r=analyze(a.symbol)
        for scenario,trades in r.pop("ledgers").items():
            if trades:
                with (a.output_dir/(scenario+"_TRADES.csv")).open("w",encoding="utf8",newline="") as f:
                    writer=csv.DictWriter(f,fieldnames=trades[0].keys())
                    writer.writeheader();writer.writerows(trades)
        doc.update(r)
        doc["status"]="HISTORICAL_NATIVE_5M_COMPLETE_NO_OOS_CREDIT"
    except Exception as e:
        doc["block_reason"]=type(e).__name__+":"+str(e)
    (a.output_dir/"RESULT.json").write_text(json.dumps(doc,sort_keys=True,indent=2)+"\n",encoding="utf8")
    print("NATIVE_5M_FINAL",json.dumps({
        "symbol":a.symbol,"status":doc["status"],
        "block_reason":doc.get("block_reason"),
        "source_counts":doc.get("source_counts"),
        "hourly_1h_source_mismatches":doc.get("official_1h_discrepancy",{}).get("official_1h_bar_mismatch_count"),
        "models":{k:{
            "return_pct":m["marked_return_pct"],"trades":m["closed_trades"],
            "pf":m["profit_factor"],"win_pct":m["win_rate_pct"],
            "dd_pct":m["max_5m_low_stress_dd_pct"],
            "fees":m["fees_usdt"],"funding":m["funding_usdt"],
            "positive_years":sum(m["annual_closed_trade_pnl_usdt"].get(str(y),0)>0 for y in (2023,2024,2025)),
            "top3_remaining_usdt":m["removed_3_biggest_net_pnl_sum_usdt"]}
                  for k,m in doc.get("models",{}).items()}},sort_keys=True),flush=True)
    if doc["status"]!="HISTORICAL_NATIVE_5M_COMPLETE_NO_OOS_CREDIT":
        raise SystemExit(2)

if __name__=="__main__":
    main()
