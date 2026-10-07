#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
import requests

CBASE="https://contract.mexc.com/api/v1/contract"
SBASE="https://api.mexc.com/api/v3"
CONTRACTS=[
    "BTC_USDT","BTC_USDC","BTC_USD1",
    "ETH_USDT","ETH_USDC","ETH_USD1",
]
SPOT_NORM=["USDCUSDT","USD1USDT","USD1USDC"]
UA={"User-Agent":"CryptoLab-MultiStable-SourceGate/0.1"}
OUT=Path("artifacts/mexc_multistable_basis/source_gate_v01/report.json")


def get(url, params=None, sleep_after=0.14):
    t0=time.perf_counter()
    r=requests.get(url,params=params,headers=UA,timeout=15)
    latency=(time.perf_counter()-t0)*1000
    body=r.content
    rec={
        "status":r.status_code,
        "latency_ms":round(latency,3),
        "sha256":hashlib.sha256(body).hexdigest(),
        "bytes":len(body),
    }
    try:
        j=r.json()
    except Exception:
        j=None
    time.sleep(sleep_after)
    return r,j,rec


def success_payload(j):
    return isinstance(j,dict) and j.get("success") is True


def main():
    report={
        "family_id":"MEXC-MULTI-STABLE-BASIS-001",
        "phase":"SOURCE_ONLY",
        "economic_outcomes_opened":False,
        "basis_calculated":False,
        "pnl_calculated":False,
        "contracts":{},
        "stablecoin_normalization":{},
    }

    # Contract metadata: one documented 1/5s request only.
    r,detail,dev=get(f"{CBASE}/detail",sleep_after=5.1)
    rows=(detail or {}).get("data") if success_payload(detail) else []
    by={x.get("symbol"):x for x in rows if isinstance(x,dict) and x.get("symbol")}
    report["contract_detail_route"]={"ok":success_payload(detail),"evidence":dev}

    for sym in CONTRACTS:
        m=by.get(sym)
        meta_ok=False
        meta={}
        if m:
            try:
                cs=float(m.get("contractSize"))
                vu=float(m.get("volUnit"))
                mv=float(m.get("minVol"))
                pu=float(m.get("priceUnit"))
                meta_ok=all(x>0 for x in (cs,vu,mv,pu))
                meta={
                    "symbol":sym,
                    "settleCoin":m.get("settleCoin"),
                    "quoteCoin":m.get("quoteCoin"),
                    "state":m.get("state"),
                    "contractSize_positive":cs>0,
                    "volUnit_positive":vu>0,
                    "minVol_positive":mv>0,
                    "priceUnit_positive":pu>0,
                    "apiAllowed":m.get("apiAllowed"),
                }
            except Exception:
                meta_ok=False

        checks={}
        routes=[
            ("ticker",f"{CBASE}/ticker",{"symbol":sym}),
            ("depth",f"{CBASE}/depth/{sym}",{"limit":5}),
            ("deals",f"{CBASE}/deals/{sym}",{"limit":5}),
            ("funding",f"{CBASE}/funding_rate/{sym}",None),
            ("index",f"{CBASE}/index_price/{sym}",None),
            ("fair",f"{CBASE}/fair_price/{sym}",None),
            ("kline_1m",f"{CBASE}/kline/{sym}",{"interval":"Min1"}),
        ]
        for name,url,params in routes:
            rr,j,ev=get(url,params)
            ok=rr.status_code==200 and (
                success_payload(j) or
                (name=="depth" and isinstance(j,dict) and bool(j.get("bids")) and bool(j.get("asks")))
            )
            timestampable=False
            if ok and isinstance(j,dict):
                d=j.get("data")
                if name=="depth":
                    timestampable=("timestamp" in j) or isinstance(j.get("data"),dict)
                elif isinstance(d,dict):
                    timestampable=any(k in d for k in ("timestamp","time","nextSettleTime"))
                elif isinstance(d,list):
                    timestampable=bool(d) and isinstance(d[0],dict) and any(k in d[0] for k in ("t","timestamp","settleTime"))
            checks[name]={"ok":ok,"timestampable":timestampable,"evidence":ev}
        report["contracts"][sym]={
            "metadata_present":m is not None,
            "metadata_valid":meta_ok,
            "metadata":meta,
            "routes":checks,
        }

    for sym in SPOT_NORM:
        exr,exj,exev=get(f"{SBASE}/exchangeInfo",{"symbol":sym},sleep_after=0.1)
        symbols=(exj or {}).get("symbols") if isinstance(exj,dict) else None
        if symbols is None and isinstance(exj,dict) and exj.get("symbol"):
            symbols=[exj]
        online=bool(symbols) and any(
            str(x.get("symbol","")).upper()==sym and str(x.get("status","")).upper() in ("1","ENABLED")
            for x in symbols if isinstance(x,dict)
        )

        br,bj,bev=get(f"{SBASE}/ticker/bookTicker",{"symbol":sym},sleep_after=0.1)
        book_ok=br.status_code==200 and isinstance(bj,dict) and bj.get("symbol")==sym and bj.get("bidPrice") is not None and bj.get("askPrice") is not None

        kr,kj,kev=get(f"{SBASE}/klines",{"symbol":sym,"interval":"1m","limit":2},sleep_after=0.1)
        kline_ok=kr.status_code==200 and isinstance(kj,list) and len(kj)>0 and isinstance(kj[0],list) and len(kj[0])>=7
        timestampable=kline_ok and isinstance(kj[0][0],(int,float)) and isinstance(kj[0][6],(int,float))

        report["stablecoin_normalization"][sym]={
            "exchange_info_ok":exr.status_code==200,
            "online":online,
            "book_ticker_ok":book_ok,
            "kline_1m_ok":kline_ok,
            "timestampable":timestampable,
            "evidence":{"exchangeInfo":exev,"bookTicker":bev,"kline":kev},
        }

    contract_pass=True
    for sym,row in report["contracts"].items():
        if not row["metadata_present"] or not row["metadata_valid"]:
            contract_pass=False
        for name,x in row["routes"].items():
            if not x["ok"]:
                contract_pass=False

    norm=report["stablecoin_normalization"]
    norm_pass=all(norm[s]["online"] and norm[s]["book_ticker_ok"] and norm[s]["kline_1m_ok"] and norm[s]["timestampable"] for s in ("USDCUSDT","USD1USDT"))

    btc_pass=all(report["contracts"][s]["metadata_valid"] and all(v["ok"] for v in report["contracts"][s]["routes"].values()) for s in CONTRACTS[:3])
    eth_pass=all(report["contracts"][s]["metadata_valid"] and all(v["ok"] for v in report["contracts"][s]["routes"].values()) for s in CONTRACTS[3:])

    if contract_pass and norm_pass:
        verdict="SOURCE_PASS"
    elif btc_pass and norm_pass and not eth_pass:
        verdict="PARTIAL_SOURCE_PASS_BTC_ONLY"
    elif not norm_pass:
        verdict="SOURCE_BLOCKED_STABLECOIN_NORMALIZATION"
    else:
        verdict="SOURCE_BLOCKED_CONTRACT_DATA"

    report["verdict"]=verdict
    report["btc_triplet_pass"]=btc_pass
    report["eth_triplet_pass"]=eth_pass
    report["normalization_pass"]=norm_pass

    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True))
    print(json.dumps({
        "verdict":verdict,
        "btc_triplet_pass":btc_pass,
        "eth_triplet_pass":eth_pass,
        "normalization_pass":norm_pass,
        "contract_route_failures":{
            s:[n for n,x in row["routes"].items() if not x["ok"]]
            for s,row in report["contracts"].items()
            if any(not x["ok"] for x in row["routes"].values())
        },
        "normalization":{
            s:{k:v for k,v in row.items() if k!="evidence"}
            for s,row in report["stablecoin_normalization"].items()
        },
        "economic_outcomes_opened":False,
        "basis_calculated":False,
    },sort_keys=True))


if __name__=="__main__":
    main()
