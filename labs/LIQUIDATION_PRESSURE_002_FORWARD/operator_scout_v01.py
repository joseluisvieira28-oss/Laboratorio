#!/usr/bin/env python3
from __future__ import annotations
import asyncio, json, math, pathlib, time
from collections import defaultdict
from datetime import datetime, timezone
import websockets

URL="wss://stream.bybit.com/v5/public/linear"
THRESHOLDS={
 "BTCUSDT":297490.25500000006,
 "ETHUSDT":334400.8419,
 "SOLUSDT":46364.0,
 "XRPUSDT":79025.72580000001,
 "DOGEUSDT":174472.60349,
}
SYMBOLS=list(THRESHOLDS)
WINDOW_MS=5000
OBS_SECONDS=180
OUT=pathlib.Path("liquidation_reversal_operator_scout.json")

def utc_now(): return datetime.now(timezone.utc).isoformat()

def valid_book(b):
    return b["bids"] and b["asks"] and max(b["bids"]) < min(b["asks"])

def best(b):
    return max(b["bids"]), min(b["asks"])

async def main():
    topics=[f"allLiquidation.{s}" for s in SYMBOLS]+[f"orderbook.50.{s}" for s in SYMBOLS]
    books={s:{"bids":{},"asks":{}} for s in SYMBOLS}
    bins=defaultdict(lambda:{"long":0.0,"short":0.0,"records":0})
    signals=[]
    start=time.monotonic()
    async with websockets.connect(URL,ping_interval=20,ping_timeout=20,max_size=2**24) as ws:
        await ws.send(json.dumps({"op":"subscribe","args":topics}))
        while time.monotonic()-start < OBS_SECONDS:
            try:
                raw=await asyncio.wait_for(ws.recv(),timeout=3)
            except asyncio.TimeoutError:
                continue
            obj=json.loads(raw)
            topic=obj.get("topic","")
            if topic.startswith("allLiquidation."):
                data=obj.get("data") or []
                if not isinstance(data,list): data=[data]
                for x in data:
                    try:
                        s=str(x["s"]); ts=int(x["T"]); side=str(x["S"])
                        n=float(x["v"])*float(x["p"])
                    except Exception:
                        continue
                    if s not in THRESHOLDS: continue
                    k=(s,(ts//WINDOW_MS)*WINDOW_MS)
                    bins[k]["records"]+=1
                    if side=="Buy": bins[k]["long"]+=n
                    elif side=="Sell": bins[k]["short"]+=n
                    total=bins[k]["long"]+bins[k]["short"]
                    if total>=THRESHOLDS[s] and not any(z["symbol"]==s and z["window_start_ms"]==k[1] for z in signals):
                        net=bins[k]["short"]-bins[k]["long"]
                        if net==0: continue
                        # reversal direction: long after long liquidations (forced sells), short after short liquidations
                        direction="SHORT" if net>0 else "LONG"
                        b=books[s]
                        bid=ask=None
                        if valid_book(b): bid,ask=best(b)
                        signals.append({
                          "symbol":s,"window_start_ms":k[1],"detected_at_utc":utc_now(),
                          "total_liq_notional":total,
                          "long_liq_notional":bins[k]["long"],
                          "short_liq_notional":bins[k]["short"],
                          "threshold":THRESHOLDS[s],
                          "reversal_direction":direction,
                          "best_bid":bid,"best_ask":ask,
                          "book_ready":bid is not None and ask is not None
                        })
            elif topic.startswith("orderbook.50."):
                d=obj.get("data") or {}
                s=d.get("s") or topic.rsplit(".",1)[-1]
                if s not in books: continue
                typ=obj.get("type")
                if typ=="snapshot":
                    books[s]={"bids":{},"asks":{}}
                for side_key,target in [("b","bids"),("a","asks")]:
                    for row in d.get(side_key) or []:
                        try: p=float(row[0]); q=float(row[1])
                        except: continue
                        if q==0: books[s][target].pop(p,None)
                        else: books[s][target][p]=q

    result={
      "observed_at_utc":utc_now(),
      "observation_seconds":OBS_SECONDS,
      "thresholds":THRESHOLDS,
      "signal_count":len(signals),
      "signals":signals,
      "verdict_now":"SHADOW_SIGNAL_PRESENT" if signals else "NO_TRADE_NOW_NO_Q95_TRIGGER",
      "scientific_state":"INSUFFICIENT_FORWARD_SAMPLE",
      "orders":False,"authenticated":False,"wallets":False
    }
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))

if __name__=="__main__":
    asyncio.run(main())
