#!/usr/bin/env python3
"""Exact public Binance fundingTime/rate/markPrice source gate + frozen V5 replay.

SOURCE_ONLY until API/official archives match; historical replay stays
descriptive and cannot establish new independent OOS or executable venue fills.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import urllib.parse
from datetime import datetime,timezone
from pathlib import Path
from research.convex_8alt_common_2023_25 import common_3yr as old
from research.convex_multialt_4tf_20261013 import multialt_matrix as source
from research.btc_convex_multifront_v01 import retrospective_diagnostic as src
from research.btc_convex_timeframe_matrix_20261013 import matrix as engine

PAIRS={"SOLUSDT":("1h",engine.HOUR),"BNBUSDT":("4h",4*engine.HOUR)}
START=int(datetime(2023,1,1,tzinfo=timezone.utc).timestamp()*1000)
END=int(datetime(2026,1,1,tzinfo=timezone.utc).timestamp()*1000)
PREVIOUS_SOURCE_RUN=38432883246
EXPECTED_SETTLEMENTS=3288
PAGE_LIMIT=1000
HOST="https://fapi.binance.com"
PATH="/fapi/v1/fundingRate"
EPS=1e-10

def approved_symbol(symbol):
    if symbol not in PAIRS:raise ValueError("ONLY_TWO_FROZEN_SYMBOLS")
    return symbol

def get_public_json_page(symbol,start):
    approved_symbol(symbol)
    if not isinstance(start,int) or not(START<=start<END):
        raise ValueError("SOURCE_PAGINATION_BOUNDARY_INVALID")
    query=urllib.parse.urlencode({"symbol":symbol,"startTime":start,
                                   "endTime":END-1,"limit":PAGE_LIMIT})
    url=HOST+PATH+"?"+query
    body=src.fetch(url,1_000_000)
    payload=json.loads(body.decode("utf-8-sig"))
    if not isinstance(payload,list):
        raise ValueError("BINANCE_PUBLIC_FUNDING_RESPONSE_NOT_LIST")
    if len(payload)>PAGE_LIMIT:raise ValueError("PUBLIC_FUNDING_PAGE_OVER_LIMIT")
    return payload,{"url":url,"sha256_raw_response":hashlib.sha256(body).hexdigest(),
                    "bytes":len(body),"records":len(payload)}

def rate_float(text):
    try:v=float(text)
    except (ValueError,TypeError):raise ValueError("INVALID_PUBLIC_FUNDING_FLOAT")
    if not math.isfinite(v):raise ValueError("NONFINITE_PUBLIC_FUNDING_VALUE")
    return v

def parse_funding_record(obj,symbol):
    if not isinstance(obj,dict) or obj.get("symbol")!=symbol:
        raise ValueError("WRONG_SYMBOL_OR_BAD_PUBLIC_FUNDING_SCHEMA")
    t=obj.get("fundingTime")
    if not isinstance(t,int) or not(START<=t<END):
        raise ValueError("FUNDING_TIMESTAMP_OUTSIDE_FROZEN_WINDOW")
    rate=rate_float(obj.get("fundingRate"))
    mark=rate_float(obj.get("markPrice"))
    if mark<=0:raise ValueError("FUNDING_MARK_PRICE_NOT_AVAILABLE")
    return t,{"rate":rate,"mark":mark,"rateType":obj.get("rateType",None)}

def collect_full_api(symbol,fetcher=get_public_json_page):
    approved_symbol(symbol)
    cursor=START
    records={}
    pages=[]
    previous=-1
    for iteration in range(20):
        payload,receipt=fetcher(symbol,cursor)
        pages.append(receipt)
        if not payload:break
        for obj in payload:
            t,rec=parse_funding_record(obj,symbol)
            if t<=previous or t<cursor or t in records:
                raise ValueError("FUNDING_PAGINATION_NONCAUSAL_DUPLICATE_OR_OUT_OF_ORDER")
            records[t]=rec
            previous=t
        if len(payload)<PAGE_LIMIT:break
        cursor=previous+1
        if cursor>=END:break
    else:
        raise ValueError("FUNDING_PAGINATION_MAX_PAGES_EXCEEDED")
    if len(records)!=EXPECTED_SETTLEMENTS:
        raise ValueError(f"PUBLIC_FUNDING_EVENT_COVERAGE_MISMATCH:{len(records)}/{EXPECTED_SETTLEMENTS}")
    return records,pages

def previous_artifact_baseline(folder,symbol):
    path=folder/"RESULT.json"
    if not path.exists():raise ValueError("PREVIOUS_IMMUTABLE_RESULT_REQUIRED")
    d=json.loads(path.read_text(encoding="utf8"))
    tf=PAIRS[symbol][0]
    if d.get("symbol")!=symbol or d.get("status")!="COMMON_2023_25_8ALT_COMPLETED_NO_OOS_CREDIT":
        raise ValueError("PARENT_ARTIFACT_IDENTITY_INVALID")
    if d.get("source_counts")!={"1h":27768,"5m":333216,"funding":3288}:
        raise ValueError("PARENT_SOURCE_COUNTS_MISMATCH")
    prior={x["month"]:x["sha256_zip"] for x in d.get("source_manifest",[])
           if x.get("kind")=="fundingRate"}
    if len(prior)!=36:raise ValueError("PARENT_36_FUNDING_MONTH_SHA_REQUIRED")
    fingerprints={}
    for cost in ("BASE","STRESS"):
        m=d["model"][tf+"_"+cost]
        fingerprints[cost]={"return_pct":m["marked_return_pct"],
                            "trades":m["closed_trades"],"pf":m["profit_factor"],
                            "funding_usdt":m["funding_usdt"],
                            "fee_usdt":m["fees_usdt"]}
    return prior,fingerprints

def verify_archive_and_api(symbol,api,sha36):
    old.apply_locked_3year_window()
    source_by_time={}
    manifests=[]
    for mo in source.FUNDING_MONTHS:
        data,receipt=source.fetch_archive(symbol,"fundingRate",mo)
        if receipt["sha256_zip"]!=sha36.get(mo):
            raise ValueError("PARENT_ARCHIVE_SHA256_CHANGED:"+symbol+":"+mo)
        m=src.funding_records(data)
        if len(set(source_by_time)&set(m)):
            raise ValueError("SOURCE_DUPLICATE_FUNDING_TIMES")
        source_by_time.update(m)
        manifests.append(receipt)
        print("FUNDING_ARCHIVE_VERIFIED",symbol,mo,flush=True)
    if len(source_by_time)!=EXPECTED_SETTLEMENTS:
        raise ValueError("PRIOR_MONTHLY_FUNDING_COUNT_CHANGED")
    if set(source_by_time)!=set(api):
        raise ValueError(f"API_VS_OFFICIAL_ARCHIVE_TIMESTAMP_SET_MISMATCH:api={len(api)},archive={len(source_by_time)}")
    discrepancies=[]
    for t,rate in source_by_time.items():
        api_rate=api[t]["rate"]
        if abs(api_rate-rate)>EPS:
            discrepancies.append({"t":t,"archive_rate":rate,"api_rate":api_rate})
    if discrepancies:
        raise ValueError(f"API_VS_ARCHIVE_FUNDING_RATE_MISMATCH:{len(discrepancies)}:{discrepancies[:3]}")
    return source_by_time,manifests

def paired_replay(symbol,api,orig_funding,original_fp):
    old.apply_locked_3year_window()
    five,official1,archive_funding,original_manifest=source.fetch_all(symbol)
    if archive_funding!=orig_funding:
        raise ValueError("CURRENT_MARKET_SOURCE_FUNDING_CHANGED")
    tf,span=PAIRS[symbol]
    bars=engine.resample(five,span)
    compare=[]
    adjustments={}
    for t in sorted(api):
        proxy=five.get(t)
        if proxy is None:raise ValueError("MISSING_5M_PROXY_AT_EXACT_FUNDING_TIMESTAMP")
        market=proxy["open"];mark=api[t]["mark"]
        if market<=0 or mark<=0:raise ValueError("INVALID_MARK_OR_MARKET")
        adjustments[t]=orig_funding[t]*mark/market
        compare.append({"t":t,"actual_mark":mark,"market_open_proxy":market,
                        "mark_minus_market_pct":100*(mark/market-1)})
    output={}
    for cost,slip in (("BASE",2),("STRESS",5)):
        prior=engine.simulate(span,bars,five,orig_funding,slip)
        original=original_fp[cost]
        for k,a,b in (("return_pct",prior["marked_return_pct"],original["return_pct"]),
                      ("trades",prior["closed_trades"],original["trades"]),
                      ("pf",prior["profit_factor"],original["pf"]),
                      ("funding_usdt",prior["funding_usdt"],original["funding_usdt"]),
                      ("fee_usdt",prior["fees_usdt"],original["fee_usdt"])):
            if not math.isclose(a,b,rel_tol=1e-8,abs_tol=0.0001):
                raise ValueError(f"ORIGINAL_PARENT_ENGINE_FINGERPRINT_NOT_REPRODUCED:{symbol}:{cost}:{k}:{a}:{b}")
        new=engine.simulate(span,bars,five,adjustments,slip)
        output[cost]={
          "original_marked_return_pct":prior["marked_return_pct"],
          "settlement_mark_marked_return_pct":new["marked_return_pct"],
          "difference_pct_points":new["marked_return_pct"]-prior["marked_return_pct"],
          "original_funding_usdt":prior["funding_usdt"],
          "settlement_mark_funding_usdt":new["funding_usdt"],
          "funding_usdt_difference":new["funding_usdt"]-prior["funding_usdt"],
          "original_closed_trades":prior["closed_trades"],
          "exact_mark_closed_trades":new["closed_trades"],
          "original_pf":prior["profit_factor"],
          "exact_mark_pf":new["profit_factor"],
          "original_5m_low_dd_pct":prior["max_5m_low_stress_dd_pct"],
          "exact_mark_5m_low_dd_pct":new["max_5m_low_stress_dd_pct"],
          "still_model_only_no_venue_fills":True}
    deviations=sorted((abs(x["mark_minus_market_pct"]) for x in compare))
    return {
      "status":"HISTORICAL_BINANCE_FUNDING_SETTLEMENT_MARK_REPLAY_SOURCE_PASS_NO_OOS",
      "pricing":output,
      "source_mark_comparison":{
        "events":len(compare),"abs_diff_median_percent":deviations[len(deviations)//2],
        "abs_diff_max_percent":max(deviations),
        "top_10_abs_mark_vs_market_disagreements":sorted(compare,key=lambda x:abs(x["mark_minus_market_pct"]),reverse=True)[:10]},
      "market_archive_sha256_manifest":[x for x in original_manifest if x["kind"]=="5m"]
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--symbol",required=True,choices=tuple(PAIRS))
    p.add_argument("--prior-artifact",type=Path,required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    a=p.parse_args()
    a.output_dir.mkdir(parents=True,exist_ok=True)
    result={"symbol":a.symbol,"status":"SOURCE_BLOCKED",
            "source":"PUBLIC_BINANCE_USDM_FUNDING_RATE_WITH_EXACT_SETTLEMENT_MARK",
            "historical_replay":"2023-01-01..2025-12-31",
            "never_independent_OOS":True,"real_venue_fills_proven":False,
            "trading_authority":"NONE"}
    try:
        source_sha,original_fp=previous_artifact_baseline(a.prior_artifact,a.symbol)
        api,pages=collect_full_api(a.symbol)
        result["public_page_receipts"]=pages
        result["event_count"]=len(api)
        result["mark_extremes"]={"min":min(v["mark"] for v in api.values()),
                                 "max":max(v["mark"] for v in api.values())}
        archived,receipts=verify_archive_and_api(a.symbol,api,source_sha)
        result["published_funding_monthly_receipts"]=receipts
        result.update(paired_replay(a.symbol,api,archived,original_fp))
    except Exception as exc:
        result["status"]="SOURCE_BLOCKED"
        result["block_reason"]=type(exc).__name__+":"+str(exc)
    (a.output_dir/"EXACT_SETTLEMENT_MARK_GATE.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print("EXACT_MARK_FINAL",json.dumps({k:v for k,v in result.items() if k in ("symbol","status","block_reason","event_count","pricing","source_mark_comparison")},sort_keys=True),flush=True)
    if result["status"]!="HISTORICAL_BINANCE_FUNDING_SETTLEMENT_MARK_REPLAY_SOURCE_PASS_NO_OOS":
        raise SystemExit(2)
if __name__=="__main__":main()
