#!/usr/bin/env python3
"""LIQMAP005: Does executed liquidation volume add to PRICE-only four-hour TAIL-RISK forecasts?
All read-only, historical, unlevered hypothetical exposure. Not an executable trading bot.
"""
import collections
import datetime as dt
import json
import math
import pathlib
import random
import statistics
import sys

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT=pathlib.Path(__file__).resolve().parent
OUT=ROOT/"study_results"
PARENT=ROOT.parent/"liqmap-diamante-004"
sys.path.insert(0,str(PARENT))
import study as old

FIRST_TRAIN=pd.Timestamp("2026-07-15T00:00:00Z")
SEP=pd.Timestamp("2026-09-01T00:00:00Z")
OCT=pd.Timestamp("2026-10-01T00:00:00Z")
END=pd.Timestamp("2026-11-01T00:00:00Z")
HISTORY=336
FUTURE=4
CUT=0.20
SLIP_BPS=5
FEE_BPS=(10,35)
PRICE_KEYS=("abs_close4_logret","std24_1h_close_logret","current_1h_log_range")
LIQ_KEYS=("log_liquidated_USD_vs_past_95p","log_count_liquidated_positions")

def nearest_rank(values,q):
    arr=np.asarray(values,dtype=float)
    if len(arr)==0 or not np.all(np.isfinite(arr)):
        raise ValueError("SOURCE_BLOCKED invalid trailing quantile")
    return float(np.sort(arr)[max(0,math.ceil(q*len(arr))-1)])

def historical_excursions(p):
    """For j, evaluate j+1..j+4; known by time j+4, never by j."""
    n=len(p["open"])
    result=np.full(n,np.nan)
    for j in range(n-FUTURE):
        entry=float(p["open"][j+1])
        hi=float(max(p["high"][j+1:j+FUTURE+1]))
        lo=float(min(p["low"][j+1:j+FUTURE+1]))
        if not (entry>0 and 0<lo<=hi):
            raise ValueError("SOURCE_BLOCKED invalid outcome OHLC")
        result[j]=max(hi/entry-1.,1.-lo/entry)
    return result

def build_panel(raw_events,raw_candles):
    """Reuse frozen 004 integrity validators; attach same-exchange high/low."""
    data=old.prepare(raw_events,raw_candles)
    x=raw_candles.copy()
    x["timestamp"]=pd.to_datetime(x["timestamp"],utc=True)
    full=pd.date_range(old.T0,old.T1-pd.Timedelta(hours=1),freq="h")
    for coin in old.COINS:
        subset=x[(x.market==coin)&(x.timestamp>=old.T0)&(x.timestamp<old.T1)]
        if subset.duplicated("timestamp").any():raise ValueError("PRICE_SOURCE_BLOCKED duplicate 1h bar")
        subset=subset.set_index("timestamp").reindex(full)
        if subset[["high","low"]].isna().any().any():
            raise ValueError("PRICE_SOURCE_BLOCKED missing 1h high/low")
        highs=subset["high"].to_numpy(dtype=float)
        lows=subset["low"].to_numpy(dtype=float)
        if not np.all(np.isfinite(highs)) or not np.all(np.isfinite(lows)):
            raise ValueError("PRICE_SOURCE_BLOCKED nonfinite 1h range")
        if (lows<=0).any() or (highs < lows).any():
            raise ValueError("PRICE_SOURCE_BLOCKED invalid 1h range")
        data[coin]["high"]=highs;data[coin]["low"]=lows
    return data

