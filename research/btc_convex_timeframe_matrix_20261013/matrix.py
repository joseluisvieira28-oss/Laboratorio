#!/usr/bin/env python3
"""BTC-CONVEX frozen matched TF 15m,30m,1h,4h historical matrix, 2021-2025.
Pure retrospective *research*; no private endpoints, no orders or 2026 outcomes.
Borrow checksum-verified public archive parsing and recovered-parent indicators from
unmodified existing modules in the same research branch.
"""
from __future__ import annotations
import csv
import json
import math
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path

from research.btc_convex_multifront_v01 import retrospective_diagnostic as src

M5=300_000
HOUR=3_600_000
TFS=(("15m",3*M5),("30m",6*M5),("1h",12*M5),("4h",48*M5))
START=src.START_MS
END=src.STOP_MS
PRE=int(datetime(2020,11,1,tzinfo=timezone.utc).timestamp()*1000)
FEE=0.0008
STOP=0.04
TRAIL=0.12
ACTIVATE=0.05
PCT_NOTIONAL=0.20
ROOT=Path(__file__).resolve().parent
OUT=ROOT/"receipts"
MONTHS=(lambda: [(f"{y:04}-{m:02}") for y in range(2020,2026)
                  for m in range(1,13) if (y,m)>=(2020,11) and (y,m)<=(2025,12)])()

def fetch_sources():
    market5={};market1={};funding={};manifest=[]
    for ym in MONTHS:
        for kind in ("5m","1h")+(("fundingRate",) if ym>="2021-01" else ()):
            raw,receipt=src.collect(kind,ym)
            part=src.funding_records(raw) if kind=="fundingRate" else src.candles(raw,M5 if kind=="5m" else HOUR)
            target={"5m":market5,"1h":market1,"fundingRate":funding}[kind]
            if target.keys()&part.keys():raise ValueError("DUPLICATE_MONTH_SOURCE:"+kind+ym)
            target.update(part)
            manifest.append(receipt)
        print("SOURCE_MONTH_OK",ym,flush=True)
    for title,source,step in (("5m",market5,M5),("1h",market1,HOUR)):
        count=(END-PRE)//step
        if len(source)!=count or set(source)!=set(range(PRE,END,step)):
            raise ValueError("SOURCE_GAP_OR_OUTSIDE:"+title+":"+str(len(source))+"/"+str(count))
    if len(funding)<4000:raise ValueError("FUNDING_COVERAGE_BLOCKED")
    if any(t<START or t>=END for t in funding):
        raise ValueError("FUNDING_OUT_OF_PERIOD")
    return market5,market1,funding,manifest

def resample(market5,tf):
    if tf%M5:raise ValueError("NON_MULTIPLE")
    n=tf//M5
    out=[]
    prev=None
    row=None
    count=0
    for t in sorted(market5):
        b=market5[t]
        group=t//tf*tf
        if group!=prev:
            if prev is not None:
                if count!=n:raise ValueError("INCOMPLETE_AGGREGATION")
                out.append(row)
            if group!=t:raise ValueError("LEFT_ALIGN_BLOCKED")
            row={"t":group,"open":b["open"],"high":b["high"],"low":b["low"],
                 "close":b["close"],"volume":0.0}
            prev=group
            count=0
        if t!=group+count*M5:raise ValueError("AGGREGATION_GAP")
        row["high"]=max(row["high"],b["high"])
        row["low"]=min(row["low"],b["low"])
        row["close"]=b["close"]
        row["volume"]+=b["volume"]
        count+=1
    if count!=n:raise ValueError("LAST_AGGREGATION_INCOMPLETE")
    out.append(row)
    expected=(END-PRE)//tf
    if len(out)!=expected:raise ValueError("AGGREGATION_COUNT_BLOCKED")
    return out

def verify_one_hour_parity(resampled,official):
    if len(resampled)!=len(official):raise ValueError("ONE_HOUR_PARITY_COUNT")
    maxdiff=0.0
    for bar in resampled:
        expected=official.get(bar["t"])
        if expected is None:raise ValueError("ONE_HOUR_PARITY_TIME")
        for key in ("open","high","low","close","volume"):
            observed,reference=bar[key],expected[key]
            delta=abs(observed-reference)
            maxdiff=max(maxdiff,delta)
            if not math.isclose(observed,reference,rel_tol=0.000001,abs_tol=0.000001):
                raise ValueError(f"ONE_HOUR_PARITY_MISMATCH:{bar['t']}:{key}:{observed}:{reference}")
    return {"checked":len(resampled),"max_abs_difference":maxdiff,"status":"PASS"}

