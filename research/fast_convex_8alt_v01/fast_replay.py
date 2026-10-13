#!/usr/bin/env python3
"""FAST-CONVEX V1: eight fixed alts, 5m/15m/30m/1h, fast primary 8h and 24h control.

Research historical 2023-25 only. Original recovered V5 LONG entry signals,
NEVER historical OOS or real executable fills. Original source feeds unchanged.
"""
from __future__ import annotations
import argparse,csv,json,math
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
from research.convex_8alt_common_2023_25 import common_3yr as common
from research.convex_multialt_4tf_20261013 import multialt_matrix as source
from research.btc_convex_timeframe_matrix_20261013 import matrix as old
from research.btc_convex_multifront_v01 import retrospective_diagnostic as parent

ASSETS=source.ASSETS
TIMEFRAMES=(("5m",old.M5),("15m",3*old.M5),("30m",6*old.M5),("1h",old.HOUR))
HORIZONS=(("FAST8H",8*old.HOUR),("FAST24H",24*old.HOUR))
COSTS=(("BASE",2),("STRESS",5))
INITIAL_EQUITY=10000.
RISK_NOTIONAL=0.20
TAKER_FEE=0.0008
TARGET=0.012
STOP=0.006
STOP_FIRST_ALWAYS=True
PERIOD_START=common.ECON_MS
PERIOD_END=common.END_MS
MIN_TRADES_PER_CAL_YEAR=52
MIN_CAGR_PCT=10.
MAX_DD_PCT=-20.
MIN_PROFIT_FACTOR=1.15

def annual_year(t):
    return str(datetime.fromtimestamp((t-1)/1000,timezone.utc).year)

def event_sig(bars,span):
    if span%old.M5!=0 or span not in dict(TIMEFRAMES).values():
        raise ValueError("UNFROZEN_TIMEFRAME")
    build=parent.load_parent()
    vals,_=build(bars)
    if len(vals)!=len(bars):
        raise ValueError("SIGNAL_LENGTH_BAD")
    return {b["t"]+span for b,v in zip(bars,vals) if v and PERIOD_START<=b["t"]<PERIOD_END}

