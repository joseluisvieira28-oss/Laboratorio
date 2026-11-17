#!/usr/bin/env python3
import bisect,csv,gzip,heapq,json,statistics,sys,urllib.request,zipfile
from pathlib import Path

from research.microstructure_scalping.l2_replay import L2Replay
from research.microstructure_scalping.partition_guard_v01 import authorize_date
from research.microstructure_scalping.sweep_features_v01 import sweep_features

DATES=("2024-03-06","2024-06-05","2024-09-04","2024-12-04")
CAL=DATES[0]
MAX_MESSAGES=250_000
ANCHOR_MS=1000
COOLDOWN_MS=10000
HORIZONS=(5000,15000,30000,60000)
UA={"User-Agent":"Mozilla/5.0 Crypto-Lab-SWEEP-CONT-003/0.1"}


def get(url,path):
    req=urllib.request.Request(url,headers=UA)
    total=0
    with urllib.request.urlopen(req,timeout=180) as r,open(path,"wb") as f:
        while True:
            c=r.read(1024*1024)
            if not c: break
            total+=len(c); f.write(c)
    return total


def qtile(xs,p):
    if not xs:return None
    s=sorted(xs);return s[int((len(s)-1)*p)]


def top10(replay):
    b=heapq.nlargest(10,replay.bids.items(),key=lambda x:x[0])
    a=heapq.nsmallest(10,replay.asks.items(),key=lambda x:x[0])
    return sum(q for _,q in b),sum(q for _,q in a)


def build_l2(date,path):
    r=L2Replay();times=[];bids=[];asks=[];anchors=[]
    last=None;missing_cts=0
    with zipfile.ZipFile(path) as zf:
        if zf.testzip() is not None:raise RuntimeError(f"{date}:CRC_FAIL")
        names=[n for n in zf.namelist() if not n.endswith("/")]
        if len(names)!=1:raise RuntimeError(f"{date}:MEMBERS")
        with zf.open(names[0]) as fh:
            for i,raw in enumerate(fh):
                if i>=MAX_MESSAGES:break
                m=json.loads(raw);st=r.apply(m,compute_depth_features=False)
                t=st.cts if st.cts is not None else st.ts
                if st.cts is None:missing_cts+=1
                times.append(int(t));bids.append(st.best_bid);asks.append(st.best_ask)
                if last is not None and t-last<ANCHOR_MS:continue
                bd,ad=top10(r)
                anchors.append({"t":int(t),"bid":st.best_bid,"ask":st.best_ask,
                                "bid_depth":bd,"ask_depth":ad})
                last=int(t)
    if len(times)<100_000:raise RuntimeError(f"{date}:INSUFFICIENT_L2")
    return {"times":times,"bids":bids,"asks":asks,"anchors":anchors,
            "missing_cts":missing_cts}


def trades(date,path,lo,hi):
    times=[];pb=[0.0];ps=[0.0];prev=None
    with gzip.open(path,"rt",encoding="utf-8",newline="") as fh:
        for x in csv.DictReader(fh):
            t=int(round(float(x["timestamp"])*1000))
            if prev is not None and t<prev:raise RuntimeError(f"{date}:TRADE_TIME")
            prev=t
            if t<lo-61000:continue
            if t>=hi:break
            n=float(x["size"])*float(x["price"])
            times.append(t)
            pb.append(pb[-1]+(n if x["side"]=="Buy" else 0.0))
            ps.append(ps[-1]+(n if x["side"]=="Sell" else 0.0))
    if len(times)<10000:raise RuntimeError(f"{date}:INSUFFICIENT_TRADES")
    return times,pb,ps


def attach_features(l2,tt,pb,ps):
    a=l2["anchors"]
    for i in range(1,len(a)):
        cur=a[i];prev=a[i-1]
        f=sweep_features(
            cur["t"],prev["bid"],prev["ask"],prev["bid_depth"],prev["ask_depth"],
            cur["bid"],cur["ask"],cur["bid_depth"],cur["ask_depth"],
            tt,pb,ps,1000,60000)
        cur["sweep"]=f


def future(l2,t):
    j=bisect.bisect_left(l2["times"],t)
    if j>=len(l2["times"]):return None
    return {"bid":l2["bids"][j],"ask":l2["asks"][j]}


def midret(a,f,d):
    am=(a["bid"]+a["ask"])/2;fm=(f["bid"]+f["ask"])/2
    return d*(fm-am)/am*10000


def taker(a,f,d):
    if d>0:return (f["bid"]-a["ask"])/a["ask"]*10000
    return (a["bid"]-f["ask"])/a["bid"]*10000


def maker(a,f,d):
    if d>0:return (f["ask"]-a["bid"])/a["bid"]*10000
    return (a["ask"]-f["bid"])/a["ask"]*10000


