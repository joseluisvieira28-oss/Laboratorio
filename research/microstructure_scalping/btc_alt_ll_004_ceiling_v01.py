#!/usr/bin/env python3
import bisect, csv, gzip, json, statistics, urllib.request, zipfile
from pathlib import Path

from research.microstructure_scalping.l2_replay import L2Replay
from research.microstructure_scalping.partition_guard_v01 import authorize_date

DATES=("2024-05-01","2024-06-05","2024-07-03")
CALIBRATION_DATE=DATES[0]
FOLLOWERS=("ETHUSDT","SOLUSDT")
MAX_MESSAGES=250_000
ANCHOR_MS=1000
WINDOWS=(1000,5000)
HORIZONS=(1000,5000,15000,30000,60000,120000)
MAX_STALE_MS=250
PCTS=(0.95,0.99)
UA={"User-Agent":"Mozilla/5.0 Crypto-Lab-BTC-ALT-LL-004/0.1"}


def head(url):
    req=urllib.request.Request(url,headers=UA,method="HEAD")
    with urllib.request.urlopen(req,timeout=30) as r:
        return r.status,int(r.headers.get("Content-Length") or 0)


def download(url,path):
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
    s=sorted(xs); return s[int((len(s)-1)*p)]


def sign(x):
    return 1 if x>0 else (-1 if x<0 else 0)


def load_btc_l2(date,path):
    replay=L2Replay(); anchors=[]; last=None
    with zipfile.ZipFile(path) as zf:
        if zf.testzip() is not None: raise RuntimeError(f"{date}:BTC_L2_CRC_FAIL")
        names=[n for n in zf.namelist() if not n.endswith("/")]
        if len(names)!=1: raise RuntimeError(f"{date}:BTC_L2_MEMBERS")
        with zf.open(names[0]) as fh:
            for i,raw in enumerate(fh):
                if i>=MAX_MESSAGES: break
                m=json.loads(raw)
                st=replay.apply(m,compute_depth_features=False)
                t=int(st.cts if st.cts is not None else st.ts)
                if last is not None and t-last<ANCHOR_MS: continue
                anchors.append({"t":t,"mid":st.mid})
                last=t
    if len(anchors)<1000: raise RuntimeError(f"{date}:BTC_ANCHORS_LOW")
    return anchors


def load_trades(date,symbol,path,lo,hi):
    rows=[]
    with gzip.open(path,"rt",encoding="utf-8",newline="") as fh:
        reader=csv.DictReader(fh)
        prev=None
        for r in reader:
            t=int(round(float(r["timestamp"])*1000.0))
            if prev is not None and t<prev: raise RuntimeError(f"{date}:{symbol}:NONMONOTONIC")
            prev=t
            if t<lo-5000: continue
            if t>hi+max(HORIZONS)+MAX_STALE_MS: break
            px=float(r["price"]); sz=float(r["size"])
            rows.append((t,r["side"],px,sz))
    if len(rows)<1000: raise RuntimeError(f"{date}:{symbol}:TRADES_LOW")
    return rows


def build_trade_index(rows):
    times=[]; prices=[]; pb=[0.0]; ps=[0.0]
    for t,side,px,sz in rows:
        times.append(t); prices.append(px)
        notion=px*sz
        pb.append(pb[-1]+(notion if side=="Buy" else 0.0))
        ps.append(ps[-1]+(notion if side=="Sell" else 0.0))
    return {"times":times,"prices":prices,"pb":pb,"ps":ps}


def last_trade_price(idx,t):
    times=idx["times"]; prices=idx["prices"]
    i=bisect.bisect_right(times,t)-1
    if i<0: return None
    lag=t-times[i]
    if lag>MAX_STALE_MS: return None
    return prices[i]


def first_trade_price(idx,t):
    times=idx["times"]; prices=idx["prices"]
    i=bisect.bisect_left(times,t)
    if i>=len(times): return None
    lag=times[i]-t
    if lag>MAX_STALE_MS: return None
    return prices[i]


