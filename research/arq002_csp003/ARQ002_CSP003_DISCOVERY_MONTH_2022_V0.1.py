#!/usr/bin/env python3
"""ARQ-002-CSP-003 frozen 2022 Discovery monthly shard."""
from __future__ import annotations
import argparse,csv,hashlib,io,json,math,re,time,urllib.request,zipfile,calendar
from bisect import bisect_right
from datetime import datetime,timezone,date,timedelta
from pathlib import Path

BASE="https://data.binance.vision/data/futures/um"; SYMBOL="BTCUSDT"; UTC=timezone.utc
UA="Crypto-Lab-ARQ002-CSP003-Discovery/0.1"
SOURCE=Path("research/arq002_csp003/ARQ002_CSP003_SOURCE_CLOSEOUT_V0.1.json")
COST_LOW=0.0010; COST_BASE=0.0014; COST_STRESS=0.0020
LIGHT_RECEIPT="45c9ab2c9fd6803738bcc85854df2efdd3e0be2ff7cc96c2e27dd106551f9817"
AGG_RECEIPT="634e61249cb73734ff9174a2d3182df219b5b0610ee4471afa0a8dcc47172579"
WARM_RECEIPT="99cb50dcb0d08bed6bf38ef153db9dbbdc2957a8b26a7fd911b7df550351eea5"
FUND_TIME=("calc_time","fundingTime","funding_time"); FUND_RATE=("last_funding_rate","fundingRate","funding_rate")
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
def cs(u):
    s=req(u+".CHECKSUM").decode("utf-8","replace");m=re.search(r"(?i)\b([0-9a-f]{64})\b",s)
    if not m:raise E(f"CHECKSUM_PARSE:{u}")
    return m.group(1).lower()
def verified(u):
    raw=req(u);pub=cs(u);act=hashlib.sha256(raw).hexdigest()
    if act!=pub:raise E(f"CHECKSUM:{u}")
    return raw
def rows(raw,u):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        bad=z.testzip()
        if bad:raise E(f"ZIP_CRC:{u}:{bad}")
        ns=[n for n in z.namelist() if n.lower().endswith(".csv") and not n.endswith("/")]
        if len(ns)!=1:raise E(f"CSV_COUNT:{u}:{len(ns)}")
        txt=z.read(ns[0]).decode("utf-8-sig")
    return [r for r in csv.reader(io.StringIO(txt)) if r]
def ms(v):
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
def iso(t):return datetime.fromtimestamp(t/1000,tz=UTC).isoformat().replace("+00:00","Z")
def day0(d):return int(datetime(d.year,d.month,d.day,tzinfo=UTC).timestamp()*1000)
def days(y,m):return [date(y,m,d) for d in range(1,calendar.monthrange(y,m)[1]+1)]
def load_kline(d):
    ds=d.isoformat();u=f"{BASE}/daily/klines/{SYMBOL}/1m/{SYMBOL}-1m-{ds}.zip"
    rr=rows(verified(u),u);body=rr
    try:ms(rr[0][0])
    except Exception:body=rr[1:]
    out={}
    for r in body:
        if len(r)<12:raise E(f"KLINE_WIDTH:{ds}")
        t=ms(r[0]);v=tuple(float(r[i]) for i in (1,2,3,4))
        if not all(math.isfinite(x) and x>0 for x in v):raise E(f"KLINE_VALUE:{ds}:{t}")
        out[t]=v
    exp=[day0(d)+i*60000 for i in range(1440)]
    if sorted(out)!=exp:raise E(f"KLINE_GRID:{ds}:{len(out)}")
    return out

def load_metrics(d):
    ds=d.isoformat();u=f"{BASE}/daily/metrics/{SYMBOL}/{SYMBOL}-metrics-{ds}.zip"
    rr=rows(verified(u),u);h=[x.strip() for x in rr[0]]
    ti=h.index("create_time");oi=h.index("sum_open_interest");si=h.index("symbol")
    groups={}
    for r in rr[1:]:
        if r[si].strip()!=SYMBOL:raise E(f"MET_SYMBOL:{ds}")
        groups.setdefault(ms(r[ti]),[]).append(r)
    valid={};invalid=[];observed=set()
    lo=day0(d);exp={lo+i*300000 for i in range(288)}
    for t,rs in groups.items():
        if t not in exp:raise E(f"MET_OFFGRID:{ds}:{t}")
        if len({tuple(x) for x in rs})!=1:raise E(f"MET_CONFLICT:{ds}:{t}")
        observed.add(t);rawv=rs[0][oi].strip();reason=None
        try:
            v=float(rawv)
            if not math.isfinite(v):reason="NONFINITE"
            elif v<=0:reason="NONPOSITIVE"
        except Exception:reason="NONNUMERIC"
        if reason:invalid.append({"reason":reason,"timestamp_utc":iso(t)})
        else:valid[t]=v
    missing=[iso(t) for t in sorted(exp-observed)]
    return valid,invalid,missing

