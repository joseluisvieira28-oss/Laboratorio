#!/usr/bin/env python3
from __future__ import annotations
import json,requests,hashlib,zipfile,io,csv
from pathlib import Path
from datetime import datetime,timezone
OUT=Path("artifacts/mexc_global_assets/apple_source_gate_v01"); OUT.mkdir(parents=True,exist_ok=True)
UA="CryptoLab-MEXC-APPLE-SourceGate/0.1"; DAY="2026-09-30"
def req(u,p=None,t=60): return requests.get(u,params=p,headers={"User-Agent":UA},timeout=t)
def sha(b): return hashlib.sha256(b).hexdigest()
def save(n,r):
    (OUT/n).write_bytes(r.content)
    (OUT/(n+".meta.json")).write_text(json.dumps({"url":r.url,"status":r.status_code,"sha256":sha(r.content),"captured_at_utc":datetime.now(timezone.utc).isoformat()},indent=2))
def main():
    rep={"lab":"MEXC_APPLE_SOURCE_GATE_V0_1","source_only":True,"historical_outcomes_opened":0,"signal_tested":False}
    r=req("https://api.mexc.com/api/v1/contract/detail"); save("mexc_contract_detail_all.json",r)
    j=r.json(); data=j.get("data") or []
    candidates=[x for x in data if any(k in str(x.get("symbol","")).upper() for k in ("APPLE","AAPL"))]
    rep["mexc_candidates"]=[{k:x.get(k) for k in ["symbol","indexOrigin","apiAllowed","isZeroFeeSymbol","makerFeeRate","takerFeeRate","contractSize","maxLeverage","state"]} for x in candidates]
    if len(candidates)!=1:
        rep["verdict"]="SOURCE_BLOCKED_APPLE_SYMBOL_AMBIGUOUS"; (OUT/"APPLE_SOURCE_GATE_RECEIPT_V01.json").write_text(json.dumps(rep,indent=2)); print(json.dumps(rep,indent=2)); return
    d=candidates[0]; sym=d["symbol"]; rep["target_symbol"]=sym
    start=int(datetime.fromisoformat(DAY+"T14:30:00+00:00").timestamp()); end=int(datetime.fromisoformat(DAY+"T19:00:00+00:00").timestamp())
    r=req(f"https://api.mexc.com/api/v1/contract/kline/{sym}",{"interval":"Min1","start":str(start),"end":str(end)}); save("mexc_apple_history.json",r)
    mj=r.json() if r.status_code==200 else {}; md=mj.get("data") or {}; rep["mexc_rows"]=len(md.get("time") or [])
    # Probe both common external tickers.
    ext={}
    for esym in ("AAPLUSDT","APPLEUSDT"):
        rr=req(f"https://data.binance.vision/data/futures/um/daily/klines/{esym}/1m/{esym}-1m-{DAY}.zip",t=90); save(f"binance_{esym}.zip",rr)
        core=0
        if rr.status_code==200:
            try:
                z=zipfile.ZipFile(io.BytesIO(rr.content)); names=z.namelist()
                if len(names)==1:
                    for row in csv.reader(io.TextIOWrapper(z.open(names[0]),encoding="utf-8")):
                        try: ts=int(row[0])//1000
                        except: continue
                        if start<=ts<=end: core+=1
            except: pass
        br=req("https://api.bitget.com/api/v2/mix/market/ticker",{"symbol":esym,"productType":"USDT-FUTURES"}); save(f"bitget_{esym}_ticker.json",br)
        bj=br.json() if br.status_code==200 else {}
        ext[esym]={"binance_core_rows":core,"bitget_live_ok":br.status_code==200 and bj.get("code")=="00000" and bool(bj.get("data"))}
    rep["external_symbol_probes"]=ext
    chosen=next((k for k,v in ext.items() if v["binance_core_rows"]>=260 and v["bitget_live_ok"]),None)
    rep["external_symbol"]=chosen
    if chosen:
        chunks=[]; total=0; ok=True
        for i,(a,b) in enumerate(((start,start+134*60),(start+135*60,end))):
            rr=req("https://api.bitget.com/api/v2/mix/market/history-candles",{"symbol":chosen,"productType":"USDT-FUTURES","granularity":"1m","startTime":str(a*1000),"endTime":str(b*1000),"limit":"200"}); save(f"bitget_history_{i}.json",rr)
            bj=rr.json() if rr.status_code==200 else {}; rows=bj.get("data") or []; total+=len(rows); ok=ok and rr.status_code==200 and bj.get("code")=="00000" and len(rows)>=120
        rep["bitget_history_rows"]=total; rep["bitget_history_ok"]=ok
    pr=req("https://hermes.pyth.network/v2/price_feeds",{"query":"AAPL"}); save("pyth_aapl_probe.json",pr)
    rep["pyth_status"]=pr.status_code
    if pr.status_code==200:
        try: rep["pyth_candidates"]=pr.json()
        except: pass
    gates={"mexc_symbol_unique":len(candidates)==1,"mexc_history":rep["mexc_rows"]>=260,"external_symbol_resolved":chosen is not None,"bitget_history":bool(rep.get("bitget_history_ok"))}
    rep["gates"]=gates; rep["verdict"]="APPLE_REGSESSION_PUBLIC_CORE_SOURCE_PASS" if all(gates.values()) else "SOURCE_BLOCKED_APPLE_REGSESSION"
    rep.update({"private_endpoints_used":False,"account_reads":False,"orders":False,"exchange_mutation":False,"live_trading_authorized":False})
    (OUT/"APPLE_SOURCE_GATE_RECEIPT_V01.json").write_text(json.dumps(rep,indent=2,sort_keys=True)); print(json.dumps(rep,indent=2,sort_keys=True))
if __name__=="__main__": main()
