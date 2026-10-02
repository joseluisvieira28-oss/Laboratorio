#!/usr/bin/env python3
"""
ETF-CME -> Event Futures Min30 proxy transfer V1.0.2.

Research only. Public CFTC + public MEXC. No authentication, no orders, no 2026 scoring.
"""
import csv, io, json, math, os, time
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
import requests
from scipy.stats import binomtest

CFTC_URL="https://publicreporting.cftc.gov/resource/6dca-aqww.csv"
CFTC_CODE="133741"
MEXC_URL="https://contract.mexc.com/api/v1/contract/kline/index_price/BTC_USDT"
HORIZONS=[30,60,1440]
PAYOUTS=[0.70,0.75,0.80,0.85,0.90]
P0=1/1.8
BH_Q=0.05
Z95=1.959963984540054
RAW_INTERVAL="Min30"
STEP=1800
DISC_START=datetime(2022,1,1,tzinfo=timezone.utc)
DISC_END=datetime(2025,1,1,tzinfo=timezone.utc)
OOS_START=DISC_END
OOS_END=datetime(2026,1,1,tzinfo=timezone.utc)
SOURCE_START=datetime(2021,1,1,tzinfo=timezone.utc)
HEADERS={"User-Agent":"crypto-lab-etf-cme-event-transfer-v1.0.2"}

def fetch_cftc():
    where=(
      f"cftc_contract_market_code='{CFTC_CODE}' AND "
      f"report_date_as_yyyy_mm_dd >= '{SOURCE_START.date().isoformat()}T00:00:00.000' AND "
      f"report_date_as_yyyy_mm_dd < '{OOS_END.date().isoformat()}T00:00:00.000'"
    )
    url=CFTC_URL+"?"+urlencode({"$limit":"2000","$order":"report_date_as_yyyy_mm_dd ASC","$where":where})
    r=requests.get(url,headers=HEADERS,timeout=30); r.raise_for_status()
    rows=list(csv.DictReader(io.StringIO(r.text.lstrip("\ufeff"))))
    obs=[]
    for row in rows:
        d=datetime.fromisoformat(row["report_date_as_yyyy_mm_dd"].replace("Z","+00:00")).date()
        oi=float(row["open_interest_all"])
        if oi<=0: raise RuntimeError(f"invalid OI {d}")
        obs.append({
          "date":d,"oi":oi,
          "long":float(row["noncomm_positions_long_all"]),
          "short":float(row["noncomm_positions_short_all"]),
        })
    dates=[x["date"] for x in obs]
    if not obs or dates!=sorted(dates) or len(dates)!=len(set(dates)):
        raise RuntimeError("CFTC chronology/uniqueness failure")
    return url,obs

def make_signals(obs):
    out=[]
    for p,c in zip(obs,obs[1:]):
        value=((c["long"]-c["short"])-(p["long"]-p["short"]))/c["oi"]
        direction=1 if value>0 else (-1 if value<0 else 0)
        entry=datetime.combine(c["date"]+timedelta(days=8),datetime.min.time(),tzinfo=timezone.utc)
        out.append({
          "previous_date":p["date"].isoformat(),
          "current_date":c["date"].isoformat(),
          "signal_value":value,
          "direction":direction,
          "entry_utc":entry,
        })
    return out

def fetch_price_window(entry):
    # Need prior raw 23:30 bar whose close becomes observable at exact 00:00 entry.
    start=int((entry-timedelta(hours=1)).timestamp())
    end=int((entry+timedelta(days=1,hours=1)).timestamp())
    last=None
    for i in range(5):
        try:
            r=requests.get(MEXC_URL,params={"interval":RAW_INTERVAL,"start":start,"end":end},headers=HEADERS,timeout=25)
            r.raise_for_status()
            j=r.json()
            if not isinstance(j,dict) or j.get("success") is not True:
                raise RuntimeError(f"non-success {j}")
            d=j.get("data") or {}
            prices={}
            for s,p in zip(d.get("time") or [],d.get("close") or []):
                prices[int(s)+STEP]=float(p)
            return prices
        except Exception as e:
            last=e; time.sleep(0.5*(i+1))
    raise last

