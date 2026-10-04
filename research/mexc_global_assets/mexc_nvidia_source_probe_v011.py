#!/usr/bin/env python3
"""NVIDIA source coverage amendment V0.1.1. SOURCE-ONLY, no returns."""
from __future__ import annotations
import csv, io, json, zipfile, hashlib
from datetime import datetime, timezone
from pathlib import Path
import requests

OUT=Path("artifacts/mexc_global_assets/nvidia_source_gate_v011")
UA="CryptoLab-MEXC-NVIDIA-SourceGate/0.1.1"
DATES=["2026-04-01","2026-09-29"]
PYTH_US_NVDA_ID="b1073854ed24cbc755dc527418f52b7d271f6cc967bbf8d8129112b18860a593"

def now(): return datetime.now(timezone.utc).isoformat()
def sha(b): return hashlib.sha256(b).hexdigest()
def epoch(day,hh=13,mm=20):
    return int(datetime.fromisoformat(day+"T%02d:%02d:00+00:00"%(hh,mm)).timestamp())

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
    rep={"lab":"MEXC_NVIDIA_SOURCE_COVERAGE_V0_1_1","source_only":True,
         "captured_at_utc":now(),"historical_outcomes_opened":0,
         "signal_tested":False,"dates":{},"pyth":{}}

    for day in DATES:
        start=epoch(day,13,20); end=epoch(day,13,45)
        d={"outcome_scored":False}

        # MEXC 1m transport around US cash open.
        r=req("https://api.mexc.com/api/v1/contract/kline/NVIDIA_USDT",
              {"interval":"Min1","start":str(start),"end":str(end)})
        save(f"mexc_{day}.json",r)
        mj=r.json() if r.status_code==200 else {}
        md=mj.get("data") or {} if isinstance(mj,dict) else {}
        d["mexc"]={"status":r.status_code,"success":mj.get("success") if isinstance(mj,dict) else None,
                   "rows":len(md.get("time") or []),"schema_ok":len(md.get("time") or [])>=20}

        # Bitget historical 1m.
        r=req("https://api.bitget.com/api/v2/mix/market/history-candles",{
          "symbol":"NVDAUSDT","productType":"USDT-FUTURES","granularity":"1m",
          "startTime":str(start*1000),"endTime":str(end*1000),"limit":"200"
        })
        save(f"bitget_{day}.json",r)
        bj=r.json() if r.status_code==200 else {}
        bd=bj.get("data") or [] if isinstance(bj,dict) else []
        d["bitget"]={"status":r.status_code,"code":bj.get("code") if isinstance(bj,dict) else None,
                     "rows":len(bd),"schema_ok":len(bd)>=20}

        # Binance official daily archive.
        url=f"https://data.binance.vision/data/futures/um/daily/klines/NVDAUSDT/1m/NVDAUSDT-1m-{day}.zip"
        r=req(url)
        save(f"binance_{day}.zip",r)
        rows=0; schema=False; name=None
        if r.status_code==200:
            try:
                z=zipfile.ZipFile(io.BytesIO(r.content)); names=z.namelist()
                name=names[0] if len(names)==1 else None
                if name:
                    rr=list(csv.reader(io.TextIOWrapper(z.open(name),encoding="utf-8")))
                    rows=len(rr); schema=rows>100
            except Exception:
                pass
        d["binance"]={"status":r.status_code,"rows":rows,"schema_ok":schema,
                      "archive_sha256":sha(r.content) if r.status_code==200 else None,
                      "csv_file":name}
        rep["dates"][day]=d

    # Pyth historical endpoint anonymous probe on a burned source-verification timestamp.
    pts=epoch("2026-09-30",13,30)
    r=req(f"https://hermes.pyth.network/v2/updates/price/{pts}",
          {"ids[]":PYTH_US_NVDA_ID,"parsed":"true"})
    save("pyth_nvda_historical_anonymous_probe.json",r)
    pj=None
    if r.status_code==200:
        try: pj=r.json()
        except Exception: pj=None
    rep["pyth"]={"feed_id":PYTH_US_NVDA_ID,"symbol":"Equity.US.NVDA/USD",
                 "historical_anonymous_status":r.status_code,
                 "historical_anonymous_accessible":r.status_code==200,
                 "auth_used":False,
                 "parsed_count":len((pj or {}).get("parsed") or []) if isinstance(pj,dict) else 0}

    gates={}
    for day in DATES:
        for venue in ("mexc","bitget","binance"):
            gates[f"{venue}_{day}_transport"]=bool(rep["dates"][day][venue]["schema_ok"])
    rep["gates"]=gates
    rep["broad_free_transport_pass"]=all(gates.values())
    rep["verdict"]="NVIDIA_BROAD_FREE_HISTORICAL_TRANSPORT_PASS" if all(gates.values()) else "SOURCE_BLOCKED_NVIDIA_BROAD_HISTORY"
    rep["historical_outcomes_opened"]=0
    rep["private_endpoints_used"]=False
    rep["account_reads"]=False
    rep["orders"]=False
    rep["exchange_mutation"]=False
    rep["live_trading_authorized"]=False

    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"MEXC_NVIDIA_SOURCE_COVERAGE_RECEIPT_V011.json").write_text(json.dumps(rep,indent=2,sort_keys=True))
    print(json.dumps(rep,indent=2,sort_keys=True))

if __name__=="__main__": main()
