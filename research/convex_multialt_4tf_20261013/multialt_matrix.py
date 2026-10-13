#!/usr/bin/env python3
"""Frozen 8-altcoin x 4-timeframe Quant Trailing V5 historical diagnostic.

Identical original recovered signal, 5m canonical SOURCE design, one asset
and eight scenarios PER Actions matrix job. Official Binance Vision public
archive; no private endpoints, orders or account access; protected 2026 untouched.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
import sys
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from research.btc_convex_timeframe_matrix_20261013 import matrix as base
from research.btc_convex_multifront_v01 import retrospective_diagnostic as src

ASSETS=("ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT","DOGEUSDT","ADAUSDT","LINKUSDT","AVAXUSDT")
YEARS=(2021,2022,2023,2024,2025)
TIMEFRAMES=base.TFS
SCENARIOS=(("BASE",2),("STRESS",5))
FIRST_PRICE_MONTH="2020-11"
START_PRICE=int(datetime(2020,11,1,tzinfo=timezone.utc).timestamp()*1000)
START=base.START
END=base.END
MONTHS=tuple(f"{y:04d}-{m:02d}" for y in range(2020,2026)
             for m in range(1,13) if (y,m)>=(2020,11) and (y,m)<=(2025,12))
FUNDING_MONTHS=tuple(s for s in MONTHS if s>="2021-01")
KIND_ORDER=("5m","1h","fundingRate")
OFFICIAL="https://data.binance.vision/data/futures/um/monthly"

def archive_path(symbol,kind,month):
    if symbol not in ASSETS:raise ValueError("SYMBOL_NOT_FROZEN")
    if kind not in KIND_ORDER:raise ValueError("KIND_NOT_FROZEN")
    if month not in MONTHS:raise ValueError("MONTH_NOT_FROZEN")
    if kind=="fundingRate":
        return f"fundingRate/{symbol}/{symbol}-fundingRate-{month}.zip"
    return f"klines/{symbol}/{kind}/{symbol}-{kind}-{month}.zip"

def fetch_archive(symbol,kind,month):
    rel=archive_path(symbol,kind,month)
    url=OFFICIAL+"/"+rel
    binary=src.fetch(url,25_000_000)
    checksum=src.fetch(url+".CHECKSUM",1200).decode("utf-8-sig").strip().split()[0].lower()
    digest=hashlib.sha256(binary).hexdigest()
    if not re.fullmatch("[0-9a-f]{64}",checksum) or digest!=checksum:
        raise ValueError("PUBLISHER_SHA256_MISMATCH:"+url)
    with zipfile.ZipFile(io.BytesIO(binary)) as z:
        names=[x for x in z.namelist() if x.lower().endswith(".csv")]
        if len(names)!=1:raise ValueError("ARCHIVE_CSV_MEMBER_COUNT_BAD:"+url)
        data=z.read(names[0]).decode("utf-8-sig")
    rows=list(csv.reader(io.StringIO(data)))
    if not rows:raise ValueError("ARCHIVE_EMPTY:"+url)
    return rows,{"symbol":symbol,"kind":kind,"month":month,
                 "official_url":url,"sha256_zip":digest,"zip_bytes":len(binary),
                 "csv_rows":len(rows)}

def fetch_all(symbol):
    if symbol not in ASSETS:raise ValueError("SYMBOL_NOT_FROZEN")
    five={};one={};funding={};manifest=[]
    month_funding={}
    for month in MONTHS:
        kinds=("5m","1h","fundingRate") if month in FUNDING_MONTHS else ("5m","1h")
        for kind in kinds:
            rows,record=fetch_archive(symbol,kind,month)
            parsed=src.funding_records(rows) if kind=="fundingRate" else src.candles(
                rows,base.M5 if kind=="5m" else base.HOUR)
            if not parsed:raise ValueError(f"EMPTY_PARSED_MONTH:{symbol}:{kind}:{month}")
            target={"5m":five,"1h":one,"fundingRate":funding}[kind]
            if target.keys()&parsed.keys():
                raise ValueError(f"ARCHIVE_OVERLAPPING_MONTHS:{symbol}:{kind}:{month}")
            target.update(parsed)
            manifest.append(record)
            if kind=="fundingRate":
                month_funding[month]=len(parsed)
                ms_lo=int(datetime(int(month[:4]),int(month[5:7]),1,tzinfo=timezone.utc).timestamp()*1000)
                y,m=int(month[:4]),int(month[5:7])
                y2,m2=(y+1,1) if m==12 else (y,m+1)
                ms_hi=int(datetime(y2,m2,1,tzinfo=timezone.utc).timestamp()*1000)
                if any(not(ms_lo<=t<ms_hi) for t in parsed):
                    raise ValueError(f"FUNDING_MONTH_TIME_BOUNDARY:{symbol}:{month}")
        print("ALT_SOURCE_OK",symbol,month,flush=True)
    validate_coverage(five,one,funding,month_funding)
    return five,one,funding,manifest

def validate_coverage(five,one,funding,month_funding):
    expected5=(END-START_PRICE)//base.M5
    expected1=(END-START_PRICE)//base.HOUR
    for label,d,step,num in (
        ("5m",five,base.M5,expected5),("1h",one,base.HOUR,expected1)):
        if len(d)!=num or not d:
            raise ValueError(f"PRICE_COVERAGE_INCOMPLETE:{label}:{len(d)}/{num}")
        if min(d)!=START_PRICE or max(d)!=END-step or (
            len(d)!=((max(d)-min(d))//step)+1):
            raise ValueError(f"PRICE_GAP_OR_BAD_END:{label}")
        if any(t%step for t in d):
            raise ValueError(f"PRICE_UNALIGNED:{label}")
    if set(month_funding)!=set(FUNDING_MONTHS):
        raise ValueError("FUNDING_MONTHS_MISSING")
    if any(month_funding[mo]<=0 for mo in FUNDING_MONTHS):
        raise ValueError("FUNDING_MONTH_WITH_NO_RECORDS")
    if not funding or any(t<START or t>=END for t in funding):
        raise ValueError("FUNDING_SCOPE_BAD")
    return True

def symbol_diagnostic(symbol, five,one,funding):
    if symbol not in ASSETS:raise ValueError("SYMBOL_NOT_FROZEN")
    tf_bars={name:base.resample(five,tf) for name,tf in TIMEFRAMES}
    price_audit=base.verify_one_hour_parity(tf_bars["1h"],one)
    # The V5 recovered Parent signal is used directly, without a new threshold.
    build=src.load_parent()
    can,_=build(tf_bars["1h"])
    official,_=build([one[t] for t in sorted(one)])
    disagreements=[b["t"] for i,b in enumerate(tf_bars["1h"]) if
                   b["t"]>=START and can[i]!=official[i]]
    models={}
    ledgers={}
    for name,tf in TIMEFRAMES:
        for cost,slip in SCENARIOS:
            key=name+"_"+cost
            obj=base.simulate(tf,tf_bars[name],five,funding,slip,include_trades=True)
            ledger=obj.pop("trades")
            if obj["closed_trades"]!=len(ledger):
                raise ValueError("MODEL_LEDGER_COUNT_MISMATCH:"+key)
            obj["asset"]=symbol
            obj["timeframe"]=name
            obj["research_only"]=True
            obj["recovered_v5_signal_unchanged"]=True
            models[key]=obj
            ledgers[key]=ledger
            print("ALT_MODEL",symbol,key,"closed",obj["closed_trades"],
                  "terminal_pct",round(obj["marked_return_pct"],6),
                  "pf",round(obj["profit_factor"],4) if obj["profit_factor"] is not None else None,
                  flush=True)
    if set(models)!={name+"_"+cost for name,_ in TIMEFRAMES for cost,_ in SCENARIOS}:
        raise ValueError("INCOMPLETE_MODEL_MATRIX")
    return {
        "model":models,
        "trade_ledgers":ledgers,
        "source_audit":price_audit,
        "source_signal_disagreement_count_1h":len(disagreements),
        "first_10_source_signal_disagreements_1h":disagreements[:10],
        "aggregated_bars":{k:len(v) for k,v in tf_bars.items()},
        "original_source_1h_equivalent":price_audit["official_1h_bar_mismatch_count"]==0,
    }

def main():
    args=argparse.ArgumentParser()
    args.add_argument("--symbol",required=True,choices=ASSETS)
    args.add_argument("--output-dir",type=Path,required=True)
    a=args.parse_args()
    a.output_dir.mkdir(parents=True,exist_ok=True)
    report={"status":"SOURCE_BLOCKED","symbol":a.symbol,
            "frozen_assets":list(ASSETS),"timeframes":[x for x,_ in TIMEFRAMES],
            "scenarios":[x for x,_ in SCENARIOS],"frozen_start_utc":"2021-01-01",
            "frozen_end_exclusive_utc":"2026-01-01",
            "preoutcome_freeze":"PRE_OUTCOME_PROTOCOL.md",
            "source_family":"OFFICIAL_BINANCE_USDM_CANONICAL_5M_ONLY",
            "execution_model":"20pct equity notional 1x, V5 confirmed TF close +5m first entry",
            "fees_taker_bps_side":8,
            "funding_price_used":"FIVE_MINUTE_MARKET_OPEN_PROXY_NOT_OFFICIAL_MARK",
            "independent_OOS":False,"actual_venue_fills":False,"live_authority":False}
    try:
        five,one,funding,manifest=fetch_all(a.symbol)
        report["source_manifest"]=manifest
        report["source_counts"]={"5m":len(five),"1h":len(one),"funding":len(funding)}
        out=symbol_diagnostic(a.symbol,five,one,funding)
        for key,rows in out.pop("trade_ledgers").items():
            if rows:
                path=a.output_dir/(key+"_TRADES.csv")
                with path.open("w",encoding="utf-8",newline="") as f:
                    w=csv.DictWriter(f,fieldnames=rows[0])
                    w.writeheader();w.writerows(rows)
        report.update(out)
        report["status"]="HISTORICAL_MULTI_ALT_4TF_COMPLETED_NO_OOS_CREDIT"
    except Exception as exc:
        report["blocked_reason"]=type(exc).__name__+":"+str(exc)
    (a.output_dir/"RESULT.json").write_text(
        json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    model_summary={k:{"ret":round(v["marked_return_pct"],4),
                      "dd":round(v["max_5m_low_stress_dd_pct"],4),
                      "pf":round(v["profit_factor"],4) if v["profit_factor"] is not None else None,
                      "closed":v["closed_trades"]}
                   for k,v in report.get("model",{}).items()}
    print("ALT_FINAL",json.dumps({"symbol":a.symbol,"status":report["status"],
          "blocked_reason":report.get("blocked_reason"),
          "counts":report.get("source_counts"),
          "one_hour_price_mismatch_count":report.get("source_audit",{}).get("per_field_mismatch_count"),
          "signal_mismatch_count":report.get("source_signal_disagreement_count_1h"),
          "models":model_summary},sort_keys=True),flush=True)
    if report["status"]!="HISTORICAL_MULTI_ALT_4TF_COMPLETED_NO_OOS_CREDIT":
        raise SystemExit(2)

if __name__=="__main__":
    main()
