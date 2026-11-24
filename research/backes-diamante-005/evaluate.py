#!/usr/bin/env python3
"""BACKES-005: research-only, defense overlays on FROZEN002/MOM8.
No trading APIs, orders, payments or actual user portfolio.
Historical 2018-2026 results are retrospective and never true prospective OOS.
"""
import datetime as dt
import hashlib
import importlib.util
import json
import math
import pathlib
import random
import statistics
import sys

HERE=pathlib.Path(__file__).resolve().parent
OUT=HERE/"results"
SOURCE_SHA="4e256e2f0d4359943f96e9b1eb87e7cfe8cd6d6ca07728db7d5aa2dd4800d828"
ECON_SHA="aa7305b470b3e4623965216608ef80c932682ac072b254c75b1200771454beb2"
ARCHIVE_SHA="73a3e5349930d8b8d8dab46fa69fb8989a118c79cb7f6f7a59260b2f50641d7b"
S=HERE.parent/"backes-diamante-004"/"analyze.py"
spec=importlib.util.spec_from_file_location("b004_reference",S)
b004=importlib.util.module_from_spec(spec);spec.loader.exec_module(b004)
SYSTEMS=("CASH","BTC","ETH","MIX","FROZEN002","MOM8",
         "HALF_ROT","BTC_TREND40","ROT_TREND40","MOM8_TREND40",
         "ROT_TREND40_VOL20","MOM8_TREND40_VOL20")
DEFENSES=("HALF_ROT","BTC_TREND40","ROT_TREND40","MOM8_TREND40",
          "ROT_TREND40_VOL20","MOM8_TREND40_VOL20")
WINDOWS=((2018,2022),(2023,2024),(2025,2026),(2018,2026))
COSTS=(10,35,60,80,100)

def load_inputs():
    a=HERE/"inputs"/"WEEKLY_DATA.json"
    b=HERE/"inputs"/"ECONOMIC.json"
    if not a.exists() or not b.exists():raise RuntimeError("SOURCE_BLOCKED: exact previous archive is not available")
    if hashlib.sha256(a.read_bytes()).hexdigest()!=SOURCE_SHA:
        raise RuntimeError("SOURCE_BLOCKED: source weekly bytes SHA256 disagree")
    if hashlib.sha256(b.read_bytes()).hexdigest()!=ECON_SHA:
        raise RuntimeError("SOURCE_BLOCKED: parent economic report SHA256 disagree")
    sources=json.loads(a.read_text())
    prior=json.loads(b.read_text())
    if set(sources)!={"Binance","Coinbase"}:raise ValueError("SOURCE_BLOCKED: unexpected venues")
    for venue in sources:
        b004.check_data(sources[venue])
    return sources,prior

def annual_vol(data,symbol,i):
    """At Monday i, use 12 finished weekly log close-to-close returns."""
    if i<13:return None
    price=data[symbol]
    samples=[math.log(price[j]["close"]/price[j-1]["close"]) for j in range(i-12,i)]
    if len(samples)!=12:raise ValueError("bad historical vol window")
    return statistics.stdev(samples)*math.sqrt(52)

def trend40(data,i):
    if i<40:return False
    price=data["BTC"]
    return price[i-1]["close"] > sum(x["close"] for x in price[i-40:i])/40

def alloc(data,pos,system,i):
    """Target risky BTC and ETH fractions at weekly OPEN; remainder in non-yielding cash."""
    if system=="CASH":return 0.,0.
    if system=="BTC":return 1.,0.
    if system=="ETH":return 0.,1.
    if system=="MIX":return .5,.5
    if system=="BTC_TREND40":
        return (1.,0.) if trend40(data,i) else (0.,0.)
    selected=("FROZEN002" if system in ("FROZEN002","HALF_ROT","ROT_TREND40","ROT_TREND40_VOL20")
        else "MOM8")
    chosen=pos[selected][i]
    if system in ("ROT_TREND40","MOM8_TREND40","ROT_TREND40_VOL20","MOM8_TREND40_VOL20") and not trend40(data,i):
        return 0.,0.
    fraction=.5 if system=="HALF_ROT" else 1.
    if system in ("ROT_TREND40_VOL20","MOM8_TREND40_VOL20"):
        vol=annual_vol(data,chosen,i)
        fraction=0. if vol is None else min(1.,.20/max(vol,.10))
    if chosen=="BTC":return fraction,0.
    if chosen=="ETH":return 0.,fraction
    raise ValueError("unexpected signal "+str(chosen))

