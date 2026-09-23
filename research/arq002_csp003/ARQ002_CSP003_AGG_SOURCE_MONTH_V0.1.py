#!/usr/bin/env python3
"""ARQ-002-CSP-003 2022 aggTrades source census month — outcome blind."""
from __future__ import annotations
import argparse,csv,hashlib,io,json,re,time,urllib.request,zipfile,calendar
from datetime import datetime,timezone,date
from pathlib import Path

BASE="https://data.binance.vision/data/futures/um/daily/aggTrades/BTCUSDT"
UTC=timezone.utc
UA="Crypto-Lab-ARQ002-CSP003-AggSource/0.1"
class E(RuntimeError):pass
def req(u,attempts=5):
    last=None
    for i in range(attempts):
        try:
            r=urllib.request.Request(u,headers={"User-Agent":UA})
            with urllib.request.urlopen(r,timeout=180) as x:return x.read()
        except Exception as e:
            last=e
            if i+1<attempts:time.sleep(min(10,2*(i+1)))
    raise E(f"DOWNLOAD:{u}:{last}")
def csum(u):
    s=req(u+".CHECKSUM").decode("utf-8","replace")
    m=re.search(r"(?i)\b([0-9a-f]{64})\b",s)
    if not m:raise E("CHECKSUM_PARSE")
    return m.group(1).lower()
def scan(d):
    ds=d.isoformat();u=f"{BASE}/BTCUSDT-aggTrades-{ds}.zip"
    raw=req(u);pub=csum(u);act=hashlib.sha256(raw).hexdigest()
    if act!=pub:raise E(f"CHECKSUM:{ds}")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        bad=z.testzip()
        if bad:raise E(f"ZIP_CRC:{ds}:{bad}")
        ns=[n for n in z.namelist() if n.lower().endswith(".csv") and not n.endswith("/")]
        if len(ns)!=1:raise E(f"CSV_COUNT:{ds}:{len(ns)}")
        fh=io.TextIOWrapper(z.open(ns[0]),encoding="utf-8-sig",newline="")
        rd=csv.reader(fh)
        count=0;prev=None;first_ts=None;last_ts=None;bool_ok=True;first=True
        for r in rd:
            if not r:continue
            if first:
                first=False
                try:int(float(r[0]))
                except Exception:continue
            if len(r)<7:raise E(f"WIDTH:{ds}")
            aid=int(float(r[0]));ts=int(float(r[5]))
            if ts>10**14:ts//=1000
            if prev is not None and aid<=prev:raise E(f"ID_ORDER:{ds}")
            prev=aid
            if r[6].strip().lower() not in {"true","false"}:bool_ok=False
            first_ts=ts if first_ts is None else first_ts;last_ts=ts;count+=1
        fh.close()
    lo=int(datetime(d.year,d.month,d.day,tzinfo=UTC).timestamp()*1000);hi=lo+86400000
    if count<=0 or first_ts<lo or last_ts>=hi:raise E(f"SCOPE:{ds}:{count}")
    if not bool_ok:raise E(f"BUYER_MAKER:{ds}")
    return {"date":ds,"rows":count,"sha256":act,"first_ts":first_ts,"last_ts":last_ts}
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--month",required=True);a=ap.parse_args()
    y,m=map(int,a.month.split("-"))
    if y!=2022:raise SystemExit("2022 only")
    r={"lab_id":"ARQ-002-CSP-003","gate":"AGG_SOURCE_MONTH_V0.1","month":a.month,
       "classification":"RUNNING","days":[],"economic_values_opened":False,"outcomes_opened":False,"errors":[]}
    try:
        for dd in range(1,calendar.monthrange(y,m)[1]+1):
            r["days"].append(scan(date(y,m,dd)))
        r["classification"]="SOURCE_MONTH_PASS"
    except Exception as e:
        r["classification"]="SOURCE_MONTH_FAIL_CLOSED";r["errors"].append(f"{type(e).__name__}:{e}")
    r["days_count"]=len(r["days"]);r["rows_total"]=sum(x["rows"] for x in r["days"])
    r["receipt_sha256"]=hashlib.sha256(json.dumps(r,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    Path(f"arq002_csp003_agg_source_{a.month}.json").write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"month":a.month,"classification":r["classification"],"days":r["days_count"],"rows_total":r["rows_total"],"errors":r["errors"],"receipt_sha256":r["receipt_sha256"]},sort_keys=True))
    return 0 if r["classification"]=="SOURCE_MONTH_PASS" else 1
if __name__=="__main__":raise SystemExit(main())
