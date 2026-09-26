#!/usr/bin/env python3
import json, urllib.request
from pathlib import Path

BASE="https://data.binance.vision/data/futures/um/monthly/klines"
SYMS=("BTCUSDT","ETHUSDT")
MONTHS=("2025-08","2025-10","2025-12")

def head(url):
    req=urllib.request.Request(url,method="HEAD",headers={"User-Agent":"Crypto-Lab-LICP-HIST/0.1"})
    with urllib.request.urlopen(req,timeout=30) as r:
        return {"status":r.status,"content_length":int(r.headers.get("Content-Length","0") or 0),
                "last_modified":r.headers.get("Last-Modified")}

def main():
    out={"purpose":"BINANCE VISION 2025 FUTURES KLINE ARCHIVE SOURCE ONLY","months":{}}
    good=True
    for m in MONTHS:
        out["months"][m]={}
        for s in SYMS:
            url=f"{BASE}/{s}/1m/{s}-1m-{m}.zip"
            try:
                x=head(url);x["url"]=url;out["months"][m][s]=x
                if x["status"]!=200 or x["content_length"]<=0:good=False
            except Exception as e:
                out["months"][m][s]={"url":url,"error":repr(e)};good=False
    out["gate"]="PASS_SAMPLE" if good else "BLOCKED"
    p=Path("research/liquidation_cascade/receipts");p.mkdir(parents=True,exist_ok=True)
    (p/"licp_hist_002_binance_vision_source_v01.json").write_text(
        json.dumps(out,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps(out,indent=2,sort_keys=True))
    raise SystemExit(0 if good else 2)

if __name__=="__main__":main()
