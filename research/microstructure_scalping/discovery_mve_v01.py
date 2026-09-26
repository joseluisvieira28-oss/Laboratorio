#!/usr/bin/env python3
import json, math, statistics, sys, urllib.request, zipfile
from pathlib import Path

from research.microstructure_scalping.dataset_builder_v01 import build_rows
from research.microstructure_scalping.cost_model_v01 import taker_net_bps
from research.microstructure_scalping.partition_guard_v01 import authorize_date

DATE="2023-01-18"
URL="https://quote-saver.bycsi.com/orderbook/linear/BTCUSDT/2023-01-18_BTCUSDT_ob500.data.zip"
MAX_MESSAGES=250_000
ANCHOR_MS=1000
HORIZONS=(100,500,1000,5000,15000,30000)
UA={"User-Agent":"Mozilla/5.0 Crypto-Lab-Discovery-MVE/0.1"}


def sign(x):
    return 1 if x>0 else (-1 if x<0 else 0)


def pct(xs,p):
    if not xs: return None
    s=sorted(xs)
    return s[int((len(s)-1)*p)]


def executable_gross(row,h,direction):
    if direction>0:
        entry=row["best_ask"]
        exit_=row[f"fwd_bid_{h}ms"]
        return (exit_-entry)/entry*10000.0
    if direction<0:
        entry=row["best_bid"]
        exit_=row[f"fwd_ask_{h}ms"]
        return (entry-exit_)/entry*10000.0
    return None


def directional_mid(row,h,direction):
    return direction*row[f"fwd_return_bps_{h}ms"]


def summarize(rows,feature):
    result={}
    for h in HORIZONS:
        gross=[]; mid=[]; net_bybit=[]; hurdle_mexc=[]
        for r in rows:
            d=sign(r[feature])
            if d==0: continue
            g=executable_gross(r,h,d)
            gross.append(g)
            mid.append(directional_mid(r,h,d))
            net_bybit.append(taker_net_bps(g,"BYBIT_VIP0_REF",0.0))
            # Cross-venue feasibility only: compare same gross move with MEXC API fee hurdle.
            hurdle_mexc.append(g-16.0)
        result[str(h)]={
          "n":len(gross),
          "mean_directional_mid_bps":statistics.fmean(mid) if mid else None,
          "median_directional_mid_bps":statistics.median(mid) if mid else None,
          "directional_mid_hit_rate":sum(x>0 for x in mid)/len(mid) if mid else None,
          "mean_executable_gross_bps":statistics.fmean(gross) if gross else None,
          "median_executable_gross_bps":statistics.median(gross) if gross else None,
          "gross_positive_rate":sum(x>0 for x in gross)/len(gross) if gross else None,
          "mean_bybit_taker_net_bps_ref":statistics.fmean(net_bybit) if net_bybit else None,
          "p95_executable_gross_bps":pct(gross,.95),
          "mean_gross_minus_mexc_fee_hurdle_bps":statistics.fmean(hurdle_mexc) if hurdle_mexc else None,
        }
    return result


def main():
    authorize_date(DATE,"DISCOVERY")
    p=Path("/tmp/discovery_mve.zip")
    req=urllib.request.Request(URL,headers=UA)
    with urllib.request.urlopen(req,timeout=90) as r, p.open("wb") as f:
        while True:
            c=r.read(1024*1024)
            if not c: break
            f.write(c)
    messages=[]
    with zipfile.ZipFile(p) as zf:
        if zf.testzip() is not None: raise RuntimeError("CRC_FAIL")
        names=[n for n in zf.namelist() if not n.endswith("/")]
        with zf.open(names[0]) as fh:
            for i,raw in enumerate(fh):
                if i>=MAX_MESSAGES: break
                messages.append(json.loads(raw))
    rows=build_rows(messages,horizons_ms=HORIZONS,anchor_interval_ms=ANCHOR_MS)
    features=["microprice_displacement_bps","imbalance_l1","imbalance_l5","imbalance_l10"]
    result={
      "status":"DISCOVERY_MVE_ONLY",
      "date":DATE,
      "source":URL,
      "messages":len(messages),
      "anchor_interval_ms":ANCHOR_MS,
      "rows_with_all_labels":len(rows),
      "features":{f:summarize(rows,f) for f in features},
      "decision_rule":"No promotion from this one-day MVE. Inspect whether any raw predictive direction exists and whether economics are remotely plausible. No threshold tuning.",
      "oos_opened":False,
      "holdout_2026_opened":False
    }
    out=Path("research/microstructure_scalping/receipts")
    out.mkdir(parents=True,exist_ok=True)
    (out/"discovery_mve_v01.json").write_text(json.dumps(result,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    sys.exit(main())