def main():
    for d in DATES:authorize_date(d,"DISCOVERY")
    root=Path("/tmp/sweep_cont_003");root.mkdir(exist_ok=True)
    ds={};sources={}
    for date in DATES:
        l2u=f"https://quote-saver.bycsi.com/orderbook/linear/BTCUSDT/{date}_BTCUSDT_ob500.data.zip"
        tru=f"https://public.bybit.com/trading/BTCUSDT/BTCUSDT{date}.csv.gz"
        l2p=root/f"{date}_l2.zip";trp=root/f"{date}_tr.csv.gz"
        lb=get(l2u,l2p);tb=get(tru,trp)
        l2=build_l2(date,l2p)
        tt,pb,ps=trades(date,trp,l2["times"][0],l2["times"][-1])
        attach_features(l2,tt,pb,ps)
        ds[date]=l2
        sources[date]={"l2_bytes":lb,"trade_bytes":tb,"l2_states":len(l2["times"]),
                       "anchors":len(l2["anchors"]),"trades":len(tt),
                       "cts_coverage_rate":1-l2["missing_cts"]/len(l2["times"])}

    cal=[a["sweep"] for a in ds[CAL]["anchors"] if a.get("sweep")
         and a["sweep"]["burst_ratio"] is not None
         and a["sweep"]["displacement_bps"]>0]
    if len(cal)<100:raise RuntimeError("INSUFFICIENT_CALIBRATION_EVENTS")
    thresholds={
      "burst":{"95":qtile([x["burst_ratio"] for x in cal],.95),
               "99":qtile([x["burst_ratio"] for x in cal],.99)},
      "disp":{"90":qtile([x["displacement_bps"] for x in cal],.90),
              "95":qtile([x["displacement_bps"] for x in cal],.95)},
      "repl":{"75":qtile([x["replenishment_failure"] for x in cal],.75)}
    }
    variants={
      "A_B95_X90":("95","90",False),
      "B_B99_X90":("99","90",False),
      "C_B95_X95":("95","95",False),
      "D_B99_X95":("99","95",False),
      "E_B95_X90_R75":("95","90",True),
      "F_B99_X90_R75":("99","90",True),
    }
    result={"status":"SWEEP_CONT_003_FRESH_DISCOVERY_CEILING","dates":DATES,
            "calibration_date":CAL,"thresholds":thresholds,"sources":sources,
            "variants":{},"survivors":[],"oos_2025_opened":False,"holdout_2026_opened":False}

    for name,(bp,xp,use_r) in variants.items():
        bydate={};pool={h:{"mid":[],"tg":[],"mm":[]} for h in HORIZONS}
        for date in DATES:
            sel=[];last=None
            for a in ds[date]["anchors"]:
                f=a.get("sweep")
                if not f or f["burst_ratio"] is None:continue
                if f["burst_ratio"]<thresholds["burst"][bp]:continue
                if f["displacement_bps"]<thresholds["disp"][xp]:continue
                if use_r and f["replenishment_failure"]<thresholds["repl"]["75"]:continue
                if last is not None and a["t"]-last<COOLDOWN_MS:continue
                sel.append(a);last=a["t"]
            hr={}
            for h in HORIZONS:
                mids=[];tgs=[];mms=[]
                for a in sel:
                    f=future(ds[date],a["t"]+h)
                    if not f:continue
                    d=a["sweep"]["direction"]
                    mids.append(midret(a,f,d));tgs.append(taker(a,f,d));mms.append(maker(a,f,d))
                pool[h]["mid"].extend(mids);pool[h]["tg"].extend(tgs);pool[h]["mm"].extend(mms)
                hr[str(h)]={"n":len(mms),
                    "mean_mid_bps":statistics.fmean(mids) if mids else None,
                    "mean_mexc_taker_net_bps":statistics.fmean(tgs)-16 if tgs else None,
                    "mean_maker_ceiling_gross_bps":statistics.fmean(mms) if mms else None,
                    "mean_mexc_maker_ceiling_net_bps":statistics.fmean(mms)-12 if mms else None}
            bydate[date]=hr
        pooled={}
        for h in HORIZONS:
            mm=pool[h]["mm"];tg=pool[h]["tg"];mid=pool[h]["mid"]
            pos=sum(1 for d in DATES if bydate[d][str(h)]["n"]>0 and
                    bydate[d][str(h)]["mean_mexc_maker_ceiling_net_bps"]>0)
            rec={"n":len(mm),"date_positive_count":pos,
                 "mean_mid_bps":statistics.fmean(mid) if mid else None,
                 "mean_mexc_taker_net_bps":statistics.fmean(tg)-16 if tg else None,
                 "mean_maker_ceiling_gross_bps":statistics.fmean(mm) if mm else None,
                 "mean_mexc_maker_ceiling_net_bps":statistics.fmean(mm)-12 if mm else None,
                 "p95_maker_ceiling_gross_bps":qtile(mm,.95) if mm else None}
            if rec["n"]>=40 and rec["mean_mexc_maker_ceiling_net_bps"]>0 and pos>=3:
                result["survivors"].append({"variant":name,"horizon_ms":h,
                    "n":rec["n"],"date_positive_count":pos,
                    "mean_mexc_maker_ceiling_net_bps":rec["mean_mexc_maker_ceiling_net_bps"]})
            pooled[str(h)]=rec
        result["variants"][name]={"by_date":bydate,"pooled":pooled}

    result["decision"]="CEILING_SURVIVOR_EXISTS" if result["survivors"] else "SWEEP_CONT_003_MEXC_ECONOMIC_CEILING_FAIL"
    out=Path("research/microstructure_scalping/receipts");out.mkdir(parents=True,exist_ok=True)
    (out/"sweep_cont_003_ceiling_v01.json").write_text(json.dumps(result,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    sys.exit(main())
