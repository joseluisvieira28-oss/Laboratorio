#!/usr/bin/env python3
"""MEXC NVIDIA cash-close source transport V0.3. SOURCE-ONLY."""
from __future__ import annotations
import csv, io, json, zipfile, hashlib
from datetime import datetime, timezone
from pathlib import Path
import requests

OUT=Path("artifacts/mexc_global_assets/nvidia_cashclose_source_v03")
UA="CryptoLab-MEXC-NVIDIA-CashClose-Source/0.3"

def sha(b): return hashlib.sha256(b).hexdigest()
def now(): return datetime.now(timezone.utc).isoformat()
def req(url,params=None,timeout=60):
    r=requests.get(url,params=params,headers={"User-Agent":UA},timeout=timeout)
    return r
def save(name,r):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/name).write_bytes(r.content)
    (OUT/(name+".meta.json")).write_text(json.dumps({
      "url":r.url,"status_code":r.status_code,"captured_at_utc":now(),
      "sha256":sha(r.content),"bytes":len(r.content)
    },indent=2,sort_keys=True))

def main():
    day="2026-09-30"
    start=int(datetime.fromisoformat(day+"T19:50:00+00:00").timestamp())
    end=int(datetime.fromisoformat(day+"T20:35:00+00:00").timestamp())
    rep={"lab":"MEXC_NVIDIA_CASHCLOSE_SOURCE_V0_3","source_only":True,
         "verification_date":day,"historical_outcomes_opened":0,"signal_tested":False,
         "window_utc":"19:50-20:35","venues":{}}

    r=req("https://api.mexc.com/api/v1/contract/kline/NVIDIA_USDT",
          {"interval":"Min1","start":str(start),"end":str(end)})
    save("mexc_close_probe.json",r)
    mj=r.json() if r.status_code==200 else {}
    md=mj.get("data") or {} if isinstance(mj,dict) else {}
    rep["venues"]["MEXC"]={
      "status":r.status_code,"success":mj.get("success") if isinstance(mj,dict) else None,
      "rows":len(md.get("time") or []),
      "schema_ok":len(md.get("time") or [])>=40
    }

    r=req("https://api.bitget.com/api/v2/mix/market/history-candles",{
      "symbol":"NVDAUSDT","productType":"USDT-FUTURES","granularity":"1m",
      "startTime":str(start*1000),"endTime":str(end*1000),"limit":"200"
    })
    save("bitget_close_probe.json",r)
    bj=r.json() if r.status_code==200 else {}
    bd=bj.get("data") or [] if isinstance(bj,dict) else []
    rep["venues"]["BITGET"]={
      "status":r.status_code,"code":bj.get("code") if isinstance(bj,dict) else None,
      "rows":len(bd),"schema_ok":len(bd)>=40
    }

    url=f"https://data.binance.vision/data/futures/um/daily/klines/NVDAUSDT/1m/NVDAUSDT-1m-{day}.zip"
    r=req(url,timeout=90)
    save("binance_close_probe.zip",r)
    rows=0; schema=False; name=None
    if r.status_code==200:
        try:
            z=zipfile.ZipFile(io.BytesIO(r.content)); names=z.namelist()
            if len(names)==1:
                name=names[0]
                rr=list(csv.reader(io.TextIOWrapper(z.open(name),encoding="utf-8")))
                rows=len(rr); schema=rows>100
        except Exception:
            pass
    rep["venues"]["BINANCE"]={"status":r.status_code,"rows":rows,"schema_ok":schema,
                              "csv_file":name,"archive_sha256":sha(r.content) if r.status_code==200 else None}

    gates={k.lower()+"_transport":bool(v["schema_ok"]) for k,v in rep["venues"].items()}
    rep["gates"]=gates
    rep["verdict"]="NVIDIA_CASHCLOSE_SOURCE_PASS" if all(gates.values()) else "SOURCE_BLOCKED_NVIDIA_CASHCLOSE"
    rep["historical_outcomes_opened"]=0
    rep["private_endpoints_used"]=False
    rep["account_reads"]=False
    rep["orders"]=False
    rep["exchange_mutation"]=False
    rep["live_trading_authorized"]=False

    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"MEXC_NVIDIA_CASHCLOSE_SOURCE_RECEIPT_V03.json").write_text(json.dumps(rep,indent=2,sort_keys=True))
    print(json.dumps(rep,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
