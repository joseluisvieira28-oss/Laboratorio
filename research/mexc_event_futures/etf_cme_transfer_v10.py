#!/usr/bin/env python3
"""
MEXC Event Futures Lab V1.0 — ETF-CME external-signal transfer.

Research only.
- Public CFTC source.
- Public MEXC standard-futures index-price proxy.
- No authentication, no orders, no 2026 scoring.
"""
import csv
import io
import json
import math
import os
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import requests
from scipy.stats import binomtest

CFTC_DATASET = "6dca-aqww"
CFTC_URL = f"https://publicreporting.cftc.gov/resource/{CFTC_DATASET}.csv"
CFTC_CODE = "133741"

MEXC_BASE = "https://contract.mexc.com"
MEXC_SYMBOL = "BTC_USDT"
MEXC_KLINE = f"{MEXC_BASE}/api/v1/contract/kline/index_price/{MEXC_SYMBOL}"

HORIZONS = [10, 30, 60, 1440]
PAYOUTS = [0.70, 0.75, 0.80, 0.85, 0.90]
P0 = 1.0 / 1.8
Z95 = 1.959963984540054
BH_Q = 0.05
STEP = 300

SOURCE_START = datetime(2021,1,1,tzinfo=timezone.utc)
SOURCE_END = datetime(2026,1,1,tzinfo=timezone.utc)
DISC_START = datetime(2022,1,1,tzinfo=timezone.utc)
DISC_END = datetime(2025,1,1,tzinfo=timezone.utc)
OOS_START = DISC_END
OOS_END = datetime(2026,1,1,tzinfo=timezone.utc)

HEADERS = {"User-Agent":"crypto-lab-event-futures-etf-transfer-v1.0"}

def fetch_cftc():
    where = (
        f"cftc_contract_market_code='{CFTC_CODE}' AND "
        f"report_date_as_yyyy_mm_dd >= '{SOURCE_START.date().isoformat()}T00:00:00.000' AND "
        f"report_date_as_yyyy_mm_dd < '{SOURCE_END.date().isoformat()}T00:00:00.000'"
    )
    params = {
        "$limit":"2000",
        "$order":"report_date_as_yyyy_mm_dd ASC",
        "$where":where,
    }
    url = CFTC_URL + "?" + urlencode(params)
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    rows = list(csv.DictReader(io.StringIO(r.text.lstrip("\ufeff"))))
    out = []
    for row in rows:
        d = datetime.fromisoformat(row["report_date_as_yyyy_mm_dd"].replace("Z","+00:00")).date()
        obs = {
            "date":d,
            "open_interest":float(row["open_interest_all"]),
            "long":float(row["noncomm_positions_long_all"]),
            "short":float(row["noncomm_positions_short_all"]),
        }
        if obs["open_interest"] <= 0:
            raise RuntimeError(f"invalid open interest {d}")
        out.append(obs)
    dates=[x["date"] for x in out]
    if not out:
        raise RuntimeError("CFTC source returned zero rows")
    if dates != sorted(dates) or len(dates) != len(set(dates)):
        raise RuntimeError("CFTC chronology/uniqueness failure")
    return url,out

def signal_rows(obs):
    out=[]
    for prev,cur in zip(obs,obs[1:]):
        delta_net=(cur["long"]-cur["short"])-(prev["long"]-prev["short"])
        value=delta_net/cur["open_interest"]
        direction=1 if value>0 else (-1 if value<0 else 0)
        entry=datetime.combine(cur["date"]+timedelta(days=8), datetime.min.time(), tzinfo=timezone.utc)
        out.append({
            "previous_date":prev["date"].isoformat(),
            "current_date":cur["date"].isoformat(),
            "signal_value":value,
            "direction":direction,
            "entry_utc":entry,
        })
    return out

def mexc_window(entry):
    start=int((entry-timedelta(minutes=10)).timestamp())
    end=int((entry+timedelta(days=1,minutes=5)).timestamp())
    params={"interval":"Min5","start":start,"end":end}
    last=None
    for attempt in range(5):
        try:
            r=requests.get(MEXC_KLINE,params=params,headers=HEADERS,timeout=25)
            r.raise_for_status()
            j=r.json()
            if not isinstance(j,dict) or j.get("success") is not True:
                raise RuntimeError(f"MEXC non-success {j}")
            d=j.get("data") or {}
            times=d.get("time") or []
            closes=d.get("close") or []
            prices={}
            for raw_t,p in zip(times,closes):
                mapped=int(raw_t)+STEP
                prices[mapped]=float(p)
            return r.url,prices
        except Exception as e:
            last=e
            time.sleep(0.5*(attempt+1))
    raise last

