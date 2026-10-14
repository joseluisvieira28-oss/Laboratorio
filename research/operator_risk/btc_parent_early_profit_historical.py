#!/usr/bin/env python3
"""Retrospective BTC-CONVEX 1h Parent vs EARLY-PROFIT-001 bar-open proxy.

Unchanged signal math imported from prior pinned PR#194. This is NOT BBO trading,
NOT independent OOS, NOT real broker STOP proof. Science/rules in candidate freeze.
"""
from __future__ import annotations
import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path

def load_parent():
    import sys
    root = Path(__file__).resolve().parents[2] / "historical_parent" / "research" / "payoff_40_10_btc_001"
    if not root.exists():
        raise RuntimeError("PINNED_PARENT_CHECKOUT_MISSING")
    sys.path.insert(0,str(root))
    import engine as parent
    return parent

def replay_child(b, funding, marks, fee, slip, parent):
    """Use only certified 1h-close signals and NEXT-open exit witnesses.

    PRICE_OHLC_PROXY_ONLY: no executable BBO, no tick/lot/funding exact settlement
    mark. Model partial fill, delayed remainder BE, full ledger cash and fees.
    """
    parent.check_bars(b,parent.START,parent.FINISH)
    sig=parent.signals(b)
    eq=parent.EQUITY0
    p=None
    pending=False
    legs=[]
    trade_count=0
    partials=0
    closed=0
    net_pos=0
    stop_first_ambiguous=0
    pending_take_count=0
    year=None
    year_start=None
    yearly={}
    max_dd=0.
    mtm_peak=eq
    completed_pos=[]
    closed_fees=0.
    entry_fees=0.
    funding_total=0.
    all_trade_funding=0.
    episode_id=0
    exit_count={}
    signal_count=0

    def exit_lot(t, raw, reason, quantity, final):
        nonlocal p,eq,closed,net_pos,closed_fees
        assert p is not None and 0<quantity<=p["qty"]
        total_before=p["qty"]
        share=quantity/total_before
        fill=raw*(1-slip)
        fee_cash=quantity*fill*fee
        price_pnl=quantity*(fill-p["fill"])
        allocated_entry_fee=p["remaining_entry_fee"]*share
        allocated_funding=p["funding_cash"]*share
        pnl=price_pnl-allocated_entry_fee-fee_cash+allocated_funding
        eq+=price_pnl-fee_cash
        closed_fees+=fee_cash
        leg={"entry_t":p["entry_t"],"exit_t":t,"trade_id":p["trade_id"],
             "quantity":quantity,"reason":reason,"entry_price":p["fill"],
             "exit_price":fill,"gross":price_pnl,
             "entry_fee_alloc":allocated_entry_fee,"exit_fee":fee_cash,
             "funding_alloc":allocated_funding,"net":pnl,"is_final":bool(final)}
        legs.append(leg)
        p["qty"]-=quantity
        p["remaining_entry_fee"]-=allocated_entry_fee
        p["funding_cash"]-=allocated_funding
        p["net_realized"]+=pnl
        if final:
            if abs(p["qty"])>max(1e-9,total_before*1e-8):
                raise ValueError("FINAL_POSITION_QTY_NOT_CLOSED")
            completed_pos.append({"trade_id":p["trade_id"],"net":p["net_realized"],
                                  "entry_t":p["entry_t"],"exit_t":t,
                                  "early_half":p["took_half"]})
            closed+=1
            if p["net_realized"]>0:net_pos+=1
            p=None
        if eq<=0 or not math.isfinite(eq):
            raise ValueError("CHILD_EQUITY_INSOLVENT")
        exit_count[reason]=exit_count.get(reason,0)+1

    for i,k in enumerate(b):
        t=k["t"]
        if t<parent.START or t>parent.FINISH:
            continue
        yy=datetime.fromtimestamp(t/1000,timezone.utc).year
        if year is None:
            year=yy;year_start=eq
        if year!=yy:
            yearly[str(year)]=eq/year_start-1
            year=yy;year_start=eq

        if pending and p is None:
            fill=k["open"]*(1+slip)
            notional=eq*.20
            qty=notional/fill
            fee_cash=qty*fill*fee
            eq-=fee_cash;entry_fees+=fee_cash
            episode_id+=1;trade_count+=1
            p={"trade_id":episode_id,"entry_t":t,"fill":fill,"qty":qty,
               "initial_qty":qty,"initial_stop":fill*.96,"stop":fill*.96,
               "peak":fill,"funding_cash":0.,"remaining_entry_fee":fee_cash,
               "net_realized":0.,"took_half":False,"pending_take":False,
               "first_partial_t":None,"force_exit_next_open":False}
            stop_price=fill*.96
            unit_r=(fill-stop_price*(1-slip))+(fill*fee)+(stop_price*(1-slip)*fee)+(fill*.0005)
            p["original_r_cash"]=qty*unit_r
            pending=False

        # Original Parent gap stop precedes funding. Do not pretend exit at stop
        # if the bar opens below it. No partial action when stop already crossed.
        if p and k["open"]<=p["stop"]:
            exit_lot(t,k["open"],"STOP_GAP",p["qty"],True)
        elif p and p["force_exit_next_open"]:
            # A stop already crossed at the LAST completed close cannot get
            # an imaginary fill at that historic close; sell NEXT hour open.
            exit_lot(t,k["open"],"BREAKEVEN_CROSSED_NEXT_OPEN",p["qty"],True)

        # Partial fills may only be proposed at the NEXT 1h OPEN after a
        # qualifying PREVIOUS 1h CLOSE. The prior stop remains until next bar.
        if p is not None and p["pending_take"] and not p["took_half"]:
            full_qty=p["qty"]
            # Simulation of 50% decimal BTC; actual exchange min lot unproven
            take=full_qty*.5
            raw=k["open"]
            fill=raw*(1-slip)
            prorata=take/full_qty
            net_est=(fill-p["fill"])*take -take*fill*fee \
                    -p["remaining_entry_fee"]*prorata+p["funding_cash"]*prorata
            if net_est>=.25*p["original_r_cash"]:
                exit_lot(t,raw,"EARLY_HALF",take,False)
                partials+=1
                p["took_half"]=True
                p["first_partial_t"]=t
                p["pending_take"]=False
            else:
                p["pending_take"]=False
        if p is not None and t in funding and p["entry_t"]<t:
            if t not in marks:
                raise ValueError("MISSING_FUNDING_MARK_PROXY")
            cash=-p["qty"]*float(marks[t]["open"])*funding[t]
            p["funding_cash"]+=cash
            eq+=cash
            funding_total+=cash
            all_trade_funding+=cash
            if eq<=0:raise ValueError("FUNDING_EQUITY_INSOLVENT")
        if p is not None:
            if t not in marks:raise ValueError("MISSING_MARK_PRICE")
            if k["low"]<=p["stop"]:
                exit_lot(t,p["stop"],"STOP",p["qty"],True)
            else:
                # Only after the fully finished bar's next boundary may we
                # tighten stop; this avoids optimistic within-bar stop raise.
                p["peak"]=max(p["peak"],k["high"])
                gain=(k["close"]-p["fill"])/p["fill"]
                parent_stop=max(p["initial_stop"],p["peak"]*.88) \
                    if gain>=.05 else p["initial_stop"]
                if p["took_half"]:
                    # Fee/funding aware break-even for currently remaining
                    # position; this is idealized ACK by following hour only.
                    q=p["qty"]
                    modeled_be=(q*p["fill"]+p["remaining_entry_fee"]-p["funding_cash"]) \
                              / (q*(1-fee)*(1-slip))
                    new_stop=max(p["stop"],parent_stop,modeled_be)
                    # Break-even candidate not executable at past completed
                    # close. If already crossed, schedule NEXT-hour market exit
                    # with observed next-open gap; preserve original broker stop.
                    if new_stop>=k["close"]:
                        p["force_exit_next_open"]=True
                    else:
                        p["stop"]=new_stop
                else:
                    # Operator stop invariant applies even BEFORE partial:
                    # never allow Parent's activation/deactivation reset
                    # to weaken an already-tightened CHILD protective stop.
                    p["stop"]=max(p["stop"],parent_stop)
                    if k["close"]-p["fill"]>=p["fill"]-p["initial_stop"]:
                        p["pending_take"]=True
                        pending_take_count+=1

        if p is None and sig[i]:
            pending=True
            signal_count+=1
        # Conservative hourly close mark-to-market, without real executable
        # quotes; no intra-hour liquidation floor is guaranteed.
        mtm=eq
        if p is not None:
            mtm+=p["qty"]*(k["close"]-p["fill"])-p["qty"]*k["close"]*fee
        if mtm<=0:
            raise ValueError("CHILD_MTM_INSOLVENT")
        mtm_peak=max(mtm_peak,mtm)
        max_dd=min(max_dd,mtm/mtm_peak-1)
    if year is not None:
        yearly[str(year)]=eq/year_start-1
    winners=[x["net"] for x in completed_pos if x["net"]>0]
    losers=[-x["net"] for x in completed_pos if x["net"]<0]
    last=b[-1]["close"]
    terminal=eq+(p["qty"]*(last-p["fill"])-p["qty"]*last*fee if p else 0)
    completed_nets=sorted(winners,reverse=True)
    return {
        "state":"HISTORICAL_BAR_OPEN_PROXY_DIAGNOSTIC_ONLY",
        "parental_comparison":"ORIGINAL_SIGNAL_UNCHANGED",
        "capital":parent.EQUITY0,
        "closed_equity":eq,
        "return_pct":100*(eq/parent.EQUITY0-1),
        "terminal_equity_proxy":terminal,
        "terminal_return_pct":100*(terminal/parent.EQUITY0-1),
        "closed_positions":closed,
        "entries":trade_count,
        "profitable_closed_positions":net_pos,
        "partial_50pct_count":partials,
        "candidate_qualified_1h_close_count":pending_take_count,
        "exit_leg_count":len(legs),
        "full_exit_count":sum(l["is_final"] for l in legs),
        "closed_position_net_profit_factor":sum(winners)/sum(losers) if losers else None,
        "closed_positions_net":sum(x["net"] for x in completed_pos),
        "top3_net_winners":sum(completed_nets[:3]),
        "closed_net_excluding_top3_static":sum(x["net"] for x in completed_pos)-sum(completed_nets[:3]),
        "paid_opening_fees":entry_fees,
        "paid_closing_fees":closed_fees,
        "funding_total":funding_total,
        "hourly_close_mtm_max_dd_pct":max_dd*100,
        "years_cash_return_proxy":yearly,
        "exit_counts":exit_count,
        "open_position":p is not None,
        "open_qty":p["qty"] if p else 0,
        "source_implementation_caveats":[
            "1h bar close signal / next 1h open is NOT original fresh executable BBO",
            "broker stop/partial order ACK simulated, never actually verified",
            "funding 1h mark-open proxy, missing true settlement marks",
            "within-hour stop exit always before new partial decision",
            "minimum contract round/down unavailable on actual MEXC account",
            "2020-25 historical already viewed elsewhere, zero independent OOS",
        ],
        "closed_leg_ledger":legs,
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    source=json.loads(args.source.read_text())
    if source.get("status")!="SOURCE_OK":
        raise SystemExit("SOURCE_BLOCKED")
    parent=load_parent()
    hours=source["bars"]
    rates={int(t):float(v) for t,v in source["funding"].items()}
    marks={int(t):v for t,v in source["marks"].items()}
    out={"scope":"RETROSPECTIVE_ONLY","no_trading":True,
         "child":"HALF_AT_PLUS_1R_CONFIRMED_HOURLY_CLOSE_NEXT_OPEN_PROXY",
         "parent_source_ref":"PAYOFF PR194 commit 2e68dbce5705e4d285f6805933768878fb34dea1",
         "scenarios":{}}
    for name,(fee,slip) in parent.CONFIGS.items():
        baseline=parent.replay(hours,rates,marks,"PARENT",fee,slip)
        if name=="BASE":
            if baseline["trades_closed"]!=89 or not .30<baseline["closed_equity_return"]<.35:
                raise ValueError("PARENT_BASE_CONTROL_NOT_REPRODUCED")
        if name=="STRESS":
            if not .28<baseline["closed_equity_return"]<.33:
                raise ValueError("PARENT_STRESS_CONTROL_NOT_REPRODUCED")
        kid=replay_child(hours,rates,marks,fee,slip,parent)
        out["scenarios"][name]={
            "parent_control":{k:v for k,v in baseline.items() if k!="trade_ledger"},
            "child":{k:v for k,v in kid.items() if k!="closed_leg_ledger"},
            "child_minus_parent_closed_equity_pct_points":kid["return_pct"]-baseline["closed_equity_return"]*100,
            "exact_terminal_net_comparison":"UNRESOLVED_DIFFERENT_END_POSITIONS_NO_FAKE_MARK_PARITY",
        }
        (args.output.parent/(name+"_child_legs.json")).write_text(
            json.dumps(kid["closed_leg_ledger"],sort_keys=True))
        print("HIST_PROXY_EXIT_COMPARISON",name,json.dumps({
            "parent_closed":baseline["trades_closed"],
            "parent_return_pct":baseline["closed_equity_return"]*100,
            "child_closed":kid["closed_positions"],
            "child_return_pct":kid["return_pct"],
            "child_terminal_pct":kid["terminal_return_pct"],
            "child_partials":kid["partial_50pct_count"],
            "parent_pf":baseline["profit_factor"],
            "child_pf":kid["closed_position_net_profit_factor"],
            "closed_eq_delta_pp":out["scenarios"][name]["child_minus_parent_closed_equity_pct_points"],
        },sort_keys=True),flush=True)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
if __name__=="__main__":
    main()
