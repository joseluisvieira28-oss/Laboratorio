#!/usr/bin/env python3
"""One-shot public-source paired-perp funding screen. No account, orders or trading."""
import argparse
import datetime as datetime
import hashlib
import json
import pathlib
import time
from decimal import Decimal, InvalidOperation
from urllib.request import Request, urlopen

ASSETS = ("BTC", "ETH", "SOL")
FEE_BPS = Decimal("24")  # 4 fills * hypothetical 6bps/fill, not user fee
MAX_BOOK_AGE_MS = 30000
MAX_COLLECTION_MS = 30000
EIGHT_HOURS_MS = 28800000
TWO_MINUTES_MS = 120000

def D(value):
    try:
        v = Decimal(str(value))
    except (TypeError, ValueError, InvalidOperation) as exc:
        raise ValueError("INVALID_DECIMAL") from exc
    if not v.is_finite():
        raise ValueError("NONFINITE_DECIMAL")
    return v

def millis(v):
    if v is None:
        raise ValueError("MISSING_TIMESTAMP")
    return int(v)

def bbo(bid, ask, bid_qty, ask_qty):
    b, a, bq, aq = (D(x) for x in (bid, ask, bid_qty, ask_qty))
    if min(b, a, bq, aq) <= 0 or b >= a:
        raise ValueError("INVALID_OR_CROSSED_BBO")
    return {"bid": str(b), "ask": str(a), "spread_bps": (a-b)/((a+b)/2)*10000}

def screen_pair(asset, objects, now):
    oid = asset + "-USDT-SWAP"
    bid = asset + "USDT"
    of = objects["okx_funding"]["data"]
    ob = objects["okx_book"]["data"]
    bt = objects["bybit_ticker"]["result"]["list"]
    bi = objects["bybit_instrument"]["result"]["list"]
    bb = objects["bybit_book"]["result"]
    if any(len(items) != 1 for items in (of, ob, bt, bi)):
        raise ValueError("BAD_RESPONSE_CARDINALITY")
    of, ob, bt, bi = of[0], ob[0], bt[0], bi[0]
    if of["instId"] != oid or bt["symbol"] != bid or bi["symbol"] != bid or bb["s"] != bid:
        raise ValueError("INSTRUMENT_MISMATCH")
    if int(bi["fundingInterval"]) != 480:
        raise ValueError("BYBIT_NOT_8H")
    ot, op = millis(of["fundingTime"]), millis(of["prevFundingTime"])
    bytime = millis(bt["nextFundingTime"])
    if ot - op != EIGHT_HOURS_MS or min(ot, bytime) <= now or abs(ot-bytime) > TWO_MINUTES_MS:
        raise ValueError("FUNDING_TIME_NOT_FUTURE_ALIGNED_8H")
    okxbooktime = millis(ob["ts"])
    bybooktime = millis(bb.get("ts"))
    if not (0 <= now-okxbooktime <= MAX_BOOK_AGE_MS and 0 <= now-bybooktime <= MAX_BOOK_AGE_MS):
        raise ValueError("STALE_OR_FUTURE_BOOK")
    obid, oask = ob["bids"][0], ob["asks"][0]
    bbid, bask = bb["b"][0], bb["a"][0]
    o = bbo(obid[0], oask[0], obid[1], oask[1])
    b = bbo(bbid[0], bask[0], bbid[1], bask[1])
    ofr, bfr = D(of["fundingRate"]), D(bt["fundingRate"])
    predicted_gross = abs(ofr-bfr)*10000
    spread_proxy = o["spread_bps"] + b["spread_bps"]
    hurdle = FEE_BPS + spread_proxy
    margin = predicted_gross - hurdle
    return {
        "asset":asset, "verdict": "SOURCE_SCREEN_POSITIVE_NOT_EDGE" if margin > 0 else "SINGLE_INTERVAL_ESTIMATE_BELOW_FROZEN_HURDLE",
        "okx_predicted_rate":str(ofr),"bybit_predicted_rate":str(bfr),
        "higher_predicted_funding_venue": "OKX" if ofr>bfr else ("BYBIT" if bfr>ofr else "EQUAL"),
        "settlement_okx_ms":ot,"settlement_bybit_ms":bytime,
        "predicted_single_settlement_gross_bps":float(predicted_gross),
        "frozen_hypothetical_four_fill_fees_bps":float(FEE_BPS),
        "current_roundtrip_spread_proxy_bps":float(spread_proxy),
        "screen_margin_bps":float(margin),
        "okx_bbo_bid":o["bid"], "okx_bbo_ask":o["ask"],
        "bybit_bbo_bid":b["bid"],"bybit_bbo_ask":b["ask"],
        "not_proven": ["settled_funding","actual_fills","future_exit_prices","basis_drift","account_fees","net_profit","capital_feasibility"]
    }

