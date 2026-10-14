#!/usr/bin/env python3
import bisect, csv, gzip, heapq, json, statistics, sys, urllib.request, zipfile
from pathlib import Path

from research.microstructure_scalping.l2_replay import L2Replay
from research.microstructure_scalping.partition_guard_v01 import authorize_date

DATES=("2023-04-05","2023-07-05","2023-10-04","2024-01-03")
CALIBRATION_DATE=DATES[0]
MAX_MESSAGES=250_000
ANCHOR_MS=1000
COOLDOWN_MS=5000
HORIZONS=(5000,15000,30000,60000)
FLOW_WINDOWS=(1000,5000)
DEP_PCTS=(0.90,0.95,0.99)
FLOW_PCTS=(0.75,0.90,0.95)
VARIANTS=(("90","75"),("95","75"),("95","90"),("99","90"),("99","95"))
UA={"User-Agent":"Mozilla/5.0 Crypto-Lab-LVAC-TF-002/0.1"}


def get(url,path):
    req=urllib.request.Request(url,headers=UA)
    total=0
    with urllib.request.urlopen(req,timeout=120) as r, open(path,"wb") as f:
        while True:
            c=r.read(1024*1024)
            if not c: break
            total += len(c); f.write(c)
    return total


def qtile(xs,p):
    if not xs: return None
    s=sorted(xs)
    return s[int((len(s)-1)*p)]


def top10_depths(replay):
    tb=heapq.nlargest(10,replay.bids.items(),key=lambda x:x[0])
    ta=heapq.nsmallest(10,replay.asks.items(),key=lambda x:x[0])
    return sum(q for _,q in tb),sum(q for _,q in ta)


def build_l2(date,zip_path):
    replay=L2Replay()
    times=[]; bids=[]; asks=[]; anchors=[]
    last_anchor=None; prev_depth=None
    missing_cts=0

    with zipfile.ZipFile(zip_path) as zf:
        if zf.testzip() is not None:
            raise RuntimeError(f"{date}:CRC_FAIL")
        names=[n for n in zf.namelist() if not n.endswith("/")]
        if len(names)!=1:
            raise RuntimeError(f"{date}:UNEXPECTED_MEMBERS")
        with zf.open(names[0]) as fh:
            for i,raw in enumerate(fh):
                if i>=MAX_MESSAGES: break
                m=json.loads(raw)
                st=replay.apply(m,compute_depth_features=False)
                t=st.cts if st.cts is not None else st.ts
                if st.cts is None: missing_cts += 1
                times.append(int(t)); bids.append(st.best_bid); asks.append(st.best_ask)

                if last_anchor is not None and t-last_anchor<ANCHOR_MS:
                    continue
                bd,ad=top10_depths(replay)
                if prev_depth is not None:
                    pbd,pad=prev_depth
                    bdep=max(0.0,(pbd-bd)/pbd) if pbd>0 else 0.0
                    adep=max(0.0,(pad-ad)/pad) if pad>0 else 0.0
                    direction=1 if adep>bdep else (-1 if bdep>adep else 0)
                    anchors.append({
                        "t":int(t),"bid":st.best_bid,"ask":st.best_ask,
                        "bid_depletion":bdep,"ask_depletion":adep,
                        "direction":direction,"strength":max(bdep,adep),
                    })
                prev_depth=(bd,ad); last_anchor=int(t)

    if len(times)<100_000:
        raise RuntimeError(f"{date}:INSUFFICIENT_L2")
    return {
        "times":times,"bids":bids,"asks":asks,"anchors":anchors,
        "missing_cts":missing_cts,
    }


def load_trades(date,gz_path,lo,hi):
    times=[]; buy=[]; sell=[]
    with gzip.open(gz_path,"rt",encoding="utf-8",newline="") as fh:
        reader=csv.DictReader(fh)
        prev=None
        for r in reader:
            t=int(round(float(r["timestamp"])*1000.0))
            if prev is not None and t<prev:
                raise RuntimeError(f"{date}:NONMONOTONIC_TRADES")
            prev=t
            if t<lo-5000: continue
            if t>=hi: break
            notional=float(r["size"])*float(r["price"])
            side=r["side"]
            times.append(t)
            buy.append(notional if side=="Buy" else 0.0)
            sell.append(notional if side=="Sell" else 0.0)
    if len(times)<10_000:
        raise RuntimeError(f"{date}:INSUFFICIENT_TRADES")

    pb=[0.0]; ps=[0.0]
    for b,s in zip(buy,sell):
        pb.append(pb[-1]+b); ps.append(ps[-1]+s)
    return times,pb,ps


