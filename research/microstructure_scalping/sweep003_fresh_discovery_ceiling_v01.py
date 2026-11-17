#!/usr/bin/env python3
import bisect, csv, gzip, json, statistics, urllib.request, zipfile
from collections import deque
from pathlib import Path

from research.microstructure_scalping.l2_replay import L2Replay
from research.microstructure_scalping.partition_guard_v01 import authorize_date

DATES=("2024-02-07","2024-03-06","2024-04-03")
CALIBRATION_DATE=DATES[0]
MAX_MESSAGES=250_000
ANCHOR_MS=1000
COOLDOWN_MS=10000
WINDOWS=(500,1000)
HORIZONS=(5000,15000,30000,60000,120000)
NOTIONAL_PCTS=(0.90,0.95,0.99)
SPAN_PCTS=(0.75,0.90,0.95)
VARIANTS=(
    ("90","75",2),
    ("95","75",3),
    ("95","90",3),
    ("99","90",3),
    ("99","95",5),
)
UA={"User-Agent":"Mozilla/5.0 Crypto-Lab-SWEEP003/0.1"}


def dl(url,path):
    req=urllib.request.Request(url,headers=UA)
    total=0
    with urllib.request.urlopen(req,timeout=120) as r, open(path,"wb") as f:
        while True:
            c=r.read(1024*1024)
            if not c: break
            total+=len(c); f.write(c)
    return total


def qtile(xs,p):
    if not xs: return None
    s=sorted(xs)
    return s[int((len(s)-1)*p)]


def load_l2(date,path):
    replay=L2Replay()
    times=[]; bids=[]; asks=[]; anchors=[]
    last_anchor=None; prev_anchor_mid=None
    with zipfile.ZipFile(path) as zf:
        if zf.testzip() is not None: raise RuntimeError(f"{date}:CRC_FAIL")
        names=[n for n in zf.namelist() if not n.endswith("/")]
        if len(names)!=1: raise RuntimeError(f"{date}:UNEXPECTED_MEMBERS")
        with zf.open(names[0]) as fh:
            for i,raw in enumerate(fh):
                if i>=MAX_MESSAGES: break
                m=json.loads(raw)
                st=replay.apply(m,compute_depth_features=False)
                t=int(st.cts if st.cts is not None else st.ts)
                times.append(t); bids.append(st.best_bid); asks.append(st.best_ask)
                if last_anchor is not None and t-last_anchor<ANCHOR_MS: continue
                mid=(st.best_bid+st.best_ask)/2.0
                move=0.0 if prev_anchor_mid is None else (mid-prev_anchor_mid)/prev_anchor_mid*10000.0
                anchors.append({"t":t,"bid":st.best_bid,"ask":st.best_ask,"mid":mid,"prior_1s_mid_move_bps":move})
                prev_anchor_mid=mid; last_anchor=t
    if len(times)<100_000: raise RuntimeError(f"{date}:INSUFFICIENT_L2")
    return {"times":times,"bids":bids,"asks":asks,"anchors":anchors}


def load_trades(date,path,lo,hi):
    rows=[]
    with gzip.open(path,"rt",encoding="utf-8",newline="") as fh:
        reader=csv.DictReader(fh)
        prev=None
        for r in reader:
            t=int(round(float(r["timestamp"])*1000.0))
            if prev is not None and t<prev: raise RuntimeError(f"{date}:NONMONOTONIC_TRADES")
            prev=t
            if t<lo-1000: continue
            if t>=hi: break
            rows.append((t,r["side"],float(r["price"]),float(r["size"])))
    if len(rows)<10_000: raise RuntimeError(f"{date}:INSUFFICIENT_TRADES")
    return rows


