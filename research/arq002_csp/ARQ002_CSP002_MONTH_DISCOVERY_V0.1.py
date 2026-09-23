#!/usr/bin/env python3
"""ARQ-002-CSP-002 frozen monthly Discovery materializer.

Economic rules are frozen in ARQ002_CSP002_SOURCE_MASKED_AUTHORITY_V0.1
and the CSP-001 economic authority it inherits.
"""
from __future__ import annotations
import argparse,bisect,csv,hashlib,io,json,math,re,sys,time,urllib.request,zipfile,calendar
from collections import defaultdict
from datetime import datetime,timezone,date,timedelta
from pathlib import Path

BASE="https://data.binance.vision/data/futures/um"
SYMBOL="BTCUSDT"
UA="Crypto-Lab-ARQ002-CSP002-Discovery/0.1"
UTC=timezone.utc
MASKED={"2024-02-16","2024-10-28"}
WARMUP_DATE="2023-12-31"
END_2024_MS=int(datetime(2025,1,1,tzinfo=UTC).timestamp()*1000)

METRICS_REQUIRED={"create_time","symbol","sum_open_interest","sum_open_interest_value",
"count_toptrader_long_short_ratio","sum_toptrader_long_short_ratio","count_long_short_ratio","sum_taker_long_short_vol_ratio"}
FUND_TIME=("calc_time","fundingTime","funding_time")
FUND_RATE=("last_funding_rate","fundingRate","funding_rate")

class FrozenError(RuntimeError):pass

def sha(b):return hashlib.sha256(b).hexdigest()
def req(u,attempts=5):
    last=None
    for i in range(attempts):
        try:
            r=urllib.request.Request(u,headers={"User-Agent":UA})
            with urllib.request.urlopen(r,timeout=120) as x:return x.read()
        except Exception as e:
            last=e
            if i+1<attempts:time.sleep(min(8,1.5*(i+1)))
    raise FrozenError(f"DOWNLOAD_FAILED:{u}:{type(last).__name__}:{last}")
def published(u):
    t=req(u+".CHECKSUM").decode("utf-8","replace")
    m=re.search(r"(?i)\b([0-9a-f]{64})\b",t)
    if not m:raise FrozenError(f"CHECKSUM_PARSE:{u}")
    return m.group(1).lower()
def download_bound(u,expected):
    b=req(u); actual=sha(b); pub=published(u)
    if actual!=pub:raise FrozenError(f"PUBLISHED_CHECKSUM_MISMATCH:{u}")
    if actual!=expected:raise FrozenError(f"SOURCE_PROVENANCE_DRIFT:{u}:{actual}:{expected}")
    return b

