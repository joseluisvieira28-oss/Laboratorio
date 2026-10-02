#!/usr/bin/env python3
"""
OPTIONS-SPOTPERP-001-V2.1 -> MEXC Event Futures short-horizon proxy transfer V1.1.

Uses only prior signal_date + position fields from immutable prior artifacts.
Does not use prior forward returns / PnL / skew magnitude / RV weights in scoring.
No auth, no orders, no 2026.
"""
import argparse
import csv
import json
import math
import os
import time
from datetime import date, datetime, timedelta, timezone

import requests
from scipy.stats import binomtest

MEXC_URL="https://contract.mexc.com/api/v1/contract/kline/index_price/BTC_USDT"
INTERVAL="Min30"
STEP=1800
HORIZONS=[30,60]
PAYOUTS=[0.70,0.75,0.80,0.85,0.90]
P0=1/1.8
Z95=1.959963984540054
BH_Q=0.05
HEADERS={"User-Agent":"crypto-lab-options-v21-event-transfer-v1.1"}

DISC_SIGNAL_START=date(2022,1,1)
DISC_SIGNAL_END=date(2025,1,1)
OOS_SIGNAL_START=date(2025,1,1)
OOS_SIGNAL_END=date(2025,12,30)  # source ledger last allowed 2025-12-29

def load_signal_ledger(path,start,end):
    out=[]
    with open(path,newline="",encoding="utf-8") as f:
        r=csv.DictReader(f)
        required={"signal_date","position"}
        if not required.issubset(set(r.fieldnames or [])):
            raise RuntimeError(f"missing required signal columns in {path}")
        for row in r:
            d=date.fromisoformat(row["signal_date"])
            if not (start<=d<end):
                continue
            p=int(row["position"])
            if p not in (-1,0,1):
                raise RuntimeError(f"invalid position {p} on {d}")
            out.append({"signal_date":d,"position":p})
    dates=[x["signal_date"] for x in out]
    if len(dates)!=len(set(dates)):
        raise RuntimeError(f"duplicate signal dates in {path}")
    if any(d.year>=2026 for d in dates):
        raise RuntimeError("2026 signal leak")
    return sorted(out,key=lambda x:x["signal_date"])

def month_starts(start_year,end_year_inclusive):
    for y in range(start_year,end_year_inclusive+1):
        for m in range(1,13):
            yield y,m

def month_bounds(y,m):
    start=datetime(y,m,1,tzinfo=timezone.utc)
    if m==12:
        end=datetime(y+1,1,1,tzinfo=timezone.utc)
    else:
        end=datetime(y,m+1,1,tzinfo=timezone.utc)
    return start,end

def fetch_month(y,m):
    start,end=month_bounds(y,m)
    params={"interval":INTERVAL,"start":int((start-timedelta(hours=1)).timestamp()),"end":int((end+timedelta(hours=1)).timestamp())}
    last=None
    for attempt in range(5):
        try:
            r=requests.get(MEXC_URL,params=params,headers=HEADERS,timeout=30)
            r.raise_for_status()
            j=r.json()
            if not isinstance(j,dict) or j.get("success") is not True:
                raise RuntimeError(f"MEXC non-success {j}")
            d=j.get("data") or {}
            prices={}
            for s,p in zip(d.get("time") or [],d.get("close") or []):
                try:
                    mapped=int(s)+STEP
                    prices[mapped]=float(p)
                except Exception:
                    continue
            return r.url,prices
        except Exception as e:
            last=e
            time.sleep(0.6*(attempt+1))
    raise last

def fetch_years(start_year,end_year):
    prices={}
    receipts=[]
    for y,m in month_starts(start_year,end_year):
        url,p=fetch_month(y,m)
        prices.update(p)
        vals=sorted(p)
        receipts.append({
          "year":y,"month":m,"url":url,"rows":len(p),
          "first":vals[0] if vals else None,"last":vals[-1] if vals else None
        })
        time.sleep(0.10)
    return prices,receipts

def entry_ts(signal_date):
    d=signal_date+timedelta(days=1)
    return int(datetime.combine(d,datetime.min.time(),tzinfo=timezone.utc).timestamp())

