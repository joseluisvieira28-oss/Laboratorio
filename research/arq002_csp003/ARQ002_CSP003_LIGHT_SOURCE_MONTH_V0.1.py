#!/usr/bin/env python3
"""ARQ-002-CSP-003 2022 light source census month — outcome blind."""
from __future__ import annotations
import argparse,csv,hashlib,io,json,math,re,time,urllib.request,zipfile,calendar
from datetime import datetime,timezone,date
from pathlib import Path

BASE="https://data.binance.vision/data/futures/um"
SYMBOL="BTCUSDT"
UTC=timezone.utc
UA="Crypto-Lab-ARQ002-CSP003-LightSource/0.1"
FUND_TIME=("calc_time","fundingTime","funding_time")
FUND_RATE=("last_funding_rate","fundingRate","funding_rate")
REQ_MET={"create_time","symbol","sum_open_interest"}

class E(RuntimeError):pass

def req(u,attempts=5):
    last=None
    for i in range(attempts):
        try:
            r=urllib.request.Request(u,headers={"User-Agent":UA})
            with urllib.request.urlopen(r,timeout=90) as x:
                if x.status!=200: raise E(f"HTTP_{x.status}:{u}")
                return x.read()
        except Exception as e:
            last=e
            if i+1<attempts:time.sleep(min(8,1.5*(i+1)))
    raise E(f"DOWNLOAD:{u}:{last}")

def checksum(u):
    s=req(u+".CHECKSUM").decode("utf-8","replace")
    m=re.search(r"(?i)\b([0-9a-f]{64})\b",s)
    if not m:raise E("CHECKSUM_PARSE")
    return m.group(1).lower()

def verified(u):
    raw=req(u); pub=checksum(u); act=hashlib.sha256(raw).hexdigest()
    if act!=pub:raise E(f"CHECKSUM_MISMATCH:{u}")
    return raw,act

def rows(raw,u):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        bad=z.testzip()
        if bad:raise E(f"ZIP_CRC:{u}:{bad}")
        ns=[n for n in z.namelist() if n.lower().endswith(".csv") and not n.endswith("/")]
        if len(ns)!=1:raise E(f"CSV_COUNT:{u}:{len(ns)}")
        txt=z.read(ns[0]).decode("utf-8-sig")
    return [r for r in csv.reader(io.StringIO(txt)) if r]

def to_ms(v):
    s=v.strip()
    try:
        x=float(s)
        if x>1e14:return int(x/1000)
        if x>1e11:return int(x)
        if x>1e9:return int(x*1000)
    except ValueError:pass
    d=datetime.fromisoformat(s.replace("Z","+00:00"))
    if d.tzinfo is None:d=d.replace(tzinfo=UTC)
    return int(d.timestamp()*1000)

def iso(ms):return datetime.fromtimestamp(ms/1000,tz=UTC).isoformat().replace("+00:00","Z")

def scan_kline(d):
    ds=d.isoformat(); u=f"{BASE}/daily/klines/{SYMBOL}/1m/{SYMBOL}-1m-{ds}.zip"
    raw,sha=verified(u); rr=rows(raw,u)
    body=rr
    try:to_ms(rr[0][0])
    except Exception:body=rr[1:]
    ts=[to_ms(r[0]) for r in body]
    lo=int(datetime(d.year,d.month,d.day,tzinfo=UTC).timestamp()*1000)
    exp=[lo+i*60000 for i in range(1440)]
    if ts!=exp:raise E(f"KLINE_GRID:{ds}:{len(ts)}")
    return {"sha256":sha,"rows":len(ts)}

