#!/usr/bin/env python3
import json, statistics, sys, urllib.request, zipfile
from pathlib import Path

from research.microstructure_scalping.dataset_builder_v01 import build_rows
from research.microstructure_scalping.partition_guard_v01 import authorize_date

DATE="2023-01-18"
URL="https://quote-saver.bycsi.com/orderbook/linear/BTCUSDT/2023-01-18_BTCUSDT_ob500.data.zip"
MAX_MESSAGES=250_000
HORIZONS=(5000,15000,30000)
FEATURES=("microprice_displacement_bps","imbalance_l1","imbalance_l5","imbalance_l10")
PCTS=(0.50,0.75,0.90,0.95,0.99)
UA={"User-Agent":"Mozilla/5.0 Crypto-Lab-Extreme-Ceiling/0.1"}

def sign(x):
    return 1 if x>0 else (-1 if x<0 else 0)

def qtile(xs,p):
    s=sorted(xs)
    return s[int((len(s)-1)*p)]

def maker_taker_gross(r,h,d):
    if d>0:
        entry=r["best_bid"]; exit_=r[f"fwd_bid_{h}ms"]
        return (exit_-entry)/entry*10000.0
    entry=r["best_ask"]; exit_=r[f"fwd_ask_{h}ms"]
    return (entry-exit_)/entry*10000.0

def maker_maker_ceiling_gross(r,h,d):
    if d>0:
        entry=r["best_bid"]; exit_=r[f"fwd_ask_{h}ms"]
        return (exit_-entry)/entry*10000.0
    entry=r["best_ask"]; exit_=r[f"fwd_bid_{h}ms"]
    return (entry-exit_)/entry*10000.0

def main():
    authorize_date(DATE,"DISCOVERY")
    p=Path("/tmp/extreme_l2.zip")
    req=urllib.request.Request(URL,headers=UA)
    with urllib.request.urlopen(req,timeout=90) as resp, p.open("wb") as f:
        while True:
            c=resp.read(1024*1024)
            if not c: break
            f.write(c)

    messages=[]
    with zipfile.ZipFile(p) as zf:
        if zf.testzip() is not None: raise RuntimeError("CRC_FAIL")
        name=[n for n in zf.namelist() if not n.endswith("/")][0]
        with zf.open(name) as fh:
            for i,raw in enumerate(fh):
                if i>=MAX_MESSAGES: break
                messages.append(json.loads(raw))

    rows=build_rows(messages,horizons_ms=HORIZONS,anchor_interval_ms=1000)
    result={"status":"EXTREME_STATE_ECONOMIC_CEILING_DISCOVERY_MVE",
            "date":DATE,"messages":len(messages),"rows":len(rows),
            "oos_2025_opened":False,"holdout_2026_opened":False,"features":{}}
    survivors=[]
    for feat in FEATURES:
        mags=[abs(r[feat]) for r in rows]
        thresholds={str(int(p*100)):qtile(mags,p) for p in PCTS}
        fo={"thresholds":thresholds,"buckets":{}}
        for label,thr in thresholds.items():
            selected=[r for r in rows if abs(r[feat])>=thr and sign(r[feat])!=0]
            bo={}
            for h in HORIZONS:
                mt=[maker_taker_gross(r,h,sign(r[feat])) for r in selected]
                mm=[maker_maker_ceiling_gross(r,h,sign(r[feat])) for r in selected]
                rec={
                  "n":len(selected),
                  "mean_maker_taker_gross_bps":statistics.fmean(mt) if mt else None,
                  "mean_bybit_maker_taker_net_bps_ref":statistics.fmean(mt)-7.5 if mt else None,
                  "mean_mexc_maker_taker_net_bps":statistics.fmean(mt)-14.0 if mt else None,
                  "mean_maker_maker_ceiling_gross_bps":statistics.fmean(mm) if mm else None,
                  "mean_bybit_maker_maker_ceiling_net_bps_ref":statistics.fmean(mm)-4.0 if mm else None,
                  "mean_mexc_maker_maker_ceiling_net_bps":statistics.fmean(mm)-12.0 if mm else None,
                  "positive_mexc_maker_maker_ceiling_rate":sum((x-12.0)>0 for x in mm)/len(mm) if mm else None,
                }
                if len(selected)>=100 and rec["mean_mexc_maker_maker_ceiling_net_bps"]>0:
                    survivors.append({"feature":feat,"percentile":label,"horizon_ms":h,
                                      "mean_net_bps":rec["mean_mexc_maker_maker_ceiling_net_bps"],
                                      "n":len(selected)})
                bo[str(h)]=rec
            fo["buckets"][label]=bo
        result["features"][feat]=fo

    result["mexc_ceiling_survivors"]=survivors
    result["decision"]="CEILING_SURVIVOR_EXISTS" if survivors else "MEXC_MAKER_ECONOMIC_CEILING_FAIL_SAMPLE"
    out=Path("research/microstructure_scalping/receipts"); out.mkdir(parents=True,exist_ok=True)
    (out/"extreme_state_ceiling_mve_v01.json").write_text(json.dumps(result,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    sys.exit(main())