def add_sweep_features(anchors,trades):
    trade_times=[x[0] for x in trades]
    for a in anchors:
        t=a["t"]
        for w in WINDOWS:
            lo=bisect.bisect_left(trade_times,t-w)
            hi=bisect.bisect_left(trade_times,t)  # strictly pre-anchor
            buy_not=0.0; sell_not=0.0; buy_px=[]; sell_px=[]
            for _,side,px,sz in trades[lo:hi]:
                n=px*sz
                if side=="Buy":
                    buy_not+=n; buy_px.append(px)
                else:
                    sell_not+=n; sell_px.append(px)
            total=buy_not+sell_not
            flow=(buy_not-sell_not)/total if total else 0.0
            if flow>0:
                dom_not=buy_not; pxs=buy_px; direction=1
            elif flow<0:
                dom_not=sell_not; pxs=sell_px; direction=-1
            else:
                dom_not=0.0; pxs=[]; direction=0
            levels=len(set(pxs))
            if len(pxs)>=2:
                pmin=min(pxs); pmax=max(pxs); center=(pmin+pmax)/2.0
                span=(pmax-pmin)/center*10000.0 if center else 0.0
            else:
                span=0.0
            a[f"direction_{w}"]=direction
            a[f"signed_flow_{w}"]=flow
            a[f"dom_notional_{w}"]=dom_not
            a[f"levels_{w}"]=levels
            a[f"span_bps_{w}"]=span


def future(l2,t):
    j=bisect.bisect_left(l2["times"],t)
    if j>=len(l2["times"]): return None
    return {"bid":l2["bids"][j],"ask":l2["asks"][j]}


def directional_mid(a,f,d):
    fm=(f["bid"]+f["ask"])/2.0
    return d*(fm-a["mid"])/a["mid"]*10000.0


def maker_gross(a,f,d):
    if d>0: return (f["ask"]-a["bid"])/a["bid"]*10000.0
    return (a["ask"]-f["bid"])/a["ask"]*10000.0


def taker_gross(a,f,d):
    if d>0: return (f["bid"]-a["ask"])/a["ask"]*10000.0
    return (a["bid"]-f["ask"])/a["bid"]*10000.0