def scan_metrics(d):
    ds=d.isoformat(); u=f"{BASE}/daily/metrics/{SYMBOL}/{SYMBOL}-metrics-{ds}.zip"
    raw,sha=verified(u); rr=rows(raw,u)
    if len(rr)<2:raise E(f"MET_EMPTY:{ds}")
    h=[x.strip() for x in rr[0]]
    if not REQ_MET.issubset(set(h)):raise E(f"MET_SCHEMA:{ds}:{h}")
    ti=h.index("create_time"); si=h.index("symbol"); oi=h.index("sum_open_interest")
    groups={}
    for r in rr[1:]:
        if len(r)<=max(ti,si,oi):raise E(f"MET_WIDTH:{ds}")
        if r[si].strip()!=SYMBOL:raise E(f"MET_SYMBOL:{ds}")
        t=to_ms(r[ti]); groups.setdefault(t,[]).append(r)
    obs={}; invalid=[]; exact_dupes=0
    for t,rs in groups.items():
        urows={tuple(x) for x in rs}
        if len(urows)!=1:raise E(f"MET_CONFLICT:{ds}:{t}")
        exact_dupes+=len(rs)-1
        r=rs[0]; rawv=r[oi].strip(); reason=None
        try:
            v=float(rawv)
            if not math.isfinite(v):reason="NONFINITE"
            elif v<=0:reason="NONPOSITIVE"
        except Exception:reason="NONNUMERIC"
        obs[t]=reason
        if reason:invalid.append({"timestamp_utc":iso(t),"reason":reason})
    lo=int(datetime(d.year,d.month,d.day,tzinfo=UTC).timestamp()*1000)
    expected=[lo+i*300000 for i in range(288)]
    if any((t-lo)%300000!=0 for t in obs):raise E(f"MET_OFFGRID:{ds}")
    missing=[iso(t) for t in expected if t not in obs]
    return {
        "sha256":sha,"observed":len(obs),"missing":missing,"invalid":invalid,
        "exact_duplicate_rows_removed":exact_dupes
    }

def find(h,als):
    for a in als:
        if a in h:return h.index(a)
    raise E(f"ALIAS:{als}:{h}")

def scan_funding(y,m):
    ym=f"{y:04d}-{m:02d}";u=f"{BASE}/monthly/fundingRate/{SYMBOL}/{SYMBOL}-fundingRate-{ym}.zip"
    raw,sha=verified(u);rr=rows(raw,u)
    h=[x.strip() for x in rr[0]]
    ti=find(h,FUND_TIME); find(h,FUND_RATE)
    ts=[to_ms(r[ti]) for r in rr[1:] if len(r)>ti]
    if len(ts)!=len(rr)-1 or len(ts)!=len(set(ts)):raise E(f"FUND_TS:{ym}")
    ts=sorted(ts);g=[b-a for a,b in zip(ts,ts[1:])]
    if g and max(g)>12*3600*1000:raise E(f"FUND_GAP:{ym}:{max(g)}")
    return {"sha256":sha,"rows":len(ts),"max_gap_ms":max(g) if g else None}

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--month",required=True);a=ap.parse_args()
    y,m=map(int,a.month.split("-"))
    if y!=2022:raise SystemExit("2022 only")
    rec={"lab_id":"ARQ-002-CSP-003","gate":"LIGHT_SOURCE_MONTH_V0.1","month":a.month,
         "classification":"RUNNING","days":[],"funding":None,
         "economic_values_opened":False,"outcomes_opened":False,"errors":[]}
    try:
        for dd in range(1,calendar.monthrange(y,m)[1]+1):
            d=date(y,m,dd)
            rec["days"].append({"date":d.isoformat(),"kline":scan_kline(d),"metrics":scan_metrics(d)})
        rec["funding"]=scan_funding(y,m)
        rec["classification"]="SOURCE_MONTH_PASS"
    except Exception as e:
        rec["classification"]="SOURCE_MONTH_FAIL_CLOSED";rec["errors"].append(f"{type(e).__name__}:{e}")
    rec["days_count"]=len(rec["days"])
    rec["metrics_missing_count"]=sum(len(x["metrics"]["missing"]) for x in rec["days"])
    rec["metrics_invalid_count"]=sum(len(x["metrics"]["invalid"]) for x in rec["days"])
    rec["metrics_exact_dupes_removed"]=sum(x["metrics"]["exact_duplicate_rows_removed"] for x in rec["days"])
    rec["missing_slots"]=[s for x in rec["days"] for s in x["metrics"]["missing"]]
    rec["invalid_slots"]=[s for x in rec["days"] for s in x["metrics"]["invalid"]]
    rec["receipt_sha256"]=hashlib.sha256(json.dumps(rec,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    p=Path(f"arq002_csp003_light_source_{a.month}.json")
    p.write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"month":a.month,"classification":rec["classification"],"missing":rec["metrics_missing_count"],
      "invalid":rec["metrics_invalid_count"],"days":rec["days_count"],"errors":rec["errors"],"receipt_sha256":rec["receipt_sha256"]},sort_keys=True))
    return 0 if rec["classification"]=="SOURCE_MONTH_PASS" else 1
if __name__=="__main__":raise SystemExit(main())
