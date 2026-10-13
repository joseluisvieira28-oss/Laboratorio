"""Separate post-source-gap COMMON 2023–2025 8-alt 4-TF exploratory replay.
Requires original unmodified V5 engine; not standalone forward or live trading.
"""
from __future__ import annotations
import argparse
import csv
import json
from datetime import datetime,timezone
from pathlib import Path
from research.convex_multialt_4tf_20261013 import multialt_matrix as old

START_UTC="2023-01-01T00:00:00Z"
END_UTC="2026-01-01T00:00:00Z"
SOURCE_PRE_UTC="2022-11-01T00:00:00Z"
FIRST=datetime(2022,11,1,tzinfo=timezone.utc)
ECON=datetime(2023,1,1,tzinfo=timezone.utc)
END=datetime(2026,1,1,tzinfo=timezone.utc)
PRE_MS=int(FIRST.timestamp()*1000)
ECON_MS=int(ECON.timestamp()*1000)
END_MS=int(END.timestamp()*1000)
MONTHS=tuple(f"{y:04d}-{m:02d}" for y in range(2022,2026)
             for m in range(1,13) if (y,m)>=(2022,11))
FUNDING_MONTHS=tuple(mo for mo in MONTHS if mo>="2023-01")

def apply_locked_3year_window():
    """Mutate only period globals of the imported identical BTC V5 simulator.

    Does not alter indicators, costs, original thresholds or paper sizing.
    """
    if not(len(MONTHS)==38 and len(FUNDING_MONTHS)==36):
        raise AssertionError("MONTH_WINDOW_WRONG")
    old.START_PRICE=PRE_MS
    old.START=ECON_MS
    old.END=END_MS
    old.MONTHS=MONTHS
    old.FUNDING_MONTHS=FUNDING_MONTHS
    old.base.START=ECON_MS
    old.base.END=END_MS
    old.base.PRE=PRE_MS
    if old.ASSETS!=("ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT",
                    "DOGEUSDT","ADAUSDT","LINKUSDT","AVAXUSDT"):
        raise AssertionError("ASSET_LIST_REPLACED")
    if old.base.FEE!=.0008 or old.base.STOP!=.04 or old.base.TRAIL!=.12 or old.base.ACTIVATE!=.05:
        raise AssertionError("PARENT_SETTINGS_CHANGED")
    return True

def analyze_symbol(symbol):
    if symbol not in old.ASSETS:raise ValueError("NOT_FROZEN_SYMBOL")
    apply_locked_3year_window()
    five,one,funding,manifest=old.fetch_all(symbol)
    rows=old.symbol_diagnostic(symbol,five,one,funding)
    return {
        "period_start":START_UTC,"period_end_exclusive":END_UTC,
        "source_warmup_start":SOURCE_PRE_UTC,
        "frozen_source_3year":True,
        "source_counts":{"5m":len(five),"1h":len(one),"funding":len(funding)},
        "source_manifest":manifest,
        **rows}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--symbol",required=True,choices=old.ASSETS)
    p.add_argument("--output-dir",type=Path,required=True)
    a=p.parse_args()
    a.output_dir.mkdir(parents=True,exist_ok=True)
    out={"symbol":a.symbol,"status":"SOURCE_BLOCKED",
         "source_protocol":"PRE_OUTCOME_3YEAR_FREEZE.md",
         "original_2021_25_SOURCE_BLOCKED_NOT_OVERRIDDEN":True,
         "period_start":START_UTC,"period_end_exclusive":END_UTC,
         "independent_OOS":False,"actual_venue_fills":False,
         "live_authority":False,"risk_and_cost_rules_unchanged":True}
    try:
        res=analyze_symbol(a.symbol)
        for key,ledger in res.pop("trade_ledgers").items():
            if ledger:
                with (a.output_dir/(key+"_TRADES.csv")).open("w",encoding="utf8",newline="") as f:
                    w=csv.DictWriter(f,fieldnames=ledger[0])
                    w.writeheader();w.writerows(ledger)
        out.update(res)
        out["status"]="COMMON_2023_25_8ALT_COMPLETED_NO_OOS_CREDIT"
    except Exception as exc:
        out["blocked_reason"]=type(exc).__name__+":"+str(exc)
    (a.output_dir/"RESULT.json").write_text(json.dumps(out,sort_keys=True,indent=2)+"\n",encoding="utf8")
    print("COMMON_3YEAR_FINAL",json.dumps({"symbol":a.symbol,"status":out["status"],
        "source_counts":out.get("source_counts"),"block":out.get("blocked_reason"),
        "1h_signal_divergences":out.get("source_signal_disagreement_count_1h"),
        "models":{k:{"net":round(v["marked_return_pct"],4),
                     "pf":round(v["profit_factor"],4) if v["profit_factor"] else None,
                     "drawdown":round(v["max_5m_low_stress_dd_pct"],4),
                     "closed":v["closed_trades"]}
                  for k,v in out.get("model",{}).items()}},sort_keys=True),flush=True)
    if out["status"]!="COMMON_2023_25_8ALT_COMPLETED_NO_OOS_CREDIT":
        raise SystemExit(2)
if __name__=="__main__":
    main()