def wilson(w,l):
    n=w+l
    if not n:return None
    p=w/n;z2=Z95*Z95
    return (p+z2/(2*n)-Z95*math.sqrt((p*(1-p)+z2/(4*n))/n))/(1+z2/n)

def pv(w,l):
    n=w+l
    return None if not n else float(binomtest(w,n,P0,alternative="greater").pvalue)

def score(signals,h,start,end):
    w=l=ties=missing=flat=0
    seq=[]
    for rec in signals:
        entry=rec["entry_utc"]
        if not (start<=entry<end):continue
        if rec["direction"]==0:
            flat+=1;continue
        t=int(entry.timestamp());aft=t+h*60
        pr=rec.get("prices") or {}
        if t not in pr or aft not in pr:
            missing+=1;continue
        d=pr[aft]-pr[t]
        if d==0:
            ties+=1;seq.append("T")
        elif (d>0 and rec["direction"]>0) or (d<0 and rec["direction"]<0):
            w+=1;seq.append("W")
        else:
            l+=1;seq.append("L")
    nt=[x for x in seq if x!="T"];n=w+l
    thirds=[]
    for k in range(3):
        a=k*len(nt)//3;b=(k+1)*len(nt)//3;s=nt[a:b]
        sw=s.count("W");sl=s.count("L")
        thirds.append(sw/(sw+sl) if sw+sl else None)
    den=w+l+ties
    out={
      "wins":w,"losses":l,"ties":ties,"missing":missing,"flat":flat,
      "non_ties":n,"accuracy":w/n if n else None,
      "wilson95_lower":wilson(w,l),"p_value_vs_be80":pv(w,l),
      "third_accuracies":thirds,
      "required_payout_for_ev0":l/w if w else None,
    }
    for p in PAYOUTS:out[f"ev{int(p*100)}"]=(w*p-l)/den if den else None
    return out

def basic(r):
    return (
      r["non_ties"]>=100 and r["accuracy"] is not None and r["accuracy"]>P0
      and r["wilson95_lower"] is not None and r["wilson95_lower"]>0.50
      and all(x is not None and x>0.50 for x in r["third_accuracies"])
      and r["p_value_vs_be80"] is not None
    )

def bh(cells):
    e=[x for x in cells if x["basic_pass"]];e.sort(key=lambda x:x["discovery"]["p_value_vs_be80"])
    m=len(e);cut=None
    for i,x in enumerate(e,1):
        if x["discovery"]["p_value_vs_be80"]<=i/m*BH_Q:cut=x["discovery"]["p_value_vs_be80"]
    return ([] if cut is None else [x for x in e if x["discovery"]["p_value_vs_be80"]<=cut]),m,cut

def oos_pass(r):
    return (
      r["non_ties"]>=30 and r["accuracy"] is not None and r["accuracy"]>P0
      and r["wilson95_lower"] is not None and r["wilson95_lower"]>0.50
      and r["p_value_vs_be80"] is not None and r["p_value_vs_be80"]<0.05
      and r["ev80"] is not None and r["ev80"]>0
    )