def trailing_flow(anchor_t,window,times,pb,ps):
    # Strictly pre-anchor: exclude trades with timestamp >= anchor_t.
    right=bisect.bisect_left(times,anchor_t)
    left=bisect.bisect_left(times,anchor_t-window,0,right)
    b=pb[right]-pb[left]
    s=ps[right]-ps[left]
    total=b+s
    return (b-s)/total if total>0 else 0.0, total


def add_flow(anchors,trade_times,pb,ps):
    for a in anchors:
        for w in FLOW_WINDOWS:
            imb,total=trailing_flow(a["t"],w,trade_times,pb,ps)
            a[f"flow_imb_{w}"]=imb
            a[f"flow_notional_{w}"]=total


def future_state(l2,t):
    j=bisect.bisect_left(l2["times"],t)
    if j>=len(l2["times"]): return None
    return {"bid":l2["bids"][j],"ask":l2["asks"][j]}


def maker_ceiling_gross(a,f,d):
    if d>0:
        return (f["ask"]-a["bid"])/a["bid"]*10000.0
    return (a["ask"]-f["bid"])/a["ask"]*10000.0


def taker_gross(a,f,d):
    if d>0:
        return (f["bid"]-a["ask"])/a["ask"]*10000.0
    return (a["bid"]-f["ask"])/a["bid"]*10000.0


def directional_mid(a,f,d):
    am=(a["bid"]+a["ask"])/2.0
    fm=(f["bid"]+f["ask"])/2.0
    return d*(fm-am)/am*10000.0


def summarize(xs):
    if not xs: return None
    return {
        "n":len(xs),
        "mean":statistics.fmean(xs),
        "median":statistics.median(xs),
        "p95":qtile(xs,.95),
    }