def alias(h,names):
    for n in names:
        if n in h:return h.index(n)
    raise E(f"ALIAS:{names}:{h}")
def load_funding(y,m):
    ym=f"{y:04d}-{m:02d}";u=f"{BASE}/monthly/fundingRate/{SYMBOL}/{SYMBOL}-fundingRate-{ym}.zip"
    rr=rows(verified(u),u);h=[x.strip() for x in rr[0]];ti=alias(h,FUND_TIME);ri=alias(h,FUND_RATE)
    out={}
    for r in rr[1:]:
        t=ms(r[ti]);v=float(r[ri])
        if not math.isfinite(v):raise E(f"FUND_VALUE:{ym}:{t}")
        if t in out:raise E(f"FUND_DUP:{ym}:{t}")
        out[t]=v
    return out

def load_agg(d,candidates):
    ds=d.isoformat();u=f"{BASE}/daily/aggTrades/{SYMBOL}/{SYMBOL}-aggTrades-{ds}.zip";raw=verified(u)
    signed={t:0.0 for t in candidates};total={t:0.0 for t in candidates}
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        ns=[n for n in z.namelist() if n.lower().endswith(".csv") and not n.endswith("/")]
        if len(ns)!=1:raise E(f"AGG_CSV:{ds}")
        fh=io.TextIOWrapper(z.open(ns[0]),encoding="utf-8-sig",newline="");rd=csv.reader(fh)
        first=True;prev=None
        for r in rd:
            if not r:continue
            if first:
                first=False
                try:int(float(r[0]))
                except Exception:continue
            aid=int(float(r[0]))
            if prev is not None and aid<=prev:raise E(f"AGG_ID:{ds}")
            prev=aid;t=ms(r[5]);minute=(t//60000)*60000
            if minute not in signed:continue
            px=float(r[1]);qty=float(r[2]);bm=r[6].strip().lower()
            if not (math.isfinite(px) and px>0 and math.isfinite(qty) and qty>0):raise E(f"AGG_VALUE:{ds}:{aid}")
            if bm not in {"true","false"}:raise E(f"AGG_SIDE:{ds}:{aid}")
            n=px*qty;total[minute]+=n;signed[minute]+=(-n if bm=="true" else n)
        fh.close()
    return {t:(signed[t],total[t]) for t in candidates}

def latest_funding(f,ts,e):
    i=bisect_right(ts,e)-1
    if i<0:return None
    t=ts[i]
    if e-t>8*3600000+5*60000:return None
    return f[t]

def guard():
    if not SOURCE.exists():raise E("SOURCE_CLOSEOUT_MISSING")
    s=json.loads(SOURCE.read_text())
    if s.get("lab_id")!="ARQ-002-CSP-003" or s.get("classification")!="SOURCE_CENSUS_PASS":raise E("SOURCE_NOT_PASS")
    if s["light_source"]["receipt_sha256"]!=LIGHT_RECEIPT:raise E("LIGHT_BIND")
    if s["aggtrades_source"]["receipt_sha256"]!=AGG_RECEIPT:raise E("AGG_BIND")
    if s["warmup_source"]["receipt_sha256"]!=WARM_RECEIPT:raise E("WARM_BIND")
    if any(s["firewalls"].get(k) is not False for k in ["economic_values_opened","outcomes_opened","protected_2025_accessed","protected_2026_accessed"]):raise E("SOURCE_FIREWALL")
    return s

def main():
    source=guard()
    ap=argparse.ArgumentParser();ap.add_argument("--month",required=True);a=ap.parse_args()
    y,m=map(int,a.month.split("-"))
    if y!=2022:raise SystemExit("2022 only")
    ds=days(y,m);first,last=ds[0],ds[-1]
    kdays=[first-timedelta(days=1)]+ds+([] if last==date(2022,12,31) else [last+timedelta(days=1)])
    mdays=[first-timedelta(days=1)]+ds
    kl={};metrics={};current_invalid=[];current_missing=[]
    for d in kdays:kl.update(load_kline(d))
    for d in mdays:
        v,inv,mis=load_metrics(d);metrics.update(v)
        if d.year==2022 and d.month==m:
            current_invalid+=inv;current_missing+=mis

    frozen=source["light_source"]["mask_by_month"][a.month]
    inv_sorted=sorted(current_invalid,key=lambda x:(x["timestamp_utc"],x["reason"]))
    inv_sha=hashlib.sha256(json.dumps(inv_sorted,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    mis_sorted=sorted(current_missing)
    mis_sha=hashlib.sha256(json.dumps(mis_sorted,separators=(",",":")).encode()).hexdigest()
    if len(inv_sorted)!=frozen["invalid_count"] or inv_sha!=frozen["invalid_mask_sha256"]:raise E(f"INVALID_MASK_DRIFT:{a.month}")
    if len(mis_sorted)!=frozen["missing_count"] or mis_sha!=frozen["missing_mask_sha256"]:raise E(f"MISSING_MASK_DRIFT:{a.month}")

    pm=first.replace(day=1)-timedelta(days=1)
    fund={};fund.update(load_funding(pm.year,pm.month));fund.update(load_funding(y,m));fts=sorted(fund)

    cand_by_day={d:[] for d in ds};cand={};masked=amb=0
    for d in ds:
        lo=day0(d)
        for i in range(1440):
            t=lo+i*60000
            if t+5*60000 not in kl:continue
            refs=[kl.get(t-j*60000) for j in range(1,31)]
            if any(x is None for x in refs):continue
            cur=kl[t];h30=max(x[1] for x in refs);l30=min(x[2] for x in refs)
            hs=cur[1]>h30 and cur[3]<h30;ls=cur[2]<l30 and cur[3]>l30
            if hs and ls:amb+=1;continue
            if not hs and not ls:continue
            direction=-1 if hs else 1;e=t+60000;now=(e//300000)*300000;prev=now-300000
            if now not in metrics or prev not in metrics:masked+=1;continue
            cand[t]={"direction":direction,"now":metrics[now],"prev":metrics[prev]};cand_by_day[d].append(t)

    cvd={}
    for d in ds:
        if cand_by_day[d]:cvd.update(load_agg(d,set(cand_by_day[d])))

    ev=[];ab={"A":0,"B":0,"C":0,"D":0};nocvd=0
    for t in sorted(cand):
        c=cand[t];direction=c["direction"];signed,total=cvd.get(t,(0.0,0.0))
        if total<=0:nocvd+=1;continue
        ratio=signed/total;b=(ratio>0 if direction<0 else ratio<0)
        oich=math.log(c["now"]/c["prev"]);cc=b and oich>0
        e=t+60000;fv=latest_funding(fund,fts,e);fundok=False
        if fv is not None:fundok=(fv>0 if direction<0 else fv<0)
        dd=cc and fundok
        ab["A"]+=1;ab["B"]+=int(b);ab["C"]+=int(cc);ab["D"]+=int(dd)
        entry=kl[t+60000][0];exitp=kl[t+5*60000][3];gross=direction*math.log(exitp/entry)
        ev.append({"event_ts_ms":t,"event_utc":iso(t),"utc_day":datetime.fromtimestamp(t/1000,tz=UTC).date().isoformat(),
          "month":a.month,"direction":"LONG" if direction>0 else "SHORT","d_confirmed":dd,
          "gross":gross,"low10":gross-COST_LOW,"base14":gross-COST_BASE,"stress20":gross-COST_STRESS})

    rec={"lab_id":"ARQ-002-CSP-003","month":a.month,"classification":"DISCOVERY_MONTH_COMPLETE",
      "source_light_receipt_sha256":LIGHT_RECEIPT,"source_agg_receipt_sha256":AGG_RECEIPT,
      "invalid_mask_sha256":inv_sha,"missing_mask_sha256":mis_sha,"source_mask_drift":False,
      "ablation_counts":ab,"source_masked_sweep_events":masked,"ambiguous_both_sides":amb,
      "no_cvd_notional_events":nocvd,"events":ev,
      "replication_2023_accessed":False,"year_2024_scored":False,"protected_2025_accessed":False,
      "protected_2026_accessed":False,"live_trading":False,"exchange_mutation":False}
    rec["receipt_sha256"]=hashlib.sha256(json.dumps(rec,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    p=Path(f"arq002_csp003_discovery_{a.month}.json");p.write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"month":a.month,"classification":rec["classification"],"A":ab["A"],"B":ab["B"],"C":ab["C"],"D":ab["D"],
      "masked":masked,"events":len(ev),"receipt_sha256":rec["receipt_sha256"]},sort_keys=True))
if __name__=="__main__":raise SystemExit(main())
