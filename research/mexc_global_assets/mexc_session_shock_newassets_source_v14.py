#!/usr/bin/env python3
from __future__ import annotations
import csv,io,json,zipfile,hashlib,time
from datetime import datetime
from pathlib import Path
import requests
HERE=Path(__file__).resolve().parent
MAP=json.loads((HERE/"MEXC_SESSION_SHOCK_NEWASSET_ALIAS_MAP_V1.4.json").read_text())
OUT=Path("artifacts/mexc_global_assets/session_shock_newassets_v14_source")
DAY="2026-09-30"; UA="CryptoLab-SessionShock-NewAssets-Source/1.4"
def H(b): return hashlib.sha256(b).hexdigest()
def ts(s): return int(datetime.fromisoformat(s.replace("Z","+00:00")).timestamp())
def req(url,params=None,timeout=70):
    for i in range(4):
        try:return requests.get(url,params=params,headers={"User-Agent":UA},timeout=timeout)
        except Exception:time.sleep(.5*(i+1))
    raise RuntimeError(url)
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    a=ts(DAY+"T14:20:00Z"); b=ts(DAY+"T19:00:00Z")
    rows=[]
    for target,ext in MAP["alias_map"].items():
        mr=req(f"https://api.mexc.com/api/v1/contract/kline/{target}",{"interval":"Min1","start":str(a),"end":str(b)})
        mc=0
        if mr.status_code==200:
            try:mc=len((mr.json().get("data") or {}).get("time") or [])
            except:pass
        br=req(f"https://data.binance.vision/data/futures/um/daily/klines/{ext}/1m/{ext}-1m-{DAY}.zip",timeout=90)
        bc=0
        if br.status_code==200:
            try:
                z=zipfile.ZipFile(io.BytesIO(br.content));names=z.namelist()
                if len(names)==1:
                    for row in csv.reader(io.TextIOWrapper(z.open(names[0]),encoding="utf-8")):
                        try:t=int(row[0])//1000;float(row[4])
                        except:continue
                        if a<=t<=b:bc+=1
            except:pass
        total=0; hs=[]
        for x,y in [(a,a+139*60),(a+140*60,b)]:
            gr=req("https://api.bitget.com/api/v2/mix/market/history-candles",{
              "symbol":ext,"productType":"USDT-FUTURES","granularity":"1m",
              "startTime":str(x*1000),"endTime":str(y*1000),"limit":"200"})
            hs.append(H(gr.content)); rr=[]
            if gr.status_code==200:
                try:rr=gr.json().get("data") or []
                except:pass
            total+=len(rr);time.sleep(.02)
        rec={"target":target,"external":ext,
             "mexc":{"http":mr.status_code,"rows":mc,"ok":mc>=260,"sha256":H(mr.content)},
             "binance":{"http":br.status_code,"rows":bc,"ok":bc>=260,"sha256":H(br.content) if br.status_code==200 else None},
             "bitget":{"rows":total,"ok":total>=250,"chunk_sha256":hs}}
        rec["source_pass"]=rec["mexc"]["ok"] and rec["binance"]["ok"] and rec["bitget"]["ok"]
        rows.append(rec);print(target,ext,"PASS" if rec["source_pass"] else "FAIL",mc,bc,total)
    passed=[{"target":x["target"],"external":x["external"]} for x in rows if x["source_pass"]]
    rep={"gate_id":"MEXC_SESSION_SHOCK_NEWASSETS_SOURCE_V1_4","source_only":True,"verification_date":DAY,
         "source_pass":passed,"source_pass_count":len(passed),"results":rows,
         "verdict":"NEWASSET_SOURCE_CANDIDATES_FOUND" if passed else "NEWASSET_SOURCE_BLOCKED",
         "outcomes_opened":0,"private_endpoints_used":False,"account_reads":False,"orders":False,"live_trading":False}
    (OUT/"MEXC_SESSION_SHOCK_NEWASSETS_SOURCE_V14.json").write_text(json.dumps(rep,indent=2,sort_keys=True))
    print(json.dumps({"verdict":rep["verdict"],"source_pass_count":len(passed),"source_pass":passed},indent=2))
if __name__=="__main__":main()
