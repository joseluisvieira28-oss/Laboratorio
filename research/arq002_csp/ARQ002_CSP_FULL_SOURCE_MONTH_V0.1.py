#!/usr/bin/env python3
"""ARQ-002-CSP full 2024 source census — monthly shard, outcome blind."""
from __future__ import annotations
import argparse,csv,hashlib,io,json,re,sys,time,urllib.request,urllib.error,zipfile,calendar
from datetime import datetime,timezone,date,timedelta
from pathlib import Path

BASE="https://data.binance.vision/data/futures/um"
SYMBOL="BTCUSDT"
UA="Crypto-Lab-ARQ002-CSP-FullSource/0.1"
PROTECTED_MS=int(datetime(2025,1,1,tzinfo=timezone.utc).timestamp()*1000)
METRICS_REQUIRED={
 "create_time","symbol","sum_open_interest","sum_open_interest_value",
 "count_toptrader_long_short_ratio","sum_toptrader_long_short_ratio",
 "count_long_short_ratio","sum_taker_long_short_vol_ratio",
}
FUND_TIME=("calc_time","fundingTime","funding_time")
FUND_RATE=("last_funding_rate","fundingRate","funding_rate")

class GateError(RuntimeError): pass

def req(url,attempts=5):
    last=None
    for i in range(attempts):
        try:
            r=urllib.request.Request(url,headers={"User-Agent":UA})
            with urllib.request.urlopen(r,timeout=120) as x:
                if x.status!=200: raise GateError(f"HTTP_{x.status}:{url}")
                return x.read()
        except Exception as e:
            last=e
            if i+1<attempts: time.sleep(min(8,1.5*(i+1)))
    raise GateError(f"DOWNLOAD_FAILED:{url}:{type(last).__name__}:{last}")

def checksum(url):
    raw=req(url+".CHECKSUM").decode("utf-8","replace")
    m=re.search(r"(?i)\b([0-9a-f]{64})\b",raw)
    if not m: raise GateError(f"CHECKSUM_PARSE:{url}")
    return m.group(1).lower()

def verified(url):
    raw=req(url); pub=checksum(url); actual=hashlib.sha256(raw).hexdigest()
    if actual!=pub: raise GateError(f"CHECKSUM_MISMATCH:{url}")
    return raw,actual

def open_csv(raw,url):
    z=zipfile.ZipFile(io.BytesIO(raw))
    bad=z.testzip()
    if bad: z.close(); raise GateError(f"ZIP_CRC:{url}:{bad}")
    names=[n for n in z.namelist() if n.lower().endswith(".csv") and not n.endswith("/")]
    if len(names)!=1: z.close(); raise GateError(f"CSV_COUNT:{url}:{len(names)}")
    fh=io.TextIOWrapper(z.open(names[0]),encoding="utf-8-sig",newline="")
    return z,fh,csv.reader(fh)

def to_ms(v):
    s=v.strip()
    try:
        x=float(s)
        if x>1e14:return int(x/1000)
        if x>1e11:return int(x)
        if x>1e9:return int(x*1000)
    except ValueError: pass
    dt=datetime.fromisoformat(s.replace("Z","+00:00"))
    if dt.tzinfo is None:dt=dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp()*1000)

def day_iter(y,m):
    for d in range(1,calendar.monthrange(y,m)[1]+1):
        yield date(y,m,d)

def scan_agg(day):
    ds=day.isoformat()
    url=f"{BASE}/daily/aggTrades/{SYMBOL}/{SYMBOL}-aggTrades-{ds}.zip"
    raw,sha=verified(url)
    z,fh,rd=open_csv(raw,url)
    count=0; first_ts=None; last_ts=None; prev_id=None; buyer_bool=True; header_checked=False
    try:
        for row in rd:
            if not row: continue
            if not header_checked:
                header_checked=True
                try: int(float(row[0]))
                except Exception: continue
            if len(row)<7: raise GateError(f"AGG_WIDTH:{ds}")
            aid=int(float(row[0])); ts=to_ms(row[5]); bm=row[6].strip().lower()
            if prev_id is not None and aid<=prev_id: raise GateError(f"AGG_ID_ORDER:{ds}")
            prev_id=aid
            if bm not in {"true","false"}: buyer_bool=False
            first_ts=ts if first_ts is None else first_ts
            last_ts=ts; count+=1
    finally:
        fh.close(); z.close()
    if count<=0: raise GateError(f"AGG_EMPTY:{ds}")
    lo=int(datetime(day.year,day.month,day.day,tzinfo=timezone.utc).timestamp()*1000); hi=lo+86400000
    if first_ts<lo or last_ts>=hi or last_ts>=PROTECTED_MS: raise GateError(f"AGG_SCOPE:{ds}")
    if not buyer_bool: raise GateError(f"AGG_BUYER_MAKER:{ds}")
    return {"date":ds,"rows":count,"sha256":sha,"first_ts":first_ts,"last_ts":last_ts}

def scan_kline(day):
    ds=day.isoformat()
    url=f"{BASE}/daily/klines/{SYMBOL}/1m/{SYMBOL}-1m-{ds}.zip"
    raw,sha=verified(url)
    z,fh,rd=open_csv(raw,url)
    ts=[]; first=True
    try:
        for row in rd:
            if not row: continue
            if first:
                first=False
                try: to_ms(row[0])
                except Exception: continue
            if len(row)<12: raise GateError(f"KLINE_WIDTH:{ds}")
            ts.append(to_ms(row[0]))
    finally: fh.close(); z.close()
    lo=int(datetime(day.year,day.month,day.day,tzinfo=timezone.utc).timestamp()*1000)
    exp=[lo+i*60000 for i in range(1440)]
    if ts!=exp: raise GateError(f"KLINE_GRID:{ds}:{len(ts)}/1440")
    return {"date":ds,"rows":len(ts),"sha256":sha}

