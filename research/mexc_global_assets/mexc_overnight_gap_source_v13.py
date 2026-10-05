#!/usr/bin/env python3
from __future__ import annotations
import csv,io,json,time,zipfile,hashlib
from datetime import datetime,timezone
from pathlib import Path
import requests
HERE=Path(__file__).resolve().parent
B=json.loads((HERE/"MEXC_CASHOPEN_EXTMOM_SOURCE_BINDING_V1.2.json").read_text())
OUT=Path("artifacts/mexc_global_assets/overnight_gap_v13_source")
CUR="2026-09-30"; PREV="2026-09-29"; UA="CryptoLab-OvernightGap-Source/1.3"
def H(b):return hashlib.sha256(b).hexdigest()
def ts(s):return int(datetime.fromisoformat(s.replace("Z","+00:00")).timestamp())
def req(url,params=None,timeout=60):
    for i in range(4):
        try:return requests.get(url,params=params,headers={"User-Agent":UA},timeout=timeout)
        except Exception:time.sleep(.5*(i+1))
    raise RuntimeError(url)
def binance_rows(sym,day,a,b):
    r=req(f"https://data.binance.vision/data/futures/um/daily/klines/{sym}/1m/{sym}-1m-{day}.zip",timeout=90)
    n=0
    if r.status_code==200:
        try:
            z=zipfile.ZipFile(io.BytesIO(r.content)); names=z.namelist()
            if len(names)==1:
                for row in csv.reader(io.TextIOWrapper(z.open(names[0]),encoding="utf-8")):
                    try:t=int(row[0])//1000;float(row[4])
                    except:continue
                    if a<=t<=b:n+=1
        except:pass
    return r,n
def bitget_rows(sym,a,b):
    r=req("https://api.bitget.com/api/v2/mix/market/history-candles",{"symbol":sym,"productType":"USDT-FUTURES","granularity":"1m","startTime":str(a*1000),"endTime":str(b*1000),"limit":"100"})
    n=0
    if r.status_code==200:
        try:n=len(r.json().get("data") or [])
        except:pass
    return r,n
def mexc_rows(sym,a,b):
    r=req(f"https://api.mexc.com/api/v1/contract/kline/{sym}",{"interval":"Min1","start":str(a),"end":str(b)})
    n=0
    if r.status_code==200:
        try:n=len((r.json().get("data") or {}).get("time") or [])
        except:pass
    return r,n
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    p0=ts(PREV+"T19:50:00Z");p1=ts(PREV+"T20:05:00Z")
    c0=ts(CUR+"T13:20:00Z");c1=ts(CUR+"T14:05:00Z")
    rows=[]
    for c in B["candidates"]:
        target=c["target"];ext=c["external_binance"]
        mr1,m1=mexc_rows(target,p0,p1);mr2,m2=mexc_rows(target,c0,c1)
        br1,b1=binance_rows(ext,PREV,p0,p1);br2,b2=binance_rows(ext,CUR,c0,c1)
        gr1,g1=bitget_rows(ext,p0,p1);gr2,g2=bitget_rows(ext,c0,c1)
        ok=min(m1,m2,b1,b2,g1,g2)>=10
        rows.append({"target":target,"external":ext,"source_pass":ok,
          "prev":{"mexc":m1,"binance":b1,"bitget":g1},
          "current":{"mexc":m2,"binance":b2,"bitget":g2},
          "sha":{"mexc_prev":H(mr1.content),"mexc_cur":H(mr2.content),"bin_prev":H(br1.content),"bin_cur":H(br2.content),"bit_prev":H(gr1.content),"bit_cur":H(gr2.content)}})
        print(target,ok,m1,m2,b1,b2,g1,g2);time.sleep(.02)
    passed=[{"target":x["target"],"external":x["external"]} for x in rows if x["source_pass"]]
    rep={"gate_id":"MEXC_OVERNIGHT_GAP_SOURCE_V1_3","source_only":True,"burned_current_date":CUR,"burned_previous_date":PREV,
         "source_pass_count":len(passed),"source_pass":passed,"results":rows,
         "verdict":"OVERNIGHT_GAP_SOURCE_PASS" if len(passed)==len(rows) else "OVERNIGHT_GAP_SOURCE_PARTIAL_OR_BLOCKED",
         "outcomes_opened":0,"private_endpoints_used":False,"account_reads":False,"orders":False,"live_trading":False}
    (OUT/"MEXC_OVERNIGHT_GAP_SOURCE_V13.json").write_text(json.dumps(rep,indent=2,sort_keys=True))
    print(json.dumps({"verdict":rep["verdict"],"source_pass_count":len(passed)},indent=2))
if __name__=="__main__":main()
