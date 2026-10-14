#!/usr/bin/env python3
"""BTC PAYOFF 4R vs exact same SIGNAL with early 50%-at-+1R and remaining net BE.

2020-25 already-seen public source; retrospective only, no 2026 or live broker calls.
"""
from __future__ import annotations
import argparse,json,math
from pathlib import Path
from datetime import datetime,timezone

HOUR=3600_000
PUBLIC_PARENT_COMMIT="2e68dbce5705e4d285f6805933768878fb34dea1"


def pinned_parent():
    from btc_parent_early_profit_historical import load_parent
    return load_parent()


def child_replay(b,funding,marks,parent,fee,slip):
    sig=parent.signals(b)
    eq=parent.EQUITY0
    p=None
    pending=False
    peak_mtm=eq
    dd_mtm=0.
    completed=[]
    legs=[]
    entry_fees=0.;exit_fees=0.;funding_paid=0.
    partial_count=0
    entered=0
    cum_signals=0
    exit_reasons={}
    year=None; year_first=None; yearly={}
    liquidation_warning_hours=0
    refused_half=0
    force_flat_count=0

    def exit_leg(t,raw,reason,quantity):
        nonlocal p,eq,exit_fees,partial_count
        if p is None or quantity<=0 or quantity>p["qty"]*(1+1e-12):
            raise ValueError("CLOSE_QTY_UNSAFE")
        prior=p["qty"]
        fraction=quantity/prior
        exitfill=raw*(1-slip)
        closing_fee=exitfill*quantity*fee
        price_net=quantity*(exitfill-p["entry"])
        alloc_fee=p["remaining_fee"]*fraction
        alloc_funding=p["funding"]*fraction
        pnl=price_net-alloc_fee-closing_fee+alloc_funding
        eq+=price_net-closing_fee
        exit_fees+=closing_fee
        p["qty"]-=quantity
        p["remaining_fee"]-=alloc_fee
        p["funding"]-=alloc_funding
        p["closed_net"]+=pnl
        legs.append({"id":p["id"],"entry_t":p["entry_t"],"exit_t":t,
                     "reason":reason,"qty":quantity,"entry":p["entry"],
                     "exit":exitfill,"price_pnl":price_net,
                     "entry_fee_prorata":alloc_fee,"exit_fee":closing_fee,
                     "funding_prorata":alloc_funding,"net":pnl})
        exit_reasons[reason]=exit_reasons.get(reason,0)+1
        if eq<=0: raise ValueError("INSOLVENT")
        if reason=="EARLY_HALF":
            partial_count+=1
            return
        if abs(p["qty"])>1e-8:
            raise ValueError("INCOMPLETE_FINAL_CLOSURE")
        completed.append({"id":p["id"],"net":p["closed_net"],
                          "entry_t":p["entry_t"],"exit_t":t,"early_half":p["did_half"]})
        p=None

    for i,k in enumerate(b):
        t=k["t"]
        if not(parent.START<=t<=parent.FINISH):
            continue
        yy=datetime.fromtimestamp(t/1000,timezone.utc).year
        if year is None:year=yy;year_first=eq
        if yy!=year:
            yearly[str(year)]=eq/year_first-1
            year=yy;year_first=eq

        if pending and p is None:
            fill=k["open"]*(1+slip)
            qty=eq*.20/fill
            orig_fee=qty*fill*fee
            eq-=orig_fee;entry_fees+=orig_fee
            target,stop=parent.nominal_bounds(fill)
            if not (stop<fill<target):raise ValueError("PAYOFF_BOUNDS_INVERTED")
            entered+=1
            unit_loss=fill-stop*(1-slip)+fill*fee+stop*(1-slip)*fee+fill*.0005
            p={"id":entered,"entry_t":t,"entry":fill,"qty":qty,
               "orig_qty":qty,"remaining_fee":orig_fee,"funding":0.,
               "closed_net":0.,"target":target,"stop":stop,
               "initial_stop":stop,"initial_r_cash":qty*unit_loss,
               "did_half":False,"pending_half":False,
               "force_exit_next":False}
            pending=False
        if p is not None:
            if t>=p["entry_t"]+parent.EXPIRE:
                exit_leg(t,k["open"],"TIME_EXIT",p["qty"])
            elif k["open"]<=p["stop"]:
                exit_leg(t,k["open"],"STOP_GAP",p["qty"])
            elif k["open"]>=p["target"]:
                exit_leg(t,k["open"],"TARGET_GAP",p["qty"])
            elif p["force_exit_next"]:
                force_flat_count+=1
                exit_leg(t,k["open"],"NET_BE_CROSSED_NEXT_OPEN",p["qty"])

        if p is not None and t in funding and p["entry_t"]<t:
            if t not in marks:raise ValueError("FUNDING_MARK_OPEN_PROXY_MISSING")
            paid=-p["qty"]*float(marks[t]["open"])*funding[t]
            eq+=paid
            p["funding"]+=paid
            funding_paid+=paid
            if eq<=0:raise ValueError("FUNDING_INSOLVENCY")

        if p is not None:
            if t not in marks: raise ValueError("MARK_BAR_MISSING")
            # Maint margin model is inherited warning only, NOT venue liquidation.
            liq_proxy=p["entry"]*(1-1/parent.LEV+parent.MAINT_PROXY+fee)
            if float(marks[t]["low"])<=liq_proxy:
                liquidation_warning_hours+=1

            if p["pending_half"] and not p["did_half"]:
                half=p["qty"]*.5
                sell=k["open"]*(1-slip)
                expected_net=half*(sell-p["entry"]) -p["remaining_fee"]*.5 \
                        +p["funding"]*.5-half*sell*fee
                if expected_net>=p["initial_r_cash"]*.25:
                    exit_leg(t,k["open"],"EARLY_HALF",half)
                    p["did_half"]=True
                else:
                    refused_half+=1
                p["pending_half"]=False

            if p is not None:
                stop_hit=k["low"]<=p["stop"]
                target_hit=k["high"]>=p["target"]
                # Original PAYOFF ambiguous intrabar ordering = STOP FIRST.
                if stop_hit:
                    exit_leg(t,p["stop"],"STOP_FIRST" if target_hit else "STOP",p["qty"])
                elif target_hit:
                    exit_leg(t,p["target"],"TARGET",p["qty"])
                elif p["did_half"]:
                    q=p["qty"]
                    be=(q*p["entry"]+p["remaining_fee"]-p["funding"]) / \
                       (q*(1-fee)*(1-slip))
                    candidate=max(p["stop"],be)
                    # Only completed hour witness: no fabricated previous CLOSE exit.
                    if candidate>=k["close"]:
                        p["force_exit_next"]=True
                    else:
                        p["stop"]=candidate
                elif k["close"]-p["entry"]>=p["entry"]-p["initial_stop"]:
                    p["pending_half"]=True

        if p is None and sig[i]:
            pending=True
            cum_signals+=1

        mark=eq+(p["qty"]*(k["close"]-p["entry"])-p["qty"]*k["close"]*fee
                 if p is not None else 0)
        if mark<=0:raise ValueError("MTM_INSOLVENCY")
        peak_mtm=max(peak_mtm,mark)
        dd_mtm=min(dd_mtm,mark/peak_mtm-1)
    if year is not None:yearly[str(year)]=eq/year_first-1
    last=next(x["close"] for x in reversed(b) if x["t"]==parent.FINISH)
    unreal=(p["qty"]*(last-p["entry"])-p["qty"]*last*fee-p["remaining_fee"]+
            p["funding"] if p else 0)
    closed_nets=[tr["net"] for tr in completed]
    gains=sorted([x for x in closed_nets if x>0],reverse=True)
    losses=[-x for x in closed_nets if x<=0]
    return {
        "capital":parent.EQUITY0,
        "closed_equity_usdt":eq,
        "closed_equity_return_pct":100*(eq/parent.EQUITY0-1),
        "marked_terminal_equity_usdt":eq+unreal,
        "marked_terminal_return_pct":100*((eq+unreal)/parent.EQUITY0-1),
        "closed_positions":len(completed),
        "wins":len(gains),
        "closed_net_profit_factor":sum(gains)/sum(losses) if losses else None,
        "entries":entered,"realized_50pct_count":partial_count,
        "refused_partial_at_next_open_count":refused_half,
        "forced_stop_next_open_count":force_flat_count,
        "closed_net_pnl_usdt":sum(closed_nets),
        "top3_net":sum(gains[:3]),
        "static_closed_net_minus_top3":sum(closed_nets)-sum(gains[:3]),
        "max_hourly_close_mtm_dd_pct":100*dd_mtm,
        "fee_entry_total":entry_fees,"fee_exit_total":exit_fees,
        "signed_funding_total":funding_paid,
        "cash_returns_per_year":yearly,"exit_reasons":exit_reasons,
        "warning_liq_proxy_hours":liquidation_warning_hours,
        "unresolved_at_cutoff":p is not None,
        "unresolved_unrealized_pnl_if_last_close":unreal if p is not None else None,
        "full_closed_trade_ledger":completed,"closed_exit_leg_ledger":legs,
        "historical_BBO_not_available":True,"independent_OOS":False,"real_broker_ACK":False,
        "study":"RETROSPECTIVE_OHLC_NEXT_HOUR_OPEN_ONLY",
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args();a.output.parent.mkdir(parents=True,exist_ok=True)
    out={"status":"SOURCE_OR_PARENT_PARITY_BLOCKED","parent_commit":PUBLIC_PARENT_COMMIT,
         "live_authority":False,"independent_oos":False}
    try:
        p=pinned_parent()
        j=json.loads(a.source.read_text())
        if j.get("status")!="SOURCE_OK":raise ValueError("PUBLISHER_SOURCE_NOT_VERIFIED")
        if j.get("counts",{}).get("market")!=51864:raise ValueError("MARKET_COUNT_CHANGED")
        market=j["bars"];rates={int(t):float(v) for t,v in j["funding"].items()}
        marks={int(t):v for t,v in j["marks"].items()}
        if len(marks)!=51864 or len(rates)<6000:raise ValueError("MISSING_MARK_OR_FUNDING")
        out["source_manifest"]=j["manifests"]
        out["source_counts"]=j["counts"]
        out["scenarios"]={}
        for scenario,(fee,slip) in p.CONFIGS.items():
            parent=p.replay(market,rates,marks,"PAYOFF",fee,slip)
            if parent["trades_closed"]!=111 or not (0.25<parent["closed_equity_return"]<0.29):
                raise ValueError("FROZEN_4R_PARENT_PARITY_"+scenario)
            child=child_replay(market,rates,marks,p,fee,slip)
            legs=child.pop("closed_exit_leg_ledger")
            trades=child.pop("full_closed_trade_ledger")
            (a.output.parent/(scenario+"_exit_legs.json")).write_text(json.dumps(legs,sort_keys=True))
            (a.output.parent/(scenario+"_finished_trades.json")).write_text(json.dumps(trades,sort_keys=True))
            out["scenarios"][scenario]={
                "parent":{k:v for k,v in parent.items() if k!="trade_ledger"},
                "child":child,
                "delta_closed_eq_pp":child["closed_equity_return_pct"]-100*parent["closed_equity_return"],
            }
            print("PAYOFF_4R_EARLY_HISTORY",scenario,json.dumps({
                "parent_closed_eq_pct":100*parent["closed_equity_return"],
                "child_closed_eq_pct":child["closed_equity_return_pct"],
                "delta_pp":out["scenarios"][scenario]["delta_closed_eq_pp"],
                "parent_pf":parent["profit_factor"],"child_pf":child["closed_net_profit_factor"],
                "parent_closed":parent["trades_closed"],"child_closed":child["closed_positions"],
                "partial_count":child["realized_50pct_count"],
                "child_drawdown":child["max_hourly_close_mtm_dd_pct"]
            },sort_keys=True),flush=True)
        out["status"]="HISTORICAL_SOURCE_PASS_NO_OOS_NO_EXECUTION"
    except Exception as exc:
        out["block"]=type(exc).__name__+":"+str(exc)
        print("PAYOFF_4R_BLOCK",out["block"],flush=True)
    a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    if out["status"]!="HISTORICAL_SOURCE_PASS_NO_OOS_NO_EXECUTION":raise SystemExit(2)

if __name__=="__main__":main()
