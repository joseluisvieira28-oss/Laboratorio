#!/usr/bin/env python3
"""Source-only discovery of MEXC contracts sharing the NVDA/TSLA index architecture."""
from __future__ import annotations
import csv,io,json,zipfile,hashlib,time
from datetime import datetime
from pathlib import Path
import requests

OUT=Path("artifacts/mexc_global_assets/globalasset_source_discovery_v02")
DAY="2026-09-30"
UA="CryptoLab-GlobalAsset-SourceDiscovery/0.2"
REQ_ORIGINS={"BINANCE_FUTURE","BITGET_FUTURE","BINANCETICKER","PYTH","KAIKO"}

def sha(b): return hashlib.sha256(b).hexdigest()
def req(url,params=None,timeout=60):
    return requests.get(url,params=params,headers={"User-Agent":UA},timeout=timeout)
def ts(s): return int(datetime.fromisoformat(s.replace("Z","+00:00")).timestamp())

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    r=req("https://api.mexc.com/api/v1/contract/detail")
    if r.status_code!=200: raise RuntimeError(f"MEXC_DETAIL_HTTP_{r.status_code}")
    j=r.json()
    data=j.get("data") or []
    if not isinstance(data,list): raise RuntimeError("MEXC_DETAIL_NOT_LIST")
    candidates=[]
    for d in data:
        origins=set(str(x).upper() for x in (d.get("indexOrigin") or []))
        if REQ_ORIGINS.issubset(origins):
            candidates.append({
              "symbol":d.get("symbol"),"indexOrigin":d.get("indexOrigin"),
              "apiAllowed":d.get("apiAllowed"),"isZeroFeeSymbol":d.get("isZeroFeeSymbol"),
              "makerFeeRate":d.get("makerFeeRate"),"takerFeeRate":d.get("takerFeeRate"),
              "contractSize":d.get("contractSize"),"maxLeverage":d.get("maxLeverage"),"state":d.get("state")
            })
    start=ts(DAY+"T14:30:00Z"); end=ts(DAY+"T19:00:00Z")
    out=[]
    for c in candidates:
        symbol=c["symbol"]
        root=symbol[:-5] if symbol and symbol.endswith("_USDT") else symbol
        rec=dict(c)
        rec["root"]=root
        # MEXC history
        mr=req(f"https://api.mexc.com/api/v1/contract/kline/{symbol}",{
          "interval":"Min1","start":str(start),"end":str(end)})
        mrows=0; mok=False
        if mr.status_code==200:
            try:
                mj=mr.json(); md=mj.get("data") or {}
                mt=md.get("time") or []; mc=md.get("close") or []
                mrows=len(mt); mok=mj.get("success") is True and mrows>=260 and len(mt)==len(mc)
            except Exception: pass
        rec["mexc_history"]={"http":mr.status_code,"rows":mrows,"schema_ok":mok,"sha256":sha(mr.content)}
        # Default external alias rootUSDT
        ext=(root or "").replace("_","")+"USDT"
        rec["external_alias_default"]=ext
        # Binance daily archive
        br=req(f"https://data.binance.vision/data/futures/um/daily/klines/{ext}/1m/{ext}-1m-{DAY}.zip",timeout=90)
        bcore=0; bok=False
        if br.status_code==200:
            try:
                z=zipfile.ZipFile(io.BytesIO(br.content)); names=z.namelist()
                if len(names)==1:
                    for row in csv.reader(io.TextIOWrapper(z.open(names[0]),encoding="utf-8")):
                        try:
                            t=int(row[0])//1000; float(row[4])
                            if start<=t<=end:bcore+=1
                        except Exception: continue
                    bok=bcore>=260
            except Exception: pass
        rec["binance_history"]={"http":br.status_code,"core_rows":bcore,"schema_ok":bok,
                                "sha256":sha(br.content) if br.status_code==200 else None}
        # Bitget
        total=0; gok=True; hs=[]
        for a,b in [(start,start+134*60),(start+135*60,end)]:
            gr=req("https://api.bitget.com/api/v2/mix/market/history-candles",{
              "symbol":ext,"productType":"USDT-FUTURES","granularity":"1m",
              "startTime":str(a*1000),"endTime":str(b*1000),"limit":"200"})
            hs.append(sha(gr.content)); rows=[]
            if gr.status_code==200:
                try:
                    gj=gr.json(); rows=gj.get("data") or []
                    gok=gok and gj.get("code")=="00000" and len(rows)>=120
                except Exception:gok=False
            else:gok=False
            total+=len(rows); time.sleep(.02)
        rec["bitget_history"]={"rows":total,"schema_ok":gok,"chunk_sha256":hs}
        rec["triple_source_pass"]=bool(mok and bok and gok)
        out.append(rec)
        print(symbol, rec["triple_source_pass"], mrows,bcore,total)
        time.sleep(.03)
    rep={
      "gate_id":"MEXC_GLOBALASSET_SOURCE_DISCOVERY_V0_2",
      "source_only":True,
      "outcomes_opened":0,
      "verification_date":DAY,
      "verification_date_burned_from_outcomes":True,
      "required_index_origins":sorted(REQ_ORIGINS),
      "contract_count_matching_architecture":len(candidates),
      "candidates":out,
      "triple_source_pass_symbols":[x["symbol"] for x in out if x["triple_source_pass"]],
      "triple_source_pass_count":sum(x["triple_source_pass"] for x in out),
      "private_endpoints_used":False,"account_reads":False,"orders":False,
      "exchange_mutation":False,"live_trading_authorized":False
    }
    rep["verdict"]="GLOBALASSET_SOURCE_CANDIDATES_FOUND" if rep["triple_source_pass_count"] else "GLOBALASSET_SOURCE_BLOCKED"
    (OUT/"MEXC_GLOBALASSET_SOURCE_DISCOVERY_V02.json").write_text(json.dumps(rep,indent=2,sort_keys=True))
    print(json.dumps({
      "verdict":rep["verdict"],
      "matching_architecture":rep["contract_count_matching_architecture"],
      "triple_source_pass_count":rep["triple_source_pass_count"],
      "triple_source_pass_symbols":rep["triple_source_pass_symbols"]
    },indent=2))

if __name__=="__main__":main()
