#!/usr/bin/env python3
from __future__ import annotations
import csv,io,json,zipfile,hashlib
from pathlib import Path
from datetime import datetime,timezone
import requests

OUT=Path("artifacts/mexc_global_assets/highbeta_source_census_v01"); OUT.mkdir(parents=True,exist_ok=True)
UA="CryptoLab-MEXC-HighBeta-SourceCensus/0.1"
DAY="2026-09-30"
PRIORITY=["MSTR","COIN","PLTR","META","AMZN","MSFT"]

def req(u,p=None,t=60): return requests.get(u,params=p,headers={"User-Agent":UA},timeout=t)
def sha(b): return hashlib.sha256(b).hexdigest()
def save(n,r):
    (OUT/n).write_bytes(r.content)
    (OUT/(n+".meta.json")).write_text(json.dumps({
      "url":r.url,"status":r.status_code,"sha256":sha(r.content),
      "captured_at_utc":datetime.now(timezone.utc).isoformat()
    },indent=2))
def main():
    start=int(datetime.fromisoformat(DAY+"T14:30:00+00:00").timestamp())
    end=int(datetime.fromisoformat(DAY+"T19:00:00+00:00").timestamp())
    rep={"lab":"MEXC_HIGHBETA_EQUITY_SOURCE_CENSUS_V0_1","source_only":True,
         "priority":PRIORITY,"verification_date":DAY,"historical_outcomes_opened":0,
         "signal_tested":False,"candidates":{}}

    r=req("https://api.mexc.com/api/v1/contract/detail"); save("mexc_contract_detail_all.json",r)
    if r.status_code!=200: raise RuntimeError("MEXC_DETAIL_HTTP")
    j=r.json(); data=j.get("data") or []
    for ticker in PRIORITY:
        matches=[x for x in data if ticker in str(x.get("symbol","")).upper()]
        item={"mexc_match_count":len(matches),
              "mexc_symbols":[x.get("symbol") for x in matches],
              "source_pass":False}
        if len(matches)!=1:
            rep["candidates"][ticker]=item; continue
        d=matches[0]; msym=d.get("symbol"); item["mexc_symbol"]=msym
        item["mexc_detail"]={k:d.get(k) for k in ["symbol","indexOrigin","apiAllowed","isZeroFeeSymbol","makerFeeRate","takerFeeRate","contractSize","maxLeverage","state"]}

        mr=req(f"https://api.mexc.com/api/v1/contract/kline/{msym}",{"interval":"Min1","start":str(start),"end":str(end)})
        save(f"mexc_{ticker}_history.json",mr)
        mj=mr.json() if mr.status_code==200 else {}; md=mj.get("data") or {}
        item["mexc_rows"]=len(md.get("time") or [])
        item["mexc_history_ok"]=mr.status_code==200 and mj.get("success") is True and item["mexc_rows"]>=260

        esym=ticker+"USDT"; item["external_symbol"]=esym
        br=req(f"https://data.binance.vision/data/futures/um/daily/klines/{esym}/1m/{esym}-1m-{DAY}.zip",t=90)
        save(f"binance_{ticker}.zip",br)
        core=0
        if br.status_code==200:
            try:
                z=zipfile.ZipFile(io.BytesIO(br.content)); names=z.namelist()
                if len(names)==1:
                    for row in csv.reader(io.TextIOWrapper(z.open(names[0]),encoding="utf-8")):
                        try: ts=int(row[0])//1000
                        except: continue
                        if start<=ts<=end: core+=1
            except Exception: pass
        item["binance_core_rows"]=core; item["binance_history_ok"]=core>=260

        tr=req("https://api.bitget.com/api/v2/mix/market/ticker",{"symbol":esym,"productType":"USDT-FUTURES"})
        save(f"bitget_{ticker}_ticker.json",tr)
        tj=tr.json() if tr.status_code==200 else {}
        item["bitget_live_ok"]=tr.status_code==200 and tj.get("code")=="00000" and bool(tj.get("data"))

        total=0; histok=True
        for idx,(a,b) in enumerate(((start,start+134*60),(start+135*60,end))):
            hr=req("https://api.bitget.com/api/v2/mix/market/history-candles",{
              "symbol":esym,"productType":"USDT-FUTURES","granularity":"1m",
              "startTime":str(a*1000),"endTime":str(b*1000),"limit":"200"})
            save(f"bitget_{ticker}_history_{idx}.json",hr)
            hj=hr.json() if hr.status_code==200 else {}; rows=hj.get("data") or []
            total+=len(rows); histok=histok and hr.status_code==200 and hj.get("code")=="00000" and len(rows)>=120
        item["bitget_history_rows"]=total; item["bitget_history_ok"]=histok

        origins=[str(x).upper() for x in (d.get("indexOrigin") or [])]
        item["index_origins"]=origins
        item["source_pass"]=bool(item["mexc_history_ok"] and item["binance_history_ok"] and item["bitget_live_ok"] and item["bitget_history_ok"])
        rep["candidates"][ticker]=item

    chosen=next((t for t in PRIORITY if rep["candidates"].get(t,{}).get("source_pass")),None)
    rep["selected_ticker"]=chosen
    if chosen:
        rep["selected"]=rep["candidates"][chosen]
        rep["verdict"]="HIGHBETA_EQUITY_SOURCE_PASS__"+chosen
    else:
        rep["verdict"]="SOURCE_BLOCKED_HIGHBETA_EQUITY_CENSUS"
    rep.update({"private_endpoints_used":False,"account_reads":False,"orders":False,
                "exchange_mutation":False,"live_trading_authorized":False})
    (OUT/"MEXC_HIGHBETA_EQUITY_SOURCE_CENSUS_RECEIPT_V01.json").write_text(json.dumps(rep,indent=2,sort_keys=True))
    print(json.dumps({"verdict":rep["verdict"],"selected_ticker":chosen,
                      "summary":{t:{k:rep["candidates"][t].get(k) for k in ["mexc_symbol","external_symbol","mexc_rows","binance_core_rows","bitget_history_rows","source_pass"]} for t in PRIORITY}},indent=2))
if __name__=="__main__": main()