def csv_rows(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        bad=z.testzip()
        if bad:raise FrozenError(f"ZIP_CRC:{bad}")
        ns=[n for n in z.namelist() if n.lower().endswith(".csv") and not n.endswith("/")]
        if len(ns)!=1:raise FrozenError(f"ZIP_CSV_COUNT:{len(ns)}")
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

def dstr(tms):return datetime.fromtimestamp(tms/1000,tz=UTC).date().isoformat()
def month_prev(ym):
    y,m=map(int,ym.split("-"))
    return f"{y-1:04d}-12" if m==1 else f"{y:04d}-{m-1:02d}"
def month_next(ym):
    y,m=map(int,ym.split("-"))
    return f"{y+1:04d}-01" if m==12 else f"{y:04d}-{m+1:02d}"

def day_entry(manifest,ds):
    if ds==WARMUP_DATE:return manifest["warmup"]
    return manifest["days"].get(ds)

def eligible_2024(manifest,ds):
    v=manifest["days"].get(ds)
    return bool(v and v["source_eligible"])

def kline_url(ds):return f"{BASE}/daily/klines/{SYMBOL}/1m/{SYMBOL}-1m-{ds}.zip"
def metrics_url(ds):return f"{BASE}/daily/metrics/{SYMBOL}/{SYMBOL}-metrics-{ds}.zip"
def agg_url(ds):return f"{BASE}/daily/aggTrades/{SYMBOL}/{SYMBOL}-aggTrades-{ds}.zip"
def funding_url(ym):return f"{BASE}/monthly/fundingRate/{SYMBOL}/{SYMBOL}-fundingRate-{ym}.zip"

def parse_kline(raw,ds):
    rs=csv_rows(raw);body=rs
    try:ms(rs[0][0])
    except Exception:body=rs[1:]
    out={}
    for r in body:
        if len(r)<6:raise FrozenError(f"KLINE_WIDTH:{ds}")
        t=ms(r[0]); vals=tuple(float(r[i]) for i in (1,2,3,4))
        if not all(math.isfinite(x) and x>0 for x in vals):raise FrozenError(f"KLINE_VALUE:{ds}:{t}")
        out[t]=vals # open,high,low,close
    lo=int(datetime.fromisoformat(ds).replace(tzinfo=UTC).timestamp()*1000)
    exp=[lo+i*60000 for i in range(1440)]
    if sorted(out)!=exp:raise FrozenError(f"KLINE_GRID:{ds}:{len(out)}")
    return out

def parse_metrics(raw,ds):
    rs=csv_rows(raw);h=[x.strip() for x in rs[0]]
    if not METRICS_REQUIRED.issubset(set(h)):raise FrozenError(f"METRICS_SCHEMA:{ds}")
    ti=h.index("create_time");oi=h.index("sum_open_interest");si=h.index("symbol")
    groups={}
    for r in rs[1:]:
        if r[si].strip()!=SYMBOL:raise FrozenError(f"METRICS_SYMBOL:{ds}")
        groups.setdefault(ms(r[ti]),[]).append(r)
    out={}
    for t,g in groups.items():
        u={tuple(r) for r in g}
        if len(u)!=1:raise FrozenError(f"METRICS_CONFLICT:{ds}:{t}")
        val=float(g[0][oi])
        if not math.isfinite(val) or val<=0:raise FrozenError(f"OI_VALUE:{ds}:{t}")
        out[t]=val
    lo=int(datetime.fromisoformat(ds).replace(tzinfo=UTC).timestamp()*1000)
    exp=[lo+i*300000 for i in range(288)]
    if sorted(out)!=exp:raise FrozenError(f"METRICS_GRID:{ds}:{len(out)}")
    return out

def find_alias(h,aliases):
    for a in aliases:
        if a in h:return h.index(a)
    raise FrozenError(f"ALIAS_MISSING:{aliases}")

def parse_funding(raw,ym):
    rs=csv_rows(raw);h=[x.strip() for x in rs[0]]
    ti=find_alias(h,FUND_TIME);ri=find_alias(h,FUND_RATE)
    out=[]
    for r in rs[1:]:
        t=ms(r[ti]);v=float(r[ri])
        if not math.isfinite(v):raise FrozenError(f"FUND_VALUE:{ym}:{t}")
        if dstr(t) in MASKED:continue
        if t>=END_2024_MS:continue
        out.append((t,v))
    out.sort()
    if len({t for t,_ in out})!=len(out):raise FrozenError(f"FUND_DUP:{ym}")
    return out

def parse_agg_cvd(raw,ds):
    # Stream from archive to avoid holding millions of trades.
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        bad=z.testzip()
        if bad:raise FrozenError(f"AGG_ZIP_CRC:{ds}:{bad}")
        ns=[n for n in z.namelist() if n.lower().endswith(".csv")]
        if len(ns)!=1:raise FrozenError(f"AGG_CSV_COUNT:{ds}")
        fh=io.TextIOWrapper(z.open(ns[0]),encoding="utf-8-sig",newline="")
        rd=csv.reader(fh)
        signed=defaultdict(float);total=defaultdict(float)
        first=True
        for r in rd:
            if not r:continue
            if first:
                first=False
                try:int(float(r[0]))
                except Exception:continue
            if len(r)<7:raise FrozenError(f"AGG_WIDTH:{ds}")
            p=float(r[1]);q=float(r[2]);t=ms(r[5]);bm=r[6].strip().lower()
            if not (math.isfinite(p) and p>0 and math.isfinite(q) and q>0):raise FrozenError(f"AGG_VALUE:{ds}")
            if bm not in {"true","false"}:raise FrozenError(f"AGG_BM:{ds}")
            notion=p*q;minute=(t//60000)*60000
            s=-notion if bm=="true" else notion
            signed[minute]+=s;total[minute]+=notion
        fh.close()
    return {t:signed[t]/total[t] for t in total if total[t]>0}

def get_day_bytes(manifest,ds,kind):
    ent=day_entry(manifest,ds)
    if ent is None:raise FrozenError(f"NO_MANIFEST_DAY:{ds}")
    key={"kline":"kline_sha256","metrics":"metrics_sha256","agg":"agg_sha256"}[kind]
    if key not in ent:raise FrozenError(f"NO_MANIFEST_HASH:{ds}:{kind}")
    u={"kline":kline_url(ds),"metrics":metrics_url(ds),"agg":agg_url(ds)}[kind]
    return download_bound(u,ent[key])

def source_allowed_reference(manifest,tms):
    ds=dstr(tms)
    return ds==WARMUP_DATE or eligible_2024(manifest,ds)
def source_allowed_event(manifest,tms):
    ds=dstr(tms)
    return eligible_2024(manifest,ds)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--month",required=True)
    ap.add_argument("--manifest",required=True)
    args=ap.parse_args()
    ym=args.month
    if not ym.startswith("2024-"):raise SystemExit("2024 only")
    manifest=json.loads(Path(args.manifest).read_text())
    if manifest.get("manifest_sha256")!="67058b6e4575f1a3a442c05cf4a57a66e354ee058848aa9b10caaa0648cf36ea":
        raise FrozenError(f"MANIFEST_BINDING:{manifest.get('manifest_sha256')}")
    copied=dict(manifest);given=copied.pop("manifest_sha256",None)
    calc=hashlib.sha256(json.dumps(copied,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    if given!=calc:raise FrozenError(f"MANIFEST_HASH_INTERNAL:{given}:{calc}")
    if manifest["source_mask_receipt_sha256"]!="5d4bc118faf14234465dbcf124b895f16224f847c828651faa08f081c5602b18":
        raise FrozenError("SOURCE_MASK_BINDING")

    y,m=map(int,ym.split("-"))
    first=date(y,m,1);last=date(y,m,calendar.monthrange(y,m)[1])
    event_days=[first+timedelta(days=i) for i in range((last-first).days+1)]

    # Context dates: current month eligible days plus one day on each side when admissible.
    context=set()
    for d in event_days:
        ds=d.isoformat()
        if not eligible_2024(manifest,ds):continue
        context.add(ds)
        for off in (-1,1):
            nd=d+timedelta(days=off);nds=nd.isoformat()
            if nds==WARMUP_DATE or eligible_2024(manifest,nds):context.add(nds)

    klines={};metrics={}
    for ds in sorted(context):
        klines.update(parse_kline(get_day_bytes(manifest,ds,"kline"),ds))
        # Metrics are needed for event OI and exact adjacency. Warmup allowed.
        metrics.update(parse_metrics(get_day_bytes(manifest,ds,"metrics"),ds))

    # Funding current/previous/next month as needed, bound to census hashes.
    fmonths=[]
    for fm in (month_prev(ym),ym,month_next(ym)):
        if fm=="2025-01":continue
        if fm=="2023-12":
            exp=manifest["warmup"]["funding_sha256"]
        else:
            ent=manifest["months"].get(fm)
            if not ent:continue
            exp=ent["funding_sha256"]
        fmonths+=parse_funding(download_bound(funding_url(fm),exp),fm)
    fmonths=sorted({t:v for t,v in fmonths}.items())
    fund_ts=[t for t,_ in fmonths]; fund_val=[v for _,v in fmonths]

    outpath=Path(f"ARQ002_CSP002_OBS_{ym}.csv")
    fields=["event_ts_ms","utc_date","month","side","direction","B_cvd","C_oi","D_full",
            "cvd_ratio","oi_change","funding_rate","gross","net10","net14","net20"]
    counts={"baseline_A":0,"B":0,"C":0,"D":0,"ambiguous":0,"cvd_ineligible":0}
    h=hashlib.sha256()

    with outpath.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for d in event_days:
            ds=d.isoformat()
            if not eligible_2024(manifest,ds):continue
            # Economic aggTrades are parsed only for eligible event days.
            cvd=parse_agg_cvd(get_day_bytes(manifest,ds,"agg"),ds)
            day0=int(datetime(d.year,d.month,d.day,tzinfo=UTC).timestamp()*1000)
            for i in range(1440):
                t=day0+i*60000
                # Hard continuity: ref/event/outcome cannot touch masked/protected dates.
                ref_ts=[t-j*60000 for j in range(30,0,-1)]
                out_ts=[t+j*60000 for j in range(1,6)]
                if not all(source_allowed_reference(manifest,x) for x in ref_ts):continue
                if not source_allowed_event(manifest,t):continue
                if not all(source_allowed_event(manifest,x) for x in out_ts):continue
                needed=ref_ts+[t]+out_ts
                if any(x not in klines for x in needed):raise FrozenError(f"KLINE_CONTEXT_MISSING:{t}")

                H=max(klines[x][1] for x in ref_ts);L=min(klines[x][2] for x in ref_ts)
                op,hi,lo,cl=klines[t]
                high=hi>H and cl<H
                low=lo<L and cl>L
                if high and low:
                    counts["ambiguous"]+=1;continue
                if not high and not low:continue
                direction=-1 if high else 1
                side="HIGH_SHORT" if high else "LOW_LONG"
                counts["baseline_A"]+=1

                ratio=cvd.get(t)
                if ratio is None or not math.isfinite(ratio):
                    counts["cvd_ineligible"]+=1
                    B=False
                else:
                    B=(ratio>0) if high else (ratio<0)
                counts["B"]+=int(B)

                E=t+60000
                now=(E//300000)*300000;prev=now-300000
                oi_change=None;oi_ok=False
                if source_allowed_reference(manifest,now) and source_allowed_reference(manifest,prev) and now in metrics and prev in metrics:
                    oi_change=math.log(metrics[now]/metrics[prev])
                    oi_ok=math.isfinite(oi_change) and oi_change>0
                C=bool(B and oi_ok);counts["C"]+=int(C)

                fr=None;fund_ok=False
                ix=bisect.bisect_right(fund_ts,E)-1
                if ix>=0:
                    ft=fund_ts[ix];fv=fund_val[ix]
                    if 0<=E-ft<=8*3600000+5*60000 and dstr(ft) not in MASKED:
                        fr=fv
                        fund_ok=(fv>0) if high else (fv<0)
                D=bool(C and fund_ok);counts["D"]+=int(D)

                entry=klines[t+60000][0];exitp=klines[t+5*60000][3]
                gross=direction*math.log(exitp/entry)
                row={
                    "event_ts_ms":t,"utc_date":ds,"month":ym,"side":side,"direction":direction,
                    "B_cvd":int(B),"C_oi":int(C),"D_full":int(D),
                    "cvd_ratio":"" if ratio is None else f"{ratio:.17g}",
                    "oi_change":"" if oi_change is None else f"{oi_change:.17g}",
                    "funding_rate":"" if fr is None else f"{fr:.17g}",
                    "gross":f"{gross:.17g}","net10":f"{gross-0.0010:.17g}",
                    "net14":f"{gross-0.0014:.17g}","net20":f"{gross-0.0020:.17g}",
                }
                w.writerow(row)
    obs_sha=hashlib.sha256(outpath.read_bytes()).hexdigest()
    receipt={
        "lab_id":"ARQ-002-CSP-002","month":ym,"classification":"MONTH_OBSERVATIONS_MATERIALIZED",
        "source_manifest_sha256":given,"source_mask_receipt_sha256":manifest["source_mask_receipt_sha256"],
        "counts":counts,"observation_file":outpath.name,"observation_sha256":obs_sha,
        "masked_days":manifest["masked_days"],"protected_2025_accessed":False,"protected_2026_accessed":False,
        "live_trading":False,"exchange_mutation":False
    }
    receipt["receipt_sha256"]=hashlib.sha256(json.dumps(receipt,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    Path(f"ARQ002_CSP002_MONTH_{ym}_RECEIPT.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"month":ym,"classification":receipt["classification"],"counts":counts,
                      "observation_sha256":obs_sha,"receipt_sha256":receipt["receipt_sha256"]},sort_keys=True))
    return 0

if __name__=="__main__":raise SystemExit(main())
