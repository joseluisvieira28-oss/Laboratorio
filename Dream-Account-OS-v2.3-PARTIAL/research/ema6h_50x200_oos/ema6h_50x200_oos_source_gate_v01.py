from __future__ import annotations

import csv, hashlib, io, json, os, sys, time, urllib.request, zipfile
from dataclasses import dataclass, asdict
from pathlib import Path

EXPERIMENT_ID="EMA6H-50X200-BINANCE-OOS-2025_2026-001"
SYMBOLS=("BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT","DOGEUSDT")
MONTHS=tuple([f"2025-{m:02d}" for m in range(1,13)]+[f"2026-{m:02d}" for m in range(1,9)])
INTERVAL="15m"
STEP_MS=900_000
BASE="https://data.binance.vision/data/spot/monthly/klines"
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"research"/"local_data"/"ema6h_50x200_oos_source_v01"
CANON=OUT/"canonical_15m"
META=OUT/"monthly_meta"
RECEIPT=OUT/"EMA6H_50X200_BINANCE_OOS_2025_2026_001_SOURCE_GATE_V0.1.json"

def sha256(b:bytes)->str:return hashlib.sha256(b).hexdigest()

def get(url:str,retries:int=4)->bytes:
    last=None
    for i in range(retries):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"EMA6H-50X200-OOS source gate/1.0"})
            with urllib.request.urlopen(req,timeout=90) as r:
                if r.status!=200: raise RuntimeError(f"HTTP {r.status}")
                return r.read()
        except Exception as e:
            last=e
            if i+1<retries: time.sleep(2**i)
    raise RuntimeError(f"download failed {url}: {last}")

def checksum(payload:bytes,name:str)->str:
    line=payload.decode("utf-8").strip().splitlines()[0].replace("*"," ").split()
    if not line or len(line[0])!=64: raise ValueError(f"bad checksum {name}")
    return line[0].lower()

def to_ms(x:int)->int:
    if x>=10**15:
        if x%1000!=0 and x%1000!=999:
            # Binance close timestamps end in 999999us; floor division remains canonical.
            pass
        return x//1000
    if x>=10**12:return x
    raise ValueError(f"unexpected timestamp magnitude {x}")

@dataclass
class Audit:
    symbol:str
    archives:int=0
    checksum_pass:int=0
    rows:int=0
    duplicates:int=0
    out_of_order:int=0
    gaps:int=0
    missing_candles:int=0
    first_ms:int|None=None
    last_ms:int|None=None
    canonical_sha256:str=""

def main()->int:
    OUT.mkdir(parents=True,exist_ok=True);CANON.mkdir(parents=True,exist_ok=True);META.mkdir(parents=True,exist_ok=True)
    try:
        audits={}
        meta=[]
        for sym in SYMBOLS:
            a=Audit(sym); prev=None
            p=CANON/f"{sym}_15m.csv"
            h=hashlib.sha256()
            with p.open("w",encoding="utf-8",newline="") as fh:
                w=csv.writer(fh,lineterminator="\n");header=["open_time_ms","open","high","low","close","volume","close_time_ms"];w.writerow(header);h.update((",".join(header)+"\n").encode())
                for ym in MONTHS:
                    name=f"{sym}-{INTERVAL}-{ym}.zip";url=f"{BASE}/{sym}/{INTERVAL}/{name}"
                    z=get(url);cs=get(url+".CHECKSUM"); expected=checksum(cs,name); actual=sha256(z)
                    if actual!=expected:raise ValueError(f"checksum mismatch {sym} {ym}")
                    a.archives+=1;a.checksum_pass+=1
                    rec={"symbol":sym,"month":ym,"name":name,"zip_sha256":actual,"bytes":len(z),"url":url};meta.append(rec)
                    with zipfile.ZipFile(io.BytesIO(z)) as zf:
                        names=[n for n in zf.namelist() if not n.endswith("/")]
                        if len(names)!=1:raise ValueError(f"unexpected zip members {sym} {ym}")
                        with zf.open(names[0]) as raw:
                            r=csv.reader(io.TextIOWrapper(raw,encoding="utf-8"))
                            for row in r:
                                if not row:continue
                                try:ot=to_ms(int(row[0]))
                                except ValueError:
                                    if row[0].lower().strip() in {"open_time","open time"}:continue
                                    raise
                                ct=to_ms(int(row[6]))
                                if ot%STEP_MS!=0:raise ValueError(f"unaligned {sym} {ym} {ot}")
                                if ct!=ot+STEP_MS-1:raise ValueError(f"close relation {sym} {ym} {ot} {ct}")
                                o,hi,lo,c,v=map(float,(row[1],row[2],row[3],row[4],row[5]))
                                if min(o,hi,lo,c)<=0 or v<0 or hi<max(o,c,lo) or lo>min(o,c,hi):raise ValueError("bad ohlc")
                                if prev is not None:
                                    if ot==prev:a.duplicates+=1
                                    elif ot<prev:a.out_of_order+=1
                                    elif ot>prev+STEP_MS:
                                        a.gaps+=1;a.missing_candles+=(ot-prev)//STEP_MS-1
                                prev=ot
                                if a.first_ms is None:a.first_ms=ot
                                a.last_ms=ot;a.rows+=1
                                vals=[ot,row[1],row[2],row[3],row[4],row[5],ct]
                                sio=io.StringIO(newline="");csv.writer(sio,lineterminator="\n").writerow(vals);b=sio.getvalue().encode();fh.write(sio.getvalue());h.update(b)
            if a.duplicates or a.out_of_order:raise ValueError(f"timestamp integrity {sym}")
            a.canonical_sha256=h.hexdigest();audits[sym]=asdict(a)
        if len(meta)!=120 or sum(x["checksum_pass"] for x in audits.values())!=120:raise ValueError("archive count")
        receipt={"experiment_id":EXPERIMENT_ID,"status":"SOURCE_DATA_PASS","provider":"Binance Data Vision","market":"Spot","interval":"15m",
                 "months":list(MONTHS),"archive_count":len(meta),"audits":audits,
                 "microseconds_normalized_to_milliseconds":True,"normalization_rule":"timestamp>=1e15 => floor_divide_by_1000",
                 "outcome_evaluation_performed":False,"signal_calculation_performed":False,"return_calculation_performed":False,
                 "live_trading":False,"exchange_mutation":False,"access_after_2026_08":False}
        RECEIPT.write_text(json.dumps(receipt,indent=2,sort_keys=True),encoding="utf-8")
        (META/"archives.json").write_text(json.dumps(meta,indent=2,sort_keys=True),encoding="utf-8")
        print(json.dumps({"status":"SOURCE_DATA_PASS","archive_count":120,"rows":{s:a["rows"] for s,a in audits.items()},"gaps":{s:a["gaps"] for s,a in audits.items()}},indent=2))
        return 0
    except Exception as e:
        receipt={"experiment_id":EXPERIMENT_ID,"status":"BLOCKED_PRE_OUTCOME_SOURCE_GATE","reason":f"{type(e).__name__}: {e}",
                 "outcome_evaluation_performed":False,"signal_calculation_performed":False,"return_calculation_performed":False,
                 "live_trading":False,"exchange_mutation":False,"access_after_2026_08":False}
        RECEIPT.parent.mkdir(parents=True,exist_ok=True);RECEIPT.write_text(json.dumps(receipt,indent=2),encoding="utf-8")
        print(json.dumps(receipt,indent=2),file=sys.stderr);return 2

if __name__=="__main__":raise SystemExit(main())