def get(url, directory, label):
    req = Request(url, headers={"Accept":"application/json","User-Agent":"CryptoLab-SourceOnly/1.0"}, method="GET")
    with urlopen(req,timeout=8) as response:
        if response.status != 200:
            raise ValueError("HTTP_NOT_200")
        raw=response.read(1048577)
        if len(raw)>1048576:
            raise ValueError("OVERSIZE_JSON")
    obj=json.loads(raw)
    if ("www.okx.com" in url and str(obj.get("code"))!="0") or ("api.bybit.com" in url and str(obj.get("retCode"))!="0"):
        raise ValueError("EXCHANGE_ERROR_RESPONSE")
    (directory / (label+".json")).write_bytes(raw)
    return obj,hashlib.sha256(raw).hexdigest()

def run(out):
    output=pathlib.Path(out)
    output.mkdir(parents=True,exist_ok=True)
    start=int(time.time()*1000)
    receipt={"protocol":"FUNDING_CHEAP_FALSIFIER_PRE_SOURCE_FREEZE_2026_10_20",
             "started_utc":datetime.datetime.fromtimestamp(start/1000,datetime.timezone.utc).isoformat(),
             "mode":"PUBLIC_READ_ONLY","orders":0,"actual_profit":None,"edge_proven":False,
             "results":[],"source_receipts":[]}
    for asset in ASSETS:
        okx=asset+"-USDT-SWAP"
        by=asset+"USDT"
        urls={
            "okx_funding":f"https://www.okx.com/api/v5/public/funding-rate?instId={okx}",
            "okx_book":f"https://www.okx.com/api/v5/market/books?instId={okx}&sz=5",
            "bybit_ticker":f"https://api.bybit.com/v5/market/tickers?category=linear&symbol={by}",
            "bybit_book":f"https://api.bybit.com/v5/market/orderbook?category=linear&symbol={by}&limit=5",
            "bybit_instrument":f"https://api.bybit.com/v5/market/instruments-info?category=linear&symbol={by}"
        }
        obj={}
        for label,url in urls.items():
            try:
                value,sha=get(url,output,asset+"_"+label)
                obj[label]=value
                receipt["source_receipts"].append({"asset":asset,"source":label,"sha256":sha,"status":"OK"})
            except Exception as ex:
                receipt["source_receipts"].append({"asset":asset,"source":label,"status":"SOURCE_BLOCKED","error":str(ex)[:150]})
                break
        if len(obj) != len(urls):
            receipt["results"].append({"asset":asset,"verdict":"SOURCE_BLOCKED"})
            continue
        try:
            if int(time.time()*1000)-start > MAX_COLLECTION_MS:
                raise ValueError("SOURCE_WINDOW_OVER_30S")
            receipt["results"].append(screen_pair(asset,obj,int(time.time()*1000)))
        except Exception as ex:
            receipt["results"].append({"asset":asset,"verdict":"SOURCE_BLOCKED","error":str(ex)[:150]})
    receipt["finished_utc"]=datetime.datetime.now(datetime.timezone.utc).isoformat()
    receipt["valid_pair_count"]=sum(x["verdict"]!="SOURCE_BLOCKED" for x in receipt["results"])
    receipt["positive_screen_count"]=sum(x["verdict"]=="SOURCE_SCREEN_POSITIVE_NOT_EDGE" for x in receipt["results"])
    (output/"derived_receipt.json").write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("PUBLIC_ONE_SHOT_RECEIPT="+json.dumps(receipt,sort_keys=True))
    return receipt

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",default="source_receipt")
    run(parser.parse_args().out)
