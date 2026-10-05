#!/usr/bin/env python3
from __future__ import annotations
import csv,io,json,time,zipfile,hashlib
from datetime import datetime,timezone
from pathlib import Path
import requests

HERE=Path(__file__).resolve().parent
B=json.loads((HERE/"MEXC_PREOPEN_SHOCK_SOURCE_BINDING_V1.1.json").read_text())
OUT=Path("artifacts/mexc_global_assets/intraday_large_shock_v10_source")
DAY="2026-09-30"
UA="CryptoLab-IntradayLargeShock-Source/1.0"

def H(b): return hashlib.sha256(b).hexdigest()
def ts(hm):
    h,m=map(int,hm.split(":"))
    return int(datetime(2026,9,30,h,m,tzinfo=timezone.utc).timestamp())
SESSION_START=ts("13:30"); SESSION_END=ts("20:00")
FETCH_START=ts("13:25"); FETCH_END=ts("20:05")

def req(url,params=None,timeout=70,retries=4):
    last=None
    for i in range(retries):
        try:
            r=requests.get(url,params=params,headers={"User-Agent":UA},timeout=timeout)
            if r.status_code==200:return r
            last=RuntimeError(f"HTTP_{r.status_code}:{r.url}")
        except Exception as e:last=e
        time.sleep(.5*(i+1))
    raise last

def mexc(symbol):
    out={}; raw=[]
    cur=FETCH_START
    while cur<FETCH_END:
        end=min(cur+170*60,FETCH_END)
        r=req(f"https://api.mexc.com/api/v1/contract/kline/{symbol}",
              {"interval":"Min1","start":str(cur),"end":str(end)})
        raw.append(r.content)
        j=r.json(); z=j.get("data") or {}
        if j.get("success") is not True: raise RuntimeError("MEXC_SUCCESS_FALSE")
        for t,p in zip(z.get("time") or [],z.get("close") or []):
            try: out[int(t)+60]=float(p)
            except: pass
        cur=end
    return out,H(b"".join(raw))

def binance(symbol):
    r=req(f"https://data.binance.vision/data/futures/um/daily/klines/{symbol}/1m/{symbol}-1m-{DAY}.zip",timeout=100)
    z=zipfile.ZipFile(io.BytesIO(r.content)); names=z.namelist()
    if len(names)!=1: raise RuntimeError("BINANCE_ZIP_IDENTITY")
    out={}
    for row in csv.reader(io.TextIOWrapper(z.open(names[0]),encoding="utf-8")):
        try:t=int(row[0])//1000;p=float(row[4])
        except:continue
        out[t+60]=p
    return out,H(r.content)

def bitget(symbol):
    out={}; raw=[]
    cur=FETCH_START
    while cur<FETCH_END:
        end=min(cur+90*60,FETCH_END)
        r=req("https://api.bitget.com/api/v2/mix/market/history-candles",{
            "symbol":symbol,"productType":"USDT-FUTURES","granularity":"1m",
            "startTime":str(cur*1000),"endTime":str(end*1000),"limit":"100"})
        raw.append(r.content)
        j=r.json()
        if j.get("code")!="00000": raise RuntimeError("BITGET_CODE_"+str(j.get("code")))
        for row in j.get("data") or []:
            try:out[int(row[0])//1000+60]=float(row[4])
            except:pass
        cur=end
        time.sleep(.03)
    return out,H(b"".join(raw))

def cov(d):
    xs=sorted(t for t in d if SESSION_START<=t<=SESSION_END)
    return {"rows":len(xs),"start_exact":SESSION_START in d,"end_exact":SESSION_END in d,
            "ok":len(xs)>=390 and SESSION_START in d and SESSION_END in d}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    rows=[]
    for c in B["candidates"]:
        target=c["target"]; extb=c["external_binance"]; extg=c["external_bitget"]
        rec={"target":target,"external_binance":extb,"external_bitget":extg,"outcomes_opened":0}
        try:
            m,mh=mexc(target); b,bh=binance(extb); g,gh=bitget(extg)
            rec["mexc"]={**cov(m),"sha256":mh}
            rec["binance"]={**cov(b),"sha256":bh}
            rec["bitget"]={**cov(g),"sha256":gh}
            rec["source_pass"]=rec["mexc"]["ok"] and rec["binance"]["ok"] and rec["bitget"]["ok"]
        except Exception as e:
            rec["error"]=str(e);rec["source_pass"]=False
        rows.append(rec)
        print(target,rec["source_pass"],rec.get("mexc",{}).get("rows"),
              rec.get("binance",{}).get("rows"),rec.get("bitget",{}).get("rows"))
    passed=[x for x in rows if x["source_pass"]]
    rep={"gate_id":"MEXC_GLOBALASSET_INTRADAY_LARGE_SHOCK_SOURCE_V1_0",
         "source_only":True,"verification_date":DAY,"session_closed_utc":["13:30","20:00"],
         "candidate_count":len(rows),"source_pass_count":len(passed),
         "verdict":"SOURCE_PASS" if len(passed)==len(rows)==35 else "SOURCE_BLOCKED",
         "results":rows,"outcomes_opened":0,"private_endpoints_used":False,
         "account_reads":False,"orders":False,"exchange_mutation":False,"live_trading":False}
    p=OUT/"MEXC_GLOBALASSET_INTRADAY_LARGE_SHOCK_SOURCE_V10.json"
    body=json.dumps(rep,indent=2,sort_keys=True)
    p.write_text(body)
    print("REPORT_SHA256",hashlib.sha256(body.encode()).hexdigest())
    print(json.dumps({"verdict":rep["verdict"],"source_pass_count":len(passed),
                      "candidate_count":len(rows)},sort_keys=True))

if __name__=="__main__": main()
