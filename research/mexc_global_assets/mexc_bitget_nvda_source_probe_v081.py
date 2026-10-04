#!/usr/bin/env python3
"""V0.8.1 public/no-auth source proof: MEXC NVIDIA_USDT <-> Bitget NVDA futures.

SOURCE ONLY. No historical return scoring, account reads, credentials, orders or mutation.
"""
from __future__ import annotations
import hashlib,json,time
from datetime import datetime,timezone
from pathlib import Path
import requests

OUT=Path("artifacts/mexc_global_assets/nvda_bitget_source_gate_v081")
MEXC="https://api.mexc.com"
BITGET="https://api.bitget.com"
UA="CryptoLab-NVDA-Bitget-SourceGate/0.8.1"

def now(): return datetime.now(timezone.utc).isoformat()
def sha(b): return hashlib.sha256(b).hexdigest()

def get(url,params=None):
    r=requests.get(url,params=params,headers={"User-Agent":UA},timeout=30)
    raw=r.content
    meta={"url":r.url,"status_code":r.status_code,"captured_at_utc":now(),"sha256":sha(raw),"bytes":len(raw)}
    if r.status_code!=200:
        raise RuntimeError(f"HTTP_{r.status_code}:{r.url}:{raw[:300]!r}")
    try: j=r.json()
    except Exception as e: raise RuntimeError(f"NON_JSON:{r.url}:{e}")
    return raw,j,meta

def save(name,raw,meta):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/name).write_bytes(raw)
    (OUT/(name+".meta.json")).write_text(json.dumps(meta,indent=2,sort_keys=True),encoding="utf-8")

def ffloat(x):
    try: return float(x)
    except Exception: return None

