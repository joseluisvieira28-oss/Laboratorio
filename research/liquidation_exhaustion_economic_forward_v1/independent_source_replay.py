#!/usr/bin/env python3
"""Independent source-only replay of immutable dual-venue pilot ZIP.
Compares raw message counts with manifest without importing the collector.
No outcome prices, strategy triggers, returns, profitability or orders.
"""
import argparse
from collections import Counter
from decimal import Decimal,InvalidOperation
import hashlib
import json
from zipfile import ZipFile
from pathlib import Path

TOPICS={"allLiquidation.BTCUSDT","orderbook.50.BTCUSDT","publicTrade.BTCUSDT"}

def independent_replay(filename):
    archive=Path(filename).read_bytes()
    with ZipFile(filename) as z:
        raw=z.read("pilot_raw_public_frames.ndjson")
        rec=json.loads(z.read("pilot_receipt.json"))
    if hashlib.sha256(raw).hexdigest()!=rec["raw_sha256"]:
        raise ValueError("RAW_ARCHIVE_DIGEST_MISMATCH")
    bybit=Counter();liq=0;trade=0;book_snap=0;book_delta=0;last_u=None
    mexc_valid=0;mexc_stale=0;mexc_consecutive=0;mexc_eligible=0
    clocks={};frame_count=0;errors=[]
    for line in raw.splitlines():
        frame_count+=1
        wrap=json.loads(line)
        venue=wrap["venue"];recv=wrap["received_utc_ms"]
        mono=wrap["received_monotonic_ns"]
        if venue not in ("BYBIT","MEXC"):raise ValueError("INVALID_VENUE")
        prev=clocks.get(venue)
        if prev and mono<prev:raise ValueError("MONOTONIC_RECEIVE_CLOCK_REGRESSION")
        clocks[venue]=mono
        msg=json.loads(wrap["raw"])
        if venue=="BYBIT":
            topic=msg.get("topic")
            if topic not in TOPICS:continue
            bybit[topic]+=1
            data=msg["data"]
            if topic.startswith("orderbook."):
                if data.get("s")!="BTCUSDT":raise ValueError("WRONG_BYBIT_BOOK")
                u=data.get("u")
                if type(u) is not int:raise ValueError("MISSING_U")
                if msg["type"]=="snapshot":
                    book_snap+=1
                elif msg["type"]=="delta":
                    if last_u is None or u!=last_u+1:raise ValueError("BOOK_U_GAP")
                    book_delta+=1
                else:raise ValueError("BOOK_MESSAGE_TYPE_UNKNOWN")
                last_u=u
                lag=recv-int(msg["ts"])
                if lag < -250 or lag>1500:raise ValueError("BOOK_TIMESTAMP_STALE")
            elif topic.startswith("publicTrade."):
                for x in data:
                    if x.get("s")!="BTCUSDT" or x.get("S") not in ("Buy","Sell"):raise ValueError("TRADE_BAD")
                    lag=recv-int(x["T"])
                    if lag < -250 or lag>1500:raise ValueError("TRADE_TIMESTAMP_STALE")
                    trade+=1
            else:
                for x in data:
                    if x.get("s")!="BTCUSDT" or x.get("S") not in ("Buy","Sell"):raise ValueError("LIQ_BAD")
                    try:p=Decimal(x["p"]);v=Decimal(x["v"])
                    except (InvalidOperation,KeyError):raise ValueError("LIQ_SIZE_BAD")
                    if p<=0 or v<=0:raise ValueError("LIQ_NONPOSITIVE")
                    lag=recv-int(x["T"])
                    if lag < -250 or lag>1500:raise ValueError("LIQ_TIMESTAMP_STALE")
                    liq+=1
        else:
            if msg.get("channel")!="push.ticker":continue
            data=msg.get("data")
            if not isinstance(data,dict) or (msg.get("symbol") or data.get("symbol"))!="BTC_USDT":
                raise ValueError("MEXC_TICKER_SYMBOL_UNKNOWN")
            try:
                bid=Decimal(str(data["bid1"]));ask=Decimal(str(data["ask1"]))
            except (InvalidOperation,KeyError):raise ValueError("MEXC_BAD_BBO")
            if bid<=0 or ask<=bid:raise ValueError("MEXC_CROSSED_BBO")
            try:lag=recv-int(msg["ts"])
            except (KeyError,TypeError,ValueError):lag=10**10
            if lag < -250 or lag>1500:
                mexc_stale+=1;mexc_consecutive=0
            else:
                mexc_valid+=1;mexc_consecutive+=1
                if mexc_consecutive>=3:mexc_eligible+=1
    if liq!=rec["bybit"]["liquidation_children"]:raise ValueError("LIQ_COUNT_PARITY_FAIL")
    if dict(bybit)!=rec["bybit"]["topic_counts"]:raise ValueError("BYBIT_TOPIC_COUNT_PARITY_FAIL")
    if trade!=rec["bybit"]["bybit_trade_children"]:raise ValueError("TRADE_COUNT_PARITY_FAIL")
    if book_snap!=rec["bybit"]["book_snapshots"] or book_delta!=rec["bybit"]["book_contiguous_deltas"]:
        raise ValueError("BOOK_PARITY_FAIL")
    if mexc_valid!=rec["mexc"]["ticker_fresh_messages"] or mexc_stale!=rec["mexc"]["ticker_stale_samples"]:
        raise ValueError("MEXC_TICKER_COUNT_PARITY_FAIL")
    if mexc_eligible!=rec["mexc"]["best_bid_ask_samples"]:
        raise ValueError("MEXC_QUARANTINE_PARITY_FAIL")
    return {
      "audit":"INDEPENDENT_REAL_RAW_SOURCE_ONLY_REPLAY",
      "original_zip_sha256":hashlib.sha256(archive).hexdigest(),
      "raw_sha256":hashlib.sha256(raw).hexdigest(),
      "frames":frame_count,"bybit_topics":dict(bybit),
      "liquidation_children":liq,"trade_children":trade,
      "book_snapshots":book_snap,"book_contiguous_deltas":book_delta,
      "mexc_fresh_ticker":mexc_valid,"mexc_stale_ticker":mexc_stale,
      "mexc_quarantined_then_eligible_bbo":mexc_eligible,
      "collector_status":rec["pilot_verdict"],
      "full_census_proven":False,"economic_returns_evaluated":False,
      "live_go":False
    }

def main():
    a=argparse.ArgumentParser()
    a.add_argument("zip")
    args=a.parse_args()
    print(json.dumps(independent_replay(args.zip),indent=2,sort_keys=True))

if __name__=="__main__":main()
