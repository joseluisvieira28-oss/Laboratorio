#!/usr/bin/env python3
"""Source-only proof for MEXC NVIDIA_USDT <-> Binance NVDAUSDT."""
from __future__ import annotations
import hashlib,json,time
from datetime import datetime,timezone
from pathlib import Path
import requests

OUT=Path("artifacts/mexc_global_assets/nvda_source_gate_v08")
MEXC="https://api.mexc.com"
BINANCE="https://fapi.binance.com"
UA="CryptoLab-NVDA-SourceGate/0.8"

def now(): return datetime.now(timezone.utc).isoformat()
def sha(b): return hashlib.sha256(b).hexdigest()

def get(url,params=None):
    r=requests.get(url,params=params,headers={"User-Agent":UA},timeout=30)
    raw=r.content
    if r.status_code!=200: raise RuntimeError(f"HTTP_{r.status_code}:{url}:{raw[:300]!r}")
    return raw,r.json(),r.url

def save(name,raw,meta):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/name).write_bytes(raw)
    (OUT/(name+".meta.json")).write_text(json.dumps(meta,indent=2,sort_keys=True),encoding="utf-8")

def main():
    report={"lab":"MEXC_BINANCE_NVDA_SOURCE_GATE_V0_8","captured_at_utc":now(),
            "source_only":True,"outcomes_opened":0,"auth_used":False,"account_reads":False,
            "wallet_used":False,"orders":False,"exchange_mutation":False,
            "mexc_symbol":"NVIDIA_USDT","binance_symbol":"NVDAUSDT"}

    raw,j,url=get(MEXC+"/api/v1/contract/detail",{"symbol":"NVIDIA_USDT"})
    save("mexc_detail.json",raw,{"url":url,"sha256":sha(raw),"captured_at_utc":now()})
    d=j.get("data") if isinstance(j,dict) else None
    if isinstance(d,list): d=next((x for x in d if x.get("symbol")=="NVIDIA_USDT"),None)
    if not isinstance(d,dict): raise RuntimeError("MEXC_NVIDIA_DETAIL_MISSING")
    report["mexc_detail"]={k:d.get(k) for k in [
        "symbol","displayName","indexOrigin","apiAllowed","isZeroFeeSymbol",
        "makerFeeRate","takerFeeRate","contractSize","futureType"
    ]}

    raw,j,url=get(MEXC+"/api/v1/contract/index_price/NVIDIA_USDT")
    save("mexc_index.json",raw,{"url":url,"sha256":sha(raw),"captured_at_utc":now()})
    md=j.get("data") or {}
    mexc_index=float(md["indexPrice"])
    report["mexc_index_price"]=mexc_index
    report["mexc_index_timestamp"]=md.get("timestamp")

    raw,j,url=get(MEXC+"/api/v1/contract/ticker",{"symbol":"NVIDIA_USDT"})
    save("mexc_ticker.json",raw,{"url":url,"sha256":sha(raw),"captured_at_utc":now()})
    td=j.get("data") if isinstance(j,dict) else None
    if isinstance(td,list): td=next((x for x in td if x.get("symbol")=="NVIDIA_USDT"),None)
    td=td or {}
    report["mexc_ticker"]={k:td.get(k) for k in ["symbol","lastPrice","bid1","ask1","timestamp"]}

    raw,ex,url=get(BINANCE+"/fapi/v1/exchangeInfo")
    save("binance_exchangeInfo.json",raw,{"url":url,"sha256":sha(raw),"captured_at_utc":now()})
    syms=ex.get("symbols") or []
    bx=next((x for x in syms if x.get("symbol")=="NVDAUSDT"),None)
    if not bx: raise RuntimeError("BINANCE_NVDAUSDT_MISSING")
    report["binance_contract"]={k:bx.get(k) for k in [
        "symbol","pair","contractType","status","baseAsset","quoteAsset","marginAsset"
    ]}

    raw,bk,url=get(BINANCE+"/fapi/v1/ticker/bookTicker",{"symbol":"NVDAUSDT"})
    save("binance_bookTicker.json",raw,{"url":url,"sha256":sha(raw),"captured_at_utc":now()})
    bid=float(bk["bidPrice"]); ask=float(bk["askPrice"]); mid=(bid+ask)/2
    report["binance_book"]={"bid":bid,"ask":ask,"mid":mid,"time":bk.get("time")}

    raw,pi,url=get(BINANCE+"/fapi/v1/premiumIndex",{"symbol":"NVDAUSDT"})
    save("binance_premiumIndex.json",raw,{"url":url,"sha256":sha(raw),"captured_at_utc":now()})
    report["binance_mark"]={k:pi.get(k) for k in ["symbol","markPrice","indexPrice","time"]}

    # Source-only kline structure checks: current 5 rows only, no historical outcome scoring.
    raw,mk,url=get(MEXC+"/api/v1/contract/kline/NVIDIA_USDT",{"interval":"Min1","start":int(time.time())-600,"end":int(time.time())})
    save("mexc_kline_probe.json",raw,{"url":url,"sha256":sha(raw),"captured_at_utc":now()})
    mrows=len((mk.get("data") or {}).get("time") or [])

    raw,bkl,url=get(BINANCE+"/fapi/v1/klines",{"symbol":"NVDAUSDT","interval":"1m","limit":5})
    save("binance_kline_probe.json",raw,{"url":url,"sha256":sha(raw),"captured_at_utc":now()})
    brows=len(bkl) if isinstance(bkl,list) else 0

    rel=10000*(mexc_index/mid-1) if mid>0 else None
    report["mexc_index_vs_binance_mid_bps"]=rel
    origin=report["mexc_detail"].get("indexOrigin")
    report["gates"]={
      "mexc_exact_contract":report["mexc_detail"].get("symbol")=="NVIDIA_USDT",
      "binance_exact_contract":report["binance_contract"].get("symbol")=="NVDAUSDT",
      "binance_nvda_identity":report["binance_contract"].get("baseAsset") in ("NVDA","NVDAON"),
      "mexc_live_index":mexc_index>0,
      "binance_live_book":bid>0 and ask>=bid,
      "scale_within_500bps":rel is not None and abs(rel)<500,
      "mexc_1m_kline_public":mrows>0,
      "binance_1m_kline_public":brows>0
    }
    report["mexc_index_origin_contains_binance"]=(
      isinstance(origin,list) and any("BINANCE" in str(x).upper() for x in origin)
    )
    passed=all(report["gates"].values())
    report["verdict"]="MEXC_BINANCE_NVDA_SOURCE_PASS" if passed else "SOURCE_BLOCKED_MEXC_BINANCE_NVDA"
    report["historical_outcomes_opened"]=0
    report["lead_lag_tested"]=False
    report["live_trading_authorized"]=False

    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"MEXC_BINANCE_NVDA_SOURCE_GATE_RECEIPT_V08.json").write_text(
      json.dumps(report,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps(report,indent=2,sort_keys=True))

if __name__=="__main__": main()
