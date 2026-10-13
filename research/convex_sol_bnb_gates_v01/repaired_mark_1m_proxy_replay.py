#!/usr/bin/env python3
"""F1C frozen Binance official monthly+2023-02-24 daily 1m mark OPEN sensitivity.

Parent V5 is not modified. Exact markPrice from fundingRate API remains
HTTP451 SOURCE_BLOCKED. Source model is 1m candle OPEN, NOT settlement mark.
"""
from __future__ import annotations
import argparse,json
from datetime import datetime,timezone
from pathlib import Path

from research.convex_sol_bnb_gates_v01 import mark_1m_proxy_sensitivity as model
from research.convex_sol_bnb_gates_v01 import daily_mark_gap_probe as daily
from research.convex_sol_bnb_gates_v01 import exact_funding_mark as prior

TARGET_DATE="2023-02-24"
DAY_START=int(datetime(2023,2,24,tzinfo=timezone.utc).timestamp()*1000)
END=DAY_START+86_400_000
EXPECTED_DAILY_PUBLISHER_SHA={
    "SOLUSDT":"8faad348c53c0eacd4514f8fe615e60524b5b8629da5341294790ec78ef6837b",
    "BNBUSDT":"536e489c8f4e89527b6ba3f580417e539cc0cf6808aa415090e139cd7f9b62df"}
MISSING_SETTLEMENT_MINUTES=(
    1677196800000,1677225600000,1677254400000)

def recovered_source(symbol,month,monthly_getter=model.get_verified_mark_minute,
                    daily_getter=daily.daily_mark):
    prior.approved_symbol(symbol)
    month_prices,receipt=monthly_getter(symbol,month)
    if month!="2023-02":return month_prices,receipt
    provided,verified_daily=daily_getter(symbol,TARGET_DATE)
    if verified_daily["publisher_sha256"]!=EXPECTED_DAILY_PUBLISHER_SHA[symbol]:
        raise ValueError("DAILY_1M_SOURCE_SHA_DIFFERS_FROM_PREREGISTERED")
    if set(provided)!=set(range(DAY_START,END,60_000)):
        raise ValueError("DAILY_1M_1440_BAR_COVERAGE_NOT_EXACT")
    overlapping=set(provided)&set(month_prices)
    if overlapping:
        raise ValueError("MONTHLY_DAILY_SOURCE_OVERLAP_REQUIRES_SEPARATE_AUDIT")
    if any(t in month_prices for t in MISSING_SETTLEMENT_MINUTES):
        raise ValueError("PRIOR_THREE_MISSING_MARK_TIMES_CHANGED")
    # No market outcome selection: explicitly union ONLY full daily missing source.
    augmented=dict(month_prices)
    augmented.update(provided)
    receipt["supplement"]={
       "source_role":"OFFICIAL_DAILY_MARK_1M_SOURCE_ONLY_NOT_EXACT_FUNDING_MARK",
       "full_daily_bars":len(provided),
       "daily_source":verified_daily,
       "monthly_source_contains_any_daily_bars":False,
       "recovered_three_funding_times":list(MISSING_SETTLEMENT_MINUTES)}
    return augmented,receipt

def diagnostic(symbol,parent):
    prior.approved_symbol(symbol)
    getter=model.get_verified_mark_minute
    try:
        model.get_verified_mark_minute=recovered_source
        report=model.replay(symbol,parent)
    finally:
        model.get_verified_mark_minute=getter
    if report.get("status")!="OFFICIAL_MARK_1M_OPEN_PROXY_REPLAY_PASS_NOT_EXACT_MARK_NOT_OOS":
        raise ValueError("UNDERLYING_UNMODIFIED_MARK_MODEL_NOT_PASS")
    for row in report["mark1m_official_publisher_sha256_receipts"]:
        if row["month"]=="2023-02":
            assert row["supplement"]["full_daily_bars"]==1440
            assert row["unresolved_funding_mark_minute_bars"]==0
    report["status"]="REPAIRED_MONTHLY_AND_DAILY_1M_MARK_OPEN_PROXY_REPLAY_PASS_NOT_EXACT"
    report["source_repair_model"]="official_frozen_monthly_1m_mark_open_plus_2023-02-24_official_daily_1m_for_full_missing_day_only"
    report["exact_settlement_mark_price_verified"]=False
    report["exact_public_api_451_still_source_blocked"]=True
    report["independent_out_of_sample"]=False
    report["executable_venue_fills_verified"]=False
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--symbol",choices=tuple(prior.PAIRS),required=True)
    p.add_argument("--prior-artifact",type=Path,required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    a=p.parse_args()
    a.output_dir.mkdir(parents=True,exist_ok=True)
    out={"symbol":a.symbol,"status":"SOURCE_BLOCKED",
         "frozen_source_contract":"F1C_REPAIRED_MARK_PROXY_REPLAY_FREEZE.md",
         "trading_authority":"NONE",
         "api_exact_mark_still_451_source_blocked":True,
         "real_fills":False}
    try:out.update(diagnostic(a.symbol,a.prior_artifact))
    except Exception as exc:out["block_reason"]=type(exc).__name__+":"+str(exc)
    (a.output_dir/"REPAIRED_MONTH_DAILY_1M_MARK_PROXY_RESULT.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print("F1C_REPAIRED_PROXY_FINAL",json.dumps({k:v for k,v in out.items() if k in ("symbol","status","block_reason","source_comparison","pairs")},sort_keys=True),flush=True)
    if out["status"]!="REPAIRED_MONTHLY_AND_DAILY_1M_MARK_OPEN_PROXY_REPLAY_PASS_NOT_EXACT":
        raise SystemExit(2)
if __name__=="__main__":main()
