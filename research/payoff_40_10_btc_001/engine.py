#!/usr/bin/env python3
"""Causal, research-only BTC-CONVEX Parent versus frozen PAYOFF-40-10 engine.

Historical 2020-2025 diagnostics, zero promotion credit. Public Binance USD-M
monthly price/funding/mark source (not fill records). NO live orders/account use.
"""
from __future__ import annotations
import argparse,json,math
from collections import deque
from datetime import datetime,timezone
from pathlib import Path

HOUR=3_600_000
EXPIRE=60*24*HOUR
START=int(datetime(2020,3,1,tzinfo=timezone.utc).timestamp()*1000)
FINISH=int(datetime(2025,12,31,23,tzinfo=timezone.utc).timestamp()*1000)
EQUITY0=10489.94
LEV=2
MAINT_PROXY=.005
NOMINAL_FEE=.0008
CONFIGS={"BASE":(.0008,.0002),"STRESS":(.001,.0005)}

def sma(a,n):
    out=[None]*len(a);q=deque();s=0.
    for i,v in enumerate(a):
        q.append(v);s+=v
        if len(q)>n:s-=q.popleft()
        if len(q)==n:out[i]=s/n
    return out

def sigma(a,n):
    out=[None]*len(a);q=deque()
    for i,v in enumerate(a):
        q.append(v)
        if len(q)>n:q.popleft()
        if len(q)==n:
            m=sum(q)/n
            out[i]=math.sqrt(sum((x-m)**2 for x in q)/n)
    return out

def rma(a,n):
    out=[None]*len(a);p=None;buf=[]
    for i,v in enumerate(a):
        if v is None:continue
        if p is None:
            buf.append(v)
            if len(buf)==n:p=sum(buf)/n;out[i]=p
        else:p=(p*(n-1)+v)/n;out[i]=p
    return out

def signals(b):
    close=[x["close"] for x in b];vol=[x["volume"] for x in b]
    a20=sma(close,20);a200=sma(close,200);sd=sigma(close,20);av=sma(vol,20)
    plus=[None]*len(close);minus=[None]*len(close)
    for i in range(1,len(close)):
        d=close[i]-close[i-1];plus[i]=max(d,0.);minus[i]=max(-d,0.)
    au=rma(plus,14);ad=rma(minus,14)
    sig=[]
    for i in range(len(b)):
        if None in (a20[i],a200[i],sd[i],av[i],au[i],ad[i]) or sd[i]<=0:
            sig.append(False);continue
        rsi=100 if ad[i]==0 else 100-100/(1+au[i]/ad[i])
        z=(close[i]-a20[i])/sd[i]
        score=sum((rsi<30,z< -2,close[i]<a20[i]-2*sd[i],vol[i]>av[i]))
        sig.append(score>=3 and close[i]>a200[i])
    return sig

def nominal_bounds(entry):
    f=NOMINAL_FEE
    return (entry*(1+(.40/LEV+2*f)/(1-f)),
            entry*(1+(-.10/LEV+2*f)/(1-f)))

def check_bars(b,begin,end):
    if len(b)<201 or b[0]["t"]>begin-200*HOUR or b[-1]["t"]<end:
        raise ValueError("MISSING_WARMUP_OR_END")
    last=None
    for k in b:
        t=int(k["t"])
        o,hi,lo,c,v=[float(k[x]) for x in ("open","high","low","close","volume")]
        if not (0<lo<=min(o,c)<=max(o,c)<=hi and v>=0) or not all(map(math.isfinite,(o,hi,lo,c,v))):
            raise ValueError("INVALID_MARKET_BAR")
        if t%HOUR or last is not None and t!=last+HOUR:
            raise ValueError("HOURLY_SOURCE_GAP")
        last=t