def main():
    report={
      "lab":"MEXC_BITGET_NVDA_SOURCE_GATE_V0_8_1",
      "captured_at_utc":now(),
      "source_only":True,
      "historical_outcomes_opened":0,
      "lead_lag_tested":False,
      "auth_used":False,
      "account_reads":False,
      "wallet_used":False,
      "orders":False,
      "exchange_mutation":False,
      "mexc_symbol":"NVIDIA_USDT"
    }

    raw,j,m=get(MEXC+"/api/v1/contract/detail",{"symbol":"NVIDIA_USDT"})
    save("mexc_nvidia_detail.json",raw,m)
    if not isinstance(j,dict) or j.get("success") is not True:
        raise RuntimeError("MEXC_DETAIL_NON_SUCCESS")
    d=j.get("data")
    if isinstance(d,list):
        d=next((x for x in d if x.get("symbol")=="NVIDIA_USDT"),None)
    if not isinstance(d,dict):
        raise RuntimeError("MEXC_NVIDIA_DETAIL_MISSING")
    report["mexc_detail"]={k:d.get(k) for k in [
      "symbol","displayName","indexOrigin","apiAllowed","isZeroFeeSymbol",
      "makerFeeRate","takerFeeRate","contractSize","futureType"
    ]}

    raw,j,m=get(MEXC+"/api/v1/contract/index_price/NVIDIA_USDT")
    save("mexc_nvidia_index.json",raw,m)
    if j.get("success") is not True: raise RuntimeError("MEXC_INDEX_NON_SUCCESS")
    mi=j.get("data") or {}
    mexc_index=ffloat(mi.get("indexPrice"))
    report["mexc_index"]={"price":mexc_index,"timestamp":mi.get("timestamp")}

    raw,j,m=get(MEXC+"/api/v1/contract/ticker",{"symbol":"NVIDIA_USDT"})
    save("mexc_nvidia_ticker.json",raw,m)
    td=j.get("data") if isinstance(j,dict) else None
    if isinstance(td,list):
        td=next((x for x in td if x.get("symbol")=="NVIDIA_USDT"),None)
    td=td or {}
    report["mexc_ticker"]={k:td.get(k) for k in ["symbol","lastPrice","bid1","ask1","timestamp"]}

    now_s=int(time.time())
    raw,j,m=get(MEXC+"/api/v1/contract/kline/NVIDIA_USDT",
                {"interval":"Min1","start":now_s-900,"end":now_s})
    save("mexc_nvidia_kline_probe.json",raw,m)
    md=j.get("data") or {}
    mrows=len(md.get("time") or [])
    report["mexc_kline_rows"]=mrows

    # Bitget contract discovery. Query exact first, but also preserve the all-contract
    # response so identity can fail closed rather than guessing an alias.
    raw,bx,m=get(BITGET+"/api/v2/mix/market/contracts",
                 {"productType":"USDT-FUTURES","symbol":"NVDAUSDT"})
    save("bitget_nvda_contract_exact.json",raw,m)
    exact_data=bx.get("data") if isinstance(bx,dict) and bx.get("code")=="00000" else []
    exact=[x for x in (exact_data or []) if str(x.get("symbol","")).upper()=="NVDAUSDT"]

    raw,ba,m=get(BITGET+"/api/v2/mix/market/contracts",
                 {"productType":"USDT-FUTURES"})
    save("bitget_all_usdt_contracts.json",raw,m)
    if not isinstance(ba,dict) or ba.get("code")!="00000":
        raise RuntimeError(f"BITGET_CONTRACT_LIST_FAIL:{ba}")
    allc=ba.get("data") or []
    aliases=[
      x for x in allc
      if ("NVDA" in str(x.get("symbol","")).upper()
          or "NVIDIA" in str(x.get("symbol","")).upper()
          or str(x.get("baseCoin","")).upper() in {"NVDA","NVIDIA"})
    ]
    report["bitget_alias_candidates"]=[{
      k:x.get(k) for k in ["symbol","baseCoin","quoteCoin","symbolType","symbolStatus",
                           "launchTime","makerFeeRate","takerFeeRate","isRwa","minLever","maxLever"]
    } for x in aliases]

    if len(exact)==1:
        bc=exact[0]
        identity_mode="EXACT_NVDAUSDT"
    elif len(aliases)==1 and str(aliases[0].get("baseCoin","")).upper() in {"NVDA","NVIDIA"}:
        bc=aliases[0]
        identity_mode="UNIQUE_NVDA_BASECOIN_ALIAS"
    else:
        bc=None
        identity_mode="AMBIGUOUS_OR_MISSING"

    report["bitget_identity_mode"]=identity_mode
    if bc:
        symbol=str(bc["symbol"])
        report["bitget_symbol"]=symbol
        report["bitget_contract"]={k:bc.get(k) for k in [
          "symbol","baseCoin","quoteCoin","symbolType","symbolStatus","launchTime",
          "makerFeeRate","takerFeeRate","isRwa","minLever","maxLever","minTradeUSDT"
        ]}

        raw,t,m=get(BITGET+"/api/v2/mix/market/ticker",
                    {"productType":"USDT-FUTURES","symbol":symbol})
        save("bitget_nvda_ticker.json",raw,m)
        if not isinstance(t,dict) or t.get("code")!="00000" or not t.get("data"):
            raise RuntimeError(f"BITGET_TICKER_FAIL:{t}")
        tr=t["data"][0]
        bid=ffloat(tr.get("bidPr")); ask=ffloat(tr.get("askPr")); last=ffloat(tr.get("lastPr"))
        mid=(bid+ask)/2 if bid and ask else last
        report["bitget_ticker"]={"bid":bid,"ask":ask,"last":last,"mid":mid,"ts":tr.get("ts")}

        raw,k,m=get(BITGET+"/api/v2/mix/market/candles",
                    {"productType":"USDT-FUTURES","symbol":symbol,"granularity":"1m","limit":"5"})
        save("bitget_nvda_kline_probe.json",raw,m)
        if not isinstance(k,dict) or k.get("code")!="00000":
            raise RuntimeError(f"BITGET_KLINE_FAIL:{k}")
        brows=len(k.get("data") or [])
        report["bitget_kline_rows"]=brows
    else:
        symbol=None; bid=ask=last=mid=None; brows=0
        report["bitget_symbol"]=None
        report["bitget_kline_rows"]=0

    rel=10000*(mexc_index/mid-1) if mexc_index and mid and mid>0 else None
    report["mexc_index_vs_bitget_mid_bps"]=rel

    origin=report["mexc_detail"].get("indexOrigin")
    report["mexc_index_origin_contains_bitget"]=(
      isinstance(origin,list) and any("BITGET" in str(x).upper() for x in origin)
    )

    gates={
      "mexc_exact_contract":report["mexc_detail"].get("symbol")=="NVIDIA_USDT",
      "bitget_unique_identity":bc is not None,
      "bitget_nvda_identity":bc is not None and (
          "NVDA" in str(bc.get("symbol","")).upper()
          or str(bc.get("baseCoin","")).upper() in {"NVDA","NVIDIA"}
      ),
      "mexc_live_index":mexc_index is not None and mexc_index>0,
      "bitget_live_book_or_last":mid is not None and mid>0,
      "scale_within_500bps":rel is not None and abs(rel)<500,
      "mexc_1m_kline_public":mrows>0,
      "bitget_1m_kline_public":brows>0
    }
    report["gates"]=gates
    passed=all(gates.values())
    report["verdict"]="MEXC_BITGET_NVDA_SOURCE_PASS" if passed else "SOURCE_BLOCKED_MEXC_BITGET_NVDA"
    report["live_trading_authorized"]=False

    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"MEXC_BITGET_NVDA_SOURCE_GATE_RECEIPT_V081.json").write_text(
      json.dumps(report,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps(report,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
