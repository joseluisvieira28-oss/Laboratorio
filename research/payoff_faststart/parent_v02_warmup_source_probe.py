#!/usr/bin/env python3
"""SOURCE-ONLY BTC 1h warmup probe under preexisting Parent V0.2 forward authority.
No signals, fills, strategy returns or 2026 sealed holdout evaluation.
Only public Binance USD-M market-data GET, with immutable source receipts.
"""
from datetime import datetime,timezone
from pathlib import Path
import urllib.request,urllib.parse,json,hashlib,math
H=3600000
T0=1791936000000 # new 4R science boundary Oct14 00 UTC
PARENT_FIRST=1790233200000 # original Sept24 07 UTC authority
OUT=Path("research/payoff_faststart/data/PARENT_V02_WARMUP_PUBLIC_SOURCE.json")
def run():
    now=int(datetime.now(timezone.utc).timestamp()*1000)
    end=min((now//H)*H,T0)
    first=end-200*H
    if first<PARENT_FIRST:raise ValueError("OUTSIDE_PARENT_V02_PUBLIC_FORWARD_SCOPE")
    qs=urllib.parse.urlencode({"symbol":"BTCUSDT","interval":"1h","startTime":first,"endTime":end-1,"limit":300})
    url="https://www.binance.com/fapi/v1/klines?"+qs
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-ParentV02-WarmupSourceOnly"})
    with urllib.request.urlopen(req,timeout=30) as response:
        payload=response.read(300000)
    rows=json.loads(payload)
    if not isinstance(rows,list) or len(rows)!=200:raise ValueError("HISTORICAL_WARMUP_INCOMPLETE")
    bars=[]
    for i,x in enumerate(rows):
        t=int(x[0]);ct=int(x[6])
        values=[float(y) for y in x[1:6]]
        o,hi,lo,c,vol=values
        if t!=first+i*H or ct>=end or not all(math.isfinite(v) for v in values):
            raise ValueError("DATA_TIMESTAMP_OR_NUMERIC_INVALID")
        if not (0<lo<=min(o,c)<=max(o,c)<=hi and vol>=0):
            raise ValueError("INVALID_PUBLIC_KLINE")
        bars.append({"t":t,"open":o,"high":hi,"low":lo,"close":c,"volume":vol})
    summary={"classification":"PARENT_V02_PREBOUNDARY_INDICATOR_WARMUP_SOURCE_ONLY",
       "authority":"BTC_CONVEX_PARENT_V02_ALREADY_AUTHORIZED_PUBLIC_SOURCE",
       "parent_freeze_sha":"673d50b2f786e88c593a900db1a9aac6a265d215",
       "policy":"NO_NEW_PAYOFF_ECONOMIC_OUTCOME_OR_SIGNAL_BEFORE_2026_10_14",
       "status":"SOURCE_OBSERVED_NOT_FOR_PROMOTION",
       "requested_from_ms":first,"through_exclusive_ms":end,
       "bar_count":200,
       "source_url":url,"source_payload_sha256":hashlib.sha256(payload).hexdigest(),
       "bars_sha256":hashlib.sha256(json.dumps(bars,sort_keys=True,separators=(",",":")).encode()).hexdigest(),
       "bars":bars,"trading_authority":"NONE"}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(summary,sort_keys=True,indent=2)+"\n")
    print(json.dumps({k:v for k,v in summary.items() if k!="bars"},sort_keys=True))
if __name__=="__main__":run()
