from __future__ import annotations

import csv, hashlib, io, json, sys, time, urllib.request, zipfile
from pathlib import Path

START_YEAR,START_MONTH=2020,1
END_YEAR,END_MONTH=2026,8
BASE="https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1d"
STEP_MS=86_400_000
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"research"/"local_data"/"ema6h_50x200_regime_btc1d_v01"
CSV_OUT=OUT/"BTCUSDT_1d.csv"
RECEIPT=OUT/"BTCUSDT_1D_REGIME_SOURCE_RECEIPT_V0.1.json"

def sha256(b:bytes)->str:return hashlib.sha256(b).hexdigest()

def months():
    y,m=START_YEAR,START_MONTH
    while (y,m)<=(END_YEAR,END_MONTH):
        yield f"{y:04d}-{m:02d}"
        m+=1
        if m==13:y+=1;m=1

def get(url,retries=4):
    last=None
    for i in range(retries):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"ema-regime-diagnostic/1.0"})
            with urllib.request.urlopen(req,timeout=90) as r:return r.read()
        except Exception as e:
            last=e
            if i+1<retries:time.sleep(2**i)
    raise RuntimeError(f"download failed {url}: {last}")

def checksum(b:bytes)->str:
    x=b.decode().strip().splitlines()[0].replace("*"," ").split()[0]
    if len(x)!=64:raise ValueError("bad checksum")
    return x.lower()

def to_ms(x:int)->int:
    if x>=10**15:return x//1000
    if x>=10**12:return x
    raise ValueError(f"bad timestamp {x}")

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    rows=[];prev=None;archives=[]
    try:
        for ym in months():
            name=f"BTCUSDT-1d-{ym}.zip";url=f"{BASE}/{name}"
            z=get(url);expected=checksum(get(url+".CHECKSUM"));actual=sha256(z)
            if actual!=expected:raise ValueError(f"checksum mismatch {ym}")
            archives.append({"month":ym,"sha256":actual,"bytes":len(z)})
            with zipfile.ZipFile(io.BytesIO(z)) as zz:
                names=[n for n in zz.namelist() if not n.endswith("/")]
                if len(names)!=1:raise ValueError(f"zip members {ym}")
                with zz.open(names[0]) as f:
                    r=csv.reader(io.TextIOWrapper(f,encoding="utf-8"))
                    for x in r:
                        if not x:continue
                        try:ot=to_ms(int(x[0]))
                        except ValueError:
                            if x[0].lower().strip() in {"open_time","open time"}:continue
                            raise
                        ct=to_ms(int(x[6]))
                        if ot%STEP_MS!=0 or ct!=ot+STEP_MS-1:raise ValueError(f"alignment {ym} {ot} {ct}")
                        if prev is not None and ot!=prev+STEP_MS:raise ValueError(f"daily gap {prev}->{ot}")
                        prev=ot
                        rows.append((ot,x[1],x[2],x[3],x[4],x[5],ct))
        with CSV_OUT.open("w",encoding="utf-8",newline="") as f:
            w=csv.writer(f,lineterminator="\n");w.writerow(["open_time_ms","open","high","low","close","volume","close_time_ms"]);w.writerows(rows)
        rec={"status":"SOURCE_DATA_PASS","provider":"Binance Data Vision","symbol":"BTCUSDT","interval":"1d",
             "start_month":"2020-01","end_month":"2026-08","archive_count":len(archives),"row_count":len(rows),
             "canonical_sha256":sha256(CSV_OUT.read_bytes()),"archives":archives,
             "microseconds_normalized_to_milliseconds":True,"outcome_evaluation_performed":False}
        RECEIPT.write_text(json.dumps(rec,indent=2,sort_keys=True))
        print(json.dumps({k:rec[k] for k in ("status","archive_count","row_count","canonical_sha256")},indent=2))
        return 0
    except Exception as e:
        OUT.mkdir(parents=True,exist_ok=True)
        RECEIPT.write_text(json.dumps({"status":"BLOCKED_SOURCE","reason":f"{type(e).__name__}: {e}","outcome_evaluation_performed":False},indent=2))
        raise

if __name__=="__main__":raise SystemExit(main())