def wilson(w,l):
    n=w+l
    if not n:return None
    p=w/n;z2=Z95*Z95
    return (p+z2/(2*n)-Z95*math.sqrt((p*(1-p)+z2/(4*n))/n))/(1+z2/n)

def pval(w,l):
    n=w+l
    return None if not n else float(binomtest(w,n,P0,alternative="greater").pvalue)

def score(signals,prices,horizon):
    w=l=ties=missing=flat=0
    by_year={}
    for s in signals:
        if s["position"]==0:
            flat+=1;continue
        t=entry_ts(s["signal_date"])
        aft=t+horizon*60
        if t not in prices or aft not in prices:
            missing+=1;continue
        move=prices[aft]-prices[t]
        yr=s["signal_date"].year
        by_year.setdefault(yr,{"wins":0,"losses":0,"ties":0})
        if move==0:
            ties+=1;by_year[yr]["ties"]+=1
        elif (move>0 and s["position"]>0) or (move<0 and s["position"]<0):
            w+=1;by_year[yr]["wins"]+=1
        else:
            l+=1;by_year[yr]["losses"]+=1
    n=w+l
    year_acc={}
    for yr,z in by_year.items():
        nn=z["wins"]+z["losses"]
        year_acc[str(yr)]=z["wins"]/nn if nn else None
    den=w+l+ties
    out={
      "wins":w,"losses":l,"ties":ties,"missing":missing,"flat":flat,
      "non_ties":n,"accuracy":w/n if n else None,"wilson95_lower":wilson(w,l),
      "p_value_vs_be80":pval(w,l),"year_accuracy":year_acc,
      "required_payout_for_ev0":l/w if w else None,
    }
    for p in PAYOUTS:out[f"ev{int(p*100)}"]=(w*p-l)/den if den else None
    return out

def basic(r):
    yrs=r["year_accuracy"]
    return (
      r["non_ties"]>=800
      and r["accuracy"] is not None and r["accuracy"]>P0
      and r["wilson95_lower"] is not None and r["wilson95_lower"]>0.50
      and all(yrs.get(str(y)) is not None and yrs[str(y)]>0.50 for y in (2022,2023,2024))
      and r["p_value_vs_be80"] is not None
    )

def bh(cells):
    e=[c for c in cells if c["basic_pass"]]
    e.sort(key=lambda x:x["discovery"]["p_value_vs_be80"])
    m=len(e);cut=None
    for rank,c in enumerate(e,1):
        if c["discovery"]["p_value_vs_be80"]<=rank/m*BH_Q:
            cut=c["discovery"]["p_value_vs_be80"]
    return ([] if cut is None else [c for c in e if c["discovery"]["p_value_vs_be80"]<=cut]),m,cut

