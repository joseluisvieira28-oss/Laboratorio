#!/usr/bin/env python3
"""Retrospective SOL1h or BNB4h 2023–2025 early-50% historical model.
Only public checksum-verified archives, original V5 imported at PINNED SHA.
Broker STOP ACK/fills and executable BBO are NOT modelled or claimed.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sys

M5=300_000
END=1767225600000  # 2026-01-01T00Z, EXCLUSIVE. Do not use 2026 market data.
CANDIDATES={"SOLUSDT":("1h",3_600_000,59.38828758,84),
            "BNBUSDT":("4h",14_400_000,27.37792782,28)}
CHECKPOINTS={"SOLUSDT":{"BASE":59.38828758,"STRESS":58.29547408},
             "BNBUSDT":{"BASE":27.37792782,"STRESS":27.05530671}}
FEE=.0008
INITIAL_EQUITY=10000.0
FIXED_STOP_PCT=.04
TRAIL=.12
ACTIVATE=.05
SOURCE_REF="42d6748864dd78b911b5f1fc775ff1950b556d2b"


def old_code():
    root=Path(__file__).resolve().parents[2]/"historical_parent"
    if not (root/"research/convex_8alt_common_2023_25/common_3yr.py").exists():
        raise ValueError("PINNED_PARENT_COMPARATOR_MISSING")
    sys.path.insert(0,str(root))
    from research.convex_8alt_common_2023_25 import common_3yr
    common_3yr.apply_locked_3year_window()
    return common_3yr,common_3yr.old,common_3yr.old.base,common_3yr.old.src


def run_child(symbol,tf, bars_tf, market5, funding, slip_bps, source):
    """Causal exit-policy replay from raw confirmed 5m closes and next 5m opens.
    Exact Parent signals/scheduler/entry only, child dynamic stops NEVER loosen.
    """
    # common_3yr.apply_locked_3year_window() sets historical END and START.
    start=int(datetime(2023,1,1,tzinfo=timezone.utc).timestamp()*1000)
    slip=slip_bps/10000.
    build=source.load_parent()
    signals,_=build(bars_tf)
    decisions={b["t"]+tf for b,flag in zip(bars_tf,signals)
               if flag and start<=b["t"]<END}
    cash=INITIAL_EQUITY
    max_close_dd=max_low_dd=0.
    peak_eq=cash
    pos=None
    enter_at=None
    full_closed=[]
    legs=[]
    entryfees=0.;exitfees=0.;funding_cash=0.
    partial_count=0
    all_entries=0
    seen_signals=0
    skipped=0
    exit_causes=Counter()
    yearly=defaultdict(float)
    trade_id=0
    force_exit_count=0
    blocked_net_count=0
    pending_exits=0

    def close_leg(t,raw,quantity,reason):
        nonlocal cash,pos,exitfees,partial_count
        if pos is None or quantity<=0 or quantity>pos["qty"]*(1+1e-12):
            raise ValueError("CLOSE_QTY_INVALID")
        p=pos
        prior=p["qty"]
        frac=quantity/prior
        fill=raw*(1-slip)
        out_fee=quantity*fill*FEE
        gross=quantity*(fill-p["entry"])
        entry_fee_alloc=p["remain_entry_fee"]*frac
        funding_alloc=p["funding"]*frac
        net=gross-entry_fee_alloc-out_fee+funding_alloc
        cash+=gross-out_fee
        exitfees+=out_fee
        p["qty"]-=quantity
        p["remain_entry_fee"]-=entry_fee_alloc
        p["funding"]-=funding_alloc
        p["net"]+=net
        is_partial=reason=="HALF_REALIZED"
        if is_partial:partial_count+=1
        legs.append({"trade_id":p["id"],"entry_t":p["t"],"exit_t":t+M5,
                     "event_quote_t":t,"qty":quantity,"entry":p["entry"],
                     "exit":fill,"entry_fee_alloc":entry_fee_alloc,
                     "exit_fee":out_fee,"funding_alloc":funding_alloc,
                     "gross_price_pnl":gross,"net":net,"reason":reason})
        exit_causes[reason]+=1
        if cash<=0 or not math.isfinite(cash):raise ValueError("ACCOUNT_INSOLVENCY")
        if not is_partial:
            if abs(p["qty"])>1e-8:
                raise ValueError("NONFINAL_POSITION_QTY")
            item={"trade_id":p["id"],"entry_t":p["t"],"exit_t":t+M5,
                  "net":p["net"],"early_half":p["half"]}
            full_closed.append(item)
            year=datetime.fromtimestamp((t+M5-1)/1000,timezone.utc).year
            yearly[str(year)]+=p["net"]
            pos=None

    for t in range(start,END,M5):
        bar=market5[t]
        opened=False
        if enter_at==t:
            if pos is not None:raise AssertionError("QUEUED_WITH_ACTIVE_POSITION")
            entry=bar["open"]*(1+slip)
            qty=cash*.20/entry
            fee=qty*entry*FEE
            cash-=fee
            entryfees+=fee
            trade_id+=1
            all_entries+=1
            original_stop=entry*(1-FIXED_STOP_PCT)
            # predeclared R CASH includes both sides fees, exit slip, and
            # +5bps notional funding reserve (scenario BASE/STRESS respective slip).
            unit_loss=entry-original_stop*(1-slip)+fee/qty + \
                      original_stop*(1-slip)*FEE +entry*.0005
            pos={"t":t,"id":trade_id,"entry":entry,"qty":qty,
                 "initial_qty":qty,"remain_entry_fee":fee,"net":0.,
                 "funding":0.,"initial_stop":original_stop,
                 "stop":original_stop,"peak":entry,"half":False,
                 "pending_half":False,"force_exit":False,
                 "initial_r_cash":qty*unit_loss}
            enter_at=None
            opened=True
        if pos is not None:
            p=pos
            # Preserve original parent funding-at-event-before-stop semantics.
            if not opened and t in funding:
                funding_move=-p["qty"]*bar["open"]*funding[t]
                cash+=funding_move
                funding_cash+=funding_move
                p["funding"]+=funding_move
                if cash<=0:raise ValueError("FUNDING_INSOLVENCY")
            if bar["open"]<=p["stop"]:
                close_leg(t,bar["open"],p["qty"],"STOP_GAP")
            elif p["force_exit"]:
                force_exit_count+=1
                close_leg(t,bar["open"],p["qty"],"BE_ALREADY_CROSSED_NEXT_OPEN")
            else:
                # No touching completed-bar high to claim immediate sell price.
                # Pending created only by an EARLIER finished 5m candle CLOSE.
                if p["pending_half"] and not p["half"]:
                    cut=p["qty"]*.5
                    sell_fill=bar["open"]*(1-slip)
                    model_cash=cut*(sell_fill-p["entry"]) - \
                               p["remain_entry_fee"]*.5 - cut*sell_fill*FEE + \
                               p["funding"]*.5
                    if model_cash>=p["initial_r_cash"]*.25:
                        close_leg(t,bar["open"],cut,"HALF_REALIZED")
                        p["half"]=True
                    else:
                        blocked_net_count+=1
                    p["pending_half"]=False
                if pos is not None and bar["low"]<=pos["stop"]:
                    close_leg(t,pos["stop"],pos["qty"],"STOP_INTRABAR")
                elif pos is not None:
                    p=pos
                    p["peak"]=max(p["peak"],bar["high"])
                    # Original V5 activation resets to 4% stop on deactivation.
                    # CHILD: enforce monotonicity even before half; never RESET.
                    if (t+M5)%tf==0:
                        close_gain=(bar["close"]-p["entry"])/p["entry"]
                        requested=max(p["initial_stop"],p["peak"]*(1-TRAIL)) \
                                  if close_gain>=ACTIVATE else p["initial_stop"]
                        p["stop"]=max(p["stop"],requested)
                    if p["half"]:
                        # Strict already-paid fee/funding-adjusted partial
                        # remaining-position break-even. Applied only AFTER
                        # this 5m bar finishes; no intrabar BE fill invented.
                        remain=p["qty"]
                        net_breakeven=(remain*p["entry"] +
                             p["remain_entry_fee"]-p["funding"]) / \
                             (remain*(1-FEE)*(1-slip))
                        requested=max(p["stop"],net_breakeven)
                        if requested>=bar["close"]:
                            # Cannot fill past just-observed completed CLOSE:
                            # next 5m opening MARKET proxy will decide.
                            p["force_exit"]=True
                        else:
                            p["stop"]=requested
                    elif bar["close"]-p["entry"]>=p["entry"]-p["initial_stop"]:
                        p["pending_half"]=True

        mark=cash+(pos["qty"]*(bar["close"]-pos["entry"]) if pos else 0)
        lowmark=cash+(pos["qty"]*(bar["low"]*(1-slip)-pos["entry"]) if pos else 0)
        if mark<=0 or lowmark<=0:raise ValueError("MTM_INSOLVENCY")
        peak_eq=max(peak_eq,mark)
        max_close_dd=min(max_close_dd,mark/peak_eq-1)
        max_low_dd=min(max_low_dd,lowmark/peak_eq-1)
        if t+M5 in decisions:
            seen_signals+=1
            if pos is None and enter_at is None:
                enter_at=t+M5+M5
            else:
                skipped+=1
        if enter_at is not None and enter_at<t:raise AssertionError("STALE_ENTRY")

    final_close=market5[END-M5]["close"]
    marked=cash+(pos["qty"]*(final_close-pos["entry"]) if pos else 0)
    complete_net=[v["net"] for v in full_closed]
    positive=sorted([x for x in complete_net if x>0],reverse=True)
    negative=[-x for x in complete_net if x<=0]
    return {
        "symbol":symbol,"tf":tf,"scenario_slip_bps":slip_bps,
        "initial_equity":INITIAL_EQUITY,
        "cash_equity":cash,"marked_equity":marked,
        "cash_return_pct":100*(cash/INITIAL_EQUITY-1),
        "marked_return_pct":100*(marked/INITIAL_EQUITY-1),
        "closed_trades":len(full_closed),"entries":all_entries,
        "partially_realized_positions":partial_count,
        "closed_win_count":len(positive),
        "closed_profit_factor":sum(positive)/sum(negative) if negative else None,
        "exit_legs_count":len(legs),"funding_paid_or_received":funding_cash,
        "entry_fees":entryfees,"exit_fees":exitfees,
        "5m_low_mtm_max_dd_pct":100*max_low_dd,
        "5m_close_mtm_max_dd_pct":100*max_close_dd,
        "year_exit_net_cash":dict(yearly),
        "top3_winner_net":sum(positive[:3]),
        "static_all_closed_minus_top3":sum(complete_net)-sum(positive[:3]),
        "signal_count":seen_signals,"skipped_signals":skipped,
        "pending_half_blocked_by_cost":blocked_net_count,
        "force_exit_next_open_count":force_exit_count,
        "exit_reasons":dict(exit_causes),
        "final_position_open":pos is not None,
        "final_position_qty":pos["qty"] if pos else 0,
        "trade_legs":legs,
        "is_real_exchange_execution":False,
        "independent_oos":False,
        "model_scope":"HISTORICAL_5M_BAR_PROXY_NO_BBO",
    }


def main():
    a=argparse.ArgumentParser()
    a.add_argument("--symbol",choices=tuple(CANDIDATES),required=True)
    a.add_argument("--outdir",type=Path,required=True)
    opt=a.parse_args()
    opt.outdir.mkdir(parents=True,exist_ok=True)
    record={"state":"SOURCE_BLOCKED_OR_PARENT_PARITY_FAIL",
            "symbol":opt.symbol,"original_git_sha":SOURCE_REF,
            "no_orders":True,"independent_OOS":False}
    try:
        orig,old,base,source=old_code()
        price5,price1,fd,manifest=old.fetch_all(opt.symbol)
        tf_name,tf,expected,n=CANDIDATES[opt.symbol]
        bars=base.resample(price5,tf)
        _=base.verify_one_hour_parity(base.resample(price5,3_600_000),price1)
        record["source_counts"]={"5m":len(price5),"1h":len(price1),
                                  "funding":len(fd)}
        if record["source_counts"]!={"5m":333216,"1h":27768,"funding":3288}:
            raise ValueError("SOURCE_COUNTS_DO_NOT_MATCH_PREDECLARED")
        record["public_verified_sha_manifest"]=manifest
        rows={}
        for name,slip in (("BASE",2),("STRESS",5)):
            parent=base.simulate(tf,bars,price5,fd,slip,include_trades=True)
            if abs(parent["marked_return_pct"]-CHECKPOINTS[opt.symbol][name])>0.005:
                raise ValueError("PARENT_MARKED_RETURN_REPRODUCIBILITY_FAIL:"+
                                 name+":"+str(parent["marked_return_pct"]))
            if name=="BASE" and parent["closed_trades"]!=n:
                raise ValueError("PARENT_CLOSED_COUNT_PARITY_FAIL")
            child=run_child(opt.symbol,tf,bars,price5,fd,slip,source)
            rawlegs=child.pop("trade_legs")
            (opt.outdir/(name+"_CHILD_LEGS.json")).write_text(
                json.dumps(rawlegs,indent=2,sort_keys=True)+"\n")
            rows[name]={"parent":parent,"child":child,
                        "delta_marked_pct_points":child["marked_return_pct"]-parent["marked_return_pct"],
                        "delta_cash_pct_points":child["cash_return_pct"]-parent["realized_cash_return_pct"]}
            rows[name]["parent"].pop("trades")
            print("ALT_EARLY_PROFIT_HISTORICAL",opt.symbol,name,
                  json.dumps({"parent_return_pct":parent["marked_return_pct"],
                              "child_return_pct":child["marked_return_pct"],
                              "delta_pp":rows[name]["delta_marked_pct_points"],
                              "child_closed":child["closed_trades"],
                              "partial_count":child["partially_realized_positions"],
                              "parent_closed":parent["closed_trades"],
                              "parent_pf":parent["profit_factor"],
                              "child_pf":child["closed_profit_factor"],
                              "child_low_dd":child["5m_low_mtm_max_dd_pct"]},
                             sort_keys=True),flush=True)
        record.update({"state":"HISTORICAL_DIAGNOSTIC_COMPLETE_NO_OOS",
                       "models":rows,"source_venue":"Binance_Futures_not_MEXC",
                       "broker_stop_ack_proven":False,
                       "venue_exact_funding_settlement":False})
    except Exception as exc:
        record["block"]=type(exc).__name__+":"+str(exc)
        print("ALT_EARLY_PROFIT_SOURCE_OR_PARITY_BLOCK",
              opt.symbol,record["block"],flush=True)
    (opt.outdir/"REPORT.json").write_text(json.dumps(record,sort_keys=True,indent=2)+"\n")
    if record["state"]!="HISTORICAL_DIAGNOSTIC_COMPLETE_NO_OOS":
        raise SystemExit(2)

if __name__=="__main__":
    main()