def market_dataset(p,coin):
    c=p["close"];n=len(c)
    if n!=2952:raise ValueError("SOURCE_BLOCKED expected 2,952 contiguous bars")
    exc=historical_excursions(p)
    total=p["long"]+p["short"]
    count=p["nlong"]+p["nshort"]
    rows=[]
    for i in range(HISTORY,n-FUTURE):
        # Every past excursion reference j <= i-4: all four future bars
        # for the reference event are ALREADY closed by decision time i.
        past_ex=exc[i-HISTORY:i-FUTURE+1]
        if len(past_ex)!=HISTORY-FUTURE+1 or not np.isfinite(past_ex).all():
            raise ValueError("SOURCE_BLOCKED past excursion includes unknown return")
        threshold=nearest_rank(past_ex,.90)
        y=int(exc[i]>=threshold)
        past95=nearest_rank(total[i-HISTORY:i],.95)
        log_close4=abs(float(np.log(c[i]/c[i-4])))
        std24=float(np.std(np.diff(np.log(c[i-24:i+1])),ddof=1))
        range1=float(np.log(p["high"][i]/p["low"][i]))
        liq_rel=float(np.log1p(total[i]/(past95+1.)))
        liq_count=float(np.log1p(count[i]))
        feats=[log_close4,std24,range1,liq_rel,liq_count]
        if not all(math.isfinite(v) for v in feats):
            raise ValueError("SOURCE_BLOCKED nonfinite engineered feature")
        time=p["time"][i]
        rows.append({"index":i,"utc":time.isoformat(),"month":time.strftime("%Y-%m"),
              "x":feats,"y":y,"cutoff_excursion":threshold,
              "observed_future_excursion":float(exc[i]),
              "liq_positions":int(count[i]),
              "liq_usd":float(total[i])})
    return rows

def fit(rows,feature_count):
    train=[r for r in rows if FIRST_TRAIN<=pd.Timestamp(r["utc"])<SEP]
    X=np.array([r["x"][:feature_count] for r in train])
    y=np.array([r["y"] for r in train])
    if len(np.unique(y))!=2:raise ValueError("SOURCE_BLOCKED training has one outcome class")
    m=make_pipeline(StandardScaler(),LogisticRegression(
        C=1.0,penalty="l2",solver="lbfgs",max_iter=1000,random_state=5005))
    m.fit(X,y)
    return m,{"train_samples":len(train),"train_positives":int(sum(y)),
              "train_positive_rate":float(np.mean(y)),"feature_count":feature_count}

def evaluate_probability(rows,base,extended):
    result={}
    for period in ("2026-09","2026-10"):
        rr=[r for r in rows if r["month"]==period]
        X=np.asarray([r["x"] for r in rr],dtype=float)
        y=np.array([r["y"] for r in rr],dtype=int)
        if len(y)<500 or len(set(y))<2:
            raise ValueError("SOURCE_BLOCKED too few hourly risk labels "+period)
        pb=np.clip(base.predict_proba(X[:,:3])[:,1],1e-8,1.-1e-8)
        pe=np.clip(extended.predict_proba(X)[:,1],1e-8,1.-1e-8)
        for r,b,e in zip(rr,pb,pe):
            r["prob_price"]=float(b)
            r["prob_price_plus_liq"]=float(e)
        delta=(y-pb)**2-(y-pe)**2
        weeks=collections.defaultdict(list)
        for r,d in zip(rr,delta):
            iso=pd.Timestamp(r["utc"]).isocalendar()
            weeks[(iso.year,iso.week)].append(float(d))
        rng=random.Random(5005)
        groups=list(weeks.values())
        bootstrap=[]
        for _ in range(2000):
            values=[]
            for _ in groups:
                values.extend(groups[rng.randrange(len(groups))])
            bootstrap.append(statistics.mean(values))
        bootstrap.sort()
        brier_b=float(brier_score_loss(y,pb));brier_e=float(brier_score_loss(y,pe))
        result[period]={"n":len(y),"high_risk_count":int(y.sum()),"base_rate":float(y.mean()),
          "brier_price":brier_b,"brier_plus_liq":brier_e,
          "brier_improvement":brier_b-brier_e,
          "logloss_price":float(log_loss(y,pb)),"logloss_plus_liq":float(log_loss(y,pe)),
          "auc_price":float(roc_auc_score(y,pb)),
          "auc_plus_liq":float(roc_auc_score(y,pe)),
          "mean_prob_price":float(pb.mean()),"mean_prob_plus_liq":float(pe.mean()),
          "weekly_bootstrap_brier_improvement_CI95":{
              "low":bootstrap[49],"high":bootstrap[1950],
              "n_iso_week_blocks":len(groups)}}
    return result

