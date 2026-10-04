#!/usr/bin/env python3
"""V0.6.1 Bitget -> MEXC NVDA source gate. SOURCE ONLY."""
from __future__ import annotations
import hashlib,json,time
from datetime import datetime,timezone
from pathlib import Path
import requests

OUT=Path("artifacts/mexc_global_assets/nvda_bitget_source_gate_v061")
UA="CryptoLab-NVDA-Bitget-SourceGate/0.6.1"
MEXC="https://api.mexc.com"
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
def fl(x):
    try:return float(x)
    except:return None

def main():
    report={"lab":"NVDA_BITGET_MEXC_SOURCE_GATE_V0_6_1","captured_at_utc":now(),
            "source_only":True,"outcomes_opened":0,"auth_used":False,"private_endpoints_used":False,
            "account_reads":False,"wallets_used":False,"orders":False,"exchange_mutation":False}

    raw,j,m=get(MEXC+"/api/v1/contract/detail",{"symbol":"NVIDIA_USDT"}); save("mexc_detail.json",raw,m)
    d=j.get("data")
    if isinstance(d,list): d=next((x for x in d if x.get("symbol")=="NVIDIA_USDT"),None)
    if not isinstance(d,dict): raise RuntimeError("MEXC_NVIDIA_DETAIL_MISSING")
    report["mexc_detail"]={k:d.get(k) for k in ["symbol","indexOrigin","apiAllowed","contractSize","isZeroFeeSymbol","makerFeeRate","takerFeeRate"]}

    raw,j,m=get(MEXC+"/api/v1/contract/ticker",{"symbol":"NVIDIA_USDT"}); save("mexc_ticker.json",raw,m)
    td=j.get("data") or {}
    mexc_px=fl(td.get("lastPrice") or td.get("fairPrice") or td.get("indexPrice"))
    report["mexc_ticker"]=td

    end=int(time.time()); start=end-1800
    raw,j,m=get(MEXC+"/api/v1/contract/kline/NVIDIA_USDT",{"interval":"Min1","start":start,"end":end}); save("mexc_kline_1m.json",raw,m)
    md=j.get("data") or {}
    report["mexc_1m_rows"]=len(md.get("time") or [])

    raw,j,m=get(BITGET+"/api/v3/market/instruments",{"category":"USDT-FUTURES","symbol":"NVDAUSDT"}); save("bitget_instrument.json",raw,m)
    if str(j.get("code"))!="00000": raise RuntimeError(f"BITGET instrument non-success {j}")
    rows=j.get("data") or []
    bsym=next((x for x in rows if x.get("symbol")=="NVDAUSDT"),None)
    if not bsym: raise RuntimeError("BITGET_NVDAUSDT_MISSING")
    report["bitget_symbol"]={k:bsym.get(k) for k in ["symbol","category","baseCoin","quoteCoin","isRwa","isReality","status"]}

    raw,j,m=get(BITGET+"/api/v2/mix/market/ticker",{"symbol":"NVDAUSDT","productType":"USDT-FUTURES"}); save("bitget_ticker.json",raw,m)
    if str(j.get("code"))!="00000": raise RuntimeError(f"BITGET ticker non-success {j}")
    btd=(j.get("data") or [{}])[0]
    bit_px=fl(btd.get("lastPr")); report["bitget_ticker"]=btd

    nowms=int(time.time()*1000)
    raw,j,m=get(BITGET+"/api/v3/market/candles",{
        "category":"USDT-FUTURES","symbol":"NVDAUSDT","interval":"1m",
        "startTime":str(nowms-30*60*1000),"endTime":str(nowms),"limit":"30"
    }); save("bitget_kline_1m.json",raw,m)
    if str(j.get("code"))!="00000": raise RuntimeError(f"BITGET candles non-success {j}")
    report["bitget_1m_rows"]=len(j.get("data") or [])

    prices={"mexc":mexc_px,"bitget":bit_px}; report["live_prices"]=prices
    vals=[x for x in prices.values() if x and x>0]
    dispersion=10000*(max(vals)/min(vals)-1) if len(vals)==2 else None
    report["live_price_dispersion_bps"]=dispersion

    checks={
      "mexc_identity":d.get("symbol")=="NVIDIA_USDT",
      "mexc_declares_bitget":"BITGET_FUTURE" in (d.get("indexOrigin") or []),
      "bitget_identity":bsym.get("symbol")=="NVDAUSDT",
      "public_1m_candles":report["mexc_1m_rows"]>=10 and report["bitget_1m_rows"]>=10,
      "same_scale_under_500bps":dispersion is not None and dispersion<500
    }
    report["checks"]=checks
    report["verdict"]="NVDA_BITGET_MEXC_SOURCE_PASS" if all(checks.values()) else "SOURCE_BLOCKED_NVDA_BITGET_MEXC"
    report["binance_runtime"]="DOCUMENTED_BUT_GITHUB_RUNNER_HTTP_451"
    report["pyth_runtime"]="EXCLUDED_REQUIRES_API_KEY_CURRENTLY"
    report["historical_outcomes_opened"]=0
    report["lead_lag_tested"]=False
    report["live_trading_authorized"]=False
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"NVDA_BITGET_MEXC_SOURCE_GATE_RECEIPT_V061.json").write_text(json.dumps(report,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps({"verdict":report["verdict"],"live_prices":prices,"dispersion_bps":dispersion,
                      "checks":checks,"outcomes_opened":0,"live_trading_authorized":False},indent=2,sort_keys=True))

if __name__=="__main__": main()