def wilson_lower(w,l):
    n=w+l
    if n<=0: return None
    p=w/n
    z2=Z95*Z95
    center=p+z2/(2*n)
    rad=Z95*math.sqrt((p*(1-p)+z2/(4*n))/n)
    return (center-rad)/(1+z2/n)

def pvalue(w,l):
    n=w+l
    return None if n<=0 else float(binomtest(w,n,P0,alternative="greater").pvalue)

def score(records,horizon,period_start,period_end):
    w=l=ties=missing=flat=0
    chronological=[]
    for rec in records:
        entry=rec["entry_utc"]
        if not (period_start <= entry < period_end):
            continue
        if rec["direction"]==0:
            flat+=1
            continue
        key=int(entry.timestamp())
        after=key+horizon*60
        prices=rec.get("prices") or {}
        if key not in prices or after not in prices:
            missing+=1
            continue
        move=prices[after]-prices[key]
        if move==0:
            ties+=1
            chronological.append((entry,"T"))
        elif (move>0 and rec["direction"]>0) or (move<0 and rec["direction"]<0):
            w+=1
            chronological.append((entry,"W"))
        else:
            l+=1
            chronological.append((entry,"L"))
    n=w+l
    acc=w/n if n else None
    thirds=[]
    non_ties=[x for x in chronological if x[1]!="T"]
    if non_ties:
        size=len(non_ties)
        for k in range(3):
            a=(k*size)//3
            b=((k+1)*size)//3
            seg=non_ties[a:b]
            sw=sum(1 for _,v in seg if v=="W")
            sl=sum(1 for _,v in seg if v=="L")
            thirds.append(sw/(sw+sl) if sw+sl else None)
    else:
        thirds=[None,None,None]
    denom=w+l+ties
    out={
        "wins":w,"losses":l,"ties":ties,"missing":missing,"flat_signals":flat,
        "non_ties":n,"accuracy":acc,"wilson95_lower":wilson_lower(w,l),
        "p_value_vs_be80":pvalue(w,l),"third_accuracies":thirds,
        "required_payout_for_ev0":(l/w) if w else None,
    }
    for p in PAYOUTS:
        out[f"ev{int(p*100)}"]=((w*p-l)/denom) if denom else None
    return out

def basic_pass(r):
    return (
        r["non_ties"]>=100
        and r["accuracy"] is not None and r["accuracy"]>P0
        and r["wilson95_lower"] is not None and r["wilson95_lower"]>0.50
        and all(x is not None and x>0.50 for x in r["third_accuracies"])
        and r["p_value_vs_be80"] is not None
    )

def bh_select(cells):
    eligible=[c for c in cells if c["basic_pass"]]
    eligible.sort(key=lambda x:x["discovery"]["p_value_vs_be80"])
    m=len(eligible)
    cutoff=None
    for rank,c in enumerate(eligible,1):
        if c["discovery"]["p_value_vs_be80"] <= rank/m*BH_Q:
            cutoff=c["discovery"]["p_value_vs_be80"]
    selected=[] if cutoff is None else [c for c in eligible if c["discovery"]["p_value_vs_be80"]<=cutoff]
    return selected,m,cutoff

def oos_pass(r):
    return (
        r["non_ties"]>=30
        and r["accuracy"] is not None and r["accuracy"]>P0
        and r["wilson95_lower"] is not None and r["wilson95_lower"]>0.50
        and r["p_value_vs_be80"] is not None and r["p_value_vs_be80"]<0.05
        and r["ev80"] is not None and r["ev80"]>0
    )

