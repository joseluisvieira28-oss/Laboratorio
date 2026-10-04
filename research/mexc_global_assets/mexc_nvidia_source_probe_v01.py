#!/usr/bin/env python3
"""MEXC NVIDIA equity-dislocation source gate V0.1. SOURCE-ONLY."""
from __future__ import annotations
import csv, io, json, zipfile, hashlib
from datetime import datetime, timezone
from pathlib import Path
import requests

OUT=Path("artifacts/mexc_global_assets/nvidia_source_gate_v01")
UA="CryptoLab-MEXC-NVIDIA-SourceGate/0.1"

def now(): return datetime.now(timezone.utc).isoformat()
def sha(b): return hashlib.sha256(b).hexdigest()

def req(url,params=None,timeout=45):
    r=requests.get(url,params=params,headers={"User-Agent":UA},timeout=timeout)
    return r

def save(name,r):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/name).write_bytes(r.content)
    (OUT/(name+".meta.json")).write_text(json.dumps({
        "url":r.url,"status_code":r.status_code,"captured_at_utc":now(),
        "sha256":sha(r.content),"bytes":len(r.content)
    },indent=2,sort_keys=True),encoding="utf-8")

def j200(name,url,params=None):
    r=req(url,params)
    save(name,r)
    if r.status_code!=200:
        raise RuntimeError(f"{name}:HTTP_{r.status_code}:{r.content[:300]!r}")
    return r.json(),r

