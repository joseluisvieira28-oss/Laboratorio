#!/usr/bin/env python3
"""GOLD XAU cross-venue source probe: MEXC <-> Bitget.

SOURCE ONLY. No historical outcome scoring, accounts, keys, private endpoints,
wallets, orders, mutation or live trading.
"""
from __future__ import annotations
import hashlib, json, time
from datetime import datetime, timezone
from pathlib import Path
import requests

OUT=Path("artifacts/mexc_global_assets/gold_bitget_source_gate_v08")
UA="CryptoLab-GOLD-Bitget-SourceGate/0.8"
MEXC="https://api.mexc.com"
BITGET="https://api.bitget.com"

def now():
    return datetime.now(timezone.utc).isoformat()

def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def get(url, params=None):
    r=requests.get(url, params=params, headers={"User-Agent":UA}, timeout=30)
    raw=r.content
    meta={"url":r.url,"captured_at_utc":now(),"status_code":r.status_code,
          "sha256":sha(raw),"bytes":len(raw)}
    if r.status_code!=200:
        raise RuntimeError(f"HTTP {r.status_code} {r.url}: {raw[:300]!r}")
    return raw,r.json(),meta

def save(name,raw,meta):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/name).write_bytes(raw)
    (OUT/(name+".meta.json")).write_text(json.dumps(meta,indent=2,sort_keys=True),encoding="utf-8")

def fl(x):
    try: return float(x)
    except Exception: return None

def main():
    report={
      "lab":"GOLD_BITGET_MEXC_SOURCE_GATE_V0_8",
      "captured_at_utc":now(),
      "source_only":True,
      "outcomes_opened":0,
      "lead_lag_tested":False,
      "auth_used":False,
      "private_endpoints_used":False,
      "account_reads":False,
      "wallets_used":False,
      "orders":False,
      "exchange_mutation":False,
      "live_trading_authorized":False
    }

    raw,j,m=get(MEXC+"/api/v1/contract/detail",{"symbol":"XAU_USDT"})
    save("mexc_xau_detail.json",raw,m)
    d=j.get("data")
    if isinstance(d,list):
        d=next((x for x in d if x.get("symbol")=="XAU_USDT"),None)
    if not isinstance(d,dict):
        raise RuntimeError("MEXC_XAU_DETAIL_MISSING")
    report["mexc_detail"]={k:d.get(k) for k in
      ["symbol","indexOrigin","apiAllowed","futureType","contractSize",
       "isZeroFeeSymbol","makerFeeRate","takerFeeRate"]}

    raw,j,m=get(MEXC+"/api/v1/contract/ticker",{"symbol":"XAU_USDT"})
    save("mexc_xau_ticker.json",raw,m)
    td=j.get("data") or {}
    mexc_px=fl(td.get("lastPrice") or td.get("fairPrice") or td.get("indexPrice"))
    report["mexc_ticker"]=td

    end=int(time.time()); start=end-1800
    raw,j,m=get(MEXC+"/api/v1/contract/kline/XAU_USDT",
                {"interval":"Min1","start":start,"end":end})
    save("mexc_xau_kline_1m.json",raw,m)
    md=j.get("data") or {}
    report["mexc_1m_rows"]=len(md.get("time") or [])

    raw,j,m=get(BITGET+"/api/v3/market/instruments",
                {"category":"USDT-FUTURES","symbol":"XAUUSDT"})
    save("bitget_xau_instrument.json",raw,m)
    if str(j.get("code"))!="00000":
        raise RuntimeError(f"BITGET instrument non-success {j}")
    rows=j.get("data") or []
    bsym=next((x for x in rows if x.get("symbol")=="XAUUSDT"),None)
    if not bsym:
        raise RuntimeError("BITGET_XAUUSDT_MISSING")
    report["bitget_symbol"]={k:bsym.get(k) for k in
      ["symbol","category","baseCoin","quoteCoin","isRwa","isReality","status"]}

    raw,j,m=get(BITGET+"/api/v2/mix/market/ticker",
                {"symbol":"XAUUSDT","productType":"USDT-FUTURES"})
    save("bitget_xau_ticker.json",raw,m)
    if str(j.get("code"))!="00000":
        raise RuntimeError(f"BITGET ticker non-success {j}")
    btd=(j.get("data") or [{}])[0]
    bit_px=fl(btd.get("lastPr"))
    report["bitget_ticker"]=btd

    nowms=int(time.time()*1000)
    raw,j,m=get(BITGET+"/api/v3/market/candles",{
      "category":"USDT-FUTURES","symbol":"XAUUSDT","interval":"1m",
      "startTime":str(nowms-30*60*1000),"endTime":str(nowms),"limit":"30"
    })
    save("bitget_xau_kline_1m.json",raw,m)
    if str(j.get("code"))!="00000":
        raise RuntimeError(f"BITGET candles non-success {j}")
    report["bitget_1m_rows"]=len(j.get("data") or [])

    prices={"mexc":mexc_px,"bitget":bit_px}
    report["live_prices"]=prices
    vals=[x for x in prices.values() if x is not None and x>0]
    dispersion=10000*(max(vals)/min(vals)-1) if len(vals)==2 else None
    report["live_price_dispersion_bps"]=dispersion

    checks={
      "mexc_identity":d.get("symbol")=="XAU_USDT",
      "mexc_declares_bitget":"BITGET_FUTURE" in (d.get("indexOrigin") or []),
      "bitget_identity":bsym.get("symbol")=="XAUUSDT",
      "public_1m_candles":report["mexc_1m_rows"]>=10 and report["bitget_1m_rows"]>=10,
      "same_scale_under_500bps":dispersion is not None and dispersion<500
    }
    report["checks"]=checks
    report["verdict"]="GOLD_BITGET_MEXC_SOURCE_PASS" if all(checks.values()) else "SOURCE_BLOCKED_GOLD_BITGET_MEXC"

    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"GOLD_BITGET_MEXC_SOURCE_GATE_RECEIPT_V08.json").write_text(
      json.dumps(report,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps({
      "verdict":report["verdict"],
      "live_prices":prices,
      "dispersion_bps":dispersion,
      "checks":checks,
      "mexc_indexOrigin":d.get("indexOrigin"),
      "outcomes_opened":0,
      "live_trading_authorized":False
    },indent=2,sort_keys=True))

if __name__=="__main__":
    main()