def utility_for_period(rows,p,period,which,fee_bps):
    relevant=[r for r in rows if r["month"]==period and r["index"]%4==0]
    nav=1.;peak=1.;draw=0.;exposure=0;last_pos=0;turnover=0
    gains=[];by_event=[]
    for row in relevant:
        i=row["index"]
        pos=(1 if which=="passive" else
             int(row["prob_price_plus_liq" if which=="extended" else "prob_price"]<=CUT))
        initial_price=float(p["open"][i+1])
        final_price=float(p["close"][i+FUTURE])
        gross=pos*(final_price/initial_price-1)
        change=abs(pos-last_pos)
        cost=change*(fee_bps+SLIP_BPS)/10000
        ret=gross-cost
        nav*=1+ret
        if nav<=0:raise ValueError("SIM_BLOCKED negative NAV for unlevered proxy")
        peak=max(peak,nav);draw=min(draw,nav/peak-1)
        exposure+=pos;turnover+=change
        gains.append(ret);by_event.append({"utc":row["utc"],"position":pos,
                     "ret":ret,"switch":change,"gross":gross})
        last_pos=pos
    if last_pos:
        nav*=1-(fee_bps+SLIP_BPS)/10000
        turnover+=1
        draw=min(draw,nav/peak-1)
    return {"n_4h_blocks":len(relevant),"ending_NAV":nav,"total_net_return_pct":100*(nav-1),
        "max_close_only_drawdown_pct":100*draw,
        "fraction_in_market":exposure/len(relevant) if relevant else None,
        "position_switches_total":turnover,"fee_bps_per_side":fee_bps,
        "four_hour_net_returns":[r["ret"] for r in by_event]}

