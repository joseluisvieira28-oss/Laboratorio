#!/usr/bin/env python3
"""BACKES-004: compare original frozen pivot against plain momentum, net of costs.
Read-only model; all 2018-2026 chronology is retrospective, NOT genuine OOS.
"""
import datetime as dt
import importlib.util
import json
import math
import pathlib
import random
import statistics

HERE=pathlib.Path(__file__).resolve().parent
OUT=HERE/"results"
S=HERE.parent/"backes-diamante-002"/"rotation_backtest.py"
spec=importlib.util.spec_from_file_location("b002_frozen",S)
b002=importlib.util.module_from_spec(spec);spec.loader.exec_module(b002)
CANDIDATES=("FROZEN002","MOM4","MOM8","MOM12")
PORTFOLIOS=("BTC","ETH","MIX","CASH")+CANDIDATES
COSTS=(5,10,20,35)
WINDOWS=((2018,2022),(2023,2024),(2025,2026),(2018,2026))
PREDECESSOR_SHA="735fff332994ce546f56258a01787d7f250203efa701586fa24eefd553f1ecaf"

def positions(data):
    r=data["RATIO"]
    original=b002.signals(r)
    states={"FROZEN002":original}
    for lag in (4,8,12):
        states["MOM"+str(lag)]=["ETH" if i>=lag and r[i]["close"]>r[i-lag]["close"] else "BTC"
                                   for i in range(len(r))]
    return {k:["BTC"]+[states[k][i-1] for i in range(1,len(r))] for k in CANDIDATES}

def check_data(data):
    dates=[q["date"] for q in data["BTC"]]
    if len(dates)!=464 or any(
       dt.date.fromisoformat(dates[i])!=dt.date(2018,1,1)+dt.timedelta(days=i*7) for i in range(464)):
        raise ValueError("WEEKLY_SOURCE_GATE_FAILED")
    for s in ("ETH","RATIO"):
        if [x["date"] for x in data[s]]!=dates:raise ValueError("MISALIGNED_"+s)

def trade_model(data,by_policy,first,last,bps=10,double=False):
    """Trades at weekly open using previous week's closed signal. Last bar liquidates
    to MARK not cash; no fictitious terminal fill. One asset swap one-leg by default.
    """
    indices=list(range(first,last))
    if not indices:raise ValueError("empty period")
    assets=["BTC","ETH"]
    nav={k:1. for k in PORTFOLIOS}
    prev_weights={k:(0.,0.) for k in PORTFOLIOS}
    traces={k:[1.] for k in PORTFOLIOS}
    weekly={k:[] for k in PORTFOLIOS}
    counts={k:0 for k in PORTFOLIOS}
    exposures={k:0 for k in PORTFOLIOS}
    fees={k:0. for k in PORTFOLIOS}
    price_b=data["BTC"];price_e=data["ETH"]
    for j,i in enumerate(indices):
        ni=indices[j+1] if j+1<len(indices) else None
        br=(price_b[ni]["open"] if ni is not None else price_b[i]["close"])/price_b[i]["open"]
        er=(price_e[ni]["open"] if ni is not None else price_e[i]["close"])/price_e[i]["open"]
        for k in PORTFOLIOS:
            if k=="BTC":target=(1.,0.)
            elif k=="ETH":target=(0.,1.)
            elif k=="MIX":target=(.5,.5)
            elif k=="CASH":target=(0.,0.)
            else:target=(0.,1.) if by_policy[k][i]=="ETH" else (1.,0.)
            pb,pe=prev_weights[k];wb,we=target
            traded=max(abs(wb-pb),abs(we-pe))
            if k in CANDIDATES and j>0 and traded>.5:counts[k]+=1
            if k in CANDIDATES and we==1:exposures[k]+=1
            mul=2 if double and k in CANDIDATES and j>0 and traded>.5 else 1
            fee=bps/10000*traded*mul
            if not 0<=fee<1:raise ValueError("invalid fee")
            fees[k]+=fee
            old=nav[k]
            growth=wb*br+we*er+(1-wb-we)
            nav[k]*=(1-fee)*growth
            if growth<=0:raise ValueError("portfolio collapsed")
            prev_weights[k]=(wb*br/growth,we*er/growth)
            traces[k].append(nav[k])
            weekly[k].append(nav[k]/old-1)
    years=len(indices)*7/365.25
    out={}
    for k in PORTFOLIOS:
        peak=1.;dd=0.
        for value in traces[k]:
            peak=max(peak,value);dd=min(dd,value/peak-1)
        out[k]={"total_return_pct":round(100*(nav[k]-1),5),
                "cagr_pct":round(100*(nav[k]**(1/years)-1),5),
                "max_drawdown_pct":round(100*dd,5),
                "switches":counts[k],
                "held_eth_weeks":exposures[k],
                "n_weeks":len(indices),
                "modelled_cost_fraction_sum":round(fees[k],6)}
    return out,weekly