def main():
    outdir="artifacts/mexc_event_futures"
    os.makedirs(outdir,exist_ok=True)
    cftc_url,obs=fetch_cftc()
    signals=signal_rows(obs)

    # Fetch MEXC only for 2022-2025 entries. 2026 is never scored/fetched.
    fetch_errors=[]
    fetched=0
    for rec in signals:
        entry=rec["entry_utc"]
        if not (DISC_START <= entry < OOS_END):
            continue
        try:
            url,prices=mexc_window(entry)
            rec["prices"]=prices
            rec["mexc_url"]=url
            fetched+=1
        except Exception as e:
            rec["prices"]={}
            rec["mexc_error"]=repr(e)
            fetch_errors.append({"entry_utc":entry.isoformat(),"error":repr(e)})
        time.sleep(0.08)

    discovery=[]
    for h in HORIZONS:
        r=score(signals,h,DISC_START,DISC_END)
        discovery.append({
            "horizon_min":h,
            "discovery":r,
            "basic_pass":basic_pass(r),
        })

    selected,m,cutoff=bh_select(discovery)
    selected_h={c["horizon_min"] for c in selected}

    oos=[]
    survivors=[]
    for c in selected:
        h=c["horizon_min"]
        r=score(signals,h,OOS_START,OOS_END)
        passed=oos_pass(r)
        row={"horizon_min":h,"oos":r,"pass":passed}
        oos.append(row)
        if passed:
            survivors.append({
                "horizon_min":h,
                "discovery":c["discovery"],
                "oos":r,
            })

    source_coverage={
        "cftc_observations":len(obs),
        "derived_signals":len(signals),
        "price_windows_fetched":fetched,
        "price_fetch_errors":len(fetch_errors),
        "discovery_signal_count":sum(1 for x in signals if DISC_START<=x["entry_utc"]<DISC_END),
        "oos_signal_count":sum(1 for x in signals if OOS_START<=x["entry_utc"]<OOS_END),
    }

    # If every discovery cell has zero usable observations, classify source-blocked.
    usable=sum(c["discovery"]["non_ties"] for c in discovery)
    verdict=(
        "SOURCE_BLOCKED"
        if usable==0
        else ("EXTERNAL_SIGNAL_EVENT_FUTURES_PROXY_CANDIDATE" if survivors else "NO_SURVIVOR_AT_FROZEN_V10_GATE")
    )

    report={
        "lab":"MEXC_EVENT_FUTURES_ETF_CME_TRANSFER_V1.0",
        "generated_at_utc":datetime.now(timezone.utc).isoformat(),
        "signal_strategy":"ETF-CME-INSTFLOW-001",
        "cftc_dataset":CFTC_DATASET,
        "cftc_contract_code":CFTC_CODE,
        "cftc_query_url":cftc_url,
        "price_proxy":"MEXC_BTC_USDT_STANDARD_FUTURES_INDEX_PRICE_MIN5",
        "clock_mapping":"RAW_KLINE_TIMESTAMP_PLUS_300_SECONDS",
        "discovery_period":["2022-01-01","2025-01-01"],
        "oos_period":["2025-01-01","2026-01-01"],
        "year_2026":"LOCKED_NOT_SCORED_OR_FETCHED",
        "source_coverage":source_coverage,
        "fetch_errors":fetch_errors[:100],
        "discovery_cells":discovery,
        "bh_eligible_count":m,
        "bh_cutoff_p":cutoff,
        "bh_selected_horizons":sorted(selected_h),
        "oos_cells":oos,
        "survivors":survivors,
        "verdict":verdict,
        "exact_event_futures":"NOT_PROVEN",
        "authenticated_requests":0,
        "orders":0,
        "account_mutations":0,
    }
    path=f"{outdir}/etf_cme_transfer_v10.json"
    with open(path,"w",encoding="utf-8") as f:
        json.dump(report,f,indent=2,sort_keys=True,default=str)

    print(json.dumps({
        "verdict":verdict,
        "source_coverage":source_coverage,
        "discovery":[
            {
                "horizon_min":c["horizon_min"],
                "n":c["discovery"]["non_ties"],
                "accuracy":c["discovery"]["accuracy"],
                "wilson95_lower":c["discovery"]["wilson95_lower"],
                "p":c["discovery"]["p_value_vs_be80"],
                "ev80":c["discovery"]["ev80"],
                "basic_pass":c["basic_pass"],
            } for c in discovery
        ],
        "bh_eligible_count":m,
        "bh_selected_horizons":sorted(selected_h),
        "oos":[
            {
                "horizon_min":x["horizon_min"],
                "n":x["oos"]["non_ties"],
                "accuracy":x["oos"]["accuracy"],
                "p":x["oos"]["p_value_vs_be80"],
                "ev80":x["oos"]["ev80"],
                "pass":x["pass"],
            } for x in oos
        ],
        "survivor_count":len(survivors),
        "year_2026":"LOCKED_NOT_SCORED_OR_FETCHED",
        "authenticated_requests":0,
        "orders":0,
    },indent=2,sort_keys=True))
    print("WROTE",path)

if __name__=="__main__":
    main()
