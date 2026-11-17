#!/usr/bin/env python3
import bisect, heapq, json, statistics, sys, urllib.request, zipfile
from pathlib import Path

from research.microstructure_scalping.l2_replay import L2Replay
from research.microstructure_scalping.partition_guard_v01 import authorize_date

DATE="2023-01-18"
URL="https://quote-saver.bycsi.com/orderbook/linear/BTCUSDT/2023-01-18_BTCUSDT_ob500.data.zip"
MAX_MESSAGES=250_000
ANCHOR_MS=1000
COOLDOWN_MS=5000
PCTS=(0.90,0.95,0.99)
HORIZONS=(1000,5000,15000,30000)
UA={"User-Agent":"Mozilla/5.0 Crypto-Lab-LVAC001/0.1"}

def qtile(xs,p):
    s=sorted(xs); return s[int((len(s)-1)*p)]

def depths(replay,n=10):
    tb=heapq.nlargest(n,replay.bids.items(),key=lambda x:x[0])
    ta=heapq.nsmallest(n,replay.asks.items(),key=lambda x:x[0])
    b=sum(q for _,q in tb); a=sum(q for _,q in ta)
    total=b+a
    imb=(b-a)/total if total else 0.0
    return b,a,imb

def taker_gross(anchor,future,d):
    if d>0:
        return (future["bid"]-anchor["ask"])/anchor["ask"]*10000.0
    return (anchor["bid"]-future["ask"])/anchor["bid"]*10000.0

def maker_maker_ceiling(anchor,future,d):
    if d>0:
        return (future["ask"]-anchor["bid"])/anchor["bid"]*10000.0
    return (anchor["ask"]-future["bid"])/anchor["ask"]*10000.0

def main():
    authorize_date(DATE,"DISCOVERY")
    p=Path("/tmp/lvac_l2.zip")
    req=urllib.request.Request(URL,headers=UA)
    with urllib.request.urlopen(req,timeout=90) as resp,p.open("wb") as f:
        while True:
            c=resp.read(1024*1024)
            if not c: break
            f.write(c)

    replay=L2Replay(); times=[]; bids=[]; asks=[]; anchors=[]
    last_anchor=None; prev_depth=None
    with zipfile.ZipFile(p) as zf:
        if zf.testzip() is not None: raise RuntimeError("CRC_FAIL")
        name=[n for n in zf.namelist() if not n.endswith("/")][0]
        with zf.open(name) as fh:
            for i,raw in enumerate(fh):
                if i>=MAX_MESSAGES: break
                m=json.loads(raw)
                st=replay.apply(m,compute_depth_features=False)
                t=st.cts if st.cts is not None else st.ts
                times.append(t); bids.append(st.best_bid); asks.append(st.best_ask)
                if last_anchor is not None and t-last_anchor<ANCHOR_MS:
                    continue
                bd,ad,imb=depths(replay,10)
                if prev_depth is not None:
                    pbd,pad=prev_depth
                    bdep=max(0.0,(pbd-bd)/pbd) if pbd>0 else 0.0
                    adep=max(0.0,(pad-ad)/pad) if pad>0 else 0.0
                    d=1 if adep>bdep else (-1 if bdep>adep else 0)
                    strength=max(adep,bdep)
                    anchors.append({"t":t,"bid":st.best_bid,"ask":st.best_ask,
                                    "imbalance_l10":imb,"bid_depletion":bdep,
                                    "ask_depletion":adep,"direction":d,"strength":strength})
                prev_depth=(bd,ad); last_anchor=t

    strengths=[a["strength"] for a in anchors if a["direction"]!=0]
    thresholds={str(int(p*100)):qtile(strengths,p) for p in PCTS}
    result={"status":"LVAC_001_DISCOVERY_MVE","date":DATE,"l2_states":len(times),
            "anchors":len(anchors),"thresholds":thresholds,
            "oos_2025_opened":False,"holdout_2026_opened":False,
            "variants":{},"survivors":[]}

    for variant in ("depletion_only","depletion_plus_l10_confirm"):
        vr={}
        for label,thr in thresholds.items():
            cand=[]
            last_selected=None
            for a in anchors:
                if a["direction"]==0 or a["strength"]<thr: continue
                if variant=="depletion_plus_l10_confirm" and a["direction"]*a["imbalance_l10"]<=0:
                    continue
                if last_selected is not None and a["t"]-last_selected<COOLDOWN_MS:
                    continue
                cand.append(a); last_selected=a["t"]
            hr={}
            for h in HORIZONS:
                mid=[]; tg=[]; mm=[]
                for a in cand:
                    j=bisect.bisect_left(times,a["t"]+h)
                    if j>=len(times): continue
                    future={"bid":bids[j],"ask":asks[j]}
                    fmid=(future["bid"]+future["ask"])/2
                    amid=(a["bid"]+a["ask"])/2
                    mid.append(a["direction"]*(fmid-amid)/amid*10000.0)
                    tg.append(taker_gross(a,future,a["direction"]))
                    mm.append(maker_maker_ceiling(a,future,a["direction"]))
                rec={"n":len(mm),
                     "mean_directional_mid_bps":statistics.fmean(mid) if mid else None,
                     "mean_taker_gross_bps":statistics.fmean(tg) if tg else None,
                     "mean_mexc_taker_net_bps":statistics.fmean(tg)-16.0 if tg else None,
                     "mean_maker_maker_ceiling_gross_bps":statistics.fmean(mm) if mm else None,
                     "mean_mexc_maker_maker_ceiling_net_bps":statistics.fmean(mm)-12.0 if mm else None,
                     "p95_maker_maker_ceiling_gross_bps":qtile(mm,.95) if mm else None}
                if rec["n"]>=50 and rec["mean_mexc_maker_maker_ceiling_net_bps"]>0:
                    result["survivors"].append({"variant":variant,"percentile":label,"horizon_ms":h,
                                                "n":rec["n"],"mean_net_bps":rec["mean_mexc_maker_maker_ceiling_net_bps"]})
                hr[str(h)]=rec
            vr[label]=hr
        result["variants"][variant]=vr

    result["decision"]="CEILING_SURVIVOR_EXISTS" if result["survivors"] else "LVAC_001_MEXC_ECONOMIC_CEILING_FAIL_SAMPLE"
    out=Path("research/microstructure_scalping/receipts"); out.mkdir(parents=True,exist_ok=True)
    (out/"lvac001_ceiling_mve_v01.json").write_text(json.dumps(result,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    sys.exit(main())