def gate(stat,utility):
    checks={}
    for coin in old.COINS:
        s=stat[coin];v=utility[coin]
        octo=s["2026-10"];sept=s["2026-09"]
        u=v["2026-10"]["10"];prev=v["2026-09"]["10"]
        checks[coin]={
          "oct_500_and_40_positive_hours":octo["n"]>=500 and octo["high_risk_count"]>=40,
          "oct_brier_gain_at_least_0_005":octo["brier_improvement"]>=.005,
          "oct_week_boot_low_positive":octo["weekly_bootstrap_brier_improvement_CI95"]["low"]>0,
          "sept_positive_brier_gain":sept["brier_improvement"]>0,
          "oct_extended_NAV_above_price_and_passive":
            u["extended"]["ending_NAV"]>max(u["price"]["ending_NAV"],u["passive"]["ending_NAV"]),
          "oct_drawdown_no_worse":
            u["extended"]["max_close_only_drawdown_pct"]>=u["price"]["max_close_only_drawdown_pct"],
          "two_months_positive_relative_to_price":
            all(v[month]["10"]["extended"]["ending_NAV"]>v[month]["10"]["price"]["ending_NAV"]
                for month in ("2026-09","2026-10"))
        }
    candidate=all(all(checks[coin].values()) for coin in old.COINS)
    return {"risk_prediction_shadow_candidate":candidate,
        "by_coin":checks,
        "scientific_verdict":"CANDIDATE_SHADOW_ONLY" if candidate else "NO_GO_ADDITIONAL_LIQUIDATION_RISK_FEATURE",
        "real_capital":"NO_GO"}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    output={"experiment":"LIQMAP-DIAMANTE-005","source":"Ironflow (ironflow.sh)",
      "training":"2026-07-15..2026-08-31 UTC","validation":"September 2026","holdout":"October 2026",
      "not_2026_hypothesis_independent":True,"zero_trading":True,
      "status":"SOURCE_BLOCKED","risk_probability":{},"utility":{},"source_receipts":[]}
    try:
        events,candles,receipts=old.read_source()
        output["source_receipts"]=receipts
        panels=build_panel(events,candles)
        for coin,p in panels.items():
            rows=market_dataset(p,coin)
            base,bmeta=fit(rows,3);plus,pmeta=fit(rows,5)
            stat=evaluate_probability(rows,base,plus)
            output["risk_probability"][coin]=stat
            utility={}
            for period in ("2026-09","2026-10"):
                utility[period]={}
                for fee in FEE_BPS:
                    utility[period][str(fee)]={
                        k:utility_for_period(rows,p,period,k,fee)
                        for k in ("passive","price","extended")}
            output["utility"][coin]=utility
            output.setdefault("fit_summary",{})[coin]={"base":bmeta,"extended":pmeta}
            output.setdefault("source_counts",{})[coin]={
               "complete_price_hours":len(p["close"]),
               "actually_liquidated_positions":p["raw_position_events"]}
            print("LIQMAP005",coin,
                "October Brier gain",round(stat["2026-10"]["brier_improvement"],6),
                "October bootstrap",stat["2026-10"]["weekly_bootstrap_brier_improvement_CI95"],
                "Oct risk gate NAV",round(utility["2026-10"]["10"]["extended"]["ending_NAV"],5),
                "baseline NAV",round(utility["2026-10"]["10"]["price"]["ending_NAV"],5),
                flush=True)
        output["gate"]=gate(output["risk_probability"],output["utility"])
        output["status"]=output["gate"]["scientific_verdict"]
    except Exception as e:
        output["status"]="SOURCE_OR_TECH_BLOCKED"
        output["error"]=type(e).__name__+": "+str(e)
    (OUT/"RESULT.json").write_text(json.dumps(output,indent=2)+"\n")
    lines=["# LIQMAP005 — do liquidation cascades forecast NEXT 4h tail-risk?","",
      "Source: Ironflow (ironflow.sh) actual Hyperliquid liquidation events and same venue hourly OHLC.",
      "Retrospective not truly independent; no trading, no account/funding/executable fills.","",
      "**Status: "+output["status"]+"**",""]
    if "gate" in output:
        lines+=["| Coin | Oct Risk hours | Base Brier | Plus liquidation Brier | Improvement | Sep Brier improvement |",
          "|---|---:|---:|---:|---:|---:|"]
        for coin,st in output["risk_probability"].items():
            x=st["2026-10"];sep=st["2026-09"]
            lines.append("| "+coin+" | "+str(x["high_risk_count"])+"/"+str(x["n"])+
             " | "+str(round(x["brier_price"],6))+" | "+str(round(x["brier_plus_liq"],6))+
             " | "+str(round(x["brier_improvement"],6))+
             " | "+str(round(sep["brier_improvement"],6))+" |")
        lines+=["","## Utility 4-hour long vs cash risk policy in October (10bps fees +5bps slippage per side)","",
        "| Coin | Passive NAV | Price-only gated NAV | Price+liq gated NAV | Exposure fraction ext |",
        "|---|---:|---:|---:|---:|"]
        for coin,v in output["utility"].items():
            a=v["2026-10"]["10"]
            lines.append("| "+coin+" | "+
             str(round(a["passive"]["ending_NAV"],6))+" | "+
             str(round(a["price"]["ending_NAV"],6))+" | "+
             str(round(a["extended"]["ending_NAV"],6))+" | "+
             str(round(a["extended"]["fraction_in_market"],4))+" |")
        lines+=["","### Scientific gate","",json.dumps(output["gate"],indent=2),
          "Full Brier/log-loss/AUC, ISO weekly bootstrap, 4h long/cash costs and receipts in RESULT.json.",
          "No transaction profits claimed. Source data used after the fact and prior liquidation research affected hypothesis choice."]
    else:lines+=["","Reason: "+str(output.get("error"))]
    (OUT/"REPORT.md").write_text("\n".join(lines)+"\n")
    print("LIQMAP005_VERDICT",output["status"],flush=True)
    if output["status"]=="SOURCE_OR_TECH_BLOCKED":
        raise RuntimeError(output.get("error"))
if __name__=="__main__":main()