def oos_pass(r):
    return (
      r["non_ties"]>=250
      and r["accuracy"] is not None and r["accuracy"]>P0
      and r["wilson95_lower"] is not None and r["wilson95_lower"]>0.50
      and r["p_value_vs_be80"] is not None and r["p_value_vs_be80"]<0.05
      and r["ev80"] is not None and r["ev80"]>0
    )

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--discovery-ledger",required=True)
    ap.add_argument("--oos-ledger",required=True)
    ap.add_argument("--output",required=True)
    a=ap.parse_args()

    disc_signals=load_signal_ledger(a.discovery_ledger,DISC_SIGNAL_START,DISC_SIGNAL_END)
    oos_signals=load_signal_ledger(a.oos_ledger,OOS_SIGNAL_START,OOS_SIGNAL_END)

    if set(x["signal_date"] for x in disc_signals)&set(x["signal_date"] for x in oos_signals):
        raise RuntimeError("discovery/OOS signal overlap")

    # Discovery price outcomes only. OOS price source stays unopened until BH selection.
    disc_prices,disc_receipts=fetch_years(2022,2024)
    disc=[]
    for h in HORIZONS:
        r=score(disc_signals,disc_prices,h)
        disc.append({"horizon_min":h,"discovery":r,"basic_pass":basic(r)})
    selected,m,cut=bh(disc)

    oos_prices_accessed=False
    oos_receipts=[]
    oos=[];survivors=[]
    if selected:
        oos_prices,oos_receipts=fetch_years(2025,2025)
        oos_prices_accessed=True
        for c in selected:
            r=score(oos_signals,oos_prices,c["horizon_min"])
            ok=oos_pass(r)
            x={"horizon_min":c["horizon_min"],"oos":r,"pass":ok}
            oos.append(x)
            if ok:
                survivors.append({"horizon_min":c["horizon_min"],"discovery":c["discovery"],"oos":r})

    usable=sum(x["discovery"]["non_ties"] for x in disc)
    verdict=(
      "SOURCE_BLOCKED" if usable==0
      else ("OPTIONS_V21_TO_EVENT_FUTURES_SHORT_HORIZON_PROXY_CANDIDATE" if survivors else "NO_SURVIVOR_AT_FROZEN_V11_GATE")
    )

    report={
      "lab":"MEXC_EVENT_FUTURES_OPTIONS_V21_TRANSFER_V1.1",
      "generated_at_utc":datetime.now(timezone.utc).isoformat(),
      "signal_source":"IMMUTABLE_PRIOR_OPTIONS_V21_ARTIFACTS_SIGNAL_DATE_AND_POSITION_ONLY",
      "primary_horizons_min":HORIZONS,
      "source_unobservable_horizons_min":[10],
      "nonindependent_reference_horizons_min":[1440],
      "price_proxy":"MEXC_BTC_USDT_INDEX_PRICE_MIN30",
      "clock_mapping":"RAW_PLUS_1800_SECONDS",
      "discovery_signal_count":len(disc_signals),
      "oos_signal_count":len(oos_signals),
      "discovery_price_receipts":disc_receipts,
      "oos_price_source_accessed":oos_prices_accessed,
      "oos_price_receipts":oos_receipts,
      "discovery_cells":disc,
      "bh_eligible_count":m,"bh_cutoff_p":cut,
      "bh_selected_horizons":[x["horizon_min"] for x in selected],
      "oos_cells":oos,"survivors":survivors,"verdict":verdict,
      "year_2026":"LOCKED_NOT_FETCHED_OR_SCORED",
      "exact_event_futures":"NOT_PROVEN",
      "authenticated_requests":0,"orders":0,"account_mutations":0,
    }
    os.makedirs(a.output,exist_ok=True)
    p=os.path.join(a.output,"options_v21_transfer_v11.json")
    with open(p,"w",encoding="utf-8") as f:json.dump(report,f,indent=2,sort_keys=True)
    print(json.dumps({
      "verdict":verdict,
      "discovery_signal_count":len(disc_signals),
      "oos_signal_count":len(oos_signals),
      "discovery":[{
        "horizon_min":x["horizon_min"],"n":x["discovery"]["non_ties"],
        "accuracy":x["discovery"]["accuracy"],"wilson95_lower":x["discovery"]["wilson95_lower"],
        "p":x["discovery"]["p_value_vs_be80"],"ev80":x["discovery"]["ev80"],
        "required_payout":x["discovery"]["required_payout_for_ev0"],
        "year_accuracy":x["discovery"]["year_accuracy"],"basic_pass":x["basic_pass"]
      } for x in disc],
      "bh_selected_horizons":report["bh_selected_horizons"],
      "oos_price_source_accessed":oos_prices_accessed,
      "oos":[{
        "horizon_min":x["horizon_min"],"n":x["oos"]["non_ties"],
        "accuracy":x["oos"]["accuracy"],"wilson95_lower":x["oos"]["wilson95_lower"],
        "p":x["oos"]["p_value_vs_be80"],"ev80":x["oos"]["ev80"],
        "required_payout":x["oos"]["required_payout_for_ev0"],"pass":x["pass"]
      } for x in oos],
      "survivor_count":len(survivors),
      "year_2026":"LOCKED"
    },indent=2,sort_keys=True))
    print("WROTE",p)

if __name__=="__main__":main()
