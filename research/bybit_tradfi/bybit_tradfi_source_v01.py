#!/usr/bin/env python3
from __future__ import annotations
import csv,io,json,zipfile,hashlib,time
from datetime import datetime,timezone
from pathlib import Path
import requests

HERE=Path(__file__).resolve().parent
CFG=json.loads((HERE/"BYBIT_TRADFI_TRANSFER_SOURCE_MAP_V0.1.json").read_text())
OUT=Path("artifacts/bybit_tradfi/source_v01")
DAY=CFG["source_verification_date"]
UA="CryptoLab-Bybit-TradFi-SourceGate/0.1.1"

def h(b):return hashlib.sha256(b).hexdigest()
def sec(s):return int(datetime.fromisoformat(s.replace("Z","+00:00")).timestamp())
def req(url,params=None,timeout=70,retries=4):
    last=None
    for i in range(retries):
        try:
            return requests.get(url,params=params,headers={"User-Agent":UA},timeout=timeout)
        except Exception as e:
            last=e;time.sleep(.5*(i+1))
    raise last

def bybit_instrument(symbol):
    r=req("https://api.bybit.com/v5/market/instruments-info",{
      "category":"linear","symbol":symbol,"symbolType":"stock"})
    rec={"http":r.status_code,"sha256":h(r.content),"exists":False,"status":None,
         "retCode":None,"retMsg":None}
    if r.status_code==200:
        try:
            j=r.json();rec["retCode"]=j.get("retCode");rec["retMsg"]=j.get("retMsg")
            lst=((j.get("result") or {}).get("list") or [])
            m=next((x for x in lst if x.get("symbol")==symbol),None)
            if m:
                rec["exists"]=True;rec["status"]=m.get("status")
                rec["contractType"]=m.get("contractType")
                rec["symbolType"]=m.get("symbolType")
                rec["launchTime"]=m.get("launchTime")
                rec["fundingInterval"]=m.get("fundingInterval")
                rec["settleCoin"]=m.get("settleCoin")
        except Exception:pass
    return rec

def bybit_kline(symbol,start,end):
    r=req("https://api.bybit.com/v5/market/kline",{
      "category":"linear","symbol":symbol,"interval":"1",
      "start":str(start*1000),"end":str(end*1000),"limit":"1000"})
    out={};ok=False;ret=None;msg=None
    if r.status_code==200:
        try:
            j=r.json();ret=j.get("retCode");msg=j.get("retMsg")
            lst=((j.get("result") or {}).get("list") or [])
            for row in lst:
                t=int(row[0])//1000
                if start<=t<=end:out[t+60]=float(row[4])
            ok=(ret==0 and len(out)>=260)
        except Exception:pass
    return {"http":r.status_code,"rows":len(out),"ok":ok,"retCode":ret,"retMsg":msg,"sha256":h(r.content)}

def binance(symbol,start,end):
    r=req(f"https://data.binance.vision/data/futures/um/daily/klines/{symbol}/1m/{symbol}-1m-{DAY}.zip",timeout=90)
    n=0;ok=False
    if r.status_code==200:
        try:
            z=zipfile.ZipFile(io.BytesIO(r.content)); names=z.namelist()
            if len(names)==1:
                for row in csv.reader(io.TextIOWrapper(z.open(names[0]),encoding="utf-8")):
                    try:t=int(row[0])//1000;float(row[4])
                    except:continue
                    if start<=t<=end:n+=1
                ok=n>=260
        except Exception:pass
    return {"http":r.status_code,"core_rows":n,"ok":ok,"sha256":h(r.content) if r.status_code==200 else None}

def bitget(symbol,start,end):
    total=0;ok=True;hs=[]
    for a,b in [(start,start+134*60),(start+135*60,end)]:
        r=req("https://api.bitget.com/api/v2/mix/market/history-candles",{
          "symbol":symbol,"productType":"USDT-FUTURES","granularity":"1m",
          "startTime":str(a*1000),"endTime":str(b*1000),"limit":"200"})
        hs.append(h(r.content));rows=[]
        if r.status_code==200:
            try:
                j=r.json();rows=j.get("data") or [];ok=ok and j.get("code")=="00000" and len(rows)>=120
            except Exception:ok=False
        else:ok=False
        total+=len(rows);time.sleep(.02)
    return {"rows":total,"ok":ok,"chunk_sha256":hs}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    start=sec(DAY+"T14:30:00Z");end=sec(DAY+"T19:00:00Z")
    results=[]
    for c in CFG["candidates"]:
        s=c["bybit_target"]
        ins=bybit_instrument(s)
        bk=bybit_kline(s,start,end) if ins["exists"] else {"http":None,"rows":0,"ok":False,"sha256":None}
        bn=binance(c["binance_external"],start,end)
        bg=bitget(c["bitget_external"],start,end)
        p=bool(ins["exists"] and ins["status"]=="Trading" and bk["ok"] and bn["ok"] and bg["ok"])
        rec={**c,"bybit_instrument":ins,"bybit_history":bk,"binance_history":bn,"bitget_history":bg,
             "source_pass":p,"outcomes_opened":0}
        results.append(rec)
        print(s,"PASS" if p else "FAIL","BY",bk["rows"],"BN",bn["core_rows"],"BG",bg["rows"],
              "status",ins["status"],"type",ins.get("symbolType"),"ret",ins.get("retCode"),ins.get("retMsg"))
    passed=[x for x in results if x["source_pass"]]
    rep={"gate_id":CFG["gate_id"],"technical_amendment":"V0.1.1_symbolType_stock",
         "source_only":True,"verification_date":DAY,"verification_date_burned_from_outcomes":True,
         "candidate_count":len(results),"source_pass_count":len(passed),
         "source_pass":[{"target":x["bybit_target"],"external":x["binance_external"],"root":x["root"]} for x in passed],
         "results":results,
         "verdict":"BYBIT_TRADFI_SOURCE_PASS_CANDIDATES_FOUND" if passed else "BYBIT_TRADFI_SOURCE_BLOCKED",
         "private_endpoints_used":False,"account_reads":False,"orders":False,"exchange_mutation":False,
         "live_trading_authorized":False}
    (OUT/"BYBIT_TRADFI_SOURCE_GATE_V01.json").write_text(json.dumps(rep,indent=2,sort_keys=True))
    print(json.dumps({"verdict":rep["verdict"],"source_pass_count":len(passed),
      "source_pass":[x["bybit_target"] for x in passed]},indent=2))

if __name__=="__main__":main()
