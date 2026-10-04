#!/usr/bin/env python3
"""MEXC Coinbase regular-session source gate V0.1. SOURCE-ONLY."""
from __future__ import annotations
import csv,io,json,zipfile,hashlib
from datetime import datetime,timezone
from pathlib import Path
import requests

OUT=Path("artifacts/mexc_global_assets/crcl_source_gate_v01")
UA="CryptoLab-MEXC-CRCL-SourceGate/0.1"
DAY="2026-09-30"

def now(): return datetime.now(timezone.utc).isoformat()
def sha(b): return hashlib.sha256(b).hexdigest()
def req(url,params=None,timeout=60):
    return requests.get(url,params=params,headers={"User-Agent":UA},timeout=timeout)
def save(name,r):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/name).write_bytes(r.content)
    (OUT/(name+".meta.json")).write_text(json.dumps({
      "url":r.url,"status_code":r.status_code,"captured_at_utc":now(),
      "sha256":sha(r.content),"bytes":len(r.content)
    },indent=2,sort_keys=True))

def main():
    rep={"lab":"MEXC_CRCL_REGSESSION_SOURCE_GATE_V0_1","source_only":True,
         "historical_outcomes_opened":0,"signal_tested":False,
         "verification_date":DAY,"venues":{}}

    r=req("https://api.mexc.com/api/v1/contract/detail",{"symbol":"CRCLSTOCK_USDT"})
    save("mexc_crcl_detail.json",r)
    if r.status_code!=200: raise RuntimeError(f"MEXC_DETAIL_HTTP_{r.status_code}")
    j=r.json()
    if j.get("success") is not True: raise RuntimeError(f"MEXC_DETAIL_NON_SUCCESS:{j}")
    d=j.get("data")
    if isinstance(d,list):
        d=next((x for x in d if x.get("symbol")=="CRCLSTOCK_USDT"),None)
    if not isinstance(d,dict): raise RuntimeError("MEXC_CRCL_DETAIL_MISSING")
    rep["mexc_detail"]={k:d.get(k) for k in [
      "symbol","indexOrigin","apiAllowed","isZeroFeeSymbol","makerFeeRate",
      "takerFeeRate","contractSize","maxLeverage","state"
    ]}

    r=req("https://api.mexc.com/api/v1/contract/index_price/CRCLSTOCK_USDT")
    save("mexc_crcl_index.json",r)
    rep["mexc_index_status"]=r.status_code
    if r.status_code==200:
        try: rep["mexc_index"]=r.json().get("data")
        except Exception: pass

    start=int(datetime.fromisoformat(DAY+"T14:30:00+00:00").timestamp())
    end=int(datetime.fromisoformat(DAY+"T19:00:00+00:00").timestamp())

    r=req("https://api.mexc.com/api/v1/contract/kline/CRCLSTOCK_USDT",
          {"interval":"Min1","start":str(start),"end":str(end)})
    save("mexc_crcl_regsession_history.json",r)
    mj=r.json() if r.status_code==200 else {}
    md=mj.get("data") or {} if isinstance(mj,dict) else {}
    mt=md.get("time") or []; mc=md.get("close") or []
    rep["venues"]["MEXC"]={
      "status":r.status_code,"success":mj.get("success") if isinstance(mj,dict) else None,
      "rows":len(mt),"schema_ok":len(mt)>=260 and len(mt)==len(mc),"outcome_scored":False
    }

    url=f"https://data.binance.vision/data/futures/um/daily/klines/CRCLUSDT/1m/CRCLUSDT-1m-{DAY}.zip"
    r=req(url,timeout=90); save("binance_coin_2026-09-30.zip",r)
    rows=0; core=0; name=None; schema=False
    if r.status_code==200:
      try:
        z=zipfile.ZipFile(io.BytesIO(r.content)); names=z.namelist()
        if len(names)==1:
          name=names[0]
          for row in csv.reader(io.TextIOWrapper(z.open(name),encoding="utf-8")):
            try:
              raw=int(row[0])//1000; float(row[4]); rows+=1
              if start<=raw<=end: core+=1
            except Exception: continue
          schema=core>=260
      except Exception: pass
    rep["venues"]["BINANCE"]={
      "status":r.status_code,"rows":rows,"core_rows":core,"schema_ok":schema,
      "archive_sha256":sha(r.content) if r.status_code==200 else None,
      "csv_file":name,"outcome_scored":False
    }

    total=0; hashes=[]; ok=True
    for i,(a,b) in enumerate(((start,start+134*60),(start+135*60,end))):
      r=req("https://api.bitget.com/api/v2/mix/market/history-candles",{
        "symbol":"CRCLUSDT","productType":"USDT-FUTURES","granularity":"1m",
        "startTime":str(a*1000),"endTime":str(b*1000),"limit":"200"})
      save(f"bitget_coin_history_{i}.json",r)
      hashes.append(sha(r.content))
      bj=r.json() if r.status_code==200 else {}
      bd=bj.get("data") or [] if isinstance(bj,dict) else []
      total+=len(bd)
      ok=ok and r.status_code==200 and bj.get("code")=="00000" and len(bd)>=120
    rep["venues"]["BITGET"]={"rows":total,"schema_ok":ok,"chunk_sha256":hashes,"outcome_scored":False}

    r=req("https://api.bitget.com/api/v2/mix/market/ticker",{
      "symbol":"CRCLUSDT","productType":"USDT-FUTURES"})
    save("bitget_coin_ticker.json",r)
    bj=r.json() if r.status_code==200 else {}
    rep["venues"]["BITGET"]["live_ticker_ok"]=r.status_code==200 and bj.get("code")=="00000" and bool(bj.get("data"))

    r=req("https://hermes.pyth.network/v2/price_feeds",{"query":"CRCL"})
    save("pyth_coin_anonymous_probe.json",r)
    feeds=None
    if r.status_code==200:
      try: feeds=r.json()
      except Exception: feeds=None
    rep["venues"]["PYTH"]={
      "status":r.status_code,"anonymous_accessible":r.status_code==200,
      "candidates":feeds if isinstance(feeds,list) else None,"auth_used":False
    }

    r=req("https://us.market-api.kaiko.io/v2/data/trades.v1/exchanges/binance/spot/btc-usdt/trades",
          {"start_time":"2026-09-30T00:00:00.000Z","end_time":"2026-09-30T00:01:00.000Z","page_size":"1"})
    save("kaiko_anonymous_probe.json",r)
    rep["venues"]["KAIKO"]={"status":r.status_code,"anonymous_accessible":r.status_code==200,"auth_used":False}

    origins=[str(x).upper() for x in (d.get("indexOrigin") or [])]
    rep["mexc_index_origin_raw"]=origins
    aliases={"BINANCE_FUTURE":"BINANCE","BITGET_FUTURE":"BITGET","BINANCETICKER":"BINANCE","BYBIT_FUTURE":"BYBIT"}
    rep["mexc_index_origin_normalized"]=sorted(set(aliases.get(x,x) for x in origins))

    gates={
      "mexc_contract_exists":d.get("symbol")=="CRCLSTOCK_USDT",
      "mexc_regsession_1m_transport":rep["venues"]["MEXC"]["schema_ok"],
      "binance_regsession_1m_transport":rep["venues"]["BINANCE"]["schema_ok"],
      "bitget_regsession_1m_transport":rep["venues"]["BITGET"]["schema_ok"],
      "bitget_live_identity":rep["venues"]["BITGET"]["live_ticker_ok"]
    }
    rep["gates"]=gates
    rep["core_public_source_pass"]=all(gates.values())
    rep["verdict"]="CRCL_REGSESSION_PUBLIC_CORE_SOURCE_PASS" if all(gates.values()) else "SOURCE_BLOCKED_CRCL_REGSESSION"
    rep["classification"]="CORE_PUBLIC_SOURCES_PASS__FULL_INDEX_RECONSTRUCTION_UNPROVEN" if all(gates.values()) else "SOURCE_BLOCKED"
    rep["private_endpoints_used"]=False; rep["account_reads"]=False; rep["orders"]=False
    rep["wallets_used"]=False; rep["exchange_mutation"]=False; rep["live_trading_authorized"]=False

    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"MEXC_CRCL_SOURCE_GATE_RECEIPT_V01.json").write_text(json.dumps(rep,indent=2,sort_keys=True))
    print(json.dumps(rep,indent=2,sort_keys=True))

if __name__=="__main__": main()
