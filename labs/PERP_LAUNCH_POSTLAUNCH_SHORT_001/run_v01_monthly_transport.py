#!/usr/bin/env python3
import csv,hashlib,shutil,sys,time,urllib.request,zipfile
from datetime import datetime,timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import run_v01 as base

MONTHLY="https://data.binance.vision/data/futures/um/monthly/klines"

def months_between(a,b):
    y,m=a.year,a.month
    out=[]
    while (y,m)<=(b.year,b.month):
        out.append(f"{y:04d}-{m:02d}")
        m+=1
        if m==13:y+=1;m=1
    return out

def load_month(symbol,month,tmp,cache,prov):
    k=(symbol,month)
    if k in cache:return cache[k]
    name=f"{symbol}-1m-{month}.zip"
    url=f"{MONTHLY}/{symbol}/1m/{name}"
    z=tmp/(symbol+"_"+month+".zip");c=tmp/(symbol+"_"+month+".CHECKSUM")
    base.fetch(url,z);base.fetch(url+".CHECKSUM",c)
    exp=c.read_text().strip().split()[0].lower();act=base.sha(z)
    if act!=exp:raise RuntimeError(f"checksum mismatch {symbol} {month}")
    rows={}
    with zipfile.ZipFile(z) as zz:
        names=zz.namelist()
        if len(names)!=1:raise RuntimeError("archive members")
        with zz.open(names[0]) as raw:
            rd=csv.reader((x.decode() for x in raw))
            for r in rd:
                if not r or not str(r[0]).strip().lstrip("-").isdigit():continue
                t=int(float(r[0]));t=t if t>10**11 else t*1000
                rows[t]=float(r[1])
    cache[k]=rows
    prov.append({"symbol":symbol,"month":month,"url":url,"sha256":act,"transport":"MONTHLY_EQUIVALENT"})
    z.unlink(missing_ok=True);c.unlink(missing_ok=True)
    return rows

base.days_between=months_between
base.load_day=load_month

if __name__=="__main__":
    base.main()