def main():
    os.makedirs("artifacts/mexc_event_futures",exist_ok=True)
    cftc_url,obs=fetch_cftc();signals=make_signals(obs)
    fetch_errors=[];fetched=0;windows_with_entry=0
    for rec in signals:
        e=rec["entry_utc"]
        if not (DISC_START<=e<OOS_END):continue
        try:
            rec["prices"]=fetch_price_window(e);fetched+=1
            if int(e.timestamp()) in rec["prices"]:windows_with_entry+=1
        except Exception as exc:
            rec["prices"]={};fetch_errors.append({"entry":e.isoformat(),"error":repr(exc)})
        time.sleep(0.08)

    disc=[]
    for h in HORIZONS:
        r=score(signals,h,DISC_START,DISC_END)
        disc.append({"horizon_min":h,"discovery":r,"basic_pass":basic(r)})
    selected,m,cut=bh(disc)

    oos=[];survivors=[]
    for c in selected:
        r=score(signals,c["horizon_min"],OOS_START,OOS_END)
        ok=oos_pass(r)
        row={"horizon_min":c["horizon_min"],"oos":r,"pass":ok};oos.append(row)
        if ok:survivors.append({"horizon_min":c["horizon_min"],"discovery":c["discovery"],"oos":r})

    usable=sum(x["discovery"]["non_ties"] for x in disc)
    verdict="SOURCE_BLOCKED" if usable==0 else ("ETF_CME_TO_EVENT_FUTURES_MIN30_PRICE_PROXY_CANDIDATE" if survivors else "NO_SURVIVOR_AT_FROZEN_V102_GATE")
    report={
      "lab":"ETF_CME_EVENT_FUTURES_MIN30_TRANSFER_V1.0.2",
      "generated_at_utc":datetime.now(timezone.utc).isoformat(),
      "cftc_url":cftc_url,"cftc_observations":len(obs),"derived_signals":len(signals),
      "price_proxy":"MEXC_BTC_USDT_INDEX_PRICE_MIN30","clock_mapping":"RAW_PLUS_1800_SECONDS",
      "source_unobservable_horizons_min":[10],
      "price_windows_fetched":fetched,"windows_with_exact_entry":windows_with_entry,
      "price_fetch_errors":fetch_errors[:100],
      "discovery_signal_count":sum(1 for x in signals if DISC_START<=x["entry_utc"]<DISC_END),
      "oos_signal_count":sum(1 for x in signals if OOS_START<=x["entry_utc"]<OOS_END),
      "discovery_cells":disc,"bh_eligible_count":m,"bh_cutoff_p":cut,
      "bh_selected_horizons":[x["horizon_min"] for x in selected],
      "oos_cells":oos,"survivors":survivors,"verdict":verdict,
      "year_2026":"LOCKED_NOT_SCORED_OR_FETCHED","exact_event_futures":"NOT_PROVEN",
      "authenticated_requests":0,"orders":0,"account_mutations":0,
    }
    p="artifacts/mexc_event_futures/etf_cme_min30_transfer_v102.json"
    with open(p,"w",encoding="utf-8") as f:json.dump(report,f,indent=2,sort_keys=True,default=str)
    print(json.dumps({
      "verdict":verdict,
      "price_windows_fetched":fetched,"windows_with_exact_entry":windows_with_entry,
      "discovery_signal_count":report["discovery_signal_count"],"oos_signal_count":report["oos_signal_count"],
      "discovery":[{
        "horizon_min":x["horizon_min"],"n":x["discovery"]["non_ties"],
        "accuracy":x["discovery"]["accuracy"],"wilson95_lower":x["discovery"]["wilson95_lower"],
        "p":x["discovery"]["p_value_vs_be80"],"ev80":x["discovery"]["ev80"],
        "required_payout":x["discovery"]["required_payout_for_ev0"],"basic_pass":x["basic_pass"]
      } for x in disc],
      "bh_selected_horizons":report["bh_selected_horizons"],
      "oos":[{
        "horizon_min":x["horizon_min"],"n":x["oos"]["non_ties"],"accuracy":x["oos"]["accuracy"],
        "wilson95_lower":x["oos"]["wilson95_lower"],"p":x["oos"]["p_value_vs_be80"],
        "ev80":x["oos"]["ev80"],"required_payout":x["oos"]["required_payout_for_ev0"],"pass":x["pass"]
      } for x in oos],
      "survivor_count":len(survivors),"2026":"LOCKED"
    },indent=2,sort_keys=True))
    print("WROTE",p)

if __name__=="__main__":main()
