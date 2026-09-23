#!/usr/bin/env python3
"""ARQ-002 source-only OI validity diagnostic for 2024.

Reads only BTCUSDT metrics archives and classifies sum_open_interest validity.
Does not read price, aggTrades, funding, returns or outcomes.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,math,re,time,urllib.request,zipfile,calendar
from datetime import datetime,timezone,date
from pathlib import Path

BASE="https://data.binance.vision/data/futures/um/daily/metrics/BTCUSDT"
UA="Crypto-Lab-ARQ002-OIValidity/0.1"
UTC=timezone.utc

def req(u,attempts=5):
    last=None
    for i in range(attempts):
        try:
            r=urllib.request.Request(u,headers={"User-Agent":UA})
            with urllib.request.urlopen(r,timeout=90) as x:return x.read()
        except Exception as e:
            last=e
            if i+1<attempts:time.sleep(1.5*(i+1))
    raise RuntimeError(f"DOWNLOAD_FAILED:{u}:{last}")

def checksum(u):
    x=req(u+".CHECKSUM").decode("utf-8","replace")
    m=re.search(r"(?i)\b([0-9a-f]{64})\b",x)
    if not m:raise RuntimeError("CHECKSUM_PARSE")
    return m.group(1).lower()

def to_ms(v):
    x=float(v)
    if x>1e14:return int(x/1000)
    if x>1e11:return int(x)
    if x>1e9:return int(x*1000)
    raise RuntimeError(f"TS_PARSE:{v}")

def iso(ms):return datetime.fromtimestamp(ms/1000,tz=UTC).isoformat().replace("+00:00","Z")

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--month",required=True);a=ap.parse_args()
    y,m=map(int,a.month.split("-"))
    if y!=2024:raise SystemExit("2024 only")
    rec={"lab_id":"ARQ-002-SOURCE-DIAGNOSTIC","month":a.month,"classification":"RUNNING",
         "invalid_oi_slots":[],"missing_slots":[],"files_verified":0,
         "price_values_opened":False,"cvd_values_opened":False,"funding_values_opened":False,
         "returns_opened":False,"outcomes_opened":False,"errors":[]}
    try:
        for dd in range(1,calendar.monthrange(y,m)[1]+1):
            d=date(y,m,dd);ds=d.isoformat()
            u=f"{BASE}/BTCUSDT-metrics-{ds}.zip"
            raw=req(u);pub=checksum(u);act=hashlib.sha256(raw).hexdigest()
            if act!=pub:raise RuntimeError(f"CHECKSUM:{ds}")
            rec["files_verified"]+=1
            with zipfile.ZipFile(io.BytesIO(raw)) as z:
                names=[n for n in z.namelist() if n.endswith(".csv")]
                txt=z.read(names[0]).decode("utf-8-sig")
            rows=[r for r in csv.reader(io.StringIO(txt)) if r]
            h=[x.strip() for x in rows[0]]
            ti=h.index("create_time");oi=h.index("sum_open_interest")
            groups={}
            for r in rows[1:]:
                t=to_ms(r[ti]);groups.setdefault(t,[]).append(r)
            observed=set()
            for t,rs in groups.items():
                if len({tuple(x) for x in rs})!=1:raise RuntimeError(f"CONFLICT_DUP:{ds}:{t}")
                observed.add(t)
                rawv=rs[0][oi].strip()
                valid=True;reason=None
                try:
                    v=float(rawv)
                    if not math.isfinite(v):valid=False;reason="NONFINITE"
                    elif v<=0:valid=False;reason="NONPOSITIVE"
                except Exception:
                    valid=False;reason="NONNUMERIC"
                if not valid:
                    rec["invalid_oi_slots"].append({"timestamp_utc":iso(t),"reason":reason})
            lo=int(datetime(y,m,dd,tzinfo=UTC).timestamp()*1000)
            expected={lo+i*300000 for i in range(288)}
            for t in sorted(expected-observed):
                rec["missing_slots"].append(iso(t))
        rec["classification"]="SOURCE_DIAGNOSTIC_COMPLETE"
    except Exception as e:
        rec["classification"]="SOURCE_DIAGNOSTIC_FAIL_CLOSED";rec["errors"].append(f"{type(e).__name__}:{e}")
    rec["invalid_oi_count"]=len(rec["invalid_oi_slots"]);rec["missing_count"]=len(rec["missing_slots"])
    rec["receipt_sha256"]=hashlib.sha256(json.dumps(rec,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    Path(f"arq002_oi_diag_{a.month}.json").write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"month":a.month,"classification":rec["classification"],"invalid_oi_count":rec["invalid_oi_count"],
                      "missing_count":rec["missing_count"],"errors":rec["errors"]},sort_keys=True))
if __name__=="__main__":main()
