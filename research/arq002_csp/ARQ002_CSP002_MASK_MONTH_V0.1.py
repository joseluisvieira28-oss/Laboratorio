#!/usr/bin/env python3
"""ARQ-002-CSP-002 source-mask census for February/October 2024.
Outcome-blind. Incomplete metrics day => mask whole day, not hard fail.
All other source failures remain fail-closed.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,re,sys,time,urllib.request,zipfile,calendar
from datetime import datetime,timezone,date
from pathlib import Path

BASE="https://data.binance.vision/data/futures/um"
SYMBOL="BTCUSDT"
UA="Crypto-Lab-ARQ002-CSP002-MaskCensus/0.1"
METRICS_REQUIRED={"create_time","symbol","sum_open_interest","sum_open_interest_value",
"count_toptrader_long_short_ratio","sum_toptrader_long_short_ratio","count_long_short_ratio","sum_taker_long_short_vol_ratio"}
FUND_TIME=("calc_time","fundingTime","funding_time")
FUND_RATE=("last_funding_rate","fundingRate","funding_rate")
PROTECTED=int(datetime(2025,1,1,tzinfo=timezone.utc).timestamp()*1000)

class GateError(RuntimeError):pass
def req(u,attempts=5):
    last=None
    for i in range(attempts):
        try:
            r=urllib.request.Request(u,headers={"User-Agent":UA})
            with urllib.request.urlopen(r,timeout=120) as x:return x.read()
        except Exception as e:
            last=e
            if i+1<attempts:time.sleep(min(8,1.5*(i+1)))
    raise GateError(f"DOWNLOAD:{u}:{type(last).__name__}:{last}")
def ck(u):
    t=req(u+".CHECKSUM").decode("utf-8","replace")
    m=re.search(r"(?i)\b([0-9a-f]{64})\b",t)
    if not m:raise GateError(f"CK_PARSE:{u}")
    return m.group(1).lower()
def ver(u):
    b=req(u); a=hashlib.sha256(b).hexdigest(); p=ck(u)
    if a!=p:raise GateError(f"CK_MISMATCH:{u}")
    return b,a
def rows(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        bad=z.testzip()
        if bad:raise GateError(f"ZIP_CRC:{bad}")
        ns=[n for n in z.namelist() if n.endswith(".csv")]
        if len(ns)!=1:raise GateError(f"CSV_COUNT:{len(ns)}")
        txt=z.read(ns[0]).decode("utf-8-sig")
    return [r for r in csv.reader(io.StringIO(txt)) if r]
def ms(v):
    s=v.strip()
    try:
        x=float(s)
        if x>1e14:return int(x/1000)
        if x>1e11:return int(x)
        if x>1e9:return int(x*1000)
    except:pass
    d=datetime.fromisoformat(s.replace("Z","+00:00"))
    if d.tzinfo is None:d=d.replace(tzinfo=timezone.utc)
    return int(d.timestamp()*1000)
def daylo(d):return int(datetime(d.year,d.month,d.day,tzinfo=timezone.utc).timestamp()*1000)

def agg_ok(d):
    ds=d.isoformat(); u=f"{BASE}/daily/aggTrades/{SYMBOL}/{SYMBOL}-aggTrades-{ds}.zip"
    raw,sha=ver(u); rs=rows(raw); body=rs
    try:int(float(rs[0][0]))
    except:body=rs[1:]
    prev=None; first=None; last=None; n=0
    for r in body:
        if len(r)<7:raise GateError(f"AGG_WIDTH:{ds}")
        aid=int(float(r[0])); t=ms(r[5])
        if prev is not None and aid<=prev:raise GateError(f"AGG_ID:{ds}")
        if r[6].strip().lower() not in {"true","false"}:raise GateError(f"AGG_BM:{ds}")
        prev=aid; first=t if first is None else first; last=t;n+=1
    lo=daylo(d)
    if n<=0 or first<lo or last>=lo+86400000 or last>=PROTECTED:raise GateError(f"AGG_SCOPE:{ds}")
    return {"rows":n,"sha256":sha}

def kline_ok(d):
    ds=d.isoformat();u=f"{BASE}/daily/klines/{SYMBOL}/1m/{SYMBOL}-1m-{ds}.zip"
    raw,sha=ver(u);rs=rows(raw);body=rs
    try:ms(rs[0][0])
    except:body=rs[1:]
    ts=[ms(r[0]) for r in body]
    lo=daylo(d);exp=[lo+i*60000 for i in range(1440)]
    if ts!=exp:raise GateError(f"KLINE_GRID:{ds}:{len(ts)}")
    return {"rows":1440,"sha256":sha}

def metrics_status(d):
    ds=d.isoformat();u=f"{BASE}/daily/metrics/{SYMBOL}/{SYMBOL}-metrics-{ds}.zip"
    raw,sha=ver(u);rs=rows(raw)
    if len(rs)<2:raise GateError(f"METRICS_EMPTY:{ds}")
    h=[x.strip() for x in rs[0]];miss=METRICS_REQUIRED.difference(h)
    if miss:raise GateError(f"METRICS_SCHEMA:{ds}")
    ti=h.index("create_time");si=h.index("symbol");groups={}
    for r in rs[1:]:
        if r[si].strip()!=SYMBOL:raise GateError(f"METRICS_SYMBOL:{ds}")
        t=ms(r[ti]);groups.setdefault(t,[]).append(r)
    ts=[];exact=0
    for t,g in groups.items():
        urows={tuple(x) for x in g}
        if len(urows)!=1:raise GateError(f"METRICS_CONFLICT:{ds}:{t}")
        ts.append(t);exact+=len(g)-1
    ts=sorted(ts);lo=daylo(d);exp=[lo+i*300000 for i in range(288)]
    present=set(ts);missing=[x for x in exp if x not in present]
    offgrid=[x for x in ts if x not in set(exp)]
    if offgrid or any(x>=PROTECTED for x in ts):raise GateError(f"METRICS_OFFGRID:{ds}")
    return {"sha256":sha,"unique_slots":len(ts),"missing_slots":len(missing),
            "complete":ts==exp,"exact_dupes_removed":exact}

def alias(h,aa):
    for a in aa:
        if a in h:return h.index(a)
    raise GateError("FUND_ALIAS")
def funding_ok(y,m):
    ym=f"{y:04d}-{m:02d}";u=f"{BASE}/monthly/fundingRate/{SYMBOL}/{SYMBOL}-fundingRate-{ym}.zip"
    raw,sha=ver(u);rs=rows(raw);h=[x.strip() for x in rs[0]]
    ti=alias(h,FUND_TIME);alias(h,FUND_RATE)
    ts=sorted(ms(r[ti]) for r in rs[1:])
    if len(ts)!=len(set(ts)) or any(x>=PROTECTED for x in ts):raise GateError(f"FUND_TS:{ym}")
    if any(b-a>12*3600000 for a,b in zip(ts,ts[1:])):raise GateError(f"FUND_GAP:{ym}")
    return {"rows":len(ts),"sha256":sha}

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--month",required=True);a=ap.parse_args()
    y,m=map(int,a.month.split("-"))
    if y!=2024 or m not in {2,10}:raise SystemExit("only 2024-02/10")
    rec={"lab_id":"ARQ-002-CSP-002","month":a.month,"classification":"RUNNING","days":[],
         "masked_days":[],"economic_values_reported":False,"outcomes_opened":False,
         "protected_2025_accessed":False,"protected_2026_accessed":False,"errors":[]}
    try:
        for dd in range(1,calendar.monthrange(y,m)[1]+1):
            d=date(y,m,dd); ag=agg_ok(d);kl=kline_ok(d);mt=metrics_status(d)
            eligible=bool(mt["complete"])
            if not eligible:rec["masked_days"].append(d.isoformat())
            rec["days"].append({"date":d.isoformat(),"source_eligible":eligible,
                                "agg_rows":ag["rows"],"agg_sha256":ag["sha256"],
                                "kline_sha256":kl["sha256"],"metrics":mt})
        rec["funding"]=funding_ok(y,m)
        rec["eligible_days"]=sum(1 for d in rec["days"] if d["source_eligible"])
        rec["total_days"]=len(rec["days"])
        rec["classification"]="SOURCE_MASK_MONTH_PASS"
    except Exception as e:
        rec["classification"]="SOURCE_MASK_MONTH_FAIL_CLOSED";rec["errors"].append(f"{type(e).__name__}:{e}")
    rec["receipt_sha256"]=hashlib.sha256(json.dumps(rec,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    Path(f"arq002_csp002_mask_{a.month}.json").write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"month":a.month,"classification":rec["classification"],
                      "eligible_days":rec.get("eligible_days"),"masked_days":rec["masked_days"],
                      "errors":rec["errors"],"receipt_sha256":rec["receipt_sha256"]},sort_keys=True))
    return 0 if rec["classification"]=="SOURCE_MASK_MONTH_PASS" else 1
if __name__=="__main__":raise SystemExit(main())