def indexed_flow(idx,t,window):
    times=idx["times"]
    lo=bisect.bisect_left(times,t-window)
    hi=bisect.bisect_left(times,t)
    b=idx["pb"][hi]-idx["pb"][lo]
    s=idx["ps"][hi]-idx["ps"][lo]
    tot=b+s
    return (b-s)/tot if tot else 0.0


def enrich_btc(anchors,trade_idx):
    anchor_times=[a["t"] for a in anchors]
    for a in anchors:
        for w in WINDOWS:
            target=a["t"]-w
            j=bisect.bisect_right(anchor_times,target)-1
            if j<0:
                a[f"ret_{w}"]=None
            else:
                lag=target-anchor_times[j]
                if lag>ANCHOR_MS:
                    a[f"ret_{w}"]=None
                else:
                    base=anchors[j]["mid"]
                    a[f"ret_{w}"]=(a["mid"]-base)/base*10000.0
            a[f"flow_{w}"]=indexed_flow(trade_idx,a["t"],w)


def follower_prior_return(idx,t,w):
    p1=last_trade_price(idx,t)
    p0=last_trade_price(idx,t-w)
    if p1 is None or p0 is None: return None
    return (p1-p0)/p0*10000.0


def follower_future_return(idx,t,h,d):
    p0=last_trade_price(idx,t)
    p1=first_trade_price(idx,t+h)
    if p0 is None or p1 is None: return None
    return d*(p1-p0)/p0*10000.0


def source_urls(date):
    urls={"BTC_L2":f"https://quote-saver.bycsi.com/orderbook/linear/BTCUSDT/{date}_BTCUSDT_ob500.data.zip",
          "BTC_TRADES":f"https://public.bybit.com/trading/BTCUSDT/BTCUSDT{date}.csv.gz"}
    for s in FOLLOWERS:
        urls[f"{s}_TRADES"]=f"https://public.bybit.com/trading/{s}/{s}{date}.csv.gz"
    return urls