def replay(b,funding,marks,mode,fee,slip,begin=START,end=FINISH):
    if mode not in ("PAYOFF","PARENT"):raise ValueError("MODE_UNKNOWN")
    check_bars(b,begin,end)
    sig=signals(b)
    eq=EQUITY0;peak_closed=eq;peak_mtm=eq;dd_closed=0.;dd_mtm=0.
    p=None;pending=False;trades=[];signal_count=0;exposure=0;fund_n=0;liq_warn=0
    year_start=None;year=None;years={}
    last_mark=next(x["close"] for x in reversed(b) if x["t"]==end)

    def exit_position(t,raw,reason,liquidation_overlap=False):
        nonlocal eq,peak_closed,dd_closed,p
        if p is None:raise ValueError("EXIT_WITHOUT_ENTRY")
        fill=raw*(1-slip)
        outfee=fill*p["qty"]*fee
        gross=(fill-p["fill"])*p["qty"]
        pnl=gross-p["entry_fee"]-outfee+p["funding_cash"]
        eq+=gross-outfee
        if eq<=0:raise ValueError("INSOLVENCY")
        peak_closed=max(peak_closed,eq)
        dd_closed=min(dd_closed,eq/peak_closed-1)
        trades.append({**p,"exit_t":t,"exit_fill":fill,"net_pnl":pnl,
                       "margin_net_return":pnl/p["margin"],
                       "reason":reason,"equity":eq,
                       "mark_liquidation_overlap":bool(liquidation_overlap)})
        p=None

    for i,k in enumerate(b):
        t=k["t"]
        if t<begin or t>end:continue
        yy=datetime.fromtimestamp(t/1000,tz=timezone.utc).year
        if year is None:year=yy;year_start=eq
        if yy!=year:
            years[str(year)]=eq/year_start-1
            year=yy;year_start=eq

        # Entry on next bar open only, never at signal's own close.
        if pending and p is None:
            fill=k["open"]*(1+slip)
            notional=eq*.20 # same initial notional fraction for both models
            margin=notional/LEV if mode=="PAYOFF" else notional
            qty=notional/fill
            entry_fee=qty*fill*fee
            eq-=entry_fee
            target,stop=nominal_bounds(fill) if mode=="PAYOFF" else (None,fill*.96)
            p={"entry_t":t,"fill":fill,"qty":qty,"margin":margin,"entry_fee":entry_fee,
               "funding_cash":0.,"funding_count":0,"target":target,
               "stop":stop,"initial_stop":stop,"peak":fill,
               "mark_liquidation_possible":False}
            pending=False

        # Scheduled time-exit / gap at hourly open takes priority over funding.
        if p is not None:
            if mode=="PAYOFF" and t>=p["entry_t"]+EXPIRE:
                exit_position(t,k["open"],"TIME_EXIT")
            elif k["open"]<=p["stop"]:
                exit_position(t,k["open"],"STOP_GAP")
            elif mode=="PAYOFF" and k["open"]>=p["target"]:
                exit_position(t,k["open"],"TARGET_GAP")

        # Long pays positive funding. An entry at this same timestamp is excluded.
        if p is not None and t in funding and p["entry_t"]<t:
            if t not in marks:raise ValueError("FUNDING_MARK_MISSING")
            cash=-p["qty"]*float(marks[t]["open"])*funding[t]
            p["funding_cash"]+=cash;p["funding_count"]+=1
            eq+=cash;fund_n+=1
            if eq<=0:raise ValueError("FUNDING_INSOLVENCY")

        if p is not None:
            exposure+=1
            m=marks.get(t)
            if m is None:raise ValueError("MISSING_MARK_BAR")
            # This 2x maintenance-price check is a *proxy*, not a live tier model.
            threshold=p["fill"]*(1-1/LEV+MAINT_PROXY+fee) if mode=="PAYOFF" else None
            may_liquidate=bool(threshold and float(m["low"])<=threshold)
            if may_liquidate:
                liq_warn+=1;p["mark_liquidation_possible"]=True
            hit_stop=k["low"]<=p["stop"]
            if mode=="PAYOFF":
                hit_target=k["high"]>=p["target"]
                if hit_stop and hit_target:
                    exit_position(t,p["stop"],"AMBIGUOUS_STOP_FIRST",may_liquidate)
                elif hit_stop:exit_position(t,p["stop"],"STOP",may_liquidate)
                elif hit_target:exit_position(t,p["target"],"TARGET",may_liquidate)
            elif hit_stop:exit_position(t,p["stop"],"STOP_OR_TRAIL")

        # Original Parent trail rule updates only after the completed bar close.
        if p is not None and mode=="PARENT":
            p["peak"]=max(p["peak"],k["high"])
            gain=(k["close"]-p["fill"])/p["fill"]
            p["stop"]=max(p["initial_stop"],p["peak"]*.88) if gain>=.05 else p["initial_stop"]

        if p is None and sig[i]:
            pending=True;signal_count+=1

        if p is not None:
            mtm=eq+p["qty"]*(k["close"]-p["fill"])-p["qty"]*k["close"]*fee
            if mtm<=0:raise ValueError("MTM_INSOLVENCY")
            peak_mtm=max(peak_mtm,mtm);dd_mtm=min(dd_mtm,mtm/peak_mtm-1)
        else:
            peak_mtm=max(peak_mtm,eq);dd_mtm=min(dd_mtm,eq/peak_mtm-1)

    if year is not None:years[str(year)]=eq/year_start-1
    winners=[v for v in trades if v["net_pnl"]>0]
    losers=[v for v in trades if v["net_pnl"]<0]
    gw=sum(v["net_pnl"] for v in winners)
    gl=-sum(v["net_pnl"] for v in losers)
    reason={x:sum(v["reason"]==x for v in trades) for x in sorted(set(v["reason"] for v in trades))}
    unresolved=[]
    if p is not None:
        unreal=p["qty"]*(last_mark-p["fill"])-p["entry_fee"]-p["qty"]*last_mark*fee+p["funding_cash"]
        unresolved=[{"entry_t":p["entry_t"],"status":"OPEN_AT_2025_CUTOFF",
                     "unrealized_net_if_liquidated_at_last_close":unreal}]
    return {"mode":mode,"fee_per_side":fee,"slippage_per_side":slip,
            "trades_closed":len(trades),"wins":len(winners),"losses":len(losers),
            "win_rate":len(winners)/len(trades) if trades else None,
            "profit_factor":gw/gl if gl else None,
            "equity_initial":EQUITY0,"closed_equity":eq,
            "closed_equity_return":eq/EQUITY0-1,
            "closed_equity_max_dd":dd_closed,"approx_mtm_max_dd":dd_mtm,
            "historical_year_cash_returns":years,"exit_counts":reason,
            "funding_cash_total":sum(v["funding_cash"] for v in trades)+(p["funding_cash"] if p else 0),
            "funding_events":fund_n,"hours_exposed":exposure,"signal_count":signal_count,
            "mark_liquidation_warning_hours":liq_warn,
            "unresolved_at_cutoff":unresolved,
            "avg_winner_return_on_position_margin":sum(v["margin_net_return"] for v in winners)/len(winners) if winners else None,
            "avg_loser_return_on_position_margin":sum(v["margin_net_return"] for v in losers)/len(losers) if losers else None,
            "trade_ledger":trades}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    source=json.loads(a.source.read_text())
    if source.get("status")!="SOURCE_OK":raise SystemExit("SOURCE_NOT_VERIFIED")
    b=source["bars"]
    funding={int(t):float(x) for t,x in source["funding"].items()}
    marks={int(t):m for t,m in source["marks"].items()}
    out={"classification":"RETROSPECTIVE_KNOWN_OUTCOMES_DIAGNOSTIC_ONLY",
         "live_authority":"NONE","new_strategy_4to1_proven":False,
         "limitations":["Binance proxy is not venue execution","no real BBO/slippage",
                        "historical tier/tick/min-notional unverified",
                        "1h OHLC intrabar ordering","mark-based liquidation is heuristic",
                        "chosen after original historical outcome inspection"],
         "source_manifests":source["manifests"],"scenarios":{}}
    for label,(fee,slip) in CONFIGS.items():
        out["scenarios"][label]={
            mode:replay(b,funding,marks,mode,fee,slip)
            for mode in ("PARENT","PAYOFF")}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(out,indent=2,sort_keys=True))
    for name,results in out["scenarios"].items():
        for mode,v in results.items():
            print("PAYOFF_RESEARCH",name,mode,json.dumps(
                {k:z for k,z in v.items() if k not in ("trade_ledger","unresolved_at_cutoff")},
                sort_keys=True))

if __name__=="__main__":main()
