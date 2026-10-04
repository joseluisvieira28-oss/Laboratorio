#!/usr/bin/env python3
"""Source-only feasibility scan for MEXC stock-futures cross-asset transfer family V0.1."""
from __future__ import annotations
import csv, io, json, zipfile, hashlib, time
from datetime import datetime, timezone
from pathlib import Path
import requests

OUT=Path("artifacts/mexc_global_assets/stock_transfer_operational_v01_source")
DAY="2026-09-30"
UA="CryptoLab-StockTransfer-SourceGate/0.1"
CANDIDATES=[
 "INTC","HOOD","META","GE","BABA","RDDT","SNOW","COP","CVNA","MCD","CSCO","LLY",
 "ONDS","AMD","TSM","JPM","CVXSTOCK","ACN","QCOM","CRWD","BAC","MELI","MRVL"
]

def sha(b): return hashlib.sha256(b).hexdigest()
def req(url,params=None,timeout=50,retries=3):
    last=None
    for i in range(retries):
        try:
            r=requests.get(url,params=params,headers={"User-Agent":UA},timeout=timeout)
            return r
        except Exception as e:
            last=e; time.sleep(.5*(i+1))
    raise last

def utc(s): return int(datetime.fromisoformat(s.replace("Z","+00:00")).timestamp())

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    start=utc(DAY+"T14:30:00Z"); end=utc(DAY+"T19:00:00Z")
    report={
      "gate_id":"MEXC_STOCK_TRANSFER_OPERATIONAL_SOURCE_GATE_V0_1",
      "source_only":True,
      "verification_date":DAY,
      "verification_date_burned_from_outcomes":True,
      "candidate_universe":CANDIDATES,
      "outcomes_opened":0,
      "candidates":[]
    }
    for sym in CANDIDATES:
        rec={"root":sym,"target":sym+"_USDT","external":sym+"USDT","outcome_scored":False}
        # MEXC contract detail
        r=req("https://api.mexc.com/api/v1/contract/detail",{"symbol":sym+"_USDT"})
        rec["mexc_detail_http"]=r.status_code
        d=None
        if r.status_code==200:
            try:
                j=r.json(); d=j.get("data")
                if isinstance(d,list):
                    d=next((x for x in d if x.get("symbol")==sym+"_USDT"),None)
            except Exception: d=None
        if isinstance(d,dict):
            rec["mexc_detail"]={k:d.get(k) for k in [
              "symbol","indexOrigin","apiAllowed","isZeroFeeSymbol","makerFeeRate",
              "takerFeeRate","contractSize","maxLeverage","state"
            ]}
        # MEXC history
        mr=req(f"https://api.mexc.com/api/v1/contract/kline/{sym}_USDT",
               {"interval":"Min1","start":str(start),"end":str(end)})
        mrows=0; mok=False
        if mr.status_code==200:
            try:
                mj=mr.json(); md=mj.get("data") or {}
                ts=md.get("time") or []; cl=md.get("close") or []
                mrows=len(ts); mok=mj.get("success") is True and mrows>=260 and len(ts)==len(cl)
            except Exception: pass
        rec["mexc_history"]={"http":mr.status_code,"rows":mrows,"schema_ok":mok,"sha256":sha(mr.content)}
        # Binance official Vision archive
        br=req(f"https://data.binance.vision/data/futures/um/daily/klines/{sym}USDT/1m/{sym}USDT-1m-{DAY}.zip",timeout=80)
        brows=0; bcore=0; bok=False
        if br.status_code==200:
            try:
                z=zipfile.ZipFile(io.BytesIO(br.content))
                names=z.namelist()
                if len(names)==1:
                    for row in csv.reader(io.TextIOWrapper(z.open(names[0]),encoding="utf-8")):
                        try:
                            t=int(row[0])//1000; float(row[4]); brows+=1
                            if start<=t<=end: bcore+=1
                        except Exception: continue
                    bok=bcore>=260
            except Exception: pass
        rec["binance_history"]={"http":br.status_code,"rows":brows,"core_rows":bcore,"schema_ok":bok,
                                "sha256":sha(br.content) if br.status_code==200 else None}
        # Bitget
        gout=[]; gh=[]; gok=True
        chunks=[(start,start+134*60),(start+135*60,end)]
        for a,b in chunks:
            gr=req("https://api.bitget.com/api/v2/mix/market/history-candles",{
              "symbol":sym+"USDT","productType":"USDT-FUTURES","granularity":"1m",
              "startTime":str(a*1000),"endTime":str(b*1000),"limit":"200"})
            gh.append(sha(gr.content))
            rows=[]
            if gr.status_code==200:
                try:
                    gj=gr.json(); rows=gj.get("data") or []
                    gok=gok and gj.get("code")=="00000" and len(rows)>=120
                except Exception: gok=False
            else: gok=False
            gout.extend(rows); time.sleep(.02)
        rec["bitget_history"]={"rows":len(gout),"schema_ok":gok,"chunk_sha256":gh}
        rec["source_pass"]=bool(isinstance(d,dict) and mok and bok and gok)
        report["candidates"].append(rec)
        print(sym, "PASS" if rec["source_pass"] else "FAIL", "M",mrows,"B",bcore,"G",len(gout))
        time.sleep(.03)
    passed=[x["root"] for x in report["candidates"] if x["source_pass"]]
    report["source_pass_roots"]=passed
    report["source_pass_count"]=len(passed)
    report["verdict"]="STOCK_TRANSFER_SOURCE_GATE_PASS" if passed else "STOCK_TRANSFER_SOURCE_BLOCKED"
    report["private_endpoints_used"]=False
    report["account_reads"]=False
    report["orders"]=False
    report["exchange_mutation"]=False
    report["live_trading_authorized"]=False
    (OUT/"MEXC_STOCK_TRANSFER_SOURCE_GATE_V01.json").write_text(json.dumps(report,indent=2,sort_keys=True))
    print(json.dumps({"verdict":report["verdict"],"source_pass_count":len(passed),"source_pass_roots":passed},indent=2))

if __name__=="__main__": main()