def bootstrap(a,b,seed=4004):
    if len(a)!=len(b) or len(a)<8:raise ValueError("insufficient matched weeks")
    excess=[u-v for u,v in zip(a,b)]
    rng=random.Random(seed);n=len(excess);size=min(8,n)
    samples=[]
    for _ in range(2000):
        res=[]
        while len(res)<n:
            begin=rng.randint(0,n-size)
            res+=excess[begin:begin+size]
        samples.append(statistics.mean(res[:n]))
    samples.sort()
    return {"mean_weekly_excess_pp":round(100*statistics.mean(excess),6),
            "ci95_low_pp":round(100*samples[49],6),
            "ci95_high_pp":round(100*samples[1950],6)}

def historical_folds(data,policies):
    """Rolling chronological selector: 104 prior weeks -> 26 following weeks.
    These weeks have ALREADY BEEN SEEN by researchers (pseudo-OOS only).
    """
    n=len(data["BTC"])
    target={k:policies[k][:] for k in CANDIDATES}
    decisions=["BTC"]*n
    folds=[]
    for start in range(104,n,26):
        end=min(start+26,n)
        scores={}
        for k in CANDIDATES:
            stats,_=trade_model(data,{**target},start-104,start,10,False)
            scores[k]=stats[k]["total_return_pct"]
        best=sorted(CANDIDATES,key=lambda x:(-scores[x],x))[0]
        for i in range(start,end):decisions[i]=target[best][i]
        folds.append({"training_start":data["BTC"][start-104]["date"],
                      "training_end":data["BTC"][start-1]["date"],
                      "test_start":data["BTC"][start]["date"],
                      "test_end":data["BTC"][end-1]["date"],
                      "selected":best,
                      "training_net_returns_pct":scores})
    selected={**target,"WF_SELECTED":decisions}
    return selected,folds

def trade_selected(data,positions_,start,end,bps=10):
    """Use unmodified portfolio engine with custom candidate as explicit policy.
    Full 10bps cost at each fold-selected signal transition; no free resets.
    """
    ext=PORTFOLIOS+("WF_SELECTED",)
    idx=list(range(start,end))
    prev=(0.,0.);nav=1.;traj=[1.];sw=0;eth=0
    weekly=[]
    for j,i in enumerate(idx):
        nexti=idx[j+1] if j+1<len(idx) else None
        br=(data["BTC"][nexti]["open"] if nexti is not None else data["BTC"][i]["close"])/data["BTC"][i]["open"]
        er=(data["ETH"][nexti]["open"] if nexti is not None else data["ETH"][i]["close"])/data["ETH"][i]["open"]
        target=(0.,1.) if positions_["WF_SELECTED"][i]=="ETH" else (1.,0.)
        turnover=max(abs(target[0]-prev[0]),abs(target[1]-prev[1]))
        if j>0 and turnover>.5:sw+=1
        if target[1]==1:eth+=1
        fac=(1-bps/10000*turnover)*(er if target[1]==1 else br)
        nav*=fac
        traj.append(nav);weekly.append(fac-1)
        prev=target
    peak=1.;dd=0.
    for value in traj:
        peak=max(peak,value);dd=min(dd,value/peak-1)
    years=len(idx)*7/365.25
    return {"total_return_pct":round(100*(nav-1),5),
            "cagr_pct":round(100*(nav**(1/years)-1),5),
            "max_drawdown_pct":round(100*dd,5),
            "held_eth_weeks":eth,"switches":sw,"n_weeks":len(idx)},weekly