def main():
    for d in DATES: authorize_date(d,"DISCOVERY")
    root=Path("/tmp/sweep003"); root.mkdir(exist_ok=True)
    data={}; receipts={}
    for date in DATES:
        l2_url=f"https://quote-saver.bycsi.com/orderbook/linear/BTCUSDT/{date}_BTCUSDT_ob500.data.zip"
        tr_url=f"https://public.bybit.com/trading/BTCUSDT/BTCUSDT{date}.csv.gz"
        lp=root/f"{date}_l2.zip"; tp=root/f"{date}_trades.csv.gz"
        lb=dl(l2_url,lp); tb=dl(tr_url,tp)
        l2=load_l2(date,lp)
        tr=load_trades(date,tp,l2["times"][0],l2["times"][-1])
        add_sweep_features(l2["anchors"],tr)
        data[date]=l2
        receipts[date]={"l2_bytes":lb,"trade_bytes":tb,"l2_states":len(l2["times"]),
                        "anchors":len(l2["anchors"]),"overlap_trades":len(tr),
                        "l2_url":l2_url,"trade_url":tr_url}

    calib=data[CALIBRATION_DATE]["anchors"]
    thresholds={"notional":{},"span":{}}
    for w in WINDOWS:
        nvals=[a[f"dom_notional_{w}"] for a in calib if a[f"direction_{w}"]!=0]
        svals=[a[f"span_bps_{w}"] for a in calib if a[f"direction_{w}"]!=0]
        thresholds["notional"][str(w)]={str(int(p*100)):qtile(nvals,p) for p in NOTIONAL_PCTS}
        thresholds["span"][str(w)]={str(int(p*100)):qtile(svals,p) for p in SPAN_PCTS}

    result={"status":"SWEEP_003_FRESH_DISCOVERY_CEILING","dates":DATES,
            "calibration_date":CALIBRATION_DATE,"thresholds":thresholds,
            "source_receipts":receipts,"variants":{},"survivors":[],
            "oos_2025_opened":False,"holdout_2026_opened":False}

    for w in WINDOWS:
        for np,sp,min_levels in VARIANTS:
            key=f"W{w}_N{np}_SP{sp}_L{min_levels}"
            var={"continuation":{},"reversal":{}}
            for mode in ("continuation","reversal"):
                pooled={h:{"mid":[],"tg":[],"mm":[]} for h in HORIZONS}
                bydate={}
                for date in DATES:
                    selected=[]; last=None
                    for a in data[date]["anchors"]:
                        d=a[f"direction_{w}"]
                        if d==0: continue
                        if d*a["prior_1s_mid_move_bps"]<=0: continue
                        if a[f"dom_notional_{w}"] < thresholds["notional"][str(w)][np]: continue
                        if a[f"span_bps_{w}"] < thresholds["span"][str(w)][sp]: continue
                        if a[f"levels_{w}"] < min_levels: continue
                        if last is not None and a["t"]-last<COOLDOWN_MS: continue
                        selected.append(a); last=a["t"]
                    hr={}
                    for h in HORIZONS:
                        mids=[]; tgs=[]; mms=[]
                        for a in selected:
                            f=future(data[date],a["t"]+h)
                            if f is None: continue
                            base=a[f"direction_{w}"]
                            d=base if mode=="continuation" else -base
                            mids.append(directional_mid(a,f,d))
                            tgs.append(taker_gross(a,f,d))
                            mms.append(maker_gross(a,f,d))
                        pooled[h]["mid"].extend(mids); pooled[h]["tg"].extend(tgs); pooled[h]["mm"].extend(mms)
                        hr[str(h)]={"n":len(mms),
                                    "mean_directional_mid_bps":statistics.fmean(mids) if mids else None,
                                    "mean_mexc_taker_net_bps":statistics.fmean(tgs)-16 if tgs else None,
                                    "mean_maker_ceiling_gross_bps":statistics.fmean(mms) if mms else None,
                                    "mean_mexc_maker_ceiling_net_bps":statistics.fmean(mms)-12 if mms else None}
                    bydate[date]=hr

                pooled_out={}
                for h in HORIZONS:
                    mm=pooled[h]["mm"]; tg=pooled[h]["tg"]; mid=pooled[h]["mid"]
                    positives=sum(1 for d in DATES if bydate[d][str(h)]["n"]>0 and bydate[d][str(h)]["mean_mexc_maker_ceiling_net_bps"]>0)
                    rec={"n":len(mm),"date_positive_count":positives,
                         "mean_directional_mid_bps":statistics.fmean(mid) if mid else None,
                         "mean_mexc_taker_net_bps":statistics.fmean(tg)-16 if tg else None,
                         "mean_maker_ceiling_gross_bps":statistics.fmean(mm) if mm else None,
                         "mean_mexc_maker_ceiling_net_bps":statistics.fmean(mm)-12 if mm else None,
                         "p95_maker_ceiling_gross_bps":qtile(mm,.95) if mm else None}
                    if rec["n"]>=30 and rec["mean_mexc_maker_ceiling_net_bps"]>0 and positives>=2:
                        result["survivors"].append({"variant":key,"mode":mode,"horizon_ms":h,
                                                    "n":rec["n"],"date_positive_count":positives,
                                                    "mean_net_bps":rec["mean_mexc_maker_ceiling_net_bps"]})
                    pooled_out[str(h)]=rec
                var[mode]={"by_date":bydate,"pooled":pooled_out}
            result["variants"][key]=var

    result["decision"]="CEILING_SURVIVOR_EXISTS" if result["survivors"] else "SWEEP_003_MEXC_ECONOMIC_CEILING_FAIL"
    out=Path("research/microstructure_scalping/receipts"); out.mkdir(parents=True,exist_ok=True)
    (out/"sweep003_fresh_discovery_ceiling_v01.json").write_text(json.dumps(result,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
