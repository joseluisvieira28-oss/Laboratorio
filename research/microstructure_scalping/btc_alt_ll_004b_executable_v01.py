#!/usr/bin/env python3
import bisect, json, statistics, urllib.request, zipfile
from pathlib import Path

from research.microstructure_scalping.l2_replay import L2Replay
from research.microstructure_scalping.partition_guard_v01 import authorize_date

DATES=("2024-08-07","2024-09-04","2024-10-02")
MAX_MESSAGES=250_000
ANCHOR_MS=1000
SHOCK_WINDOW_MS=5000
SHOCK_THRESHOLD_BPS=7.002526745067178
HORIZON_MS=60000
MAX_ALIGN_MS=250
BYBIT_MAKER_RT_BPS=4.0
BYBIT_TAKER_RT_BPS=11.0
UA={"User-Agent":"Mozilla/5.0 Crypto-Lab-BTC-ALT-LL-004B/0.1"}


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


def load_btc_anchors(date,path):
    replay=L2Replay(); anchors=[]; last=None
    with zipfile.ZipFile(path) as zf:
        if zf.testzip() is not None: raise RuntimeError(f"{date}:BTC_CRC")
        names=[n for n in zf.namelist() if not n.endswith("/")]
        with zf.open(names[0]) as fh:
            for i,raw in enumerate(fh):
                if i>=MAX_MESSAGES: break
                m=json.loads(raw)
                st=replay.apply(m,compute_depth_features=False)
                t=int(st.cts if st.cts is not None else st.ts)
                if last is not None and t-last<ANCHOR_MS: continue
                anchors.append({"t":t,"mid":st.mid})
                last=t
    times=[a["t"] for a in anchors]
    for a in anchors:
        target=a["t"]-SHOCK_WINDOW_MS
        j=bisect.bisect_right(times,target)-1
        if j<0 or target-times[j]>ANCHOR_MS:
            a["shock_bps"]=None
        else:
            base=anchors[j]["mid"]
            a["shock_bps"]=(a["mid"]-base)/base*10000.0
    return anchors


def load_sol_states(date,path):
    replay=L2Replay(); times=[]; bids=[]; asks=[]
    with zipfile.ZipFile(path) as zf:
        if zf.testzip() is not None: raise RuntimeError(f"{date}:SOL_CRC")
        names=[n for n in zf.namelist() if not n.endswith("/")]
        with zf.open(names[0]) as fh:
            for i,raw in enumerate(fh):
                if i>=MAX_MESSAGES: break
                m=json.loads(raw)
                st=replay.apply(m,compute_depth_features=False)
                t=int(st.cts if st.cts is not None else st.ts)
                times.append(t); bids.append(st.best_bid); asks.append(st.best_ask)
    return {"times":times,"bids":bids,"asks":asks}


def current_bbo(sol,t):
    times=sol["times"]
    i=bisect.bisect_right(times,t)-1
    if i<0 or t-times[i]>MAX_ALIGN_MS: return None
    return sol["bids"][i],sol["asks"][i]


def future_bbo(sol,t):
    times=sol["times"]
    i=bisect.bisect_left(times,t)
    if i>=len(times) or times[i]-t>MAX_ALIGN_MS: return None
    return sol["bids"][i],sol["asks"][i]


def sign(x):
    return 1 if x>0 else (-1 if x<0 else 0)


def maker_gross(entry,future,d):
    eb,ea=entry; fb,fa=future
    if d>0: return (fa-eb)/eb*10000.0
    return (ea-fb)/ea*10000.0


def taker_gross(entry,future,d):
    eb,ea=entry; fb,fa=future
    if d>0: return (fb-ea)/ea*10000.0
    return (eb-fa)/eb*10000.0


def urls(date):
    return {
      "BTC":f"https://quote-saver.bycsi.com/orderbook/linear/BTCUSDT/{date}_BTCUSDT_ob500.data.zip",
      "SOL":f"https://quote-saver.bycsi.com/orderbook/linear/SOLUSDT/{date}_SOLUSDT_ob500.data.zip",
    }


