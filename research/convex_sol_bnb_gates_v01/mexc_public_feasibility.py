#!/usr/bin/env python3
"""Single public MEXC Futures feasibility snapshot, GET-only, no auth or orders.

Public top-book does not imply fill, user fee tier, country entitlement, order
acceptance, sufficient collateral, futures margin or past execution parity.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import time
import urllib.parse
import urllib.request
from decimal import Decimal,ROUND_CEILING,InvalidOperation
from pathlib import Path

SYMBOLS=("SOL_USDT","BNB_USDT")
HOST="https://contract.mexc.com"
ENDPOINTS={
    "detail":"/api/v1/contract/detail/country",
    "depth":"/api/v1/contract/depth/{symbol}",
    "funding":"/api/v1/contract/funding_rate/{symbol}",
}
PAPER_NOTIONALS=(100,2000)
TAKER_BPS_SIDE=8
MAX_LATENCY_MS=3000
MAX_AGE_MS=2000

def valid_symbol(s):
    if s not in SYMBOLS:raise ValueError("OUT_OF_SCOPE_SYMBOL")
    return s

def source_get(kind,symbol):
    valid_symbol(symbol)
    if kind not in ENDPOINTS:raise ValueError("PUBLIC_GET_ONLY_SCOPE")
    path=ENDPOINTS[kind].format(symbol=symbol)
    if kind=="detail":path+="?"+urllib.parse.urlencode({"symbol":symbol})
    if kind=="depth":path+="?"+urllib.parse.urlencode({"limit":20})
    url=HOST+path
    t0=time.monotonic_ns()
    with urllib.request.urlopen(urllib.request.Request(url,headers={
        "User-Agent":"CryptoLab-Public-Feasibility-V01/1.0","Accept":"application/json"}),timeout=12) as response:
        raw=response.read(500_001)
        if response.status!=200 or len(raw)>500_000:
            raise ValueError("PUBLIC_HTTP_ERROR_OR_TOO_LARGE")
    duration=(time.monotonic_ns()-t0)/1e6
    receipt={"url":url,"sha256_raw_response":hashlib.sha256(raw).hexdigest(),
             "local_received_ms":time.time_ns()//1_000_000,
             "request_latency_ms":duration,"raw_bytes":len(raw)}
    d=json.loads(raw.decode("utf-8-sig"))
    if not isinstance(d,dict) or d.get("success") is not True:
        raise ValueError("PUBLIC_MEXC_UNEXPECTED_RESPONSE")
    return d.get("data"),receipt

def dec(x,label):
    try:v=Decimal(str(x))
    except (InvalidOperation,ValueError,TypeError):raise ValueError(label)
    if not v.is_finite():raise ValueError(label)
    return v

def extract_detail(data,symbol):
    valid_symbol(symbol)
    if isinstance(data,list):
        matching=[item for item in data if isinstance(item,dict) and item.get("symbol")==symbol]
        if len(matching)!=1:raise ValueError("MEXC_SPEC_SYMBOL_MISSING_OR_DUPLICATE")
        obj=matching[0]
    elif isinstance(data,dict) and data.get("symbol")==symbol:
        obj=data
    else:raise ValueError("MEXC_SPEC_SYMBOL_SHAPE")
    fields=("contractSize","minVol","volUnit","maxVol","priceUnit")
    result={k:dec(obj.get(k),"MISSING_OR_BAD_SPEC_"+k) for k in fields}
    if any(result[k]<=0 for k in fields):raise ValueError("NONPOSITIVE_CONTRACT_SPEC")
    if result["maxVol"]<result["minVol"]:
        raise ValueError("CONTRACT_MIN_EXCEEDS_MAX")
    if obj.get("futureType") not in (None,1):
        raise ValueError("NOT_PERPETUAL_CONTRACT")
    if obj.get("state") not in (None,0):
        raise ValueError("NOT_ENABLED_CONTRACT")
    if obj.get("apiAllowed") is False:
        raise ValueError("CONTRACT_MARKED_API_NOT_ALLOWED")
    result["symbol"]=symbol
    result["reported_taker_fee"]=str(obj.get("takerFeeRate","NOT_ACCOUNT_VERIFIED"))
    result["reported_maker_fee"]=str(obj.get("makerFeeRate","NOT_ACCOUNT_VERIFIED"))
    return result

def book_levels(entries,name):
    if not isinstance(entries,list) or not entries:
        raise ValueError("MISSING_"+name+"_DEPTH")
    out=[]
    for e in entries:
        if not isinstance(e,list) or len(e)<3:raise ValueError("UNKNOWN_MEXC_DEPTH_ARRAY_SEMANTICS")
        price=dec(e[0],"INVALID_PRICE")
        num_orders=dec(e[1],"INVALID_ORDER_COUNT")
        contracts=dec(e[2],"INVALID_CONTRACT_QTY")
        if price<=0 or num_orders<0 or contracts<=0:
            raise ValueError("NONPOSITIVE_DEPTH")
        out.append({"price":price,"number_of_orders":num_orders,"contracts":contracts})
    if any(out[i+1]["price"]<out[i]["price"] for i in range(len(out)-1)) and name=="asks":
        raise ValueError("ASK_DEPTH_NOT_ORDERED")
    if any(out[i+1]["price"]>out[i]["price"] for i in range(len(out)-1)) and name=="bids":
        raise ValueError("BID_DEPTH_NOT_ORDERED")
    return out

def analyze_book(data,receipt,symbol,spec):
    if not isinstance(data,dict):raise ValueError("INVALID_PUBLIC_DEPTH_SHAPE")
    asks=book_levels(data.get("asks"),"asks")
    bids=book_levels(data.get("bids"),"bids")
    ask,bid=asks[0]["price"],bids[0]["price"]
    if bid>=ask:raise ValueError("CROSSED_OR_UNUSABLE_DEPTH")
    ts=data.get("timestamp")
    now=receipt["local_received_ms"]
    if not isinstance(ts,int) or ts<1_500_000_000_000:raise ValueError("DEPTH_TIMESTAMP_INVALID")
    age=now-ts
    if age<0 or age>MAX_AGE_MS:raise ValueError("SOURCE_DEPTH_STALE_OR_CLOCK_SKEW")
    if receipt["request_latency_ms"]>MAX_LATENCY_MS:
        raise ValueError("PUBLIC_QUOTE_LATENCY_EXCESSIVE")
    result={"best_ask":str(ask),"best_bid":str(bid),
            "public_spread_bps":float(10000*(ask-bid)/((ask+bid)/2)),
            "book_timestamp_ms":ts,"quote_age_ms":age,
            "public_depth_not_an_executable_fill":True,
            "samples":[]}
    for quote in PAPER_NOTIONALS:
        desired=Decimal(quote)/(ask*spec["contractSize"])
        # Exact conservative ceil of contract count to the nearest allowed step.
        vol=spec["volUnit"]*(desired/spec["volUnit"]).to_integral_value(rounding=ROUND_CEILING)
        if vol<spec["minVol"]:
            vol=spec["minVol"]+(max(Decimal(0),vol-spec["minVol"])/spec["volUnit"]).to_integral_value(rounding=ROUND_CEILING)*spec["volUnit"]
        if vol>spec["maxVol"]:raise ValueError("PAPER_VOLUME_EXCEEDS_PUBLIC_CONTRACT_MAX")
        min_notional=spec["minVol"]*ask*spec["contractSize"]
        # Client's volume step and minimum are needed for claimed feasibility.
        if vol<=0 or (vol-spec["minVol"])%spec["volUnit"]!=0:
            raise ValueError("CONTRACT_STEP_MISMATCH")
        book_qty=sum(x["contracts"] for x in asks)
        demand_qty=vol
        enough=book_qty>=demand_qty
        left=demand_qty
        cost=Decimal(0)
        for x in asks:
            take=min(left,x["contracts"])
            cost+=take*x["price"]*spec["contractSize"]
            left-=take
            if left<=0:break
        weighted=(cost/(demand_qty*spec["contractSize"])) if enough else None
        result["samples"].append({
            "hypothetical_notional_target_usdt":quote,
            "required_contracts":str(vol),
            "minimum_paper_notional_usdt":str(min_notional),
            "rounded_order_notional_at_best_ask_usdt":str(vol*ask*spec["contractSize"]),
            "ask_book_contracts_visible":str(book_qty),
            "visible_asks_cover_required_contracts":enough,
            "observed_ask_book_weighted_price_if_full_visible":str(weighted) if weighted is not None else None,
            "NOT_an_assured_fill":True})
    return result

def validate_funding(data,symbol,received_ms):
    if not isinstance(data,dict) or data.get("symbol")!=symbol:
        raise ValueError("PUBLIC_FUNDING_FIELD_IDENTITY_MISSING")
    for field in ("fundingRate","fairPrice","idxPrice"):
        x=dec(data.get(field),"FUNDING_"+field+"_INVALID")
        if field!="fundingRate" and x<=0:raise ValueError("FUNDING_REFERENCE_NONPOSITIVE")
    t=data.get("timestamp")
    if not isinstance(t,int) or abs(t-received_ms)>30_000:
        raise ValueError("FUNDING_QUOTE_TIME_STALE")
    return {"reported_funding_rate":str(data["fundingRate"]),
            "reported_fair_price":str(data["fairPrice"]),
            "reported_index_price":str(data["idxPrice"]),
            "quote_timestamp_ms":t,
            "NEXT_settlement_time_ms":data.get("nextSettleTime"),
            "NOT_historical_funding_or_user_account":True}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--symbol",required=True,choices=SYMBOLS)
    p.add_argument("--output-dir",type=Path,required=True)
    a=p.parse_args()
    a.output_dir.mkdir(parents=True,exist_ok=True)
    result={"symbol":a.symbol,"status":"PUBLIC_SOURCE_BLOCKED",
            "role":"ONE_READONLY_PUBLIC_SNAPSHOT_NOT_A_FORWARD_COLLECTOR",
            "venue":"MEXC Futures","taker_fee_assumption_bps_per_side":TAKER_BPS_SIDE,
            "user_fee_authenticated":False,"user_region_eligibility_checked":False,
            "real_fill_proven":False,"trading_authority":"NONE"}
    try:
        spec_raw,spec_recv=source_get("detail",a.symbol)
        result["public_contract_response_receipt"]=spec_recv
        spec=extract_detail(spec_raw,a.symbol)
        result["contract_spec"]={k:str(v) for k,v in spec.items()}
        depth,depth_recv=source_get("depth",a.symbol)
        result["public_depth_response_receipt"]=depth_recv
        result["quote"]=analyze_book(depth,depth_recv,a.symbol,spec)
        funding,funding_recv=source_get("funding",a.symbol)
        result["public_funding_response_receipt"]=funding_recv
        result["funding"]=validate_funding(funding,a.symbol,funding_recv["local_received_ms"])
        result["status"]="PUBLIC_ONE_SHOT_QUOTES_VALID_NOT_ACTUAL_FILLS"
    except Exception as exc:
        result["status"]="PUBLIC_SOURCE_BLOCKED"
        result["block_reason"]=type(exc).__name__+":"+str(exc)
    (a.output_dir/"PUBLIC_VENUE_PROBE.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print("VENUE_PUBLIC_FINAL",json.dumps({k:v for k,v in result.items() if k in ("symbol","status","block_reason","quote","funding","contract_spec")},sort_keys=True),flush=True)
    if result["status"]!="PUBLIC_ONE_SHOT_QUOTES_VALID_NOT_ACTUAL_FILLS":
        raise SystemExit(2)
if __name__=="__main__":main()
