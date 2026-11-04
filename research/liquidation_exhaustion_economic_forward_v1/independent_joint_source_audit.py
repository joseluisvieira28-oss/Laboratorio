#!/usr/bin/env python3
"""Independent receive-time joint-source audit; strictly no PnL or signals."""
import sys,json,hashlib,zipfile
from collections import Counter
from decimal import Decimal
from pathlib import Path

def audit(path):
    data=Path(path).read_bytes()
    with zipfile.ZipFile(path) as z:
        raw=z.read("pilot_raw_public_frames.ndjson")
        receipt=json.loads(z.read("pilot_receipt.json"))
    digest=hashlib.sha256(raw).hexdigest()
    if digest!=receipt["raw_sha256"]:raise ValueError("RAW_SHA_MISMATCH")
    counts=Counter();liq=0;covered=0;miss=Counter()
    book_u=None;book_ms=None;trade_ms=None;mexc_ms=None
    mexc_good=0;mexc_bad=0;mexc_eligible=0;consecutive=0
    first_recv=None;last_recv=None;recent_book_deltas=0
    bybit_trade_children=0
    last_mono={};last_mexc_quote=None
    for line in raw.splitlines():
        env=json.loads(line);recv=env["received_utc_ms"]
        mono=env["received_monotonic_ns"];venue=env["venue"]
        if first_recv is None:first_recv=recv
        if last_recv is not None and recv<last_recv-250:raise ValueError("CROSS_VENUE_CLOCK_JUMP")
        last_recv=recv
        if venue not in ("BYBIT","MEXC"):raise ValueError("UNKNOWN_VENUE")
        if venue in last_mono and mono<last_mono[venue]:
            raise ValueError("MONOTONIC_RECEIVE_REGRESSION")
        last_mono[venue]=mono
        msg=json.loads(env["raw"])
        if venue=="MEXC":
            if msg.get("channel")!="push.depth.full":continue
            counts["mexc_depth_frames"]+=1
            d=msg["data"]
            if (msg.get("symbol") or d.get("symbol"))!="BTC_USDT":
                raise ValueError("MEXC_BAD_SYMBOL")
            bids=d.get("bids") or [];asks=d.get("asks") or []
            if not bids or not asks:raise ValueError("MEXC_EMPTY_BOOK")
            bd=max(Decimal(str(x[0])) for x in bids)
            ak=min(Decimal(str(x[0])) for x in asks)
            if bd<=0 or bd>=ak:raise ValueError("MEXC_CROSSED_BBO")
            age=recv-int(msg["ts"])
            if -250<=age<=1500:
                mexc_good+=1;consecutive+=1
                if consecutive>=3:
                    mexc_ms=recv;last_mexc_quote=(bd,ak)
                    mexc_eligible+=1
            else:
                mexc_bad+=1;consecutive=0;mexc_ms=None
            continue
        topic=msg.get("topic")
        if topic=="orderbook.50.BTCUSDT":
            d=msg["data"];u=d["u"]
            if msg["type"]=="snapshot":
                counts["book_snapshots"]+=1
            elif msg["type"]=="delta":
                if book_u is None or u!=book_u+1:
                    raise ValueError("BYBIT_BOOK_GAP")
                recent_book_deltas+=1
            else:raise ValueError("BYBIT_BOOK_UNKNOWN_TYPE")
            book_u=u;book_ms=recv
            if not -250<=recv-int(msg["ts"])<=1500:
                raise ValueError("BYBIT_BOOK_AGE")
        elif topic=="publicTrade.BTCUSDT":
            counts["trade_messages"]+=1
            for trade in msg["data"]:
                if trade["s"]!="BTCUSDT" or trade["S"] not in ("Buy","Sell"):
                    raise ValueError("BAD_TRADE")
                if not -250<=recv-int(trade["T"])<=1500:
                    raise ValueError("TRADE_STALE")
                bybit_trade_children+=1;trade_ms=recv
        elif topic=="allLiquidation.BTCUSDT":
            counts["liq_messages"]+=1
            for x in msg["data"]:
                if x.get("s")!="BTCUSDT" or x.get("S") not in ("Buy","Sell"):
                    raise ValueError("LIQ_SCHEMA")
                if not -250<=recv-int(x["T"])<=1500:
                    raise ValueError("LIQ_STALE")
                liq+=1
                ok_book=book_ms is not None and 0<=recv-book_ms<=500
                ok_trade=trade_ms is not None and 0<=recv-trade_ms<=1500
                ok_mexc=mexc_ms is not None and 0<=recv-mexc_ms<=1500
                if ok_book and ok_trade and ok_mexc:covered+=1
                else:
                    if not ok_book:miss["book"]+=1
                    if not ok_trade:miss["trade"]+=1
                    if not ok_mexc:miss["mexc"]+=1
    expected=receipt["bybit"]["liquidation_children"]
    if liq!=expected or bybit_trade_children!=receipt["bybit"]["bybit_trade_children"]:
        raise ValueError("BYBIT_ORIGINAL_RECEIPT_PARITY")
    if counts["mexc_depth_frames"]!=receipt["mexc"]["depth_fresh_messages"]+receipt["mexc"]["depth_stale_samples"]:
        raise ValueError("MEXC_FRAMES_PARITY")
    if mexc_eligible!=receipt["mexc"]["best_bid_ask_samples"]:
        raise ValueError("MEXC_STRICT_QUARANTINE_PARITY")
    if recent_book_deltas!=receipt["bybit"]["book_contiguous_deltas"]:
        raise ValueError("BOOK_SEQUENCE_PARITY")
    status="SOURCE_CENSUS_UNPROVEN"
    if liq==0:status="JOINT_SOURCE_WINDOW_POSITIVE_EVENT_INSUFFICIENT"
    elif covered==0:status="JOINT_SOURCE_ASOF_COVERAGE_BLOCKED"
    elif covered==liq:status="JOINT_SOURCE_WINDOW_CAUSAL_PASS_LIMITED"
    else:status="JOINT_SOURCE_WINDOW_PARTIAL_ASOF_COVERAGE"
    if receipt["pilot_verdict"] in ("SOURCE_BLOCKED","MEXC_DEPTH_EXECUTABLE_QUOTE_SOURCE_BLOCKED"):
        status="SOURCE_BLOCKED"
    return {"verdict":status,"zip_sha256":hashlib.sha256(data).hexdigest(),
       "raw_sha256":digest,"bybit_liquidation_children":liq,
       "liquidations_with_causal_prior_quote_book_trade":covered,
       "missing_causal_sources":dict(miss),"bybit_trade_children":bybit_trade_children,
       "bybit_contiguous_book_deltas":recent_book_deltas,
       "mexc_depth_frames":counts["mexc_depth_frames"],"mexc_depth_fresh":mexc_good,
       "mexc_depth_stale":mexc_bad,"mexc_depth_after_strict_quarantine":mexc_eligible,
       "economic_outcomes_opened":False,"PnL":None,"all_market_liquidations_census_proven":False,
       "real_orders":0}
if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("usage: independent_joint_source_audit.py artifact.zip")
    print(json.dumps(audit(sys.argv[1]),indent=2,sort_keys=True))