def evaluate(venue,data):
    check_data(data)
    policies=positions(data)
    records=[]
    for y1,y2 in WINDOWS:
        indices=[i for i,r in enumerate(data["BTC"]) if y1<=int(r["date"][:4])<=y2]
        for bps in COSTS:
            for double in ([False,True] if bps==35 else [False]):
                result,returns=trade_model(data,policies,indices[0],indices[-1]+1,bps,double)
                record={"period":f"{y1}-{y2}","bps_per_leg":bps,
                        "two_leg_swap_stress":double,"portfolios":result}
                if (y1,y2)==(2025,2026) and bps in (10,35) and not double:
                    record["block_bootstrap_8w_vs_BTC_MIX"]={
                        k: {comp:bootstrap(returns[k],returns[comp])
                            for comp in ("BTC","MIX")} for k in CANDIDATES}
                records.append(record)
    policies2,folds=historical_folds(data,policies)
    wf,weekly=trade_selected(data,policies2,104,len(data["BTC"]),10)
    bt,_=trade_model(data,policies,104,len(data["BTC"]),10)
    reference={
        "asset":"ETHBTC direct traded",
        "weeks":len(data["BTC"]),"date_start":data["BTC"][0]["date"],
        "date_end":data["BTC"][-1]["date"],
        "comparisons":records,
        "chronological_pseudo_oos":{
           "warning":"all 2018-2026 outcomes were already available to the researcher; this is not truly unseen prospective OOS",
           "selection_rule":"best trailing 104 weeks net return at 10bps, evaluate next 26",
           "candidate_rules":list(CANDIDATES),"folds":folds,
           "selected_strategy":wf,
           "identical_window_benchmarks":{k:bt[k] for k in ("BTC","ETH","MIX","CASH")},
           "excess_vs_btc_weekly":bootstrap(weekly,[0]*len(weekly)) if False else None}}
    return reference,policies

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    path=OUT/"WEEKLY_DATA.json"
    data=json.loads(path.read_text())
    if not data:raise ValueError("NO_SOURCE_AVAILABLE")
    source=json.loads((OUT/"SOURCE_STATUS.json").read_text())
    outcomes={};states={}
    for venue,prices in data.items():
        try:
            result,pol=evaluate(venue,prices)
            outcomes[venue]=result
            states[venue]=pol
            print("ECONOMIC_DIAGNOSTIC_OK",venue,len(result["chronological_pseudo_oos"]["folds"]),"chronological folds")
        except Exception as e:
            outcomes[venue]={"status":"ANALYSIS_BLOCKED","error":repr(e)}
            print("ANALYSIS_BLOCKED",venue,repr(e))
    for a,pa in states.items():
        for b,pb in states.items():
            if a<b:
                outcomes[a].setdefault("cross_venue_agreements",{})[b]={
                     key:round(100*sum(x==y for x,y in zip(pa[key],pb[key]))/464,4)
                     for key in CANDIDATES}
    result={"study":"BACKES-DIAMANTE-004","cutoff_utc":"2026-11-22",
            "retrospective_only":True,"no_trades":True,"no_proprietary_backes_rules":True,
            "predecessor_zip_sha256":PREDECESSOR_SHA,
            "sources":source.get("source",{}),"source_errors":source.get("errors",{}),
            "venn":outcomes}
    (OUT/"ECONOMIC.json").write_text(json.dumps(result,indent=2)+"\n")
    lines=["# BACKES-DIAMANTE-004 — Independent venue comparison","",
       "**Retrospective research only. No real trades, no future-unseen validation.**",
       "Rules are Crypto Lab original ideas, NOT Augusto Backes personal strategies.",
       "Source cutoff 2026-11-22; Monday-open fill is hypothetical, not verified executable.",
       "",
       "## Market data provenance"]
    for venue,s in source.get("source",{}).items():
        lines.append("- "+venue+": "+("SOURCE_PASS" if "weeks" in s else "SOURCE_BLOCKED")+
            (" ("+source["errors"][venue]+")" if venue in source.get("errors",{}) else ""))
    lines+=["","## 10bps each side, 2025-2026 retrospective periods","",
            "| Venue | BTC | ETH | MIX | FROZEN002 | MOM4 | MOM8 | MOM12 |",
            "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for venue,r in outcomes.items():
        if "comparisons" not in r:continue
        t=next(x for x in r["comparisons"] if x["period"]=="2025-2026" and x["bps_per_leg"]==10 and not x["two_leg_swap_stress"])
        lines.append("| "+venue+" | "+" | ".join(
           f"{t['portfolios'][k]['total_return_pct']:+.2f}%" for k in ("BTC","ETH","MIX","FROZEN002","MOM4","MOM8","MOM12"))+" |")
    lines+=["","## Cross-venue 2018-2026 full results at 10bps","",
            "| Venue | FROZEN002 | MOM4 | MOM8 | MOM12 | BTC | FROZEN DD |",
            "|---|---:|---:|---:|---:|---:|---:|"]
    for venue,r in outcomes.items():
        if "comparisons" not in r:continue
        t=next(x for x in r["comparisons"] if x["period"]=="2018-2026" and x["bps_per_leg"]==10 and not x["two_leg_swap_stress"])
        lines.append("| "+venue+" | "+" | ".join(
           f"{t['portfolios'][k]['total_return_pct']:+.2f}%" for k in ("FROZEN002","MOM4","MOM8","MOM12","BTC"))+
           f" | {t['portfolios']['FROZEN002']['max_drawdown_pct']:.2f}% |")
    lines+=["","## Chronological 104-week train / 26-week pseudo-OOS folds (10bps)","",
            "| Venue | Folds | Selected strategy return | BTC same period | MIX same period | Selected max drawdown |",
            "|---|---:|---:|---:|---:|---:|"]
    for venue,r in outcomes.items():
        if "chronological_pseudo_oos" not in r:continue
        wf=r["chronological_pseudo_oos"]
        lines.append(f"| {venue} | {len(wf['folds'])} | {wf['selected_strategy']['total_return_pct']:+.2f}% | "+
           f"{wf['identical_window_benchmarks']['BTC']['total_return_pct']:+.2f}% | "+
           f"{wf['identical_window_benchmarks']['MIX']['total_return_pct']:+.2f}% | "+
           f"{wf['selected_strategy']['max_drawdown_pct']:.2f}% |")
    lines+=["","## Adversarial verdict", "",
        "All results are retrospective and cannot be called prospective edge.",
        "Compare across venues, periods and signal simplicity. Momentum and swing pivot differences are not independent discoveries.",
        "For exact costs, drawdowns, week holdings, switches, 35bps stress, bootstrap and fold selection read ECONOMIC.json.",
        "No live trading GO; eligibility for a strictly pre-frozen prospective shadow study only."]
    (OUT/"RESULT.md").write_text("\n".join(lines)+"\n")
    print("AUDIT004_COMPLETE",len([v for v in outcomes.values() if "comparisons" in v]),
          "venues,",list(source.get("errors",{})))
if __name__=="__main__":main()
