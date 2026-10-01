#!/usr/bin/env python3
from __future__ import annotations
import bisect,csv,hashlib,json,math,random,shutil,tempfile,time,urllib.request,zipfile
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path

LAB_ID="FLOW-PATH-ABSORPTION-HIST-001"
BAR_MS=300000
MINUTE_MS=60000
BASELINE=2016
COOLDOWN=12
MIN_GROUP=100
MIN_DATES=30
MIN_COVERAGE=0.99
BOOT_N=10000
BOOT_SEED=20260924
HORIZONS=(5,15,30,60,240)
BASE="https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1m"
OUT=Path("flow_path_absorption_hist/run_output")

def ms(v):
    x=int(float(v)); a=abs(x)
    if a<10**11:return x*1000
    if a<10**14:return x
    if a<10**17:return x//1000
    return x//1_000_000

def dtms(s):
    return int(datetime.fromisoformat(s.replace("Z","+00:00")).timestamp()*1000)

def months(a,b):
    y,m=map(int,a.split("-")); ey,em=map(int,b.split("-"))
    out=[]
    while (y,m)<=(ey,em):
        out.append(f"{y:04d}-{m:02d}")
        m+=1
        if m==13:y+=1;m=1
    return out

def sha256_file(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for ch in iter(lambda:f.read(1024*1024),b""):h.update(ch)
    return h.hexdigest()

def fetch(url,path):
    last=None
    for n in range(5):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-FlowPath/0.1"})
            with urllib.request.urlopen(req,timeout=60) as r, open(path,"wb") as w:
                shutil.copyfileobj(r,w,1024*1024)
            return
        except Exception as e:
            last=e;time.sleep(min(2**n,8))
    raise RuntimeError(f"download failed {url}: {last}")

def quant(sorted_vals,p):
    n=len(sorted_vals)
    if not n:return math.nan
    x=(n-1)*p;lo=int(math.floor(x));hi=int(math.ceil(x))
    if lo==hi:return sorted_vals[lo]
    w=x-lo
    return sorted_vals[lo]*(1-w)+sorted_vals[hi]*w

def remove_sorted(a,x):
    i=bisect.bisect_left(a,x)
    if i>=len(a) or a[i]!=x:raise RuntimeError("rolling quantile state mismatch")
    a.pop(i)

def finalize5(bucket):
    if len(bucket)!=5:return None
    ots=[r["open_ms"] for r in bucket]
    if any(ots[i]-ots[0]!=i*MINUTE_MS for i in range(5)):return None
    o=bucket[0]["open"];c=bucket[-1]["close"]
    vol=sum(r["volume"] for r in bucket)
    buy=sum(r["taker_buy"] for r in bucket)
    if not (vol>0 and 0<=buy<=vol):return None
    path=0.0;prev=o
    for r in bucket:
        path+=abs(r["close"]-prev);prev=r["close"]
    eff=abs(c-o)/path if path>0 else 0.0
    delta=(2*buy-vol)/vol
    bo=(ots[0]//BAR_MS)*BAR_MS
    return {"bar_open_ms":bo,"bar_close_ms":bo+BAR_MS,"open":o,"close":c,
            "agg_base_volume":vol,"agg_delta_pct":delta,
            "ltf_path_efficiency":eff,
            "bar_return_bps":(c/o-1)*10000.0}

def load_month(month,tmp,prov):
    name=f"BTCUSDT-1m-{month}.zip"
    url=f"{BASE}/{name}"
    z=tmp/name;c=tmp/(name+".CHECKSUM")
    fetch(url,z);fetch(url+".CHECKSUM",c)
    expected=c.read_text().strip().split()[0].lower()
    actual=sha256_file(z)
    if actual!=expected:raise RuntimeError(f"checksum mismatch {month}")
    prov.append({"month":month,"url":url,"zip_sha256":actual})
    out=[]
    with zipfile.ZipFile(z) as zz:
        names=zz.namelist()
        if len(names)!=1:raise RuntimeError(f"unexpected archive members {month}: {names}")
        with zz.open(names[0],"r") as raw:
            reader=csv.reader((line.decode("utf-8") for line in raw))
            cur=None;bucket=[]
            for row in reader:
                if not row or not str(row[0]).strip().lstrip("-").isdigit():continue
                if len(row)<11:raise RuntimeError(f"short kline row {month}")
                ot=ms(row[0])
                if ot%MINUTE_MS:raise RuntimeError(f"unaligned minute {ot}")
                r={"open_ms":ot,"open":float(row[1]),"close":float(row[4]),
                   "volume":float(row[5]),"taker_buy":float(row[9])}
                bo=(ot//BAR_MS)*BAR_MS
                if cur is None:cur=bo
                if bo!=cur:
                    x=finalize5(bucket)
                    if x:out.append(x)
                    bucket=[];cur=bo
                bucket.append(r)
            if bucket:
                x=finalize5(bucket)
                if x:out.append(x)
    z.unlink(missing_ok=True);c.unlink(missing_ok=True)
    return out

def load_period(month_list):
    rows=[];prov=[]
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td)
        for m in month_list:
            print(f"source {m}",flush=True)
            rows.extend(load_month(m,tmp,prov))
    rows.sort(key=lambda r:r["bar_open_ms"])
    seen=set()
    for r in rows:
        if r["bar_open_ms"] in seen:raise RuntimeError("duplicate 5m bar")
        seen.add(r["bar_open_ms"])
    return rows,prov

def classify(rows,start_ms,end_ms):
    if len(rows)<=BASELINE:return []
    vals={
      "d":sorted(abs(r["agg_delta_pct"]) for r in rows[:BASELINE]),
      "v":sorted(r["agg_base_volume"] for r in rows[:BASELINE]),
      "e":sorted(r["ltf_path_efficiency"] for r in rows[:BASELINE]),
      "r":sorted(abs(r["bar_return_bps"]) for r in rows[:BASELINE]),
    }
    out=[];cool=-1
    for i in range(BASELINE,len(rows)):
        row=rows[i]
        td=quant(vals["d"],.95);tv=quant(vals["v"],.75)
        lo=quant(vals["e"],.25);hi=quant(vals["e"],.75);tr=quant(vals["r"],.25)
        if start_ms<=row["bar_open_ms"]<end_ms:
            d=1 if row["agg_delta_pct"]>0 else -1 if row["agg_delta_pct"]<0 else 0
            extreme=d!=0 and abs(row["agg_delta_pct"])>=td and row["agg_base_volume"]>=tv
            cls="NON_EXTREME";supp=None
            if extreme:
                weak=d*row["bar_return_bps"]<=0 or abs(row["bar_return_bps"])<=tr
                cand=None
                if row["ltf_path_efficiency"]<=lo and weak:cand="FAILED_AUCTION"
                elif row["ltf_path_efficiency"]>=hi and d*row["bar_return_bps"]>0:cand="EFFICIENT_ACCEPTANCE"
                else:cls="UNCLASSIFIED_EXTREME"
                if cand:
                    if i<=cool:cls="COOLDOWN_SUPPRESSED";supp=cand
                    else:cls=cand;cool=i+COOLDOWN
            rec={**row,"direction":d,"event_class":cls,
                 "q95_abs_delta_pct":td,"q75_agg_base_volume":tv,
                 "q25_path_efficiency":lo,"q75_path_efficiency":hi,
                 "q25_abs_bar_return_bps":tr}
            if supp:rec["suppressed_candidate"]=supp
            out.append(rec)
        old=rows[i-BASELINE]
        remove_sorted(vals["d"],abs(old["agg_delta_pct"]));bisect.insort(vals["d"],abs(row["agg_delta_pct"]))
        remove_sorted(vals["v"],old["agg_base_volume"]);bisect.insort(vals["v"],row["agg_base_volume"])
        remove_sorted(vals["e"],old["ltf_path_efficiency"]);bisect.insort(vals["e"],row["ltf_path_efficiency"])
        remove_sorted(vals["r"],abs(old["bar_return_bps"]));bisect.insort(vals["r"],abs(row["bar_return_bps"]))
    return out

def add_outcomes(events,all_rows):
    idx={r["bar_open_ms"]:i for i,r in enumerate(all_rows)}
    primary=[]
    for e in events:
        if e["event_class"] not in ("FAILED_AUCTION","EFFICIENT_ACCEPTANCE"):continue
        x=dict(e);i=idx[e["bar_open_ms"]]
        for h in HORIZONS:
            j=i+h//5
            if j<len(all_rows) and all_rows[j]["bar_open_ms"]-e["bar_open_ms"]==h*60000:
                x[f"R{h}"]=e["direction"]*(all_rows[j]["close"]/e["close"]-1)*10000.0
            else:x[f"R{h}"]=None
        x["utc_date"]=datetime.fromtimestamp(e["bar_close_ms"]/1000,tz=timezone.utc).date().isoformat()
        primary.append(x)
    return primary

def median(v):
    a=sorted(v);n=len(a)
    if not n:return math.nan
    return a[n//2] if n%2 else (a[n//2-1]+a[n//2])/2

def wilson(k,n,z=1.959963984540054):
    if n<=0:return math.nan
    p=k/n;den=1+z*z/n
    cen=p+z*z/(2*n);adj=z*math.sqrt((p*(1-p)+z*z/(4*n))/n)
    return (cen-adj)/den

def boot(fa,ea):
    rng=random.Random(BOOT_SEED);d=[]
    for _ in range(BOOT_N):
        a=[fa[rng.randrange(len(fa))] for __ in range(len(fa))]
        b=[ea[rng.randrange(len(ea))] for __ in range(len(ea))]
        d.append(median(b)-median(a))
    d.sort()
    return quant(d,.025),quant(d,.975)

def adjudicate(events,source_cov):
    fa=[r for r in events if r["event_class"]=="FAILED_AUCTION"]
    ea=[r for r in events if r["event_class"]=="EFFICIENT_ACCEPTANCE"]
    dates={r["utc_date"] for r in fa+ea}
    def cov(g):
        return sum(isinstance(x.get("R60"),(int,float)) and math.isfinite(x["R60"]) for x in g)/len(g) if g else 0
    fc,ec=cov(fa),cov(ea)
    base={"lab_id":LAB_ID,"source_coverage":source_cov,"failed_auction_n":len(fa),
          "efficient_acceptance_n":len(ea),"distinct_utc_dates":len(dates),
          "failed_R60_coverage":fc,"efficient_R60_coverage":ec,"trading_authority":"NONE"}
    if source_cov<MIN_COVERAGE:return {**base,"classification":"SOURCE_BLOCKED"}
    if len(fa)<MIN_GROUP or len(ea)<MIN_GROUP or len(dates)<MIN_DATES or fc<MIN_COVERAGE or ec<MIN_COVERAGE:
        return {**base,"classification":"INSUFFICIENT_SAMPLE"}
    f=[r["R60"] for r in fa if isinstance(r.get("R60"),(int,float)) and math.isfinite(r["R60"])]
    e=[r["R60"] for r in ea if isinstance(r.get("R60"),(int,float)) and math.isfinite(r["R60"])]
    mf,me=median(f),median(e);lo,hi=boot(f,e)
    fr=sum(x<0 for x in f);er=sum(x>0 for x in e)
    frr=fr/len(f);err=er/len(e);fwl=wilson(fr,len(f));ewl=wilson(er,len(e))
    survive=mf<0 and me>0 and (me-mf)>0 and lo>0 and frr>.5 and fwl>.5 and err>.5 and ewl>.5
    return {**base,"classification":"MECHANISM_SURVIVES" if survive else "NO_MECHANISM",
      "failed_median_R60_bps":mf,"efficient_median_R60_bps":me,
      "median_contrast_R60_bps":me-mf,"bootstrap95_contrast_bps":[lo,hi],
      "failed_reversal_rate_R60":frr,"failed_reversal_wilson_lower95":fwl,
      "efficient_continuation_rate_R60":err,"efficient_continuation_wilson_lower95":ewl}

def phase(name,months_list,start,end):
    rows,prov=load_period(months_list)
    s,e=dtms(start),dtms(end)
    expected=(e-s)//BAR_MS
    inwin=[r for r in rows if s<=r["bar_open_ms"]<e]
    source_cov=len(inwin)/expected
    ev=classify(rows,s,e)
    primary=add_outcomes(ev,rows)
    report=adjudicate(primary,source_cov)
    report.update({"phase":name,"window_start":start,"window_end":end,
                   "valid_5m_bars":len(inwin),"expected_5m_bars":expected,
                   "all_class_counts":dict(sorted(__import__("collections").Counter(x["event_class"] for x in ev).items()))})
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/f"{name}_REPORT.json").write_text(json.dumps(report,indent=2,sort_keys=True,allow_nan=False)+"\n")
    (OUT/f"{name}_SOURCE_PROVENANCE.json").write_text(json.dumps(prov,indent=2,sort_keys=True)+"\n")
    fields=["bar_open_ms","bar_close_ms","utc_date","event_class","direction","agg_delta_pct","agg_base_volume",
            "ltf_path_efficiency","bar_return_bps","q95_abs_delta_pct","q75_agg_base_volume",
            "q25_path_efficiency","q75_path_efficiency","q25_abs_bar_return_bps"]+[f"R{h}" for h in HORIZONS]
    with (OUT/f"{name}_PRIMARY_EVENTS.csv").open("w",newline="") as fh:
        w=csv.DictWriter(fh,fieldnames=fields);w.writeheader()
        for r in primary:w.writerow({k:r.get(k) for k in fields})
    print(json.dumps(report,indent=2,sort_keys=True),flush=True)
    return report

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    disc_months=months("2022-12","2024-12")
    discovery=phase("DISCOVERY",disc_months,"2023-01-01T00:00:00Z","2025-01-01T00:00:00Z")
    overall={"lab_id":LAB_ID,"discovery":discovery,"trading_authority":"NONE"}
    if discovery["classification"]=="MECHANISM_SURVIVES":
        oos_months=months("2024-12","2025-12")
        oos=phase("OOS",oos_months,"2025-01-01T00:00:00Z","2026-01-01T00:00:00Z")
        overall["oos"]=oos
        overall["classification"]="OOS_REPLICATED_MECHANISM" if oos["classification"]=="MECHANISM_SURVIVES" else "OOS_FAILED"
    else:
        overall["classification"]="DISCOVERY_"+discovery["classification"]
        overall["oos_opened"]=False
    (OUT/"TERMINAL_REPORT.json").write_text(json.dumps(overall,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print("TERMINAL",json.dumps(overall,indent=2,sort_keys=True),flush=True)

if __name__=="__main__":
    main()