def turnover(prev,target,twohop=False):
    changes=(target[0]-prev[0],target[1]-prev[1])
    buys=sum(max(0.,x) for x in changes)
    sells=sum(max(0.,-x) for x in changes)
    return buys+sells if twohop else max(buys,sells)

def simulate(data,positions,start,end,bps=10,twohop=False):
    """Weekly mark-to-market. Historical last bar marked to Sunday close without terminal sale."""
    if end<=start:raise ValueError("empty interval")
    if bps<0:raise ValueError("invalid cost")
    nav={s:1. for s in SYSTEMS}
    weights={s:(0.,0.) for s in SYSTEMS}
    trace={s:[1.] for s in SYSTEMS}
    returns={s:[] for s in SYSTEMS}
    effects={s:dict(eth_weeks=0,fully_cash_weeks=0,avg_exposure_sum=0.,
                    turnover_notional=0.,modelled_fee_fraction_sum=0.,reallocations=0,
                    weekly_low_dd_proxy=0.,worst_weekly_return=1.) for s in SYSTEMS}
    peaks={s:1. for s in SYSTEMS}
    for j,i in enumerate(range(start,end)):
        bi=data["BTC"][i];ei=data["ETH"][i]
        last=(i==end-1)
        bret=(bi["close"] if last else data["BTC"][i+1]["open"])/bi["open"]
        eret=(ei["close"] if last else data["ETH"][i+1]["open"])/ei["open"]
        bl=bi["low"]/bi["open"];el=ei["low"]/ei["open"]
        for s in SYSTEMS:
            target=alloc(data,positions,s,i)
            wb,we=target
            if min(wb,we)<0 or wb+we>1.0000000001:
                raise ValueError("leveraged/negative target "+s)
            buy_sell=turnover(weights[s],target,twohop)
            charge=buy_sell*bps/10000.
            if charge>=1:raise ValueError("fee too large")
            previous=nav[s]
            after_fee=previous*(1-charge)
            residual=max(0.,1-wb-we)
            # Weekly low is a conservative portfolio stress proxy: BTC and ETH
            # weekly lows may occur at different times. Not an observed intrabar PnL.
            nav_at_low=after_fee*(wb*bl+we*el+residual)
            effects[s]["weekly_low_dd_proxy"]=min(
              effects[s]["weekly_low_dd_proxy"],nav_at_low/peaks[s]-1)
            growth=wb*bret+we*eret+residual
            if growth<=0:raise ValueError("portfolio NAV collapsed")
            new=after_fee*growth
            nav[s]=new
            weights[s]=(wb*bret/growth,we*eret/growth)
            trace[s].append(new)
            ret=new/previous-1
            returns[s].append(ret)
            d=effects[s]
            d["worst_weekly_return"]=min(d["worst_weekly_return"],ret)
            d["eth_weeks"]+=int(we>0.001)
            d["fully_cash_weeks"]+=int(wb+we<0.001)
            d["avg_exposure_sum"]+=wb+we
            d["turnover_notional"]+=buy_sell
            d["modelled_fee_fraction_sum"]+=charge
            d["reallocations"]+=int(j>0 and buy_sell>0.001)
            peaks[s]=max(peaks[s],new)
    n=end-start; years=n*7/365.25
    summary={}
    for s in SYSTEMS:
        v=nav[s]
        maxdd=0.;peak=1.
        for x in trace[s]:
            peak=max(peak,x);maxdd=min(maxdd,x/peak-1)
        cagr=v**(1/years)-1
        annvol=statistics.stdev(returns[s])*math.sqrt(52) if len(returns[s])>1 else 0.
        den=abs(maxdd)
        d=effects[s]
        summary[s]={
          "total_return_pct":round(100*(v-1),5),
          "cagr_pct":round(100*cagr,5),
          "max_drawdown_pct":round(100*maxdd,5),
          "weekly_low_drawdown_proxy_pct":round(100*d["weekly_low_dd_proxy"],5),
          "annualized_nav_vol_pct":round(100*annvol,5),
          "calmar":round(cagr/den,5) if den>0 else None,
          "worst_week_pct":round(100*d["worst_weekly_return"],5),
          "mean_invested_weight_pct":round(100*d["avg_exposure_sum"]/n,4),
          "cash_only_weeks":d["fully_cash_weeks"],
          "weeks_with_eth":d["eth_weeks"],
          "reallocation_weeks":d["reallocations"],
          "modelled_total_turnover":round(d["turnover_notional"],5),
          "modelled_fees_fraction_sum":round(d["modelled_fee_fraction_sum"],7),
          "weeks":n}
    return summary,returns

