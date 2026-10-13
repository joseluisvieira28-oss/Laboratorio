#!/usr/bin/env python3
"""Pure forward-only PAYOFF-FUNDING-NETSTOP-001 portfolio replay.

Not a trading/execution engine: consumes already-validated public hourly
observations. No network calls, exchange credentials, orders or side effects.
Never replay retrospective 2020-2025 outcomes for promotion or target choice.
"""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
import math
import sys

BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE/"payoff_40_10_btc_001"))
sys.path.insert(0,str(BASE/"payoff_funding_netstop_001"))
import engine as core
from net_risk_stop import funding_adjusted_raw_stop

def replay_forward_child(b, funding, marks, fee, slip, begin, end, *,
                         signal_override=None):
    """Recompute each position; prior-funding-adjusted stop applies NEXT hour.

    signal_override is synthetic QA-only and never used by forward orchestrator.
    """
    core.check_bars(b, begin, end)
    if begin < 1791950400000:  # 2026-10-14 00:00:00 UTC, no old outcomes
        raise ValueError("PRE_BOUNDARY_ECONOMIC_REPLAY_FORBIDDEN")
    if end <= begin or not (0 <= fee <= .01 and 0 <= slip <= .01):
        raise ValueError("INVALID_FORWARD_RANGE_OR_COST")
    sig=signal_override if signal_override is not None else core.signals(b)
    if len(sig)!=len(b):raise ValueError("SIGNAL_LENGTH_MISMATCH")
    eq=core.EQUITY0
    peak=eq;peak_mtm=eq;closed_dd=0.;mtm_dd=0.
    position=None;pending=False
    trades=[];signals_count=0;hours_exposed=0;funding_events=0;warning_hours=0
    n_dual=0;funding_stop_updates=0
    open_at_end=None

    def close(t, raw, reason):
        nonlocal eq, position, peak,closed_dd
        p=position
        if p is None:raise ValueError("NO_ACTIVE_POSITION")
        exit_fill=raw*(1-slip)
        exit_fee=p["qty"]*exit_fill*fee
        gross=p["qty"]*(exit_fill-p["fill"])
        pnl=gross-p["entry_fee"]-exit_fee+p["funding_cash"]
        eq += gross-exit_fee
        if eq<=0:raise ValueError("HYPOTHETICAL_EQUITY_INSOLVENT")
        peak=max(eq,peak)
        closed_dd=min(closed_dd,eq/peak-1)
        trades.append({"entry_t":p["entry_t"],"exit_t":t,
          "entry_fill":p["fill"],"exit_fill":exit_fill,
          "qty":p["qty"],"margin":p["margin"],"net_pnl":pnl,
          "margin_net_return":pnl/p["margin"],"reason":reason,
          "fee_entry":p["entry_fee"],"fee_exit":exit_fee,
          "funding_cash":p["funding_cash"],"funding_count":p["funding_count"],
          "hours_held":(t-p["entry_t"])/core.HOUR,
          "equity_after_exit":eq,"marked_liquidation_possible":p["marked_liquidation_possible"]})
        position=None

    for i,k in enumerate(b):
        t=int(k["t"])
        if t<begin or t>end:continue
        # Forward entry was placed only after a complete previous signal bar.
        if pending and position is None:
            entry_fill=k["open"]*(1+slip)
            notional=eq*.20
            qty=notional/entry_fill
            margin=notional/core.LEV
            entry_fee=notional*fee
            eq-=entry_fee
            target,_=core.nominal_bounds(entry_fill)
            stop=funding_adjusted_raw_stop(entry_fill=entry_fill,qty=qty,
                        initial_margin=margin,entry_fee_cash=entry_fee,
                        accrued_funding_cash=0.)
            position={"entry_t":t,"fill":entry_fill,"qty":qty,"margin":margin,
               "entry_fee":entry_fee,"funding_cash":0.,"funding_count":0,
               "target":target,"stop":stop,
               "marked_liquidation_possible":False}
            pending=False
        p=position
        # Previously committed stop/target at OPEN; funding cannot rewrite them retroactively.
        if p is not None:
            if t >= p["entry_t"]+core.EXPIRE:
                close(t,k["open"],"TIME_EXIT")
            elif k["open"] <= p["stop"]:
                close(t,k["open"],"NET_STOP_GAP")
            elif k["open"] >= p["target"]:
                close(t,k["open"],"TARGET_GAP")
        p=position
        # Funding at bar boundary is applied only to already-carried positions.
        # Its stop adjustment becomes effective on the FOLLOWING bar.
        if p is not None and p["entry_t"]<t and t in funding:
            if t not in marks:raise ValueError("FUNDING_MARK_UNAVAILABLE")
            amount=-p["qty"]*float(marks[t]["open"])*float(funding[t])
            if not math.isfinite(amount):raise ValueError("FUNDING_NONFINITE")
            p["funding_cash"]+=amount
            p["funding_count"]+=1
            eq+=amount
            funding_events+=1
            if eq<=0:raise ValueError("HYPOTHETICAL_FUNDING_INSOLVENT")
        p=position
        if p is not None:
            hours_exposed+=1
            m=marks.get(t)
            if m is None:raise ValueError("MARK_BAR_MISSING")
            illustrative_liq=p["fill"]*(1-1/core.LEV+core.MAINT_PROXY+fee)
            if m["low"]<=illustrative_liq:
                warning_hours+=1;p["marked_liquidation_possible"]=True
            hit_stop=k["low"]<=p["stop"]
            hit_target=k["high"]>=p["target"]
            if hit_stop and hit_target:
                n_dual+=1
                close(t,p["stop"],"AMBIGUOUS_STOP_FIRST")
            elif hit_stop:
                close(t,p["stop"],"NET_STOP_TOUCH")
            elif hit_target:
                close(t,p["target"],"TARGET")
        p=position
        if p is not None:
            next_stop=funding_adjusted_raw_stop(entry_fill=p["fill"],qty=p["qty"],
                      initial_margin=p["margin"],entry_fee_cash=p["entry_fee"],
                      accrued_funding_cash=p["funding_cash"])
            if not math.isclose(next_stop,p["stop"],rel_tol=0,abs_tol=1e-10):
                funding_stop_updates+=1
            p["stop"]=next_stop
        if position is None and sig[i]:
            pending=True;signals_count+=1
        p=position
        if p is not None:
            marked=eq+p["qty"]*(k["close"]-p["fill"])-fee*p["qty"]*k["close"]
            if marked<=0:raise ValueError("MARKED_EQUITY_INSOLVENT")
            peak_mtm=max(peak_mtm,marked);mtm_dd=min(mtm_dd,marked/peak_mtm-1)
        else:
            peak_mtm=max(peak_mtm,eq);mtm_dd=min(mtm_dd,eq/peak_mtm-1)

    if position is not None:
        last_mark=next(x["close"] for x in reversed(b) if x["t"]==end)
        open_at_end={"entry_t":position["entry_t"],"status":"OPEN_UNRESOLVED",
                     "last_mark":last_mark,"funding_cash":position["funding_cash"]}
    wins=[x for x in trades if x["net_pnl"]>0]
    losses=[x for x in trades if x["net_pnl"]<0]
    gross_win=sum(x["net_pnl"] for x in wins)
    gross_loss=-sum(x["net_pnl"] for x in losses)
    return {"model":"PAYOFF_FUNDING_NETSTOP_001","science":"PROSPECTIVE_RESEARCH_ONLY",
      "live_trading_authority":"NONE","initial_equity":core.EQUITY0,
      "closed_equity":eq,"closed_equity_return":eq/core.EQUITY0-1,
      "closed_equity_max_dd":closed_dd,"approx_mtm_max_dd":mtm_dd,
      "closed":len(trades),"wins":len(wins),"losses":len(losses),
      "profit_factor":gross_win/gross_loss if gross_loss>0 else None,
      "funding_events":funding_events,"hours_exposed":hours_exposed,
      "mark_liquidation_warning_hours":warning_hours,
      "same_bar_ambiguous_stop_first":n_dual,
      "funding_related_stop_updates":funding_stop_updates,
      "unresolved_at_cutoff":[open_at_end] if open_at_end else [],
      "trade_ledger":trades}
