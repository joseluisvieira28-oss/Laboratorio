#!/usr/bin/env python3
from __future__ import annotations
import csv,io,json,zipfile,hashlib,time
from datetime import datetime
from pathlib import Path
import requests

HERE=Path(__file__).resolve().parent
MAP=json.loads((HERE/"MEXC_GLOBALASSET_ALIAS_MAP_V0.4.json").read_text())
OUT=Path("artifacts/mexc_global_assets/globalasset_alias_source_v04")
DAY="2026-09-30"; UA="CryptoLab-GlobalAsset-AliasSource/0.4"

def h(b): return hashlib.sha256(b).hexdigest()
def ts(s): return int(datetime.fromisoformat(s.replace("Z","+00:00")).timestamp())
def req(url,params=None,timeout=70):
    return requests.get(url,params=params,headers={"User-Agent":UA},timeout=timeout)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    start=ts(DAY+"T14:30:00Z"); end=ts(DAY+"T19:00:00Z")
    rows=[]
    for target,external in MAP["alias_map"].items():
        rec={"target":target,"external":external,"outcomes_opened":0}
        mr=req(f"https://api.mexc.com/api/v1/contract/kline/{target}",{"interval":"Min1","start":str(start),"end":str(end)})
        mcount=0
        if mr.status_code==200:
            try:
                j=mr.json(); d=j.get("data") or {}; mcount=len(d.get("time") or [])
            except: pass
        rec["mexc"]={"http":mr.status_code,"rows":mcount,"ok":mcount>=260,"sha256":h(mr.content)}
        br=req(f"https://data.binance.vision/data/futures/um/daily/klines/{external}/1m/{external}-1m-{DAY}.zip",timeout=90)
        bcore=0
        if br.status_code==200:
            try:
                z=zipfile.ZipFile(io.BytesIO(br.content)); names=z.namelist()
                if len(names)==1:
                    for row in csv.reader(io.TextIOWrapper(z.open(names[0]),encoding="utf-8")):
                        try:
                            t=int(row[0])//1000; float(row[4])
                            if start<=t<=end:bcore+=1
                        except: pass
            except: pass
        rec["binance"]={"http":br.status_code,"core_rows":bcore,"ok":bcore>=260,
                        "sha256":h(br.content) if br.status_code==200 else None}
        total=0; gok=True; hs=[]
        for a,b in [(start,start+134*60),(start+135*60,end)]:
            gr=req("https://api.bitget.com/api/v2/mix/market/history-candles",{
              "symbol":external,"productType":"USDT-FUTURES","granularity":"1m",
              "startTime":str(a*1000),"endTime":str(b*1000),"limit":"200"})
            hs.append(h(gr.content)); rr=[]
            if gr.status_code==200:
                try:
                    gj=gr.json();rr=gj.get("data") or []
                    gok=gok and gj.get("code")=="00000" and len(rr)>=120
                except:gok=False
            else:gok=False
            total+=len(rr)
            time.sleep(.02)
        rec["bitget"]={"rows":total,"ok":gok,"chunk_sha256":hs}
        rec["source_pass"]=rec["mexc"]["ok"] and rec["binance"]["ok"] and rec["bitget"]["ok"]
        rows.append(rec)
        print(target,external,"PASS" if rec["source_pass"] else "FAIL",mcount,bcore,total)
    passed=[{"target":x["target"],"external":x["external"]} for x in rows if x["source_pass"]]
    rep={"gate_id":"MEXC_GLOBALASSET_ALIAS_SOURCE_V0_4","source_only":True,"verification_date":DAY,
         "verification_date_burned_from_outcomes":True,"results":rows,"source_pass":passed,
         "source_pass_count":len(passed),
         "verdict":"ALIAS_SOURCE_PASS_CANDIDATES_FOUND" if passed else "ALIAS_SOURCE_BLOCKED",
         "private_endpoints_used":False,"account_reads":False,"orders":False,"exchange_mutation":False,
         "live_trading_authorized":False}
    (OUT/"MEXC_GLOBALASSET_ALIAS_SOURCE_V04.json").write_text(json.dumps(rep,indent=2,sort_keys=True))
    print(json.dumps({"verdict":rep["verdict"],"source_pass_count":len(passed),"source_pass":passed},indent=2))

if __name__=="__main__":main()
