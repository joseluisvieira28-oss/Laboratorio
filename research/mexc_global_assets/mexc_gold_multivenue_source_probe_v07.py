#!/usr/bin/env python3
"""MEXC GOLD multi-venue public source gate V0.7."""
from __future__ import annotations
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
import requests

OUT=Path("artifacts/mexc_global_assets/gold_multivenue_source_gate_v07")
UA="CryptoLab-MEXC-GOLD-MultiVenue/0.7"

def now(): return datetime.now(timezone.utc).isoformat()
def sha(b): return hashlib.sha256(b).hexdigest()

def get(url,params=None):
    r=requests.get(url,params=params,headers={"User-Agent":UA},timeout=30)
    raw=r.content
    meta={"url":r.url,"status_code":r.status_code,"captured_at_utc":now(),"sha256":sha(raw),"bytes":len(raw)}
    if r.status_code!=200: raise RuntimeError(f"HTTP {r.status_code}: {r.url}: {raw[:300]!r}")
    return raw,r.json(),meta

def save(name,raw,meta):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/name).write_bytes(raw)
    (OUT/(name+".meta.json")).write_text(json.dumps(meta,indent=2,sort_keys=True),encoding="utf-8")

def f(x):
    try: return float(x)
    except Exception: return None

def main():
    report={"lab":"MEXC_GOLD_MULTIVENUE_SOURCE_GATE_V0_7","captured_at_utc":now(),
            "source_only":True,"outcomes_opened":0,"auth_used":False,
            "private_endpoints_used":False,"account_reads":False,"wallets_used":False,
            "orders":False,"exchange_mutation":False,"venues":{}}

    raw,j,m=get("https://api.mexc.com/api/v1/contract/detail",{"symbol":"XAU_USDT"})
    save("mexc_xau_detail.json",raw,m)
    if j.get("success") is not True: raise RuntimeError(f"MEXC detail non-success:{j}")
    d=j.get("data")
    if isinstance(d,list): d=next((x for x in d if x.get("symbol")=="XAU_USDT"),None)
    if not isinstance(d,dict): raise RuntimeError("MEXC_XAU_DETAIL_MISSING")
    report["mexc_detail"]={k:d.get(k) for k in ["symbol","indexOrigin","apiAllowed","isZeroFeeSymbol","makerFeeRate","takerFeeRate","contractSize"]}

    raw,j,m=get("https://api.mexc.com/api/v1/contract/index_price/XAU_USDT")
    save("mexc_xau_index.json",raw,m)
    if j.get("success") is not True: raise RuntimeError(f"MEXC index non-success:{j}")
    md=j.get("data") or {}
    mexc=f(md.get("indexPrice") if md.get("indexPrice") is not None else md.get("price"))
    if not mexc: raise RuntimeError("MEXC_XAU_INDEX_MISSING")
    report["mexc_index_price"]=mexc
    report["mexc_index_timestamp"]=md.get("timestamp")

    # Binance
    raw,b,m=get("https://fapi.binance.com/fapi/v1/ticker/bookTicker",{"symbol":"XAUUSDT"})
    save("binance_xau_book.json",raw,m)
    bb,ba=f(b.get("bidPrice")),f(b.get("askPrice"))
    bmid=(bb+ba)/2 if bb and ba else None
    report["venues"]["BINANCE"]={"bid":bb,"ask":ba,"mid":bmid,"time":b.get("time")}

    # Bybit
    raw,y,m=get("https://api.bybit.com/v5/market/tickers",{"category":"linear","symbol":"XAUUSDT"})
    save("bybit_xau_ticker.json",raw,m)
    if y.get("retCode")!=0: raise RuntimeError(f"BYBIT_NONZERO:{y}")
    yl=((y.get("result") or {}).get("list") or [])
    if not yl: raise RuntimeError("BYBIT_XAU_MISSING")
    yy=yl[0]
    yb,ya=f(yy.get("bid1Price")),f(yy.get("ask1Price"))
    ymid=(yb+ya)/2 if yb and ya else f(yy.get("lastPrice"))
    report["venues"]["BYBIT"]={"bid":yb,"ask":ya,"mid":ymid,"last":f(yy.get("lastPrice")),"time":y.get("time")}

    # Bitget
    raw,g,m=get("https://api.bitget.com/api/v2/mix/market/ticker",{"symbol":"XAUUSDT","productType":"USDT-FUTURES"})
    save("bitget_xau_ticker.json",raw,m)
    if g.get("code")!="00000": raise RuntimeError(f"BITGET_NONZERO:{g}")
    gl=g.get("data") or []
    if not gl: raise RuntimeError("BITGET_XAU_MISSING")
    gg=gl[0]
    gb,ga=f(gg.get("bidPr")),f(gg.get("askPr"))
    gmid=(gb+ga)/2 if gb and ga else f(gg.get("lastPr"))
    report["venues"]["BITGET"]={"bid":gb,"ask":ga,"mid":gmid,"last":f(gg.get("lastPr")),"time":gg.get("ts")}

    expected={"BINANCE","BITGET","BYBIT"}
    origin=set(str(x).upper() for x in (d.get("indexOrigin") or []))
    report["mexc_index_origin_normalized"]=sorted(origin)
    report["expected_origins"]=sorted(expected)

    scale={}
    for venue,v in report["venues"].items():
        mid=v.get("mid")
        scale[venue]=10000*(mexc/mid-1) if mid and mid>0 else None
    report["mexc_vs_external_mid_bps"]=scale

    gates={
      "index_origin_contains_expected": expected.issubset(origin),
      "binance_public_bbo": bmid is not None,
      "bybit_public_bbo": ymid is not None,
      "bitget_public_bbo": gmid is not None,
      "binance_scale_within_500bps": scale["BINANCE"] is not None and abs(scale["BINANCE"])<500,
      "bybit_scale_within_500bps": scale["BYBIT"] is not None and abs(scale["BYBIT"])<500,
      "bitget_scale_within_500bps": scale["BITGET"] is not None and abs(scale["BITGET"])<500,
    }
    report["gates"]=gates
    report["verdict"]="MEXC_GOLD_MULTIVENUE_SOURCE_PASS" if all(gates.values()) else "SOURCE_BLOCKED_MEXC_GOLD_MULTIVENUE"
    report["historical_outcomes_opened"]=0
    report["lead_lag_tested"]=False
    report["live_trading_authorized"]=False

    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"MEXC_GOLD_MULTIVENUE_SOURCE_GATE_RECEIPT_V07.json").write_text(json.dumps(report,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps(report,indent=2,sort_keys=True))

if __name__=="__main__": main()
