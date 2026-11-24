#!/usr/bin/env python3
"""BACKES006: public level-2 order book snapshots, no trades and no account.
Hypothetical volume impact is not a real fill and not signal performance.
"""
import datetime as dt
import hashlib
import json
import math
import pathlib
import urllib.parse
import urllib.request

OUT=pathlib.Path(__file__).resolve().parent/"results"
VALUES={"BTC":(100.,1000.,10000.),"ETH":(100.,1000.,10000.),
        "RATIO":(.001,.01,.1)}

def fetch(venue,asset,receipts):
    if venue=="Binance":
        symbol={"BTC":"BTCUSDT","ETH":"ETHUSDT","RATIO":"ETHBTC"}[asset]
        url="https://data-api.binance.vision/api/v3/depth?"+urllib.parse.urlencode({"symbol":symbol,"limit":100})
    else:
        symbol={"BTC":"BTC-USD","ETH":"ETH-USD","RATIO":"ETH-BTC"}[asset]
        url="https://api.exchange.coinbase.com/products/"+symbol+"/book?level=2"
    begin=dt.datetime.now(dt.timezone.utc).isoformat()
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-Backes006-Depth-ReadOnly/1.0","Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=30) as r:raw=r.read(8_000_000)
    end=dt.datetime.now(dt.timezone.utc).isoformat()
    if len(raw)>=8_000_000:raise ValueError("BOOK_BLOCKED oversized response")
    receipts.append({"venue":venue,"asset":asset,"symbol":symbol,"url":url,
        "start_utc":begin,"end_utc":end,"raw_sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)})
    return json.loads(raw),symbol

def validate_book(body):
    bids=[[float(z[0]),float(z[1])] for z in body.get("bids",[])]
    asks=[[float(z[0]),float(z[1])] for z in body.get("asks",[])]
    if not bids or not asks:raise ValueError("BOOK_BLOCKED missing bids/asks")
    if not all(math.isfinite(p) and math.isfinite(q) and p>0 and q>0
               for data in (bids,asks) for p,q in data):raise ValueError("BOOK_BLOCKED bad level")
    bids.sort(key=lambda x:-x[0]);asks.sort(key=lambda x:x[0])
    if bids[0][0]>asks[0][0] or asks[0][0]/bids[0][0]>1.03:
        raise ValueError("BOOK_BLOCKED crossed/wide")
    return bids,asks,(bids[0][0]+asks[0][0])/2

def vwap_quote_size(asks,bids,mid,amount):
    """Model BUY spending amount quote, SELL a base size worth amount at mid."""
    remaining=amount;qty=0.
    for price,size in asks:
        spend=min(remaining,price*size);qty+=spend/price;remaining-=spend
        if remaining<=1e-8:break
    if remaining>1e-7:buy={"status":"DEPTH_INSUFFICIENT","quote_shortfall":remaining}
    else:
        px=amount/qty
        buy={"status":"MODEL_ONLY","impact_vs_mid_bps":(px/mid-1)*10000,
             "slippage_over_best_ask_bps":(px/asks[0][0]-1)*10000}
    base=amount/mid;remain=base;earned=0.
    for price,size in bids:
        sold=min(remain,size);earned+=sold*price;remain-=sold
        if remain<=1e-9:break
    if remain>1e-9:sell={"status":"DEPTH_INSUFFICIENT","base_shortfall":remain}
    else:
        px=earned/base
        sell={"status":"MODEL_ONLY","impact_vs_mid_bps":(1-px/mid)*10000,
              "slippage_over_best_bid_bps":(1-px/bids[0][0])*10000}
    return {"quote_amount":amount,"buy":buy,"sell":sell}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    evidence={"study":"BACKES006-L2-DIAGNOSTIC","no_trading":True,"future_PnL":None,
      "started_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
      "receipts":[],"venues":{}}
    passed=0
    for venue in ("Binance","Coinbase"):
        evidence["venues"][venue]={}
        for asset in ("BTC","ETH","RATIO"):
            try:
                raw,pair=fetch(venue,asset,evidence["receipts"])
                bids,asks,mid=validate_book(raw)
                quote="BTC" if asset=="RATIO" else ("USDT" if venue=="Binance" else "USD")
                v={"status":"MODEL_ONLY","pair":pair,"quote_unit":quote,
                   "book_levels_bid":len(bids),"book_levels_ask":len(asks),
                   "mid":mid,
                   "spread_bps_mid":20000*(asks[0][0]-bids[0][0])/(asks[0][0]+bids[0][0]),
                   "best_ask_liquidity_quote":asks[0][0]*asks[0][1],
                   "best_bid_liquidity_quote":bids[0][0]*bids[0][1],
                   "what_if":[vwap_quote_size(asks,bids,mid,amt) for amt in VALUES[asset]]}
                evidence["venues"][venue][asset]=v;passed+=1
            except Exception as e:
                evidence["venues"][venue][asset]={"status":"BOOK_BLOCKED",
                  "error":type(e).__name__+": "+str(e)}
    evidence["finished_utc"]=dt.datetime.now(dt.timezone.utc).isoformat()
    (OUT/"DEPTH_PREFLIGHT.json").write_text(json.dumps(evidence,indent=2)+"\n")
    lines=["# BACKES006 — depth vs top-of-book only","",
      "**Read-only book. Not fills, not personal fees, not future PnL.**",
      "BTC / ETH hypothetical quote sizes: 100/1000/10000 USD/USDT.",
      "Direct ETH/BTC quote sizes: 0.001 / 0.01 / 0.1 BTC. Different quote numeraires.",
      "No arbitrage or exact synchronous price inference: snapshots collected sequentially.",
      "", "| Venue | Pair | Spread bps | Top ask liquidity | Mid-impact of middle hypothetical BUY |",
      "|---|---|---:|---:|---:|"]
    for venue in evidence["venues"]:
        for asset,x in evidence["venues"][venue].items():
            if x["status"]!="MODEL_ONLY":continue
            z=x["what_if"][1]["buy"]
            impact="INSUFFICIENT" if z["status"]!="MODEL_ONLY" else f"{z['impact_vs_mid_bps']:.4f}bps"
            lines.append(f"| {venue} | {x['pair']} | {x['spread_bps_mid']:.4f} | "+
              f"{x['best_ask_liquidity_quote']:.5f} {x['quote_unit']} | {impact} |")
    lines+=["","The observed book is ephemeral; future execution requires account-specific fees, order sizes and actual fills."]
    (OUT/"DEPTH_RESULT.md").write_text("\n".join(lines)+"\n")
    print("BACKES006_DEPTH",passed,"of 6 valid public orderbook snapshots")
    if passed!=6:raise RuntimeError("BOOK_SOURCE_BLOCKED "+str(6-passed))
if __name__=="__main__":main()