def main():
    for d in DATES: authorize_date(d,"DISCOVERY")

    root=Path("/tmp/lvac_tf_002"); root.mkdir(exist_ok=True)
    datasets={}
    source_receipts={}

    for date in DATES:
        l2_url=f"https://quote-saver.bycsi.com/orderbook/linear/BTCUSDT/{date}_BTCUSDT_ob500.data.zip"
        # Historical archive changed depth naming later; these deterministic dates are pre-transition.
        tr_url=f"https://public.bybit.com/trading/BTCUSDT/BTCUSDT{date}.csv.gz"
        l2_path=root/f"{date}_l2.zip"; tr_path=root/f"{date}_trades.csv.gz"
        l2_bytes=get(l2_url,l2_path)
        tr_bytes=get(tr_url,tr_path)
        l2=build_l2(date,l2_path)
        trade_times,pb,ps=load_trades(date,tr_path,l2["times"][0],l2["times"][-1])
        add_flow(l2["anchors"],trade_times,pb,ps)
        datasets[date]=l2
        source_receipts[date]={
            "l2_url":l2_url,"trade_url":tr_url,
            "l2_bytes":l2_bytes,"trade_bytes":tr_bytes,
            "l2_states":len(l2["times"]),"anchors":len(l2["anchors"]),
            "cts_coverage_rate":1.0-l2["missing_cts"]/len(l2["times"]),
            "overlap_trade_count":len(trade_times),
        }

    calib=[a for a in datasets[CALIBRATION_DATE]["anchors"] if a["direction"]!=0]
    dep_vals=[a["strength"] for a in calib]
    thresholds={
        "depletion":{str(int(p*100)):qtile(dep_vals,p) for p in DEP_PCTS},
        "flow":{}
    }
    for w in FLOW_WINDOWS:
        vals=[abs(a[f"flow_imb_{w}"]) for a in calib]
        thresholds["flow"][str(w)]={str(int(p*100)):qtile(vals,p) for p in FLOW_PCTS}

    result={
      "status":"LVAC_TF_002_FRESH_DISCOVERY_CEILING",
      "dates":DATES,
      "calibration_date":CALIBRATION_DATE,
      "thresholds":thresholds,
      "source_receipts":source_receipts,
      "variants":{},
      "survivors":[],
      "oos_2025_opened":False,
      "holdout_2026_opened":False,
    }

    for w in FLOW_WINDOWS:
        for dp,fp in VARIANTS:
            key=f"W{w}_D{dp}_F{fp}"
            date_results={}
            pooled={h:{"mid":[],"tg":[],"mm":[]} for h in HORIZONS}
            for date in DATES:
                anchors=datasets[date]["anchors"]
                dep_thr=thresholds["depletion"][dp]
                flow_thr=thresholds["flow"][str(w)][fp]
                selected=[]; last=None
                for a in anchors:
                    d=a["direction"]; fi=a[f"flow_imb_{w}"]
                    if d==0 or a["strength"]<dep_thr: continue
                    if abs(fi)<flow_thr or d*fi<=0: continue
                    if last is not None and a["t"]-last<COOLDOWN_MS: continue
                    selected.append(a); last=a["t"]

                hr={}
                for h in HORIZONS:
                    mids=[]; tgs=[]; mms=[]
                    for a in selected:
                        f=future_state(datasets[date],a["t"]+h)
                        if f is None: continue
                        d=a["direction"]
                        mids.append(directional_mid(a,f,d))
                        tgs.append(taker_gross(a,f,d))
                        mms.append(maker_ceiling_gross(a,f,d))
                    pooled[h]["mid"].extend(mids)
                    pooled[h]["tg"].extend(tgs)
                    pooled[h]["mm"].extend(mms)
                    hr[str(h)]={
                        "n":len(mms),
                        "mean_directional_mid_bps":statistics.fmean(mids) if mids else None,
                        "mean_taker_gross_bps":statistics.fmean(tgs) if tgs else None,
                        "mean_mexc_taker_net_bps":statistics.fmean(tgs)-16.0 if tgs else None,
                        "mean_maker_ceiling_gross_bps":statistics.fmean(mms) if mms else None,
                        "mean_mexc_maker_ceiling_net_bps":statistics.fmean(mms)-12.0 if mms else None,
                    }
                date_results[date]=hr

            pooled_results={}
            for h in HORIZONS:
                mm=pooled[h]["mm"]; tg=pooled[h]["tg"]; mid=pooled[h]["mid"]
                date_positive=sum(
                    1 for d in DATES
                    if date_results[d][str(h)]["n"]>0
                    and date_results[d][str(h)]["mean_mexc_maker_ceiling_net_bps"]>0
                )
                rec={
                    "n":len(mm),
                    "date_positive_count":date_positive,
                    "mean_directional_mid_bps":statistics.fmean(mid) if mid else None,
                    "mean_taker_gross_bps":statistics.fmean(tg) if tg else None,
                    "mean_mexc_taker_net_bps":statistics.fmean(tg)-16.0 if tg else None,
                    "mean_maker_ceiling_gross_bps":statistics.fmean(mm) if mm else None,
                    "mean_mexc_maker_ceiling_net_bps":statistics.fmean(mm)-12.0 if mm else None,
                    "p95_maker_ceiling_gross_bps":qtile(mm,.95) if mm else None,
                }
                if rec["n"]>=40 and rec["mean_mexc_maker_ceiling_net_bps"]>0 and date_positive>=3:
                    result["survivors"].append({
                        "variant":key,"horizon_ms":h,"n":rec["n"],
                        "date_positive_count":date_positive,
                        "mean_mexc_maker_ceiling_net_bps":rec["mean_mexc_maker_ceiling_net_bps"],
                    })
                pooled_results[str(h)]=rec

            result["variants"][key]={
                "window_ms":w,"depletion_percentile":dp,"flow_percentile":fp,
                "by_date":date_results,"pooled":pooled_results,
            }

    result["decision"]="CEILING_SURVIVOR_EXISTS" if result["survivors"] else "LVAC_TF_002_MEXC_ECONOMIC_CEILING_FAIL"
    out=Path("research/microstructure_scalping/receipts"); out.mkdir(parents=True,exist_ok=True)
    (out/"lvac_tf_002_fresh_discovery_ceiling_v01.json").write_text(
        json.dumps(result,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    sys.exit(main())