def simulate(timeframe,bars_tf,market5,funding,slipbps,*,include_trades=False):
    """All 5m bars are closed before TF trailing decisions; stop cannot peek at TF high."""
    if timeframe%M5 or timeframe<3*M5:raise ValueError("TF_NOT_AUTHORIZED")
    if not (slipbps>=0 and math.isfinite(slipbps)):raise ValueError("BAD_SLIP")
    sig,_=src.load_parent()(bars_tf)
    decisions={b["t"]+timeframe for b,s in zip(bars_tf,sig)
               if s and START<=b["t"]<END}
    cash=10000.0
    high_water=cash
    max_close_dd=0.0
    max_low_dd=0.0
    open_pos=None
    enter_at=None
    trades=[]
    starts=0
    blocked_slot=0
    signals_count=0
    all_fees=0.0
    all_funding=0.0
    starts_seen=set()
    names=Counter()
    yearly=defaultdict(float)
    slip=slipbps/10000.
    for t in range(START,END,M5):
        b=market5[t]
        # A previously completed signal is acted on at exactly its predeclared
        # next eligible 5-minute bar opening (not at the timeframe close).
        opened_this_bar=False
        if enter_at==t:
            if open_pos is not None:raise AssertionError("QUEUE_WITH_ACTIVE_SLOT")
            entry=b["open"]*(1+slip)
            qty=(cash*PCT_NOTIONAL)/entry
            fee=qty*entry*FEE
            cash-=fee
            all_fees+=fee
            open_pos={"t":t,"entry":entry,"qty":qty,"entry_fee":fee,
                      "initial_stop":entry*(1-STOP),"stop":entry*(1-STOP),
                      "peak":entry,"funding":0.0}
            enter_at=None
            opened_this_bar=True
            starts+=1

        if open_pos is not None:
            p=open_pos
            if not opened_this_bar and t in funding:
                cf=-p["qty"]*b["open"]*funding[t]
                cash+=cf
                p["funding"]+=cf
                all_funding+=cf
            stop=p["stop"]
            if b["open"]<=stop:
                raw=b["open"];reason="STOP_OPEN_GAP"
            elif b["low"]<=stop:
                raw=stop;reason="STOP_INTRABAR"
            else:
                raw=None;reason=None

            if raw is not None:
                exit_=raw*(1-slip)
                fee=p["qty"]*exit_*FEE
                all_fees+=fee
                price_pnl=p["qty"]*(exit_-p["entry"])
                net=price_pnl-p["entry_fee"]-fee+p["funding"]
                cash+=price_pnl-fee
                record={
                    "open_t":p["t"],"close_t":t+M5,"entry_price":p["entry"],
                    "exit_price":exit_,"qty":p["qty"],
                    "entry_fees":p["entry_fee"],"exit_fee":fee,
                    "funding":p["funding"],"net_pnl":net,
                    "price_pnl":price_pnl,"exit_reason":reason,
                    "exit_year":datetime.fromtimestamp((t+M5-1)/1000,timezone.utc).year,
                    "notional_return_pct":100*net/(p["qty"]*p["entry"])}
                trades.append(record)
                yearly[str(record["exit_year"])]+=net
                names[reason]+=1
                open_pos=None
            else:
                p["peak"]=max(p["peak"],b["high"])
                # STOP UPDATE ONLY when strategy timeframe closes. (Nonlatched)
                if (t+M5)%timeframe==0:
                    close_profit=(b["close"]-p["entry"])/p["entry"]
                    p["stop"]=(max(p["initial_stop"],p["peak"]*(1-TRAIL))
                               if close_profit>=ACTIVATE else p["initial_stop"])

        # Pessimistic intrabar-low MTM: only while trade remains open; stop
        # exits account at modeled stop instead of carrying fictitious OHLC low.
        close_mark=cash+(open_pos["qty"]*(b["close"]-open_pos["entry"]) if open_pos else 0)
        low_mark=cash+(open_pos["qty"]*(b["low"]*(1-slip)-open_pos["entry"]) if open_pos else 0)
        high_water=max(high_water,close_mark)
        max_close_dd=min(max_close_dd,close_mark/high_water-1)
        max_low_dd=min(max_low_dd,low_mark/high_water-1)

        # Only completed TF bars eligible. Signal availability first at this
        # 5m CLOSE, and hypothetical witness is 1 second after that close.
        if t+M5 in decisions:
            signals_count+=1
            if open_pos is None and enter_at is None:
                enter_at=t+M5+M5
            else:
                blocked_slot+=1
        if enter_at is not None and enter_at < t: raise AssertionError("STALE_PENDING_ENTRY")

    marked=cash+(open_pos["qty"]*(market5[END-M5]["close"]-open_pos["entry"])
                 if open_pos else 0)
    wins=[p["net_pnl"] for p in trades if p["net_pnl"]>0]
    loses=[-p["net_pnl"] for p in trades if p["net_pnl"]<=0]
    positive=sum(wins);negative=sum(loses)
    top3=sum(sorted(wins,reverse=True)[:3])
    cum=0;max_loss_streak=0
    for p in trades:
        cum=0 if p["net_pnl"]>0 else cum+1
        max_loss_streak=max(max_loss_streak,cum)
    result={"tf_minutes":timeframe//60_000,"cost_slippage_bps_side":slipbps,
            "initial_equity":10000.,
            "cash_equity_usdt":cash,"terminal_marked_equity_usdt":marked,
            "realized_cash_return_pct":(cash/10000-1)*100,
            "marked_return_pct":(marked/10000-1)*100,
            "closed_trades":len(trades),
            "wins":len(wins),"win_rate_pct":100*len(wins)/len(trades) if trades else None,
            "profit_factor":positive/negative if negative else None,
            "max_5m_close_mark_dd_pct":100*max_close_dd,
            "max_5m_low_stress_dd_pct":100*max_low_dd,
            "top3_winner_share_of_gross_positive_pct":100*top3/positive if positive else None,
            "removed_3_biggest_net_pnl_sum_usdt":sum(p["net_pnl"] for p in trades)-top3,
            "max_loss_streak":max_loss_streak,
            "signal_bars":signals_count,
            "skipped_signals_active_slot":blocked_slot,
            "entries":starts,
            "fees_usdt":all_fees,
            "funding_usdt":all_funding,
            "annual_closed_trade_pnl_usdt":dict(sorted(yearly.items())),
            "exit_reasons":dict(names),
            "end_position_open":bool(open_pos),
            "pending_entry_at_cutoff":enter_at is not None,
            "contemporaneous_execution_verified":False,
            "status":"RETROSPECTIVE_MODEL_ONLY_NO_OOS_CREDIT"}
    if include_trades:result["trades"]=trades
    return result

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    result={"protocol":"PRE_OUTCOME_PROTOCOL.md",
            "period":"2021-01-01/2026-01-01 UTC, 2020-11/12 source-only warmup",
            "status":"SOURCE_BLOCKED",
            "comparable_timeframes":["15m","30m","1h","4h"],
            "simulator":"Recovered Parent signal / Parent V5 4% initial + 12% nonlatched trail activated on TF close >=5%; 5m execution proxy",
            "alpha_credit":"NONE_ALREADY_KNOWN_HISTORY",
            "live_trading":False}
    try:
        five,one,funding,manifest=fetch_sources()
        result["provenance"]=manifest
        result["source_counts"]={"5m":len(five),"1h":len(one),"funding":len(funding)}
        tf_bars={label:resample(five,size) for label,size in TFS}
        result["one_hour_parity"]=verify_one_hour_parity(tf_bars["1h"],one)
        result["aggregated_bars"]={name:len(bars) for name,bars in tf_bars.items()}
        result["models"]={}
        for label,size in TFS:
            for name,slip in (("BASE",2),("STRESS",5)):
                model=simulate(size,tf_bars[label],five,funding,slip,include_trades=True)
                tr=model.pop("trades")
                key=f"{label}_{name}"
                result["models"][key]=model
                if tr:
                    with (OUT/(key+"_TRADES.csv")).open("w",newline="",encoding="utf8") as f:
                        writer=csv.DictWriter(f,fieldnames=tr[0].keys())
                        writer.writeheader();writer.writerows(tr)
                print("MODEL",key,"closed",model["closed_trades"],"net",round(model["marked_return_pct"],4),
                      "PF",round(model["profit_factor"],4) if model["profit_factor"] else None,flush=True)
        result["status"]="HISTORICAL_TIMEFRAME_MATRIX_COMPLETED_NO_OOS_CREDIT"
    except Exception as exc:
        result["reason"]=type(exc).__name__+":"+str(exc)
    (OUT/"MATRIX_RESULTS.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print("SUMMARY",json.dumps({k:v for k,v in result.items() if k in ("status","reason","source_counts","one_hour_parity","aggregated_bars","models")},sort_keys=True))
    if result["status"]!="HISTORICAL_TIMEFRAME_MATRIX_COMPLETED_NO_OOS_CREDIT":
        raise SystemExit(2)

if __name__=="__main__":
    main()