def bootstrap(a,b,seed=5005):
    if len(a)!=len(b) or len(a)<8:raise ValueError("insufficient weekly observations")
    vals=[x-y for x,y in zip(a,b)]
    n=len(vals); block=min(8,n);rng=random.Random(seed);est=[]
    for _ in range(2000):
        sample=[]
        while len(sample)<n:
            j=rng.randint(0,n-block)
            sample.extend(vals[j:j+block])
        est.append(100*statistics.mean(sample[:n]))
    est.sort()
    return {"excess_weekly_pp":round(100*statistics.mean(vals),6),
       "ci95_low_pp":round(est[49],6),"ci95_high_pp":round(est[1950],6)}

def evaluate(source,prior):
    results={}
    for venue,data in source.items():
        policies=b004.positions(data)
        venue_results=[]
        for years in WINDOWS:
            yr1,yr2=years
            ix=[i for i,w in enumerate(data["BTC"]) if yr1<=int(w["date"][:4])<=yr2]
            for bps in COSTS:
                for twohop in (False,True) if bps==80 else (False,):
                    stats,retn=simulate(data,policies,ix[0],ix[-1]+1,bps,twohop)
                    obj={"window":f"{yr1}-{yr2}","bps_per_traded_notional":bps,
                       "twohop_routing_stress":twohop,"metrics":stats}
                    if bps==80 and not twohop and years==(2025,2026):
                        obj["bootstrap_recent_vs"]={
                            k:{j:bootstrap(retn[k],retn[j]) for j in ("CASH","BTC_TREND40","FROZEN002")}
                            for k in DEFENSES}
                    venue_results.append(obj)
        # Verify old unmodified comparator has exactly original 004 economic result.
        original=next(x for x in venue_results if x["window"]=="2018-2026"
                       and x["bps_per_traded_notional"]==10 and not x["twohop_routing_stress"])
        expected=next(x for x in prior["venn"][venue]["comparisons"]
                if x["period"]=="2018-2026" and x["bps_per_leg"]==10 and not x["two_leg_swap_stress"])
        for key in ("FROZEN002","MOM8","BTC","ETH"):
            got=original["metrics"][key]["total_return_pct"]
            target=expected["portfolios"][key]["total_return_pct"]
            if abs(got-target)>0.00015:
                raise ValueError(f"PARITY_BLOCKED {venue} {key}: {got} != {target}")
        # BACKES004 charged only 0.5 of the initial MIX purchase, while
        # buying 50% BTC and 50% ETH requires 1.0 of NAV traded.
        # Assert the exact fee correction rather than hiding a prior bug.
        prior_mix_nav=1+expected["portfolios"]["MIX"]["total_return_pct"]/100
        correct_mix_nav=prior_mix_nav*(1-.001)/(1-.0005)
        got_mix_nav=1+original["metrics"]["MIX"]["total_return_pct"]/100
        if abs(correct_mix_nav-got_mix_nav)>0.0000002:
            raise ValueError(f"MIX_INITIAL_FEE_CORRECTION_FAILED {venue}: {got_mix_nav} != {correct_mix_nav}")
        results[venue]={"source_pass":True,"parity_pass":True,"scenarios":venue_results}
    return results

