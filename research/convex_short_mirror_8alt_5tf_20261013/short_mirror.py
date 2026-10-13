#!/usr/bin/env python3
"""Frozen SHORT mirror of recovered CONVEX V5, 8 Binance alts × 5 TFs.
Historical 2023–25 only; public official checksum-verified files; ZERO execution.
The original LONG parent module and engine are never modified by this child.
"""
from __future__ import annotations
import argparse
import csv
import json
import math
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
from research.convex_multialt_4tf_20261013 import multialt_matrix as old
from research.convex_8alt_common_2023_25 import common_3yr as window

ASSETS=old.ASSETS
TFS=(("5m",300000),("15m",900000),("30m",1800000),
     ("1h",3600000),("4h",14400000))
COSTS=(("BASE",2),("STRESS",5))
FEE=.0008
STOP=.04
TRAIL=.12
ACTIVATE=.05
EXPOSURE=.20
FIVE=300000

def mirror_short_signals(bars):
    """The same recovered Parent inputs, exact reversed score and regime.
    Parent evaluates 4 independently counted flags incl Z and BB redundancy.
    """
    parent=old.src.load_parent()
    _,details=parent(bars)
    sm=parent.__globals__["sma"]
    sd=parent.__globals__["stdev"]
    closes=[b["close"] for b in bars]
    ma200=sm(closes,200)
    ma20=sm(closes,20)
    std20=sd(closes,20)
    result=[]
    for i,(b,d) in enumerate(zip(bars,details)):
        if d is None or ma200[i] is None or ma20[i] is None or std20[i] is None:
            result.append(False)
            continue
        rsi_overbought=d["rsi"]>70
        z_upper=d["z"]>2.
        bb_upper=b["close"]>(ma20[i]+2*std20[i])
        high_volume=bool(d["vol_flag"])
        score=int(rsi_overbought)+int(z_upper)+int(bb_upper)+int(high_volume)
        bearish=b["close"]<ma200[i]
        result.append(bool(bearish and score>=3))
    if len(result)!=len(bars):raise AssertionError("SIGNAL_LENGTH_MISMATCH")
    return result

