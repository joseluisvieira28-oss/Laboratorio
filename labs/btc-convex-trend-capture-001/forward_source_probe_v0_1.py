#!/usr/bin/env python3
from __future__ import annotations
import json, urllib.request, urllib.parse
from datetime import datetime, timezone
from pathlib import Path

SYMBOLS=["BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT"]
BASE="https://www.binance.com"
OUT={"probe":"BTC_CONVEX_FORWARD_SOURCE_PROBE_V0.1","checked_at":datetime.now(timezone.utc).isoformat(),"symbols":{}}

def get_json(path,params):
    qs=urllib.parse.urlencode(params)
    url=BASE+path+"?"+qs
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-ForwardProbe/1.0"})
    with urllib.request.urlopen(req,timeout=30) as r:
        raw=r.read()
    return url,json.loads(raw.decode())

ok_all=True
for s in SYMBOLS:
    rec={"pass":False}
    try:
        ku,kl=get_json("/fapi/v1/klines",{"symbol":s,"interval":"1h","limit":5})
        if not isinstance(kl,list) or len(kl)<3:
            raise RuntimeError("bad kline payload")
        for q in kl:
            if not isinstance(q,list) or len(q)<7:
                raise RuntimeError("bad kline row")
            int(q[0]); float(q[1]); float(q[2]); float(q[3]); float(q[4]); float(q[5]); int(q[6])

        fu,fr=get_json("/fapi/v1/fundingRate",{"symbol":s,"limit":5})
        if not isinstance(fr,list):
            raise RuntimeError("bad funding payload")
        for x in fr:
            if "fundingTime" not in x or "fundingRate" not in x:
                raise RuntimeError("bad funding row")
            int(x["fundingTime"]); float(x["fundingRate"])
            if x.get("markPrice") not in (None,""):
                float(x["markPrice"])

        now_ms=int(datetime.now(timezone.utc).timestamp()*1000)
        complete=[q for q in kl if int(q[6])<now_ms]
        if not complete:
            raise RuntimeError("no completed kline")

        rec={
            "pass":True,
            "kline_url":ku,
            "funding_url":fu,
            "kline_rows":len(kl),
            "funding_rows":len(fr),
            "latest_completed_open_ms":int(complete[-1][0]),
            "latest_completed_close_ms":int(complete[-1][6]),
            "funding_mark_present":sum(1 for x in fr if x.get("markPrice") not in (None,"")),
        }
    except Exception as e:
        rec={"pass":False,"error":repr(e)}
        ok_all=False
    OUT["symbols"][s]=rec

OUT["overall"]="PASS" if ok_all else "FAIL_CLOSED"
p=Path(__file__).resolve().parent/"evidence"/"FORWARD_SOURCE_PROBE_V0.1.json"
p.parent.mkdir(exist_ok=True)
p.write_text(json.dumps(OUT,indent=2),encoding="utf-8")
print(json.dumps(OUT,indent=2))
if not ok_all:
    raise SystemExit("FAIL_CLOSED: forward source probe failed")
