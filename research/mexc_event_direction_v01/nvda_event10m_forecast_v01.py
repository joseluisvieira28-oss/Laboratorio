#!/usr/bin/env python3
"""Fail-closed *paper forecast decision* evaluator only. No public network calls or orders."""
import datetime as dt
import math
import re
from zoneinfo import ZoneInfo

NY=ZoneInfo("America/New_York")
START=dt.date(2026,11,2)
END=dt.date(2026,11,30)
THANKSGIVING=dt.date(2026,11,26)
SHA=re.compile(r"^[0-9a-f]{64}$")
def check(x,msg):
    if not x:raise ValueError(msg)
def finite_positive(x):
    return isinstance(x,(float,int)) and not isinstance(x,bool) and math.isfinite(x) and x>0
def slot(decision_ms):
    when=dt.datetime.fromtimestamp(decision_ms/1000,dt.timezone.utc).astimezone(NY)
    d=when.date()
    check(START<=d<=END and d.weekday()<5 and d!=THANKSGIVING,"CLOSED_SESSION")
    minute=when.hour*60+when.minute
    check((9*60+35)<=minute<=(11*60+25) and (minute-(9*60+35))%10==0,
        "NOT_FROZEN_10MIN_SLOT")
    check(5<=when.second<=30,"DECISION_TOO_EARLY_OR_LATE")
    return when
def bars_return_bps(packet,decision_ms,expected_end_ms):
    check(packet.get("symbol") in ("NVDA","NVIDIA_USDT"),"UNSUPPORTED_SYMBOL")
    check(isinstance(packet.get("sha256"),str) and SHA.fullmatch(packet["sha256"]), "SOURCE_HASH_MISSING")
    recv=packet.get("received_ms")
    check(type(recv) is int and recv<=decision_ms and decision_ms-recv<=90000,
          "SOURCE_RECEIPT_MISSING_OR_STALE")
    raw=packet.get("bars")
    check(isinstance(raw,list),"BAR_ARRAY_MISSING")
    times={expected_end_ms-4*60000,expected_end_ms-60000}
    prices={}
    for entry in raw:
        t=entry.get("start_ms")
        if t not in times:continue
        c=entry.get("close")
        observed=entry.get("received_ms")
        check(finite_positive(c),"INVALID_BAR_PRICE")
        check(type(observed) is int and t+60000<=observed<=recv,
              "FUTURE_BAR_OR_NONCAUSAL_RECEIPT")
        check(t not in prices,"DUPLICATE_BAR")
        prices[t]=c
    check(set(prices)==times,"INCOMPLETE_CAUSAL_3M_WINDOW")
    return 10000*(prices[expected_end_ms-60000]/prices[expected_end_ms-4*60000]-1)
def forecast(decision_ms,cash,index,product,tick):
    when=slot(decision_ms)
    for name,packet in (("cash",cash),("index",index)):
        check(packet.get("symbol")==("NVDA" if name=="cash" else "NVIDIA_USDT"),"WRONG_SOURCE")
    # t is minute boundary at start of decision slot. End bars were completed before t.
    start_boundary_ms=decision_ms//60000*60000
    cash_return=bars_return_bps(cash,decision_ms,start_boundary_ms)
    index_return=bars_return_bps(index,decision_ms,start_boundary_ms)
    check(product.get("symbol")=="NVIDIA_USDT" and product.get("state")=="ONLINE" and
          product.get("horizon_min")==10,"PRODUCT_NOT_ELIGIBLE")
    check(type(product.get("received_ms")) is int and
          0<=decision_ms-product["received_ms"]<=10000,"PAYOUT_NOT_CONTEMPORANEOUS")
    check(isinstance(product.get("sha256"),str) and SHA.fullmatch(product["sha256"]),
          "PAYOUT_UNHASHED")
    for field in ("up_pay_rate","down_pay_rate"):
        check(finite_positive(product.get(field)),"BAD_PAYOUT")
    check(tick.get("symbol")=="NVIDIA_USDT" and type(tick.get("received_ms")) is int
          and 0<=decision_ms-tick["received_ms"]<=2000 and
          finite_positive(tick.get("index_price")) and
          isinstance(tick.get("sha256"),str) and SHA.fullmatch(tick["sha256"]),
          "INDEX_EVENT_STREAM_UNPROVEN")
    gap=cash_return-index_return
    qualify=abs(cash_return)>=10 and abs(gap)>=5 and cash_return*gap>0
    return {
        "study":"NVIDIA_EVENT10M_CASH_REF_V01",
        "decision_ts_ms":decision_ms,
        "ny_decision":when.isoformat(),
        "expiry_target_ms":decision_ms+600000,
        "asset":"NVIDIA_USDT",
        "horizon_min":10,
        "candidate":"UP" if qualify and cash_return>0 else "DOWN" if qualify else "ABSTAIN",
        "cash_return_3m_bps":cash_return,
        "mexc_index_return_3m_bps":index_return,
        "lag_gap_bps":gap,
        "payout_up":product["up_pay_rate"],
        "payout_down":product["down_pay_rate"],
        "snapshot_hashes":{"cash":cash["sha256"],"index":index["sha256"],
                           "payout":product["sha256"],"event_index":tick["sha256"]},
        "status":"FORECAST_ONLY_SHADOW_NOT_ACTUAL_EVENT_ENTRY",
        "win_probability_calibrated":False,"economic_edge_certified":False}