def main():
    for d in DATES: authorize_date(d,"DISCOVERY")

    source_check={}
    for d in DATES:
        source_check[d]={}
        for sym,u in urls(d).items():
            st,cl=head(u)
            source_check[d][sym]={"url":u,"status":st,"content_length":cl}
            if st!=200 or cl<=0:
                receipt={"status":"BLOCKED_SOURCE","source_check":source_check,
                         "oos_2025_opened":False,"holdout_2026_opened":False}
                out=Path("research/microstructure_scalping/receipts"); out.mkdir(parents=True,exist_ok=True)
                (out/"btc_alt_ll_004b_executable_v01.json").write_text(json.dumps(receipt,indent=2,sort_keys=True))
                print(json.dumps(receipt,indent=2,sort_keys=True))
                raise SystemExit(2)

    root=Path("/tmp/btc_alt_ll_004b"); root.mkdir(exist_ok=True)
    bydate={}; pooled_m=[]; pooled_t=[]
    for d in DATES:
        us=urls(d); bp=root/f"{d}_btc.zip"; sp=root/f"{d}_sol.zip"
        download(us["BTC"],bp); download(us["SOL"],sp)
        btc=load_btc_anchors(d,bp)
        sol=load_sol_states(d,sp)
        mg=[]; tg=[]; total_signals=0; excluded_alignment=0
        for a in btc:
            shock=a["shock_bps"]
            if shock is None or abs(shock)<SHOCK_THRESHOLD_BPS: continue
            dside=sign(shock)
            if dside==0: continue
            total_signals+=1
            ent=current_bbo(sol,a["t"])
            fut=future_bbo(sol,a["t"]+HORIZON_MS)
            if ent is None or fut is None:
                excluded_alignment+=1; continue
            mg.append(maker_gross(ent,fut,dside))
            tg.append(taker_gross(ent,fut,dside))
        pooled_m.extend(mg); pooled_t.extend(tg)
        bydate[d]={
          "signals_before_alignment":total_signals,
          "excluded_alignment":excluded_alignment,
          "n":len(mg),
          "mean_maker_gross_bps":statistics.fmean(mg) if mg else None,
          "mean_bybit_maker_net_bps":statistics.fmean(mg)-BYBIT_MAKER_RT_BPS if mg else None,
          "mean_taker_gross_bps":statistics.fmean(tg) if tg else None,
          "mean_bybit_taker_net_bps":statistics.fmean(tg)-BYBIT_TAKER_RT_BPS if tg else None,
        }
        try: bp.unlink(); sp.unlink()
        except OSError: pass

    positives=sum(1 for d in DATES if bydate[d]["n"]>0 and bydate[d]["mean_bybit_maker_net_bps"]>0)
    pooled={
      "n":len(pooled_m),
      "date_positive_count":positives,
      "mean_maker_gross_bps":statistics.fmean(pooled_m) if pooled_m else None,
      "mean_bybit_maker_net_bps":statistics.fmean(pooled_m)-BYBIT_MAKER_RT_BPS if pooled_m else None,
      "mean_taker_gross_bps":statistics.fmean(pooled_t) if pooled_t else None,
      "mean_bybit_taker_net_bps":statistics.fmean(pooled_t)-BYBIT_TAKER_RT_BPS if pooled_t else None,
    }
    survives=pooled["n"]>=30 and pooled["mean_bybit_maker_net_bps"]>0 and positives>=2
    result={
      "status":"BTC_ALT_LL_004B_EXECUTABLE_BBO_VALIDATION",
      "candidate":{"follower":"SOLUSDT","shock_window_ms":SHOCK_WINDOW_MS,
                   "shock_threshold_bps":SHOCK_THRESHOLD_BPS,"horizon_ms":HORIZON_MS},
      "dates":DATES,"source_check":source_check,"by_date":bydate,"pooled":pooled,
      "decision":"EXECUTABLE_CEILING_SURVIVOR" if survives else "NO_EXECUTABLE_CEILING_EDGE",
      "oos_2025_opened":False,"holdout_2026_opened":False,
    }
    out=Path("research/microstructure_scalping/receipts"); out.mkdir(parents=True,exist_ok=True)
    (out/"btc_alt_ll_004b_executable_v01.json").write_text(json.dumps(result,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
