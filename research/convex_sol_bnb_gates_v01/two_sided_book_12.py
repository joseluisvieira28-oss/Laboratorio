#!/usr/bin/env python3
"""Frozen exactly 12 spaced public 2-sided MEXC Futures order-book snapshots.

No authenticated endpoints, orders, accounts, trading, or alpha validation.
Actual executable liquidity remains unproven.
"""
from __future__ import annotations
import argparse,json,statistics,time
from decimal import Decimal
from pathlib import Path
from research.convex_sol_bnb_gates_v01 import mexc_public_feasibility as p

N=12
MIN_INTERVAL=5.0
FEES_BPS_ROUNDTRIP=16

def vwap(books,qty,size):
    rem=qty
    amount=Decimal(0)
    for level in books:
        take=min(rem,level["contracts"])
        amount+=take*level["price"]*size
        rem-=take
        if rem<=0:break
    if rem>0:return None
    return amount/(qty*size)

def detail_snapshot(spec,book_raw,stamp,previous=None):
    q=p.analyze_book(book_raw,stamp,spec["symbol"],spec)
    version=book_raw.get("version")
    if not isinstance(version,int) or version<=0:
        raise ValueError("PUBLIC_BOOK_VERSION_MISSING")
    if previous is not None and version<=previous:
        raise ValueError("NOT_A_NEW_PUBLIC_BOOK_VERSION")
    ask=p.book_levels(book_raw["asks"],"asks")
    bid=p.book_levels(book_raw["bids"],"bids")
    available_ask=sum(z["contracts"] for z in ask)
    available_bid=sum(z["contracts"] for z in bid)
    probes=[]
    for x in q["samples"]:
        vol=Decimal(x["required_contracts"])
        buy=vwap(ask,vol,spec["contractSize"])
        sell=vwap(bid,vol,spec["contractSize"])
        probes.append({
            "target_usdt":x["hypothetical_notional_target_usdt"],
            "contracts":str(vol),
            "ask_contracts_visible":str(available_ask),
            "bid_contracts_visible":str(available_bid),
            "ask_enough":buy is not None,
            "bid_enough":sell is not None,
            "two_sided_book_depth_sufficient":buy is not None and sell is not None,
            "visible_buy_vwap":str(buy) if buy else None,
            "visible_sell_vwap":str(sell) if sell else None,
            "observed_roundtrip_buy_minus_sell_in_bps":float(10000*(buy-sell)/((buy+sell)/2)) if buy and sell else None,
            "actual_order_fill_proven":False})
    return {"book_version":version,"quote_timestamp_ms":q["book_timestamp_ms"],
            "quote_age_ms":q["quote_age_ms"],
            "observed_spread_bps":q["public_spread_bps"],
            "hurdle_base_bps_approx":q["public_spread_bps"]+FEES_BPS_ROUNDTRIP+4,
            "hurdle_stress_bps_approx":q["public_spread_bps"]+FEES_BPS_ROUNDTRIP+10,
            "probes":probes,"source_response_sha256":stamp["sha256_raw_response"],
            "source_response_latency_ms":stamp["request_latency_ms"]}

def take_many(symbol):
    p.valid_symbol(symbol)
    specraw,specreceipt=p.source_get("detail",symbol)
    spec=p.extract_detail(specraw,symbol)
    out={"symbol":symbol,"status":"SOURCE_BLOCKED",
         "source_spec_sha256":specreceipt["sha256_raw_response"],
         "contract_spec":{k:str(v) for k,v in spec.items()},
         "snapshots":[],"taker_api_assumption_bps_side":8,
         "real_fills_verified":False,
         "trading_authority":"NONE"}
    seen=None
    last_start=None
    for i in range(N):
        if last_start is not None:
            delay=MIN_INTERVAL-(time.monotonic()-last_start)
            if delay>0:time.sleep(delay)
        last_start=time.monotonic()
        try:
            raw,stamp=p.source_get("depth",symbol)
            observation=detail_snapshot(spec,raw,stamp,seen)
        except Exception as e:
            out["status"]="PUBLIC_BOOK_SOURCE_INCOMPLETE"
            out["error"]=type(e).__name__+":"+str(e)
            out["failed_sample_index"]=i
            return out
        seen=observation["book_version"]
        out["snapshots"].append(observation)
        print("PUBLIC_BOOK_SAMPLE",symbol,i+1,"bid_ask_spread_bps",round(observation["observed_spread_bps"],5),flush=True)
    if len(out["snapshots"])!=N:raise AssertionError("INCOMPLETE_TWELVE_SAMPLES")
    summary={}
    for target in p.PAPER_NOTIONALS:
        entries=[next(z for z in o["probes"] if z["target_usdt"]==target) for o in out["snapshots"]]
        both=sum(q["two_sided_book_depth_sufficient"] for q in entries)
        summary[str(target)]={
            "snapshots":len(entries),
            "both_sides_visible_20_levels_count":both,
            "both_sides_visible_percentage":100*both/len(entries),
            "not_assured_fill":True}
    spreads=[x["observed_spread_bps"] for x in out["snapshots"]]
    out["summary"]={"snapshots":N,
                   "median_spread_bps":statistics.median(spreads),
                   "max_spread_bps":max(spreads),
                   "min_spread_bps":min(spreads),
                   "source_quote_fresh_count":N,
                   "paper_target_both_side_availability":summary,
                   "real_market_impact_or_order_queue_verified":False}
    out["status"]="PUBLIC_MULTISNAPSHOT_SOURCE_PASS_NOT_ORDER_FILLS"
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--symbol",required=True,choices=p.SYMBOLS)
    ap.add_argument("--output-dir",type=Path,required=True)
    a=ap.parse_args()
    a.output_dir.mkdir(parents=True,exist_ok=True)
    receipt={"symbol":a.symbol,"status":"SOURCE_BLOCKED","snapshots":[]}
    try:receipt=take_many(a.symbol)
    except Exception as e:receipt["error"]=type(e).__name__+":"+str(e)
    (a.output_dir/"TWO_SIDED_BOOK_12_SNAPSHOTS.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print("TWELVE_PUBLIC_BOOK_FINAL",json.dumps({k:v for k,v in receipt.items() if k in ("symbol","status","error","summary","failed_sample_index")},sort_keys=True),flush=True)
    if receipt["status"]!="PUBLIC_MULTISNAPSHOT_SOURCE_PASS_NOT_ORDER_FILLS":
        raise SystemExit(2)
if __name__=="__main__":main()