def report(results):
    lines=["# BACKES-DIAMANTE-005 — Defesa de capital: resultado histórico",
       "", "**Retrospetivo, não prospetivo. Não é a estratégia privada do Augusto Backes. Sem trades.**",
       "Source 004 original SHA-256 confirmado. Bootstrap e gestão de risco não garantem perdas limitadas.",
       "## 2018–2026, comparação de 80bps por valor transacionado",
       "",
       "| Modelo | Coinbase CAGR | Coinbase MDD | Binance CAGR | Binance MDD |",
       "|---|---:|---:|---:|---:|"]
    def get(venue,window,bps=80,twohop=False):
        return next(x["metrics"] for x in results[venue]["scenarios"]
             if x["window"]==window and x["bps_per_traded_notional"]==bps
             and x["twohop_routing_stress"]==twohop)
    a=get("Coinbase","2018-2026");b=get("Binance","2018-2026")
    for k in SYSTEMS:
        lines.append("| "+k+" | "+" | ".join(
            f"{x[k]['cagr_pct']:+.2f}%"+" | "+f"{x[k]['max_drawdown_pct']:.2f}%"
            for x in (a,b))+" |")
    lines+=["","## 2025–2026, 80bps: cash/defense stress","",
        "| Modelo | Coinbase return | Coinbase DD | Binance return | Binance DD |",
        "|---|---:|---:|---:|---:|"]
    a2=get("Coinbase","2025-2026");b2=get("Binance","2025-2026")
    for k in SYSTEMS:
        lines.append("| "+k+" | "+" | ".join(
            f"{x[k]['total_return_pct']:+.2f}%"+" | "+f"{x[k]['max_drawdown_pct']:.2f}%"
            for x in (a2,b2))+" |")
    lines+=["","## Economic no-trading research gates","",
      "Candidate requires MDD <=30% full-period AND every major regime, net positive vs CASH at 80bps, "
      ">=20pp less drawdown than full ROT, and Calmar > BTC_TREND40 and HALF_ROT across both venues in >=2/3 regimes. "
      "Even a candidate is not a live economic GO without truly prospective data, spreads, historical fees and risk tails.",
      "", "All 10/35/60/80/100bps scenarios, 80bps two-hop, NAV-vol, Calmar, weeks cash, weeks in ETH and 2000x block bootstrap are in results.json.",
      "Low-week drawdown proxy based on independent OHLC lows is NOT a realized intraday drawdown or stop guarantee.",
      "CASH is zero-interest stable-numeraire cash and ignores stablecoin/custody risks.",
      "No parameter adjustment after these results."]
    return "\n".join(lines)+"\n"

def gate(results):
    reasons={}
    for system in DEFENSES:
        diag=[]
        for venue in results:
            arr=results[venue]["scenarios"]
            full=next(x["metrics"] for x in arr if x["window"]=="2018-2026"
                  and x["bps_per_traded_notional"]==80 and not x["twohop_routing_stress"])
            f=full[system];rot=full["FROZEN002"]
            c1=(f["max_drawdown_pct"]>=-30 and f["total_return_pct"]>0 and
                f["calmar"] is not None and f["calmar"]>full["BTC_TREND40"]["calmar"]
                and f["calmar"]>full["HALF_ROT"]["calmar"] and
                f["max_drawdown_pct"]>=rot["max_drawdown_pct"]+20)
            periods=0
            for period in ("2018-2022","2023-2024","2025-2026"):
                s=next(x["metrics"] for x in arr if x["window"]==period
                  and x["bps_per_traded_notional"]==80 and not x["twohop_routing_stress"])
                if s[system]["max_drawdown_pct"]>=-30 and s[system]["total_return_pct"]>0 and (
                   s[system]["calmar"] is not None and s["BTC_TREND40"]["calmar"] is not None
                   and s["HALF_ROT"]["calmar"] is not None and
                   s[system]["calmar"]>s["BTC_TREND40"]["calmar"] and
                   s[system]["calmar"]>s["HALF_ROT"]["calmar"]):
                    periods+=1
            diag.append({"venue":venue,"full_period_criteria":bool(c1),"regimes_passed":periods})
        reasons[system]={"source_comparisons":diag,
                 "research_candidate_only":all(d["full_period_criteria"] and d["regimes_passed"]>=2 for d in diag)}
    return reasons

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    try:
        source,prior=load_inputs()
        results=evaluate(source,prior)
    except Exception as e:
        (OUT/"RESULT.md").write_text("# TECH_OR_SOURCE_BLOCKED\n"+repr(e)+"\n")
        (OUT/"error.json").write_text(json.dumps({"error":repr(e),"no_trades":True},indent=2)+"\n")
        raise
    g=gate(results)
    result={"experiment":"BACKES-DIAMANTE-005","as_of":"2026-11-24",
       "historical_cutoff":"2026-11-22","not_prospective":True,
       "same_004_venue_sources_verified":True,
       "004_zip_sha256":ARCHIVE_SHA,"weekly_data_sha256":SOURCE_SHA,
       "prior_economic_sha256":ECON_SHA,"trades_executed":0,"venues":results,"gate":g,
       "candidate_count":sum(int(x["research_candidate_only"]) for x in g.values()),
       "live_trading_verdict":"NO-GO"}
    (OUT/"results.json").write_text(json.dumps(result,indent=2)+"\n")
    (OUT/"RESULT.md").write_text(report(results))
    print("DEFENSIVE_005_OK 2 venues; original FROZEN002 parity PASS; candidates",result["candidate_count"],"; LIVE_NO_GO")
if __name__=="__main__":main()