def simulate_short(tf,bars_tf,market5,funding,slip_bps,*,include_trades=False,
                   start=None,end=None,forced_signals=None):
    """One-slot SHORT, stop at 5m price high; peak-for-short is trough LOW.
    No price future can affect a signal or stop before its TF candle closes.
    """
    if tf not in [v for _,v in TFS]:raise ValueError("TIMEFRAME_NOT_FROZEN")
    if slip_bps not in (2,5):raise ValueError("COST_SCENARIO_NOT_FROZEN")
    start=old.START if start is None else start
    end=old.END if end is None else end
    signals=mirror_short_signals(bars_tf) if forced_signals is None else forced_signals
    if len(signals)!=len(bars_tf):
        raise ValueError("SIGNAL_BARS_COUNT_MISMATCH")
    decision_times={bar["t"]+tf for bar,signal in zip(bars_tf,signals)
                    if signal and start<=bar["t"]<end}
    equity=10000.
    slip=slip_bps/10000
    max_eq=equity
    max_close_dd=0.
    max_high_dd=0.
    open_trade=None
    pending_time=None
    fees_total=0.
    funding_total=0.
    entries=0
    skipped=0
    signals_seen=0
    trades=[]
    exits=Counter()
    years=defaultdict(float)
    for t in range(start,end,FIVE):
        b=market5[t]
        entered=False
        if pending_time==t:
            if open_trade is not None:raise ValueError("PENDING_WITH_ACTIVE_SHORT")
            if equity<=0:raise ValueError("NONPOSITIVE_PAPER_EQUITY")
            entry=b["open"]*(1-slip)
            qty=(equity*EXPOSURE)/entry
            fee=qty*entry*FEE
            equity-=fee
            fees_total+=fee
            open_trade={
                "t":t,"entry":entry,"qty":qty,"entry_fee":fee,
                "initial_stop":entry*(1+STOP),
                "stop":entry*(1+STOP),
                "trough":entry,
                "funding":0.
            }
            pending_time=None
            entered=True
            entries+=1
        if open_trade is not None:
            p=open_trade
            # Funding for SHORT is EXACT NEGATION of parent LONG sign.
            if not entered and t in funding:
                delta=p["qty"]*b["open"]*funding[t]
                equity+=delta
                funding_total+=delta
                p["funding"]+=delta
            stop=p["stop"]
            if b["open"]>=stop:
                raw=b["open"]; reason="STOP_OPEN_GAP"
            elif b["high"]>=stop:
                raw=stop;reason="STOP_INTRABAR"
            else:
                raw=None;reason=None
            if raw is not None:
                cover=raw*(1+slip)
                fee=p["qty"]*cover*FEE
                price_pnl=p["qty"]*(p["entry"]-cover)
                net=price_pnl-p["entry_fee"]-fee+p["funding"]
                equity+=price_pnl-fee
                fees_total+=fee
                trade={
                    "open_t":p["t"],"close_t":t+FIVE,
                    "direction":"SHORT","entry_price":p["entry"],
                    "exit_price":cover,"qty":p["qty"],
                    "entry_fees":p["entry_fee"],"exit_fee":fee,
                    "funding":p["funding"],"net_pnl":net,
                    "price_pnl":price_pnl,
                    "exit_reason":reason,
                    "exit_year":datetime.fromtimestamp((t+FIVE-1)/1000,timezone.utc).year,
                    "notional_return_pct":100*net/(p["qty"]*p["entry"])
                }
                trades.append(trade)
                years[str(trade["exit_year"])]+=net
                exits[reason]+=1
                open_trade=None
            else:
                # First observe the high-stop hit test; only surviving
                # completed timeframe bars may update a trailing stop.
                p["trough"]=min(p["trough"],b["low"])
                if (t+FIVE)%tf==0:
                    profitable=(p["entry"]-b["close"])/p["entry"]
                    p["stop"]=(min(p["initial_stop"],p["trough"]*(1+TRAIL))
                               if profitable>=ACTIVATE else p["initial_stop"])
        # For SHORT adverse MTM uses highest observed price, unlike LONG.
        mark=equity+(open_trade["qty"]*(open_trade["entry"]-b["close"]) if open_trade else 0.)
        high=equity+(open_trade["qty"]*(open_trade["entry"]-b["high"]*(1+slip)) if open_trade else 0.)
        max_eq=max(max_eq,mark)
        max_close_dd=min(max_close_dd,mark/max_eq-1)
        max_high_dd=min(max_high_dd,high/max_eq-1)
        if t+FIVE in decision_times:
            signals_seen+=1
            if open_trade is None and pending_time is None:
                pending_time=t+2*FIVE
            else:
                skipped+=1
        if pending_time is not None and pending_time<t:raise AssertionError("STALE_SHORT_PENDING")
    marked=equity+(open_trade["qty"]*(open_trade["entry"]-market5[end-FIVE]["close"])
                   if open_trade else 0.)
    wins=[p["net_pnl"] for p in trades if p["net_pnl"]>0]
    losses=[-p["net_pnl"] for p in trades if p["net_pnl"]<=0]
    pos=sum(wins)
    neg=sum(losses)
    top3=sum(sorted(wins,reverse=True)[:3])
    loss_streak=0
    worst_loss_streak=0
    for p in trades:
        loss_streak=0 if p["net_pnl"]>0 else loss_streak+1
        worst_loss_streak=max(worst_loss_streak,loss_streak)
    result={
        "direction":"SHORT","tf_minutes":tf//60000,
        "initial_equity":10000.,
        "cost_slippage_bps_side":slip_bps,
        "cash_equity_usdt":equity,"terminal_marked_equity_usdt":marked,
        "realized_cash_return_pct":100*(equity/10000-1),
        "marked_return_pct":100*(marked/10000-1),
        "closed_trades":len(trades),"entries":entries,
        "wins":len(wins),
        "win_rate_pct":100*len(wins)/len(trades) if trades else None,
        "profit_factor":pos/neg if neg else None,
        "max_5m_close_mark_dd_pct":100*max_close_dd,
        "max_5m_high_stress_dd_pct":100*max_high_dd,
        "top3_winner_share_gross_positive_pct":100*top3/pos if pos else None,
        "remaining_closed_pnl_without_top3_static_usdt":sum(p["net_pnl"] for p in trades)-top3,
        "max_loss_streak":worst_loss_streak,
        "signal_bars":signals_seen,
        "skipped_signals_active_slot":skipped,
        "fees_usdt":fees_total,"funding_usdt":funding_total,
        "annual_closed_trade_pnl_usdt":dict(sorted(years.items())),
        "exit_reasons":dict(exits),
        "end_position_open":bool(open_trade),
        "pending_entry_at_cutoff":pending_time is not None,
        "model":"PUBLIC_5M_HISTORICAL_ONLY_NO_OOS",
        "private_execution_authenticated":False}
    if include_trades:result["trades"]=trades
    return result