def run_arm(five,funding,signals,tf_ms,max_hold_ms,slip_bps):
    if tf_ms not in dict(TIMEFRAMES).values() or max_hold_ms not in dict(HORIZONS).values() or slip_bps not in (2,5):
        raise ValueError("UNFROZEN_MODEL_ARM")
    if not 0<=slip_bps<=5:raise ValueError("BAD_SLIP")
    cash=INITIAL_EQUITY
    peak_cash_mark=cash
    dd_mark=0.
    dd_low=0.
    open_pos=None
    next_entry=None
    trades=[]
    total_fees=0.
    total_funding=0.
    opportunities=0
    skipped=0
    entries=0
    exit_counts=Counter()
    yearly=defaultdict(float)
    yearly_trades=Counter()
    signal_yearly=Counter()
    slip=slip_bps/10000.
    for t in range(PERIOD_START,PERIOD_END,old.M5):
        b=five[t]
        new_pos=False
        if next_entry==t:
            if open_pos is not None:raise AssertionError("ACTIVE_POSITION_WITH_QUEUED_ENTRY")
            entry=b["open"]*(1+slip)
            if cash<=0 or entry<=0:raise ValueError("PAPER_ACCOUNT_BANKRUPT_OR_BAD_PRICE")
            notional=cash*RISK_NOTIONAL
            qty=notional/entry
            fee=notional*TAKER_FEE
            cash-=fee
            total_fees+=fee
            open_pos={"entry_t":t,"entry":entry,"qty":qty,
                      "entry_fee":fee,"stop":entry*(1-STOP),
                      "target":entry*(1+TARGET),"funding":0.0}
            next_entry=None
            new_pos=True
            entries+=1

        if open_pos is not None:
            p=open_pos
            # Open-time deadline and gaps are resolved at OPEN. 5m intrabar
            # stop/target hit occurs AFTER open; stop-first ambiguity survives.
            if t>=p["entry_t"]+max_hold_ms:
                raw=b["open"];reason="MAX_HOLD_OPEN"
            elif b["open"]<=p["stop"]:
                raw=b["open"];reason="STOP_OPEN_GAP"
            elif b["open"]>=p["target"]:
                raw=b["open"];reason="TARGET_OPEN_GAP"
            elif b["low"]<=p["stop"]:
                raw=p["stop"];reason="STOP_INTRABAR"
            elif b["high"]>=p["target"]:
                raw=p["target"];reason="TARGET_INTRABAR"
            else:
                raw=None;reason=None

            # Charge funding if position existed on arrival at settlement
            # bar OPEN. This includes a later same-candle intrabar stop/TP.
            # Entries exactly at funding instant / exits at OPEN are excluded.
            open_exit=reason in ("MAX_HOLD_OPEN","STOP_OPEN_GAP","TARGET_OPEN_GAP")
            if not new_pos and not open_exit and t in funding:
                rate=funding[t]
                cf=-p["qty"]*b["open"]*rate
                cash+=cf
                p["funding"]+=cf
                total_funding+=cf
            if raw is not None:
                exit_price=raw*(1-slip)
                exit_fee=p["qty"]*exit_price*TAKER_FEE
                realized_price=p["qty"]*(exit_price-p["entry"])
                net=realized_price-p["entry_fee"]-exit_fee+p["funding"]
                cash+=realized_price-exit_fee
                total_fees+=exit_fee
                y=annual_year(t+old.M5)
                yearly[y]+=net
                yearly_trades[y]+=1
                record={"entry_t":p["entry_t"],"exit_t":t if open_exit else t+old.M5,
                        "year":int(y),"reason":reason,"entry":p["entry"],
                        "exit":exit_price,"qty":p["qty"],"entry_fee":p["entry_fee"],
                        "exit_fee":exit_fee,"price_pnl":realized_price,
                        "funding":p["funding"],"net_pnl":net,
                        "hold_hours":((t if open_exit else t+old.M5)-p["entry_t"])/old.HOUR,
                        "notional_return_pct":100*net/(p["entry"]*p["qty"])}
                trades.append(record)
                exit_counts[reason]+=1
                open_pos=None

        close_mtm=cash+(open_pos["qty"]*(b["close"]-open_pos["entry"]) if open_pos else 0)
        low_mtm=cash+(open_pos["qty"]*(b["low"]*(1-slip)-open_pos["entry"]) if open_pos else 0)
        peak_cash_mark=max(peak_cash_mark,close_mtm)
        dd_mark=min(dd_mark,close_mtm/peak_cash_mark-1)
        dd_low=min(dd_low,low_mtm/peak_cash_mark-1)

        if t+old.M5 in signals:
            opportunities+=1
            signal_yearly[annual_year(t+old.M5)]+=1
            if open_pos is None and next_entry is None:
                next_entry=t+2*old.M5
            else:skipped+=1
        if next_entry is not None and next_entry<t:
            raise AssertionError("STALE_ENTRY_SIGNAL")

    marked=cash+(open_pos["qty"]*(five[PERIOD_END-old.M5]["close"]-open_pos["entry"])
                 if open_pos else 0)
    winners=sorted((x["net_pnl"] for x in trades if x["net_pnl"]>0),reverse=True)
    negative=sum(-x["net_pnl"] for x in trades if x["net_pnl"]<=0)
    positive=sum(winners)
    top3=sum(winners[:3])
    pf=positive/negative if negative>0 else (None if not trades else 999999.)
    net=(marked/INITIAL_EQUITY-1)*100
    durations=sorted(x["hold_hours"] for x in trades)
    result={"initial_equity_usdt":INITIAL_EQUITY,
            "cash_equity_usdt":cash,"terminal_marked_equity_usdt":marked,
            "marked_return_pct":net,
            "approx_CAGR_3y_pct":100*((marked/INITIAL_EQUITY)**(1/3)-1) if marked>0 else -100,
            "closed_net_pnl_usdt":sum(x["net_pnl"] for x in trades),
            "closed_price_pnl_usdt":sum(x["price_pnl"] for x in trades),
            "fees_total_usdt":total_fees,"funding_total_usdt":total_funding,
            "closed_trades":len(trades),"entries":entries,
            "wins":len(winners),"winrate_pct":100*len(winners)/len(trades) if trades else None,
            "profit_factor":pf,
            "max_close_mark_dd_pct":100*dd_mark,
            "max_5m_low_model_dd_pct":100*dd_low,
            "exit_reasons":dict(exit_counts),"signal_opportunities":opportunities,
            "missed_while_slot_active":skipped,
            "signal_opportunities_per_week":opportunities/(1096/7),
            "trades_per_week":len(trades)/(1096/7),
            "annual_closed_trades":{str(y):yearly_trades[str(y)] for y in range(2023,2026)},
            "annual_closed_pnl_usdt":{str(y):yearly[str(y)] for y in range(2023,2026)},
            "annual_signal_opportunities":{str(y):signal_yearly[str(y)] for y in range(2023,2026)},
            "top3_share_positive_net_pnl_pct":100*top3/positive if positive else None,
            "static_closed_pnl_without_top3_usdt":sum(x["net_pnl"] for x in trades)-top3,
            "median_hold_hours":durations[len(durations)//2] if durations else None,
            "max_hold_hours_observed":max(durations) if durations else None,
            "end_position_open":bool(open_pos),
            "terminal_pending_signal":next_entry is not None,
            "funding_price_source":"BINANCE_USDM_5M_MARKET_OPEN_PROXY_NOT_MEXC_MARK",
            "actual_fill_proof":False,"OOS_credit":False}
    if len(trades) != sum(result["annual_closed_trades"].values()):
        raise AssertionError("FULL_HISTORICAL_YEAR_RECONCILIATION")
    if not math.isclose(cash,INITIAL_EQUITY+result["closed_net_pnl_usdt"]-
                        (total_fees-sum(x["entry_fee"]+x["exit_fee"] for x in trades))+
                        (total_funding-sum(x["funding"] for x in trades)),abs_tol=1e-6):
        raise AssertionError("FULL_CASHFLOW_RESIDUAL_RECONCILIATION")
    return result,trades

def historical_gate(base,stress):
    both_positive=all(z["marked_return_pct"]>0 and z["profit_factor"] is not None
                      and z["profit_factor"]>MIN_PROFIT_FACTOR for z in (base,stress))
    every_year_min=all(base["annual_closed_trades"][str(y)]>=MIN_TRADES_PER_CAL_YEAR
                       for y in range(2023,2026))
    every_year_net=all(base["annual_closed_pnl_usdt"][str(y)]>0 for y in range(2023,2026))
    flags={"BASE_STRESS_NET_AND_PF":both_positive,
           "TRADE_FREQUENCY_EACH_YEAR_52":every_year_min,
           "ALL_THREE_CALENDAR_YEARS_NET_POSITIVE":every_year_net,
           "BASE_DRAWDOWN_WITHIN_MINUS_20PCT":base["max_5m_low_model_dd_pct"]>=MAX_DD_PCT,
           "BASE_THREE_YEAR_CAGR_AT_LEAST_10PCT":base["approx_CAGR_3y_pct"]>=MIN_CAGR_PCT,
           "BASE_CLOSED_NET_POSITIVE_AFTER_STATIC_TOP3_OMISSION":base["static_closed_pnl_without_top3_usdt"]>0}
    return {"gates":flags,"all_gates_descriptive_pass":all(flags.values()),
            "independent_OOS_promoted":False,
            "economic_classification":"HISTORICAL_FAST_CANDIDATE_ONLY" if all(flags.values())
                 else "HISTORICAL_FAST_FAMILY_NOT_PROVEN"}

def run_symbol(symbol,output_dir):
    if symbol not in ASSETS:raise ValueError("NOT_FROZEN_ALT")
    common.apply_locked_3year_window()
    five,independent1,funding,manifest=source.fetch_all(symbol)
    if len(five)!=333216 or len(independent1)!=27768 or len(funding)!=3288 or len(manifest)!=112:
        raise ValueError("PUBLIC_SOURCE_FULL_MONTH_COUNTS_CHANGED")
    resampled={name:old.resample(five,tf) for name,tf in TIMEFRAMES}
    source_discrepancy=old.verify_one_hour_parity(resampled["1h"],independent1)
    if len(resampled["5m"])!=len(five):raise ValueError("FIVE_MINUTE_MODEL_COUNT_MISMATCH")
    independent_build=parent.load_parent()
    a,_=independent_build(resampled["1h"])
    b,_=independent_build([independent1[t] for t in sorted(independent1)])
    divergences=sum(v!=w for candle,v,w in zip(resampled["1h"],a,b) if candle["t"]>=PERIOD_START)
    model={}; gates={}; ledgers={}
    for name,tf in TIMEFRAMES:
        signal_closes=event_sig(resampled[name],tf)
        for horizon,cap in HORIZONS:
            arm_pair={}
            for cost,slip in COSTS:
                key=f"{name}_{horizon}_{cost}"
                m,ledger=run_arm(five,funding,signal_closes,tf,cap,slip)
                model[key]=m
                ledgers[key]=ledger
                arm_pair[cost]=m
                print("FAST_ARM",symbol,key,"return",round(m["marked_return_pct"],4),
                      "n",m["closed_trades"],"PF",round(m["profit_factor"],3) if m["profit_factor"] is not None else None,
                      "weekly",round(m["trades_per_week"],3),flush=True)
            gates[f"{name}_{horizon}"]=historical_gate(arm_pair["BASE"],arm_pair["STRESS"])
    if len(model)!=16 or len(gates)!=8:raise AssertionError("INCOMPLETE_FAST_MATRIX")
    output_dir.mkdir(parents=True,exist_ok=True)
    for key,ledger in ledgers.items():
        if not ledger:continue
        with (output_dir/(key+"_TRADES.csv")).open("w",encoding="utf8",newline="") as f:
            w=csv.DictWriter(f,fieldnames=list(ledger[0]))
            w.writeheader();w.writerows(ledger)
    return {"status":"FAST_CONVEX_FULL_HISTORICAL_DIAGNOSTIC_ONLY",
            "symbol":symbol,"source_counts":{"5m":len(five),"1h":len(independent1),"funding":len(funding)},
            "source_manifest":manifest,"official_1h_source_conflicts":source_discrepancy,
            "source_1h_entry_signal_divergences":divergences,
            "strategy":"UNCHANGED_V5_LONG_ENTRY_WITH_NEW_PREDECLARED_TP_SL_AND_TIMEOUT",
            "timeframes":list(dict(TIMEFRAMES)),"horizons":list(dict(HORIZONS)),
            "cost_scenarios":list(dict(COSTS)),
            "models":model,"scientific_gates":gates,
            "independent_OOS":False,"trading_authority":"NONE"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--symbol",choices=ASSETS,required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    a=p.parse_args()
    a.output_dir.mkdir(parents=True,exist_ok=True)
    out={"symbol":a.symbol,"status":"SOURCE_BLOCKED","trading_authority":"NONE",
         "freeze":"research/fast_convex_8alt_v01/PREOUTCOME_FAST_EXIT_FREEZE_2026-10-13.md"}
    try:out.update(run_symbol(a.symbol,a.output_dir))
    except Exception as exc:out["block_reason"]=type(exc).__name__+":"+str(exc)
    (a.output_dir/"FAST_RESULT.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print("FAST_FINAL",json.dumps({
        "symbol":a.symbol,"status":out["status"],"block":out.get("block_reason"),
        "source_counts":out.get("source_counts"),
        "rows":{k:{"net":round(v["marked_return_pct"],3),
                    "PF":round(v["profit_factor"],3) if v["profit_factor"] is not None else None,
                    "trades":v["closed_trades"],"per_week":round(v["trades_per_week"],3),
                    "annual":v["annual_closed_trades"],
                    "dd":round(v["max_5m_low_model_dd_pct"],3)} for k,v in out.get("models",{}).items()},
        "candidate_gates":{k:v["all_gates_descriptive_pass"] for k,v in out.get("scientific_gates",{}).items()}
    },sort_keys=True),flush=True)
    if out["status"]!="FAST_CONVEX_FULL_HISTORICAL_DIAGNOSTIC_ONLY":
        raise SystemExit(2)
if __name__=="__main__":main()
