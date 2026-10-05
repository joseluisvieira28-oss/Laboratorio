#!/usr/bin/env python3
from __future__ import annotations
import csv,io,json,time,zipfile,hashlib
from datetime import datetime
from pathlib import Path
import requests

OUT=Path("artifacts/mexc_global_assets/session_shock_v12_source")
UA="CryptoLab-SessionShock-Source/1.2"
DATES=["2026-08-17","2026-08-31","2026-09-08"]
ASSETS=[
["MSTRSTOCK_USDT","MSTRUSDT"],["INTCSTOCK_USDT","INTCUSDT"],["AAPLSTOCK_USDT","AAPLUSDT"],
["GOOGLSTOCK_USDT","GOOGLUSDT"],["AMDSTOCK_USDT","AMDUSDT"],["COINBASE_USDT","COINUSDT"],
["METASTOCK_USDT","METAUSDT"],["ROBINHOOD_USDT","HOODUSDT"],["MSFTSTOCK_USDT","MSFTUSDT"],
["AVGOSTOCK_USDT","AVGOUSDT"],["TSMSTOCK_USDT","TSMUSDT"],["AMZNSTOCK_USDT","AMZNUSDT"],
["ONDSSTOCK_USDT","ONDSUSDT"],["RKLBSTOCK_USDT","RKLBUSDT"],["BABASTOCK_USDT","BABAUSDT"],
["IRENSTOCK_USDT","IRENUSDT"],["MRVLSTOCK_USDT","MRVLUSDT"],["PLTRSTOCK_USDT","PLTRUSDT"],
["NFLXSTOCK_USDT","NFLXUSDT"],["ARMSTOCK_USDT","ARMUSDT"],["CRWDSTOCK_USDT","CRWDUSDT"],
["PDDSTOCK_USDT","PDDUSDT"],["CRWVSTOCK_USDT","CRWVUSDT"],["QCOMSTOCK_USDT","QCOMUSDT"],
["LLYSTOCK_USDT","LLYUSDT"],["CSCOSTOCK_USDT","CSCOUSDT"],["JPMSTOCK_USDT","JPMUSDT"],
["WMTSTOCK_USDT","WMTUSDT"],["IBMSTOCK_USDT","IBMUSDT"],["CATSTOCK_USDT","CATUSDT"],
["COSTSTOCK_USDT","COSTUSDT"],["SMCISTOCK_USDT","SMCIUSDT"],["VRTSTOCK_USDT","VRTUSDT"],
["ASMLSTOCK_USDT","ASMLUSDT"],["QQQSTOCK_USDT","QQQUSDT"]
]

def H(b): return hashlib.sha256(b).hexdigest()
def ts(s): return int(datetime.fromisoformat(s.replace("Z","+00:00")).timestamp())
def req(url,params=None,timeout=70):
    for i in range(4):
        try:
            r=requests.get(url,params=params,headers={"User-Agent":UA},timeout=timeout)
            return r
        except Exception:
            time.sleep(.6*(i+1))
    raise RuntimeError(url)

def probe_one(target,ext,day):
    a=ts(day+"T14:20:00Z"); b=ts(day+"T19:00:00Z")
    mr=req(f"https://api.mexc.com/api/v1/contract/kline/{target}",{"interval":"Min1","start":str(a),"end":str(b)})
    mc=0
    if mr.status_code==200:
        try:
            j=mr.json(); d=j.get("data") or {}; mc=len(d.get("time") or [])
        except: pass
    br=req(f"https://data.binance.vision/data/futures/um/daily/klines/{ext}/1m/{ext}-1m-{day}.zip",timeout=90)
    bc=0
    if br.status_code==200:
        try:
            z=zipfile.ZipFile(io.BytesIO(br.content)); names=z.namelist()
            if len(names)==1:
                for row in csv.reader(io.TextIOWrapper(z.open(names[0]),encoding="utf-8")):
                    try:t=int(row[0])//1000; float(row[4])
                    except:continue
                    if a<=t<=b: bc+=1
        except: pass
    total=0; gh=[]
    for x,y in [(a,a+139*60),(a+140*60,b)]:
        gr=req("https://api.bitget.com/api/v2/mix/market/history-candles",{
            "symbol":ext,"productType":"USDT-FUTURES","granularity":"1m",
            "startTime":str(x*1000),"endTime":str(y*1000),"limit":"200"})
        gh.append(H(gr.content)); rows=[]
        if gr.status_code==200:
            try: rows=gr.json().get("data") or []
            except: pass
        total+=len(rows)
        time.sleep(.02)
    return {
      "date":day,
      "mexc":{"http":mr.status_code,"rows":mc,"ok":mc>=260,"sha256":H(mr.content)},
      "binance":{"http":br.status_code,"rows":bc,"ok":bc>=260,"sha256":H(br.content) if br.status_code==200 else None},
      "bitget":{"rows":total,"ok":total>=250,"chunk_sha256":gh}
    }

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    results=[]
    for target,ext in ASSETS:
        probes=[probe_one(target,ext,d) for d in DATES]
        passed=all(p["mexc"]["ok"] and p["binance"]["ok"] and p["bitget"]["ok"] for p in probes)
        results.append({"target":target,"external":ext,"anchor_probes":probes,"source_pass":passed})
        print(target,"PASS" if passed else "FAIL",[(p["date"],p["mexc"]["rows"],p["binance"]["rows"],p["bitget"]["rows"]) for p in probes])
    passed=[{"target":x["target"],"external":x["external"]} for x in results if x["source_pass"]]
    rep={
      "gate_id":"MEXC_SESSION_SHOCK_CLUSTER_SOURCE_V1_2",
      "source_only":True,
      "untouched_candidate_period":"2026-08-10..2026-09-08",
      "anchor_dates":DATES,
      "anchor_dates_burned_from_outcomes":True,
      "source_pass_count":len(passed),
      "source_pass":passed,
      "results":results,
      "verdict":"UNTOUCHED_HISTORY_SOURCE_PASS" if passed else "UNTOUCHED_HISTORY_SOURCE_BLOCKED",
      "outcomes_opened":0,
      "private_endpoints_used":False,"account_reads":False,"orders":False,"live_trading":False
    }
    (OUT/"MEXC_SESSION_SHOCK_CLUSTER_SOURCE_V12.json").write_text(json.dumps(rep,indent=2,sort_keys=True))
    print(json.dumps({"verdict":rep["verdict"],"source_pass_count":len(passed),"source_pass":passed},indent=2))

if __name__=="__main__": main()