def scan_metrics(day):
    ds=day.isoformat()
    url=f"{BASE}/daily/metrics/{SYMBOL}/{SYMBOL}-metrics-{ds}.zip"
    raw,sha=verified(url)
    z,fh,rd=open_csv(raw,url)
    try: rows=[r for r in rd if r]
    finally: fh.close(); z.close()
    if len(rows)<2: raise GateError(f"METRICS_EMPTY:{ds}")
    h=[x.strip() for x in rows[0]]
    miss=METRICS_REQUIRED.difference(h)
    if miss: raise GateError(f"METRICS_SCHEMA:{ds}:{sorted(miss)}")
    ti=h.index("create_time"); si=h.index("symbol")
    groups={}
    for r in rows[1:]:
        if len(r)<=max(ti,si): raise GateError(f"METRICS_WIDTH:{ds}")
        if r[si].strip()!=SYMBOL: raise GateError(f"METRICS_SYMBOL:{ds}")
        t=to_ms(r[ti]); groups.setdefault(t,[]).append(r)
    dedup=[]
    exact_removed=0
    for t,rs in groups.items():
        u={tuple(x) for x in rs}
        if len(u)!=1: raise GateError(f"METRICS_CONFLICT:{ds}:{t}")
        dedup.append(t); exact_removed+=len(rs)-1
    ts=sorted(dedup)
    lo=int(datetime(day.year,day.month,day.day,tzinfo=timezone.utc).timestamp()*1000)
    exp=[lo+i*300000 for i in range(288)]
    if ts!=exp: raise GateError(f"METRICS_GRID:{ds}:{len(ts)}/288")
    if ts[-1]>=PROTECTED_MS: raise GateError(f"METRICS_PROTECTED:{ds}")
    return {"date":ds,"rows":len(ts),"sha256":sha,"exact_dupes_removed":exact_removed}

def find_alias(h,aliases):
    for a in aliases:
        if a in h:return h.index(a)
    raise GateError(f"ALIAS_MISSING:{aliases}:{h}")

def scan_funding(y,m):
    ym=f"{y:04d}-{m:02d}"
    url=f"{BASE}/monthly/fundingRate/{SYMBOL}/{SYMBOL}-fundingRate-{ym}.zip"
    raw,sha=verified(url)
    z,fh,rd=open_csv(raw,url)
    try: rows=[r for r in rd if r]
    finally: fh.close(); z.close()
    if len(rows)<2: raise GateError(f"FUND_EMPTY:{ym}")
    h=[x.strip() for x in rows[0]]
    ti=find_alias(h,FUND_TIME); find_alias(h,FUND_RATE)
    ts=[to_ms(r[ti]) for r in rows[1:] if len(r)>ti]
    if len(ts)!=len(rows)-1 or len(ts)!=len(set(ts)): raise GateError(f"FUND_TS:{ym}")
    ts=sorted(ts)
    if any(x>=PROTECTED_MS for x in ts): raise GateError(f"FUND_PROTECTED:{ym}")
    gaps=[b-a for a,b in zip(ts,ts[1:])]
    if gaps and max(gaps)>12*3600*1000: raise GateError(f"FUND_GAP:{ym}:{max(gaps)}")
    return {"month":ym,"rows":len(ts),"sha256":sha,"max_gap_ms":max(gaps) if gaps else None}

def warmup():
    d=date(2023,12,31)
    k=scan_kline(d); m=scan_metrics(d); f=scan_funding(2023,12)
    return {"kline":k,"metrics":m,"funding":f,"pass":True}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--month",required=True); args=ap.parse_args()
    y,m=map(int,args.month.split("-"))
    if y!=2024: raise SystemExit("month must be 2024")
    rec={"lab_id":"ARQ-002-CSP-001","gate":"FULL_SOURCE_CENSUS_MONTH_V0.1","month":args.month,
         "classification":"RUNNING","days":[],"funding":None,"warmup":None,
         "economic_values_reported":False,"outcomes_opened":False,
         "protected_2025_accessed":False,"protected_2026_accessed":False,"errors":[]}
    try:
        for d in day_iter(y,m):
            rec["days"].append({"date":d.isoformat(),"agg":scan_agg(d),"kline":scan_kline(d),"metrics":scan_metrics(d)})
        rec["funding"]=scan_funding(y,m)
        if m==1: rec["warmup"]=warmup()
        rec["classification"]="SOURCE_MONTH_PASS"
    except Exception as e:
        rec["classification"]="SOURCE_MONTH_FAIL_CLOSED"; rec["errors"].append(f"{type(e).__name__}:{e}")
    rec["days_count"]=len(rec["days"])
    rec["agg_rows_total"]=sum(x["agg"]["rows"] for x in rec["days"]) if rec["days"] else 0
    rec["metrics_exact_dupes_removed"]=sum(x["metrics"]["exact_dupes_removed"] for x in rec["days"]) if rec["days"] else 0
    rec["receipt_sha256"]=hashlib.sha256(json.dumps(rec,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    out=Path(f"arq002_source_{args.month}.json")
    out.write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"month":args.month,"classification":rec["classification"],"days_count":rec["days_count"],
                      "agg_rows_total":rec["agg_rows_total"],"errors":rec["errors"],
                      "receipt_sha256":rec["receipt_sha256"]},sort_keys=True))
    return 0 if rec["classification"]=="SOURCE_MONTH_PASS" else 1

if __name__=="__main__": raise SystemExit(main())
