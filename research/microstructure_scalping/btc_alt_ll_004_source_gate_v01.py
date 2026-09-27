#!/usr/bin/env python3
import json, urllib.request
from pathlib import Path

DATE="2024-05-01"
SYMBOLS=("BTCUSDT","ETHUSDT","SOLUSDT")
UA={"User-Agent":"Mozilla/5.0 Crypto-Lab-BTC-ALT-LL-004/0.1"}

def head(url):
    req=urllib.request.Request(url,headers=UA,method="HEAD")
    with urllib.request.urlopen(req,timeout=30) as r:
        return {"status":r.status,"content_length":int(r.headers.get("Content-Length") or 0),
                "content_type":r.headers.get("Content-Type"),"last_modified":r.headers.get("Last-Modified")}

def main():
    receipt={"purpose":"BTC->ALT MICRO LEAD-LAG SOURCE GATE ONLY — NO OUTCOMES",
             "date":DATE,"symbols":{}}
    ok=True
    for s in SYMBOLS:
        l2=f"https://quote-saver.bycsi.com/orderbook/linear/{s}/{DATE}_{s}_ob500.data.zip"
        tr=f"https://public.bybit.com/trading/{s}/{s}{DATE}.csv.gz"
        item={}
        for k,u in (("l2",l2),("trades",tr)):
            try:
                item[k]={"url":u,**head(u)}
                if item[k]["status"]!=200 or item[k]["content_length"]<=0: ok=False
            except Exception as e:
                item[k]={"url":u,"error":repr(e)}
                ok=False
        receipt["symbols"][s]=item
    receipt["gate"]="PASS" if ok else "BLOCKED"
    out=Path("research/microstructure_scalping/receipts"); out.mkdir(parents=True,exist_ok=True)
    (out/"btc_alt_ll_004_source_gate_v01.json").write_text(json.dumps(receipt,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps(receipt,indent=2,sort_keys=True))
    raise SystemExit(0 if ok else 2)

if __name__=="__main__":
    main()
