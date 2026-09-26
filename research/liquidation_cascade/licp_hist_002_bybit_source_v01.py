#!/usr/bin/env python3
import datetime as dt
import json, urllib.parse, urllib.request
from pathlib import Path

BASE="https://api.bybit.com/v5/market/kline"
SYMS=("BTCUSDT","ETHUSDT")
DATES=("2025-08-10","2025-10-10","2025-12-31")

def ms(day):
    d=dt.datetime.fromisoformat(day+"T00:00:00+00:00")
    return int(d.timestamp()*1000)

def fetch(sym,day):
    start=ms(day)
    end=start+2*60*60*1000
    qs=urllib.parse.urlencode({
      "category":"linear","symbol":sym,"interval":"1",
      "start":start,"end":end,"limit":200
    })
    url=BASE+"?"+qs
    req=urllib.request.Request(url,headers={"User-Agent":"Crypto-Lab-LICP-HIST/0.1"})
    with urllib.request.urlopen(req,timeout=30) as r:
        j=json.loads(r.read().decode())
    if j.get("retCode")!=0:
        raise RuntimeError(f"retCode={j.get('retCode')}:{j.get('retMsg')}")
    rows=(j.get("result") or {}).get("list") or []
    times=sorted(int(x[0]) for x in rows)
    # SOURCE GATE deliberately discards OHLC.
    return {"count":len(times),"first_time":times[0] if times else None,
            "last_time":times[-1] if times else None}

def main():
    out={"purpose":"BYBIT 2025 HISTORICAL TIMESTAMP COVERAGE ONLY","dates":{}}
    good=True
    for d in DATES:
        out["dates"][d]={}
        for s in SYMS:
            try:
                r=fetch(s,d);out["dates"][d][s]=r
                if r["count"]==0:good=False
            except Exception as e:
                out["dates"][d][s]={"error":repr(e)};good=False
    out["gate"]="PASS_SAMPLE" if good else "BLOCKED"
    p=Path("research/liquidation_cascade/receipts");p.mkdir(parents=True,exist_ok=True)
    (p/"licp_hist_002_bybit_2025_source_v01.json").write_text(
      json.dumps(out,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps(out,indent=2,sort_keys=True))
    raise SystemExit(0 if good else 2)

if __name__=="__main__":main()