def main():
    report={
      "lab":"MEXC_NVIDIA_EQUITY_DISLOCATION_SOURCE_GATE_V0_1",
      "captured_at_utc":now(),
      "source_only":True,
      "historical_outcomes_opened":0,
      "signal_tested":False,
      "private_endpoints_used":False,
      "account_reads":False,
      "orders":False,
      "exchange_mutation":False,
      "wallets_used":False,
      "venues":{}
    }

    # MEXC contract authority + live index.
    j,r=j200("mexc_nvidia_detail.json","https://api.mexc.com/api/v1/contract/detail",
             {"symbol":"NVIDIA_USDT"})
    if j.get("success") is not True: raise RuntimeError(f"MEXC_DETAIL_NON_SUCCESS:{j}")
    d=j.get("data")
    if isinstance(d,list):
        d=next((x for x in d if x.get("symbol")=="NVIDIA_USDT"),None)
    if not isinstance(d,dict): raise RuntimeError("MEXC_NVIDIA_DETAIL_MISSING")
    report["mexc_detail"]={k:d.get(k) for k in [
      "symbol","indexOrigin","apiAllowed","isZeroFeeSymbol","makerFeeRate",
      "takerFeeRate","contractSize","maxLeverage","state"
    ]}

    j,r=j200("mexc_nvidia_index.json","https://api.mexc.com/api/v1/contract/index_price/NVIDIA_USDT")
    if j.get("success") is not True: raise RuntimeError(f"MEXC_INDEX_NON_SUCCESS:{j}")
    report["mexc_index"]=j.get("data")

    # Historical transport verification day only: 2026-09-30.
    START_MS=1790726400000
    END_MS=1790812740000
    START_S=START_MS//1000
    END_S=END_MS//1000

    j,r=j200("mexc_nvidia_history_probe.json","https://api.mexc.com/api/v1/contract/kline/NVIDIA_USDT",{
       "interval":"Min1","start":str(START_S),"end":str(END_S)
    })
    if j.get("success") is not True: raise RuntimeError(f"MEXC_HISTORY_NON_SUCCESS:{j}")
    md=j.get("data") or {}
    mts=md.get("time") or []; mcl=md.get("close") or []
    report["venues"]["MEXC"]={
       "history_1m_row_count":len(mts),
       "schema_ok":len(mts)>100 and len(mts)==len(mcl),
       "verification_date":"2026-09-30",
       "outcome_scored":False
    }

    # Binance official data archive.
    burl="https://data.binance.vision/data/futures/um/daily/klines/NVDAUSDT/1m/NVDAUSDT-1m-2026-09-30.zip"
    br=req(burl,timeout=60); save("binance_nvda_2026-09-30_1m.zip",br)
    binfo={"status_code":br.status_code,"verification_date":"2026-09-30","outcome_scored":False}
    if br.status_code==200:
        z=zipfile.ZipFile(io.BytesIO(br.content)); names=z.namelist()
        rows=list(csv.reader(io.TextIOWrapper(z.open(names[0]),encoding="utf-8"))) if len(names)==1 else []
        binfo.update({"archive_sha256":sha(br.content),"csv_file":names[0] if len(names)==1 else None,
                      "row_count":len(rows),"schema_ok":len(rows)>100})
    report["venues"]["BINANCE"]=binfo

    # Bitget live + 1m historical transport.
    j,r=j200("bitget_nvda_ticker.json","https://api.bitget.com/api/v2/mix/market/ticker",{
      "symbol":"NVDAUSDT","productType":"USDT-FUTURES"
    })
    live_ok=j.get("code")=="00000" and bool(j.get("data"))
    jh,rh=j200("bitget_nvda_history_probe.json","https://api.bitget.com/api/v2/mix/market/candles",{
      "symbol":"NVDAUSDT","productType":"USDT-FUTURES","granularity":"1m",
      "startTime":str(START_MS),"endTime":str(START_MS+59*60*1000),"limit":"1000"
    })
    hist=(jh.get("data") or []) if jh.get("code")=="00000" else []
    report["venues"]["BITGET"]={
      "live_ticker_ok":live_ok,
      "history_1m_row_count":len(hist),
      "history_1m_ok":len(hist)>=30,
      "verification_date":"2026-09-30",
      "outcome_scored":False
    }

    # Pyth anonymous metadata probe; since 2026-08-26 Hermes may require an API key.
    pr=req("https://hermes.pyth.network/v2/price_feeds",{"query":"NVDA"})
    save("pyth_nvda_anonymous_probe.json",pr)
    pyth_feeds=None
    if pr.status_code==200:
        try: pyth_feeds=pr.json()
        except Exception: pyth_feeds=None
    report["venues"]["PYTH"]={
      "anonymous_status_code":pr.status_code,
      "anonymous_accessible":pr.status_code==200,
      "nvda_feed_candidates":pyth_feeds if isinstance(pyth_feeds,list) else None,
      "auth_used":False
    }

    # Kaiko anonymous probe. This is deliberately unauthenticated.
    kr=req("https://us.market-api.kaiko.io/v2/data/trades.v1/exchanges/binance/spot/btc-usdt/trades",
           {"start_time":"2026-09-30T00:00:00.000Z","end_time":"2026-09-30T00:01:00.000Z","page_size":"1"})
    save("kaiko_anonymous_probe.json",kr)
    report["venues"]["KAIKO"]={
      "anonymous_status_code":kr.status_code,
      "anonymous_accessible":kr.status_code==200,
      "auth_used":False
    }

    origins=[str(x).upper() for x in (d.get("indexOrigin") or [])]
    report["mexc_index_origin_raw"]=origins

    # Normalize only obvious venue/source suffixes, without adding sources.
    def norm(x):
        for suf in ("_FUTURE","_FUTURES","_TICKER"):
            if x.endswith(suf): return x[:-len(suf)]
        return x
    report["mexc_index_origin_normalized"]=sorted(set(norm(x) for x in origins))

    gates={
      "mexc_contract_exists":d.get("symbol")=="NVIDIA_USDT",
      "mexc_historical_1m_accessible":report["venues"]["MEXC"]["schema_ok"],
      "binance_historical_1m_accessible":bool(report["venues"]["BINANCE"].get("schema_ok")),
      "bitget_historical_1m_accessible":report["venues"]["BITGET"]["history_1m_ok"],
      "bitget_live_accessible":report["venues"]["BITGET"]["live_ticker_ok"]
    }
    report["gates"]=gates

    free_core=all(gates.values())
    report["free_public_core_source_pass"]=free_core
    report["full_declared_index_reconstruction_public_free"]=(
       free_core and
       (("PYTH" not in origins) or report["venues"]["PYTH"]["anonymous_accessible"]) and
       (("KAIKO" not in origins) or report["venues"]["KAIKO"]["anonymous_accessible"])
    )

    report["verdict"]=(
      "NVIDIA_FREE_PUBLIC_CORE_SOURCE_PASS"
      if free_core else "SOURCE_BLOCKED_NVIDIA_FREE_PUBLIC_CORE"
    )
    if free_core and not report["full_declared_index_reconstruction_public_free"]:
        report["classification"]="CORE_PUBLIC_SOURCES_PASS__FULL_INDEX_RECONSTRUCTION_NOT_PROVEN_PUBLIC_FREE"
    elif free_core:
        report["classification"]="FULL_DECLARED_SOURCE_STACK_PUBLIC_FREE_PASS"
    else:
        report["classification"]="SOURCE_BLOCKED"

    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"MEXC_NVIDIA_SOURCE_GATE_RECEIPT_V01.json").write_text(
       json.dumps(report,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps(report,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
