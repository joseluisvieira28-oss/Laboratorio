#!/usr/bin/env python3
"""NVDA cross-venue source probe: MEXC / Binance Futures / Bitget Futures.

SOURCE ONLY. No accounts, keys, private endpoints, outcomes, orders, or mutation.
"""
from __future__ import annotations
import hashlib,json,time
from datetime import datetime,timezone
from pathlib import Path
import requests

OUT=Path("artifacts/mexc_global_assets/nvda_source_gate_v06")
UA="CryptoLab-NVDA-SourceGate/0.6"

MEXC="https://api.mexc.com"
BINANCE="https://fapi.binance.com"
BITGET="https://api.bitget.com"

def now(): return datetime.now(timezone.utc).isoformat()
def sha(b): return hashlib.sha256(b).hexdigest()

def get(url,params=None):
    r=requests.get(url,params=params,headers={"User-Agent":UA},timeout=30)
    raw=r.content
    if r.status_code!=200: raise RuntimeError(f"HTTP {r.status_code} {r.url}: {raw[:300]!r}")
    return raw,r.json(),{"url":r.url,"captured_at_utc":now(),"sha256":sha(raw),"bytes":len(raw)}

def save(name,raw,meta):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/name).write_bytes(raw)
    (OUT/(name+".meta.json")).write_text(json.dumps(meta,indent=2,sort_keys=True),encoding="utf-8")

def f(x):
    try:return float(x)
    except:return None

def main():
    report={"lab":"NVDA_CROSSVENUE_SOURCE_GATE_V0_6","captured_at_utc":now(),"source_only":True,
            "outcomes_opened":0,"auth_used":False,"private_endpoints_used":False,
            "account_reads":False,"wallets_used":False,"orders":False,"exchange_mutation":False}

    # MEXC identity + live price + small 1m sample
    raw,j,m=get(MEXC+"/api/v1/contract/detail",{"symbol":"NVIDIA_USDT"}); save("mexc_detail.json",raw,m)
    d=j.get("data")
    if isinstance(d,list): d=next((x for x in d if x.get("symbol")=="NVIDIA_USDT"),None)
    if not isinstance(d,dict): raise RuntimeError("MEXC_NVIDIA_DETAIL_MISSING")
    report["mexc_detail"]={k:d.get(k) for k in ["symbol","indexOrigin","apiAllowed","futureType","contractSize","isZeroFeeSymbol","makerFeeRate","takerFeeRate"]}

    raw,j,m=get(MEXC+"/api/v1/contract/ticker",{"symbol":"NVIDIA_USDT"}); save("mexc_ticker.json",raw,m)
    td=j.get("data") or {}
    mexc_px=f(td.get("lastPrice") or td.get("lastPrice") or td.get("fairPrice") or td.get("indexPrice"))
    report["mexc_ticker"]=td

    end=int(time.time()); start=end-1800
    raw,j,m=get(MEXC+"/api/v1/contract/kline/NVIDIA_USDT",{"interval":"Min1","start":start,"end":end}); save("mexc_kline_1m.json",raw,m)
    md=j.get("data") or {}
    report["mexc_1m_rows"]=len(md.get("time") or [])

    # Binance public identity/ticker/1m
    raw,j,m=get(BINANCE+"/fapi/v1/exchangeInfo"); save("binance_exchangeInfo.json",raw,m)
    sym=next((x for x in j.get("symbols",[]) if x.get("symbol")=="NVDAUSDT"),None)
    if not sym: raise RuntimeError("BINANCE_NVDAUSDT_MISSING")
    report["binance_symbol"]={k:sym.get(k) for k in ["symbol","pair","contractType","status","baseAsset","quoteAsset"]}

    raw,j,m=get(BINANCE+"/fapi/v1/ticker/price",{"symbol":"NVDAUSDT"}); save("binance_ticker.json",raw,m)
    bin_px=f(j.get("price")); report["binance_ticker"]=j

    raw,j,m=get(BINANCE+"/fapi/v1/klines",{"symbol":"NVDAUSDT","interval":"1m","limit":30}); save("binance_kline_1m.json",raw,m)
    report["binance_1m_rows"]=len(j) if isinstance(j,list) else 0

    # Bitget public identity/ticker/1m
    raw,j,m=get(BITGET+"/api/v3/market/instruments",{"category":"USDT-FUTURES","symbol":"NVDAUSDT"}); save("bitget_instrument.json",raw,m)
    if str(j.get("code"))!="00000": raise RuntimeError(f"BITGET instruments non-success {j}")
    data=j.get("data") or []
    bsym=next((x for x in data if x.get("symbol")=="NVDAUSDT"),None)
    if not bsym: raise RuntimeError("BITGET_NVDAUSDT_MISSING")
    report["bitget_symbol"]={k:bsym.get(k) for k in ["symbol","category","baseCoin","quoteCoin","isRwa","isReality","status"]}

    raw,j,m=get(BITGET+"/api/v2/mix/market/ticker",{"symbol":"NVDAUSDT","productType":"USDT-FUTURES"}); save("bitget_ticker.json",raw,m)
    if str(j.get("code"))!="00000": raise RuntimeError(f"BITGET ticker non-success {j}")
    btd=(j.get("data") or [{}])[0]
    bit_px=f(btd.get("lastPr")); report["bitget_ticker"]=btd

    nowms=int(time.time()*1000)
    raw,j,m=get(BITGET+"/api/v3/market/candles",{"category":"USDT-FUTURES","symbol":"NVDAUSDT","interval":"1m","startTime":str(nowms-30*60*1000),"endTime":str(nowms),"limit":"30"}); save("bitget_kline_1m.json",raw,m)
    if str(j.get("code"))!="00000": raise RuntimeError(f"BITGET candles non-success {j}")
    report["bitget_1m_rows"]=len(j.get("data") or [])

    prices={"mexc":mexc_px,"binance":bin_px,"bitget":bit_px}
    report["live_prices"]=prices
    vals=[x for x in prices.values() if x and x>0]
    if len(vals)<3: raise RuntimeError(f"LIVE_PRICE_MISSING:{prices}")
    hi=max(vals); lo=min(vals)
    dispersion_bps=10000*(hi/lo-1)
    report["live_price_dispersion_bps"]=dispersion_bps

    identity=(
      d.get("symbol")=="NVIDIA_USDT"
      and "BINANCE_FUTURE" in (d.get("indexOrigin") or [])
      and "BITGET_FUTURE" in (d.get("indexOrigin") or [])
      and sym.get("symbol")=="NVDAUSDT"
      and bsym.get("symbol")=="NVDAUSDT"
    )
    candles=(report["mexc_1m_rows"]>=10 and report["binance_1m_rows"]>=10 and report["bitget_1m_rows"]>=10)
    scale=dispersion_bps<500
    report["checks"]={"identity":identity,"public_1m_candles":candles,"same_scale_under_500bps":scale}
    report["verdict"]="NVDA_CROSSVENUE_SOURCE_PASS" if all(report["checks"].values()) else "SOURCE_BLOCKED_NVDA_CROSSVENUE"
    report["historical_outcomes_opened"]=0
    report["lead_lag_tested"]=False
    report["live_trading_authorized"]=False

    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"NVDA_CROSSVENUE_SOURCE_GATE_RECEIPT_V06.json").write_text(json.dumps(report,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps({"verdict":report["verdict"],"live_prices":prices,
                      "dispersion_bps":dispersion_bps,"checks":report["checks"],
                      "mexc_indexOrigin":d.get("indexOrigin"),"outcomes_opened":0,
                      "live_trading_authorized":False},indent=2,sort_keys=True))

if __name__=="__main__": main()
