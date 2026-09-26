#!/usr/bin/env python3
import csv,io,json,statistics,urllib.request,zipfile
from collections import defaultdict
from pathlib import Path

EVENT_URL="https://raw.githubusercontent.com/edwinyeeshunwan/forced-or-frantic/fe8e96ac2d22bc0fd40fd032f3075f2d47ec4f04/data/event_table_liq.parquet"
BASE="https://data.binance.vision/data/futures/um/monthly/klines"
START="2025-11-01T00:00:00+00:00"
END="2025-12-31T23:59:59.999999+00:00"
TARGET="SOL"
PRIMARY_DELAY_MIN=6
HORIZON_MIN=60
HURDLE_BPS=16.0
MIN_N=20
UA={"User-Agent":"Crypto-Lab-LICP-XALT-HOLDOUT/0.1"}

def get(url):
    req=urllib.request.Request(url,headers=UA)
    with urllib.request.urlopen(req,timeout=60) as r:return r.read()

def events():
    import pandas as pd
    d=pd.read_parquet(io.BytesIO(get(EVENT_URL)),columns=["t0","symbol"])
    d["t0"]=pd.to_datetime(d["t0"],utc=True)
    st=pd.Timestamp(START);en=pd.Timestamp(END)
    x=d[(d["symbol"].astype(str)=="BTC")&(d["t0"]>=st)&(d["t0"]<=en)]
    return [v.to_pydatetime() for v in x["t0"]]

def month(m):
    url=f"{BASE}/{TARGET}USDT/1m/{TARGET}USDT-1m-{m}.zip"
    raw=get(url);z=zipfile.ZipFile(io.BytesIO(raw))
    if z.testzip() is not None:raise RuntimeError(f"CRC:{m}")
    names=[n for n in z.namelist() if not n.endswith("/")]
    if len(names)!=1:raise RuntimeError(f"MEMBERS:{m}")
    out={}
    with z.open(names[0]) as fh:
        rd=csv.reader(io.TextIOWrapper(fh,encoding="utf-8"))
        for r in rd:
            if not r:continue
            try:ts=int(r[0]);op=float(r[1])
            except Exception:
                if str(r[0]).lower() in {"open_time","open time"}:continue
                raise
            out[ts]=op
    if len(out)<40000:raise RuntimeError(f"SHORT_MONTH:{m}:{len(out)}")
    return out

def stat(xs):
    return {
      "n":len(xs),
      "mean_gross_bps":statistics.fmean(xs) if xs else None,
      "median_gross_bps":statistics.median(xs) if xs else None,
      "positive_rate":sum(v>0 for v in xs)/len(xs) if xs else None,
      "mean_transfer_ceiling_net_bps":statistics.fmean(xs)-HURDLE_BPS if xs else None
    }

def main():
    ev=events()
    months=sorted(set(t.strftime("%Y-%m") for t in ev))
    if any(m not in {"2025-11","2025-12"} for m in months):
        raise RuntimeError("PARTITION_LEAK")
    books={m:month(m) for m in months}

    vals=[]; by_month=defaultdict(list); missing=0
    for t in ev:
        m=t.strftime("%Y-%m");book=books[m]
        entry_ms=int(t.timestamp()*1000)+PRIMARY_DELAY_MIN*60_000
        exit_ms=entry_ms+HORIZON_MIN*60_000
        entry=book.get(entry_ms);exit_=book.get(exit_ms)
        if entry is None or exit_ is None:
            missing+=1;continue
        g=(entry-exit_)/entry*10000.0
        vals.append(g);by_month[m].append(g)

    pooled=stat(vals)
    month_stats={m:stat(x) for m,x in sorted(by_month.items())}
    eligible=len(ev)
    missing_rate=(missing/eligible) if eligible else 1.0

    result={
      "status":"LICP_HIST_XALT_003_HOLDOUT",
      "candidate":{"target":"SOL","horizon_min":60,"direction":"SHORT","entry_delay_min":6},
      "partition":{"start":START,"end":END},
      "eligible_btc_ignition_events":eligible,
      "valid_events":len(vals),
      "missing_events":missing,
      "missing_rate":missing_rate,
      "pooled":pooled,
      "by_month":month_stats,
      "transfer_hurdle_bps":HURDLE_BPS,
      "single_pass":True,
      "discovery_reopened":False
    }

    if pooled["n"]<MIN_N:
        decision="HOLDOUT_INSUFFICIENT"
    else:
        month_ok=True
        for m in ("2025-11","2025-12"):
            s=month_stats.get(m,{"n":0,"mean_gross_bps":None})
            if s["n"]>=5 and not (s["mean_gross_bps"]>0):
                month_ok=False
        survive=(
            pooled["mean_gross_bps"]>HURDLE_BPS and
            pooled["median_gross_bps"]>0 and
            month_ok and
            missing_rate<=0.10
        )
        decision="HOLDOUT_SURVIVES" if survive else "HOLDOUT_FAIL"

    result["decision"]=decision
    p=Path("research/liquidation_cascade/receipts");p.mkdir(parents=True,exist_ok=True)
    (p/"licp_hist_xalt_003_holdout_v01.json").write_text(json.dumps(result,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__=="__main__":main()
