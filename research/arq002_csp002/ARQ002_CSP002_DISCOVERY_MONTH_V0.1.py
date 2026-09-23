#!/usr/bin/env python3
"""ARQ-002-CSP-002 frozen Discovery monthly shard.

Must only be executed after the committed CSP-002 full-source closeout is
SOURCE_CENSUS_PASS. Downloads only official Binance Vision sources, verifies
published checksums, applies the frozen OI source mask, and emits event-level
2024 Discovery observations for later immutable aggregation.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,math,re,sys,time,urllib.request,zipfile,calendar
from bisect import bisect_right
from datetime import datetime,timezone,date,timedelta
from pathlib import Path

BASE="https://data.binance.vision/data/futures/um"
SYMBOL="BTCUSDT"
UA="Crypto-Lab-ARQ002-CSP002-Discovery/0.1"
UTC=timezone.utc
SOURCE_CLOSEOUT=Path("research/arq002_csp002/ARQ002_CSP002_SOURCE_CLOSEOUT_V0.1.json")
COST_LOW=0.0010
COST_BASE=0.0014
COST_STRESS=0.0020

METRICS_REQUIRED={
 "create_time","symbol","sum_open_interest","sum_open_interest_value",
 "count_toptrader_long_short_ratio","sum_toptrader_long_short_ratio",
 "count_long_short_ratio","sum_taker_long_short_vol_ratio",
}
FUND_TIME=("calc_time","fundingTime","funding_time")
FUND_RATE=("last_funding_rate","fundingRate","funding_rate")

class FrozenError(RuntimeError): pass

def req(url,attempts=5):
    last=None
    for i in range(attempts):
        try:
            r=urllib.request.Request(url,headers={"User-Agent":UA})
            with urllib.request.urlopen(r,timeout=120) as x:
                if x.status!=200: raise FrozenError(f"HTTP_{x.status}:{url}")
                return x.read()
        except Exception as e:
            last=e
            if i+1<attempts: time.sleep(min(8,1.5*(i+1)))
    raise FrozenError(f"DOWNLOAD_FAILED:{url}:{type(last).__name__}:{last}")

def checksum(url):
    raw=req(url+".CHECKSUM").decode("utf-8","replace")
    m=re.search(r"(?i)\b([0-9a-f]{64})\b",raw)
    if not m: raise FrozenError(f"CHECKSUM_PARSE:{url}")
    return m.group(1).lower()

def verified(url):
    raw=req(url); pub=checksum(url); actual=hashlib.sha256(raw).hexdigest()
    if actual!=pub: raise FrozenError(f"CHECKSUM_MISMATCH:{url}")
    return raw

def open_rows(raw,url):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        bad=z.testzip()
        if bad: raise FrozenError(f"ZIP_CRC:{url}:{bad}")
        names=[n for n in z.namelist() if n.lower().endswith(".csv") and not n.endswith("/")]
        if len(names)!=1: raise FrozenError(f"CSV_COUNT:{url}:{len(names)}")
        text=z.read(names[0]).decode("utf-8-sig","strict")
    return [r for r in csv.reader(io.StringIO(text)) if r and any(x.strip() for x in r)]

def to_ms(v):
    s=v.strip()
    try:
        x=float(s)
        if x>1e14:return int(x/1000)
        if x>1e11:return int(x)
        if x>1e9:return int(x*1000)
    except ValueError: pass
    dt=datetime.fromisoformat(s.replace("Z","+00:00"))
    if dt.tzinfo is None:dt=dt.replace(tzinfo=UTC)
    return int(dt.timestamp()*1000)

def day_start_ms(d):
    return int(datetime(d.year,d.month,d.day,tzinfo=UTC).timestamp()*1000)

def month_days(y,m):
    return [date(y,m,d) for d in range(1,calendar.monthrange(y,m)[1]+1)]

def prev_day(d): return d-timedelta(days=1)
def next_day(d): return d+timedelta(days=1)

def load_kline_day(d):
    ds=d.isoformat()
    url=f"{BASE}/daily/klines/{SYMBOL}/1m/{SYMBOL}-1m-{ds}.zip"
    rows=open_rows(verified(url),url)
    body=rows
    try: to_ms(rows[0][0])
    except Exception: body=rows[1:]
    out={}
    for r in body:
        if len(r)<12: raise FrozenError(f"KLINE_WIDTH:{ds}")
        t=to_ms(r[0])
        vals=tuple(float(r[i]) for i in (1,2,3,4))
        if not all(math.isfinite(x) and x>0 for x in vals): raise FrozenError(f"KLINE_VALUE:{ds}:{t}")
        out[t]=vals # open,high,low,close
    lo=day_start_ms(d)
    exp=[lo+i*60000 for i in range(1440)]
    if sorted(out)!=exp: raise FrozenError(f"KLINE_GRID:{ds}:{len(out)}/1440")
    return out

def load_metrics_day(d):
    ds=d.isoformat()
    url=f"{BASE}/daily/metrics/{SYMBOL}/{SYMBOL}-metrics-{ds}.zip"
    rows=open_rows(verified(url),url)
    if len(rows)<2: raise FrozenError(f"METRICS_EMPTY:{ds}")
    h=[x.strip() for x in rows[0]]
    miss=METRICS_REQUIRED.difference(h)
    if miss: raise FrozenError(f"METRICS_SCHEMA:{ds}:{sorted(miss)}")
    ti=h.index("create_time"); oi=h.index("sum_open_interest"); si=h.index("symbol")
    groups={}
    for r in rows[1:]:
        if r[si].strip()!=SYMBOL: raise FrozenError(f"METRICS_SYMBOL:{ds}")
        t=to_ms(r[ti]); groups.setdefault(t,[]).append(r)
    out={}
    lo=day_start_ms(d); exp={lo+i*300000 for i in range(288)}
    for t,rs in groups.items():
        u={tuple(x) for x in rs}
        if len(u)!=1: raise FrozenError(f"METRICS_CONFLICT:{ds}:{t}")
        if t not in exp: raise FrozenError(f"METRICS_OFF_GRID:{ds}:{t}")
        v=float(rs[0][oi])
        if not math.isfinite(v) or v<=0: raise FrozenError(f"METRICS_OI_VALUE:{ds}:{t}")
        out[t]=v
    return out

def alias(h,names):
    for n in names:
        if n in h:return h.index(n)
    raise FrozenError(f"ALIAS_MISSING:{names}:{h}")

def load_funding_month(y,m):
    ym=f"{y:04d}-{m:02d}"
    url=f"{BASE}/monthly/fundingRate/{SYMBOL}/{SYMBOL}-fundingRate-{ym}.zip"
    rows=open_rows(verified(url),url)
    if len(rows)<2: raise FrozenError(f"FUND_EMPTY:{ym}")
    h=[x.strip() for x in rows[0]]
    ti=alias(h,FUND_TIME); ri=alias(h,FUND_RATE)
    out={}
    for r in rows[1:]:
        t=to_ms(r[ti]); v=float(r[ri])
        if not math.isfinite(v): raise FrozenError(f"FUND_VALUE:{ym}:{t}")
        if t in out: raise FrozenError(f"FUND_DUP:{ym}:{t}")
        out[t]=v
    return out

def load_agg_for_candidates(d,candidate_minutes):
    ds=d.isoformat()
    url=f"{BASE}/daily/aggTrades/{SYMBOL}/{SYMBOL}-aggTrades-{ds}.zip"
    raw=verified(url)
    # stream ZIP CSV; retain only CVD sums for pre-selected candidate minutes.
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names=[n for n in z.namelist() if n.lower().endswith(".csv") and not n.endswith("/")]
        if len(names)!=1: raise FrozenError(f"AGG_CSV_COUNT:{ds}")
        fh=io.TextIOWrapper(z.open(names[0]),encoding="utf-8-sig",newline="")
        rd=csv.reader(fh)
        signed={t:0.0 for t in candidate_minutes}
        total={t:0.0 for t in candidate_minutes}
        first=True; prev_id=None
        for row in rd:
            if not row: continue
            if first:
                first=False
                try:int(float(row[0]))
                except Exception:continue
            if len(row)<7: raise FrozenError(f"AGG_WIDTH:{ds}")
            aid=int(float(row[0]))
            if prev_id is not None and aid<=prev_id: raise FrozenError(f"AGG_ID_ORDER:{ds}")
            prev_id=aid
            ts=to_ms(row[5]); minute=(ts//60000)*60000
            if minute not in signed: continue
            px=float(row[1]); qty=float(row[2])
            if not (math.isfinite(px) and px>0 and math.isfinite(qty) and qty>0):
                raise FrozenError(f"AGG_VALUE:{ds}:{aid}")
            bm=row[6].strip().lower()
            if bm not in {"true","false"}: raise FrozenError(f"AGG_BUYER_MAKER:{ds}:{aid}")
            notion=px*qty
            total[minute]+=notion
            signed[minute]+=(-notion if bm=="true" else notion)
        fh.close()
    return {t:(signed[t],total[t]) for t in candidate_minutes}

def latest_funding(funding,sorted_ts,e):
    ix=bisect_right(sorted_ts,e)-1
    if ix<0:return None
    t=sorted_ts[ix]
    if e-t>8*3600000+5*60000:return None
    return funding[t]

def source_closeout_guard():
    if not SOURCE_CLOSEOUT.exists(): raise FrozenError("SOURCE_CLOSEOUT_MISSING")
    r=json.loads(SOURCE_CLOSEOUT.read_text())
    if r.get("lab_id")!="ARQ-002-CSP-002" or r.get("classification")!="SOURCE_CENSUS_PASS":
        raise FrozenError("SOURCE_CLOSEOUT_NOT_PASS")
    if r.get("economic_values_opened") is not False or r.get("outcomes_opened") is not False:
        raise FrozenError("SOURCE_CLOSEOUT_FIREWALL")
    return r

def main():
    source=source_closeout_guard()
    ap=argparse.ArgumentParser(); ap.add_argument("--month",required=True); args=ap.parse_args()
    y,m=map(int,args.month.split("-"))
    if y!=2024: raise SystemExit("month must be 2024")

    days=month_days(y,m)
    first,last=days[0],days[-1]
    kdays=[prev_day(first)]+days+([] if last==date(2024,12,31) else [next_day(last)])
    mdays=[prev_day(first)]+days

    klines={}
    for d in kdays: klines.update(load_kline_day(d))
    metrics={}
    for d in mdays: metrics.update(load_metrics_day(d))

    prev_month_date=first.replace(day=1)-timedelta(days=1)
    funding={}
    funding.update(load_funding_month(prev_month_date.year,prev_month_date.month))
    funding.update(load_funding_month(y,m))
    fund_ts=sorted(funding)

    # Build source-eligible non-ambiguous sweep candidates without reading aggTrade,
    # funding or future-outcome values.
    candidates_by_day={d:[] for d in days}
    candidates={}
    masked_oi=0; ambiguous=0

    for d in days:
        lo=day_start_ms(d)
        for i in range(1440):
            t=lo+i*60000
            # outcome must remain inside 2024 and all M+1..M+5 bars must exist.
            if t+5*60000 not in klines: continue
            refs=[klines.get(t-j*60000) for j in range(1,31)]
            if any(x is None for x in refs): continue
            cur=klines[t]
            h30=max(x[1] for x in refs); l30=min(x[2] for x in refs)
            hi_sweep=(cur[1]>h30 and cur[3]<h30)
            lo_sweep=(cur[2]<l30 and cur[3]>l30)
            if hi_sweep and lo_sweep:
                ambiguous+=1; continue
            if not hi_sweep and not lo_sweep: continue
            direction=-1 if hi_sweep else 1

            e=t+60000
            oi_now=(e//300000)*300000
            oi_prev=oi_now-300000
            # CSP-002 mask: exact nominal slots required; never stale fallback.
            if oi_now not in metrics or oi_prev not in metrics:
                masked_oi+=1; continue

            candidates[t]={
              "direction":direction,
              "oi_now_ts":oi_now,"oi_prev_ts":oi_prev,
              "oi_now":metrics[oi_now],"oi_prev":metrics[oi_prev]
            }
            candidates_by_day[d].append(t)

    cvd={}
    for d in days:
        if candidates_by_day[d]:
            cvd.update(load_agg_for_candidates(d,set(candidates_by_day[d])))

    out_events=[]
    ab={"A":0,"B":0,"C":0,"D":0}
    no_cvd=0
    for t in sorted(candidates):
        c=candidates[t]; direction=c["direction"]
        signed,total=cvd.get(t,(0.0,0.0))
        if total<=0:
            no_cvd+=1; continue
        ratio=signed/total
        cvd_ok=(ratio>0 if direction<0 else ratio<0)

        oi_change=math.log(c["oi_now"]/c["oi_prev"])
        oi_ok=oi_change>0

        e=t+60000
        fv=latest_funding(funding,fund_ts,e)
        fund_ok=False
        if fv is not None:
            fund_ok=(fv>0 if direction<0 else fv<0)

        b=cvd_ok
        cc=b and oi_ok
        dd=cc and fund_ok

        ab["A"]+=1; ab["B"]+=int(b); ab["C"]+=int(cc); ab["D"]+=int(dd)

        entry=klines[t+60000][0]
        exitp=klines[t+5*60000][3]
        gross=direction*math.log(exitp/entry)
        base=gross-COST_BASE
        event={
          "event_ts_ms":t,
          "event_utc":datetime.fromtimestamp(t/1000,tz=UTC).isoformat().replace("+00:00","Z"),
          "utc_day":datetime.fromtimestamp(t/1000,tz=UTC).date().isoformat(),
          "month":args.month,
          "direction":"LONG" if direction>0 else "SHORT",
          "cvd_confirmed":b,
          "oi_confirmed":oi_ok,
          "funding_confirmed":fund_ok,
          "d_confirmed":dd,
          "gross":gross,
          "low10":gross-COST_LOW,
          "base14":base,
          "stress20":gross-COST_STRESS
        }
        out_events.append(event)

    rec={
      "lab_id":"ARQ-002-CSP-002","month":args.month,
      "classification":"DISCOVERY_MONTH_COMPLETE",
      "source_closeout_receipt_sha256":source.get("receipt_sha256"),
      "ablation_counts":ab,
      "source_masked_sweep_events":masked_oi,
      "ambiguous_both_sides":ambiguous,
      "no_cvd_notional_events":no_cvd,
      "events":out_events,
      "confirmation_2025_accessed":False,
      "final_holdout_2026_accessed":False,
      "live_trading":False,"exchange_mutation":False
    }
    rec["receipt_sha256"]=hashlib.sha256(json.dumps(rec,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    out=Path(f"arq002_csp002_discovery_{args.month}.json")
    out.write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
      "month":args.month,"classification":rec["classification"],
      "A":ab["A"],"B":ab["B"],"C":ab["C"],"D":ab["D"],
      "source_masked_sweep_events":masked_oi,
      "event_rows":len(out_events),"receipt_sha256":rec["receipt_sha256"]
    },sort_keys=True))

if __name__=="__main__": raise SystemExit(main())
