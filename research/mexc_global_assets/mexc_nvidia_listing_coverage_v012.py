#!/usr/bin/env python3
"""Locate earliest usable MEXC NVIDIA_USDT cash-open history. SOURCE-ONLY."""
from __future__ import annotations
import json,time
from datetime import date,datetime,timedelta,timezone
from pathlib import Path
import requests

OUT=Path("artifacts/mexc_global_assets/nvidia_listing_coverage_v012")
UA="CryptoLab-MEXC-NVIDIA-ListingCoverage/0.1.2"
START=date(2026,4,1); END=date(2026,9,29)
HOLIDAYS={date(2026,4,3),date(2026,5,25),date(2026,6,19),date(2026,7,3),date(2026,9,7)}

def trade_days():
    d=START
    while d<=END:
        if d.weekday()<5 and d not in HOLIDAYS: yield d
        d+=timedelta(days=1)

def utcsec(d,hh,mm):
    return int(datetime(d.year,d.month,d.day,hh,mm,tzinfo=timezone.utc).timestamp())

def main():
    rows=[]
    for d in trade_days():
        s=utcsec(d,13,27); e=utcsec(d,13,38)
        r=requests.get("https://api.mexc.com/api/v1/contract/kline/NVIDIA_USDT",
          params={"interval":"Min1","start":str(s),"end":str(e)},
          headers={"User-Agent":UA},timeout=30)
        n=0; success=False
        if r.status_code==200:
            try:
                j=r.json(); success=j.get("success") is True
                n=len((j.get("data") or {}).get("time") or []) if success else 0
            except Exception: pass
        rows.append({"date":d.isoformat(),"http":r.status_code,"success":success,"row_count":n,"outcome_scored":False})
        time.sleep(0.04)

    usable=[x for x in rows if x["row_count"]>=8]
    first=usable[0]["date"] if usable else None
    after=[x for x in rows if first and x["date"]>=first]
    cov=(sum(x["row_count"]>=8 for x in after)/len(after)) if after else 0.0
    rep={
      "lab":"MEXC_NVIDIA_LISTING_COVERAGE_V0_1_2",
      "source_only":True,
      "historical_outcomes_opened":0,
      "signal_tested":False,
      "calendar_authority":"Nasdaq 2026 weekday schedule; closures Apr03 May25 Jun19 Jul03 Sep07",
      "probe_window_utc":"13:27-13:38",
      "first_usable_cash_open_date":first,
      "usable_trade_days":len(usable),
      "total_trade_days_probed":len(rows),
      "post_first_date_coverage_ratio":cov,
      "rows":rows,
      "verdict":"MEXC_NVIDIA_LISTING_COVERAGE_RESOLVED" if first and cov>=0.95 else "SOURCE_BLOCKED_MEXC_NVIDIA_LISTING_COVERAGE",
      "private_endpoints_used":False,"account_reads":False,"orders":False,
      "exchange_mutation":False,"live_trading_authorized":False
    }
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"MEXC_NVIDIA_LISTING_COVERAGE_RECEIPT_V012.json").write_text(json.dumps(rep,indent=2,sort_keys=True))
    print(json.dumps({k:rep[k] for k in ["first_usable_cash_open_date","usable_trade_days","total_trade_days_probed","post_first_date_coverage_ratio","verdict","historical_outcomes_opened","signal_tested"]},indent=2))

if __name__=="__main__": main()