def run_symbol(symbol):
    if symbol not in ASSETS:raise ValueError("SYMBOL_NOT_FROZEN")
    window.apply_locked_3year_window()
    if (old.base.FEE,old.base.STOP,old.base.TRAIL,old.base.ACTIVATE,old.base.PCT_NOTIONAL)!=(FEE,STOP,TRAIL,ACTIVATE,EXPOSURE):
        raise ValueError("ORIGINAL_LONG_ECONOMICS_DIVERGED")
    five,one,funding,manifest=old.fetch_all(symbol)
    bars={label:[five[t] for t in sorted(five)] if tf==FIVE else old.base.resample(five,tf)
          for label,tf in TFS}
    hourly_source=old.base.verify_one_hour_parity(bars["1h"],one)
    # No result rescue by comparing one-hour alternative supplier prices.
    mods={};ledger={}
    for tf_name,tf in TFS:
        for cost,slip in COSTS:
            key=tf_name+"_"+cost
            result=simulate_short(tf,bars[tf_name],five,funding,slip,include_trades=True)
            trade_rows=result.pop("trades")
            if len(trade_rows)!=result["closed_trades"]:raise ValueError("TRADE_COUNT_MISMATCH")
            mods[key]=result;ledger[key]=trade_rows
            print("SHORT_MODEL",symbol,key,"trades",result["closed_trades"],
                  "net",round(result["marked_return_pct"],6),
                  "pf",round(result["profit_factor"],4) if result["profit_factor"] else None,flush=True)
    return {"model":mods,"trade_ledgers":ledger,
            "source_counts":{"5m":len(five),"1h":len(one),"funding":len(funding)},
            "source_manifest":manifest,
            "official_hourly_discrepancy":hourly_source}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--symbol",required=True,choices=ASSETS)
    p.add_argument("--output-dir",type=Path,required=True)
    a=p.parse_args()
    a.output_dir.mkdir(parents=True,exist_ok=True)
    report={"symbol":a.symbol,"status":"SOURCE_OR_MODEL_BLOCKED",
            "strategy":"CONVEX_V5_EXACT_SYMMETRIC_SHORT_MIRROR",
            "protocol":"PRE_OUTCOME_FREEZE.md",
            "frozen_years":"2023_2024_2025",
            "timeframes":[name for name,_ in TFS],
            "scenarios":[name for name,_ in COSTS],
            "independent_oos":False,"live_authority":"NONE",
            "funding_mark":"five_minute_market_open_proxy_NOT_official_mark"}
    try:
        found=run_symbol(a.symbol)
        for k,rows in found.pop("trade_ledgers").items():
            if rows:
                with (a.output_dir/(k+"_TRADES.csv")).open("w",newline="",encoding="utf8") as f:
                    writer=csv.DictWriter(f,fieldnames=rows[0])
                    writer.writeheader();writer.writerows(rows)
        report.update(found)
        report["status"]="SHORT_10_ARMS_COMPLETED_RETROSPECTIVE_ONLY"
    except Exception as ex:
        report["blocked_reason"]=type(ex).__name__+":"+str(ex)
    (a.output_dir/"SHORT_RESULT.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print("SHORT_FINAL",json.dumps({"symbol":a.symbol,"status":report["status"],
          "blocked_reason":report.get("blocked_reason"),
          "source_counts":report.get("source_counts"),
          "arms":{k:{"net_pct":round(v["marked_return_pct"],4),
                     "pf":round(v["profit_factor"],4) if v["profit_factor"] else None,
                     "closed":v["closed_trades"],
                     "dd_pct":round(v["max_5m_high_stress_dd_pct"],4),
                     "funding_usdt":round(v["funding_usdt"],2),
                     "static_top3_remaining":round(v["remaining_closed_pnl_without_top3_static_usdt"],2),
                     "yearly":v["annual_closed_trade_pnl_usdt"]}
                  for k,v in report.get("model",{}).items()}},sort_keys=True),flush=True)
    if report["status"]!="SHORT_10_ARMS_COMPLETED_RETROSPECTIVE_ONLY":raise SystemExit(2)
if __name__=="__main__":
    main()
