#!/usr/bin/env python3
"""Source-only gate for MEXC WTI + official EIA WPSR schedule.

No historical return scoring. No accounts, credentials, orders, wallets or mutation.
"""
from __future__ import annotations
import hashlib,json,time,re
from datetime import datetime,timezone
from pathlib import Path
import requests

OUT=Path("artifacts/mexc_global_assets/wti_eia_source_gate_v12")
MEXC="https://api.mexc.com"
EIA_SCHEDULE="https://www.eia.gov/petroleum/supply/weekly/schedule.php"
UA="CryptoLab-WTI-EIA-SourceGate/1.2"

def now(): return datetime.now(timezone.utc).isoformat()
def sha(b): return hashlib.sha256(b).hexdigest()

def get(url,params=None):
    r=requests.get(url,params=params,headers={"User-Agent":UA},timeout=30)
    raw=r.content
    meta={"url":r.url,"status_code":r.status_code,"captured_at_utc":now(),
          "sha256":sha(raw),"bytes":len(raw),"content_type":r.headers.get("content-type")}
    if r.status_code!=200:
        raise RuntimeError(f"HTTP_{r.status_code}:{r.url}:{raw[:300]!r}")
    return raw,r,meta

def save(name,raw,meta):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/name).write_bytes(raw)
    (OUT/(name+".meta.json")).write_text(json.dumps(meta,indent=2,sort_keys=True),encoding="utf-8")

def ff(x):
    try:return float(x)
    except:return None

def main():
    rep={
      "lab":"MEXC_WTI_EIA_SOURCE_GATE_V1_2",
      "captured_at_utc":now(),
      "source_only":True,
      "historical_outcomes_opened":0,
      "historical_wti_backtest_run":False,
      "inventory_surprise_used":False,
      "consensus_used":False,
      "auth_used":False,
      "account_reads":False,
      "wallet_used":False,
      "orders":False,
      "exchange_mutation":False,
      "live_trading_authorized":False,
      "mexc_symbol":"USOIL_USDT"
    }

    raw,r,m=get(MEXC+"/api/v1/contract/detail",{"symbol":"USOIL_USDT"})
    save("mexc_usoil_detail.json",raw,m)
    j=r.json()
    if not isinstance(j,dict) or j.get("success") is not True:
        raise RuntimeError(f"MEXC_DETAIL_NON_SUCCESS:{j}")
    d=j.get("data")
    if isinstance(d,list):
        d=next((x for x in d if x.get("symbol")=="USOIL_USDT"),None)
    if not isinstance(d,dict):
        raise RuntimeError("MEXC_USOIL_DETAIL_MISSING")
    rep["mexc_detail"]={k:d.get(k) for k in [
      "symbol","displayName","indexOrigin","apiAllowed","isZeroFeeSymbol",
      "makerFeeRate","takerFeeRate","contractSize","futureType","state"
    ]}

    # Current index is source-only; no historical outcome implication.
    raw,r,m=get(MEXC+"/api/v1/contract/index_price/USOIL_USDT")
    save("mexc_usoil_index.json",raw,m)
    j=r.json()
    if not isinstance(j,dict) or j.get("success") is not True:
        raise RuntimeError(f"MEXC_INDEX_NON_SUCCESS:{j}")
    x=j.get("data") or {}
    idx=ff(x.get("indexPrice"))
    rep["mexc_index"]={"price":idx,"timestamp":x.get("timestamp")}

    raw,r,m=get(MEXC+"/api/v1/contract/ticker",{"symbol":"USOIL_USDT"})
    save("mexc_usoil_ticker.json",raw,m)
    j=r.json()
    td=j.get("data") if isinstance(j,dict) else None
    if isinstance(td,list):
        td=next((x for x in td if x.get("symbol")=="USOIL_USDT"),None)
    td=td or {}
    rep["mexc_ticker"]={k:td.get(k) for k in ["symbol","lastPrice","bid1","ask1","timestamp"]}

    now_s=int(time.time())
    raw,r,m=get(MEXC+"/api/v1/contract/kline/USOIL_USDT",
                {"interval":"Min1","start":now_s-900,"end":now_s})
    save("mexc_usoil_kline_probe.json",raw,m)
    j=r.json()
    if not isinstance(j,dict) or j.get("success") is not True:
        raise RuntimeError(f"MEXC_KLINE_NON_SUCCESS:{j}")
    kd=j.get("data") or {}
    rows=len(kd.get("time") or [])
    rep["mexc_1m_probe_rows"]=rows

    raw,r,m=get(EIA_SCHEDULE)
    save("eia_wpsr_schedule.html",raw,m)
    text=r.text
    clean=re.sub(r"\s+"," ",text).lower()

    # Intentionally broad textual proofs to survive harmless HTML formatting changes.
    std=(
      "10:30" in clean
      and "wednesday" in clean
      and "weekly petroleum status report" in clean
    )
    ex_feb=("february 19, 2026" in clean and "12:00" in clean)
    ex_may=("may 28, 2026" in clean and "12:00" in clean)
    ex_sep=("september 10, 2026" in clean and "12:00" in clean)

    display=str(rep["mexc_detail"].get("displayName") or "").upper()
    origin=rep["mexc_detail"].get("indexOrigin")
    identity=(
      rep["mexc_detail"].get("symbol")=="USOIL_USDT"
      and ("OIL" in display or "WTI" in display or "USOIL" in display)
    )

    gates={
      "mexc_exact_contract":rep["mexc_detail"].get("symbol")=="USOIL_USDT",
      "mexc_wti_identity":identity,
      "mexc_api_allowed":rep["mexc_detail"].get("apiAllowed") is True,
      "mexc_live_index":idx is not None and idx>0,
      "mexc_public_1m_kline":rows>0,
      "eia_schedule_retrievable":len(raw)>1000,
      "eia_standard_wed_1030et_proven":std,
      "eia_2026_feb_exception_proven":ex_feb,
      "eia_2026_may_exception_proven":ex_may,
      "eia_2026_sep_exception_proven":ex_sep
    }
    rep["gates"]=gates
    rep["mexc_index_origin"]=origin
    rep["verdict"]="MEXC_WTI_EIA_SOURCE_PASS" if all(gates.values()) else "SOURCE_BLOCKED_MEXC_WTI_EIA"

    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"MEXC_WTI_EIA_SOURCE_GATE_RECEIPT_V12.json").write_text(
      json.dumps(rep,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps(rep,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
