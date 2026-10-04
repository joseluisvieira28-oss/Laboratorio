#!/usr/bin/env python3
"""MEXC NVIDIA regular-session lead-lag source gate V0.4. SOURCE-ONLY."""
from __future__ import annotations
import csv, io, json, zipfile, hashlib
from datetime import datetime, timezone
from pathlib import Path
import requests

OUT=Path("artifacts/mexc_global_assets/nvidia_regsession_source_v04")
UA="CryptoLab-MEXC-NVIDIA-RegSession-Source/0.4"

def sha(b): return hashlib.sha256(b).hexdigest()
def now(): return datetime.now(timezone.utc).isoformat()
def req(url,params=None,timeout=60):
    return requests.get(url,params=params,headers={"User-Agent":UA},timeout=timeout)
def save(name,r):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/name).write_bytes(r.content)
    (OUT/(name+".meta.json")).write_text(json.dumps({
      "url":r.url,"status_code":r.status_code,"captured_at_utc":now(),
      "sha256":sha(r.content),"bytes":len(r.content)
    },indent=2,sort_keys=True))

def main():
    day="2026-09-30"
    start=int(datetime.fromisoformat(day+"T14:30:00+00:00").timestamp())
    mid=int(datetime.fromisoformat(day+"T16:45:00+00:00").timestamp())
    end=int(datetime.fromisoformat(day+"T19:00:00+00:00").timestamp())

    rep={"lab":"MEXC_NVIDIA_REGSESSION_SOURCE_V0_4","source_only":True,
         "verification_date":day,"window_utc":"14:30-19:00",
         "historical_outcomes_opened":0,"signal_tested":False,"venues":{}}

    # MEXC full 270m transport.
    r=req("https://api.mexc.com/api/v1/contract/kline/NVIDIA_USDT",
          {"interval":"Min1","start":str(start),"end":str(end)})
    save("mexc_regsession_probe.json",r)
    mj=r.json() if r.status_code==200 else {}
    md=mj.get("data") or {} if isinstance(mj,dict) else {}
    mt=md.get("time") or []; mc=md.get("close") or []
    rep["venues"]["MEXC"]={"status":r.status_code,
      "success":mj.get("success") if isinstance(mj,dict) else None,
      "rows":len(mt),"schema_ok":len(mt)>=260 and len(mt)==len(mc)}

    # Bitget in two chunks to avoid limit ambiguity.
    bit_rows=0; bit_hashes=[]; bit_ok=True
    for idx,(a,b) in enumerate(((start,mid-60),(mid,end))):
        r=req("https://api.bitget.com/api/v2/mix/market/history-candles",{
          "symbol":"NVDAUSDT","productType":"USDT-FUTURES","granularity":"1m",
          "startTime":str(a*1000),"endTime":str(b*1000),"limit":"200"
        })
        save(f"bitget_regsession_probe_{idx}.json",r)
        bj=r.json() if r.status_code==200 else {}
        bd=bj.get("data") or [] if isinstance(bj,dict) else []
        bit_rows+=len(bd); bit_hashes.append(sha(r.content))
        bit_ok=bit_ok and r.status_code==200 and bj.get("code")=="00000" and len(bd)>=120
    rep["venues"]["BITGET"]={"rows":bit_rows,"schema_ok":bit_ok,"chunk_sha256":bit_hashes}

    # Binance official daily archive.
    url=f"https://data.binance.vision/data/futures/um/daily/klines/NVDAUSDT/1m/NVDAUSDT-1m-{day}.zip"
    r=req(url,timeout=90); save("binance_regsession_probe.zip",r)
    rows=0; core_rows=0; schema=False; name=None
    if r.status_code==200:
        try:
            z=zipfile.ZipFile(io.BytesIO(r.content)); names=z.namelist()
            if len(names)==1:
                name=names[0]
                for row in csv.reader(io.TextIOWrapper(z.open(name),encoding="utf-8")):
                    try:
                        raw=int(row[0])//1000; float(row[4]); rows+=1
                        if start<=raw<=end: core_rows+=1
                    except Exception:
                        continue
                schema=core_rows>=260
        except Exception:
            pass
    rep["venues"]["BINANCE"]={"status":r.status_code,"rows":rows,"core_rows":core_rows,
                              "schema_ok":schema,"archive_sha256":sha(r.content) if r.status_code==200 else None,
                              "csv_file":name}

    gates={k.lower()+"_transport":bool(v["schema_ok"]) for k,v in rep["venues"].items()}
    rep["gates"]=gates
    rep["verdict"]="NVIDIA_REGSESSION_SOURCE_PASS" if all(gates.values()) else "SOURCE_BLOCKED_NVIDIA_REGSESSION"
    rep["historical_outcomes_opened"]=0
    rep["private_endpoints_used"]=False
    rep["account_reads"]=False
    rep["orders"]=False
    rep["exchange_mutation"]=False
    rep["live_trading_authorized"]=False

    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"MEXC_NVIDIA_REGSESSION_SOURCE_RECEIPT_V04.json").write_text(json.dumps(rep,indent=2,sort_keys=True))
    print(json.dumps(rep,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