def main():
    for d in DATES: authorize_date(d,"DISCOVERY")

    # Fail closed on all sources before downloading any outcome inputs.
    source_check={}
    for d in DATES:
        source_check[d]={}
        for name,url in source_urls(d).items():
            st,cl=head(url)
            source_check[d][name]={"url":url,"status":st,"content_length":cl}
            if st!=200 or cl<=0:
                out=Path("research/microstructure_scalping/receipts"); out.mkdir(parents=True,exist_ok=True)
                receipt={"status":"BLOCKED_SOURCE","source_check":source_check,
                         "oos_2025_opened":False,"holdout_2026_opened":False}
                (out/"btc_alt_ll_004_ceiling_v01.json").write_text(json.dumps(receipt,indent=2,sort_keys=True))
                print(json.dumps(receipt,indent=2,sort_keys=True))
                raise SystemExit(2)

    root=Path("/tmp/btc_alt_ll_004"); root.mkdir(exist_ok=True)
    data={}

    for d in DATES:
        urls=source_urls(d)
        lp=root/f"{d}_btc_l2.zip"; bp=root/f"{d}_btc_trades.csv.gz"
        download(urls["BTC_L2"],lp); download(urls["BTC_TRADES"],bp)
        anchors=load_btc_l2(d,lp)
        lo,hi=anchors[0]["t"],anchors[-1]["t"]
        btc_rows=load_trades(d,"BTCUSDT",bp,lo,hi)
        btc_idx=build_trade_index(btc_rows)
        enrich_btc(anchors,btc_idx)
        followers={}
        for s in FOLLOWERS:
            tp=root/f"{d}_{s}_trades.csv.gz"
            download(urls[f"{s}_TRADES"],tp)
            follower_rows=load_trades(d,s,tp,lo,hi)
            followers[s]=build_trade_index(follower_rows)
        data[d]={"anchors":anchors,"followers":followers}
        try: lp.unlink(); bp.unlink()
        except OSError: pass
        for s in FOLLOWERS:
            try:(root/f"{d}_{s}_trades.csv.gz").unlink()
            except OSError: pass

    calib=data[CALIBRATION_DATE]["anchors"]
    thresholds={}
    for w in WINDOWS:
        vals=[abs(a[f"ret_{w}"]) for a in calib if a.get(f"ret_{w}") is not None]
        thresholds[str(w)]={str(int(p*100)):qtile(vals,p) for p in PCTS}

    result={"status":"BTC_ALT_LL_004_INFORMATIONAL_CEILING",
            "dates":DATES,"calibration_date":CALIBRATION_DATE,
            "thresholds":thresholds,"source_check":source_check,
            "followers":{},"survivors":[],
            "oos_2025_opened":False,"holdout_2026_opened":False}

    for follower in FOLLOWERS:
        fres={}
        for w in WINDOWS:
            for pct in ("95","99"):
                for flow_gate in (False,True):
                    for lag_gate in (False,True):
                        if lag_gate and not flow_gate: continue
                        key=f"W{w}_P{pct}"+("_FLOW" if flow_gate else "")+("_LAG" if lag_gate else "")
                        bydate={}; pooled={h:[] for h in HORIZONS}
                        for d in DATES:
                            selected=[]
                            thr=thresholds[str(w)][pct]
                            idx=data[d]["followers"][follower]
                            for a in data[d]["anchors"]:
                                r=a.get(f"ret_{w}")
                                if r is None or abs(r)<thr or sign(r)==0: continue
                                direction=sign(r)
                                if flow_gate and direction*a[f"flow_{w}"]<=0: continue
                                if lag_gate:
                                    fr=follower_prior_return(idx,a["t"],w)
                                    if fr is None: continue
                                    if direction*fr >= abs(r): continue
                                selected.append((a,direction))
                            hr={}
                            for h in HORIZONS:
                                vals=[]
                                for a,direction in selected:
                                    x=follower_future_return(idx,a["t"],h,direction)
                                    if x is not None: vals.append(x)
                                pooled[h].extend(vals)
                                hr[str(h)]={"n":len(vals),
                                            "mean_gross_bps":statistics.fmean(vals) if vals else None,
                                            "mean_mexc_maker_fee_only_net_bps":statistics.fmean(vals)-12 if vals else None,
                                            "mean_mexc_taker_fee_only_net_bps":statistics.fmean(vals)-16 if vals else None,
                                            "p95_gross_bps":qtile(vals,.95) if vals else None}
                            bydate[d]=hr
                        pout={}
                        for h in HORIZONS:
                            vals=pooled[h]
                            positives=sum(1 for d in DATES if bydate[d][str(h)]["n"]>0 and bydate[d][str(h)]["mean_mexc_maker_fee_only_net_bps"]>0)
                            rec={"n":len(vals),"date_positive_count":positives,
                                 "mean_gross_bps":statistics.fmean(vals) if vals else None,
                                 "mean_mexc_maker_fee_only_net_bps":statistics.fmean(vals)-12 if vals else None,
                                 "mean_mexc_taker_fee_only_net_bps":statistics.fmean(vals)-16 if vals else None,
                                 "p95_gross_bps":qtile(vals,.95) if vals else None}
                            if rec["n"]>=30 and rec["mean_mexc_maker_fee_only_net_bps"]>0 and positives>=2:
                                result["survivors"].append({"follower":follower,"variant":key,"horizon_ms":h,
                                                            "n":rec["n"],"date_positive_count":positives,
                                                            "mean_net_bps":rec["mean_mexc_maker_fee_only_net_bps"]})
                            pout[str(h)]=rec
                        fres[key]={"by_date":bydate,"pooled":pout}
        result["followers"][follower]=fres

    result["decision"]="CEILING_SURVIVOR_EXISTS" if result["survivors"] else "BTC_ALT_LL_004_MEXC_INFORMATIONAL_CEILING_FAIL"
    out=Path("research/microstructure_scalping/receipts"); out.mkdir(parents=True,exist_ok=True)
    (out/"btc_alt_ll_004_ceiling_v01.json").write_text(json.dumps(result,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
