#!/usr/bin/env python3
import csv,io,json,statistics,urllib.request,zipfile
from collections import defaultdict
from pathlib import Path

EVENT_URL="https://raw.githubusercontent.com/edwinyeeshunwan/forced-or-frantic/fe8e96ac2d22bc0fd40fd032f3075f2d47ec4f04/data/event_table_liq.parquet"
BASE="https://data.binance.vision/data/futures/um/monthly/klines"
START="2025-08-10T00:00:00+00:00"
END="2025-10-31T23:59:59.999999+00:00"
TARGETS=("ETH","SOL")
HORIZONS=(5,15,30,60)
PRIMARY_DELAY=6
CEILING_DELAY=5
HURDLE=16.0
UA={"User-Agent":"Crypto-Lab-LICP-XALT/0.1"}

def get(url):
    req=urllib.request.Request(url,headers=UA)
    with urllib.request.urlopen(req,timeout=60) as r:return r.read()

def events():
    import pandas as pd
    d=pd.read_parquet(io.BytesIO(get(EVENT_URL)),columns=["t0","symbol"])
    d["t0"]=pd.to_datetime(d["t0"],utc=True)
    st=pd.Timestamp(START);en=pd.Timestamp(END)
    x=d[(d["symbol"].astype(str)=="BTC")&(d["t0"]>=st)&(d["t0"]<=en)]
    if x.empty:raise RuntimeError("NO_BTC_DISCOVERY_EVENTS")
    return [v.to_pydatetime() for v in x["t0"]]

def month(sym,m):
    url=f"{BASE}/{sym}USDT/1m/{sym}USDT-1m-{m}.zip"
    raw=get(url);z=zipfile.ZipFile(io.BytesIO(raw))
    if z.testzip() is not None:raise RuntimeError(f"CRC:{sym}:{m}")
    names=[n for n in z.namelist() if not n.endswith("/")]
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
    if len(out)<40000:raise RuntimeError(f"SHORT_MONTH:{sym}:{m}:{len(out)}")
    return out

def stat(xs):
    return {"n":len(xs),
      "mean_gross_bps":statistics.fmean(xs) if xs else None,
      "median_gross_bps":statistics.median(xs) if xs else None,
      "positive_rate":sum(v>0 for v in xs)/len(xs) if xs else None,
      "mean_transfer_ceiling_net_bps":statistics.fmean(xs)-HURDLE if xs else None}

def run(delay,ev,px):
    res={}
    for target in TARGETS:
        hrs={h:[] for h in HORIZONS};mos={h:defaultdict(list) for h in HORIZONS}
        for t in ev:
            m=t.strftime("%Y-%m");book=px[(target,m)]
            entry_ms=int(t.timestamp()*1000)+delay*60_000
            entry=book.get(entry_ms)
            if entry is None:continue
            for h in HORIZONS:
                fut=book.get(entry_ms+h*60_000)
                if fut is None:continue
                g=(entry-fut)/entry*10000.0
                hrs[h].append(g);mos[h][m].append(g)
        res[target]={}
        for h in HORIZONS:
            res[target][str(h)]={"pooled":stat(hrs[h]),
              "by_month":{m:stat(x) for m,x in sorted(mos[h].items())}}
    return res

def main():
    ev=events()
    months=sorted(set(t.strftime("%Y-%m") for t in ev))
    if any(m not in {"2025-08","2025-09","2025-10"} for m in months):
        raise RuntimeError("HOLDOUT_MONTH_LEAK")
    px={(s,m):month(s,m) for s in TARGETS for m in months}
    primary=run(PRIMARY_DELAY,ev,px)
    ceiling=run(CEILING_DELAY,ev,px)
    survivors=[]
    for target in TARGETS:
        for h in HORIZONS:
            x=primary[target][str(h)]
            p=x["pooled"]
            posm=sum(1 for z in x["by_month"].values() if z["n"] and z["mean_gross_bps"]>0)
            if p["n"]>=30 and p["mean_gross_bps"]>16 and p["median_gross_bps"]>0 and posm>=2:
                survivors.append({"target":target,"horizon_min":h,"n":p["n"],
                  "mean_gross_bps":p["mean_gross_bps"],
                  "median_gross_bps":p["median_gross_bps"],
                  "mean_transfer_ceiling_net_bps":p["mean_transfer_ceiling_net_bps"],
                  "positive_months":posm})
    out={
      "status":"LICP_HIST_XALT_003_DISCOVERY",
      "btc_ignition_events":len(ev),
      "primary_delay_min":PRIMARY_DELAY,
      "ceiling_delay_min":CEILING_DELAY,
      "primary":primary,"optimistic_ceiling":ceiling,
      "survivors":survivors,"holdout_opened":False
    }
    if survivors:
        rank={"ETH":0,"SOL":1}
        selected=sorted(survivors,key=lambda x:(-x["mean_transfer_ceiling_net_bps"],x["horizon_min"],rank[x["target"]]))[0]
        out["decision"]="DISCOVERY_SURVIVOR_EXISTS";out["selected_candidate"]=selected
    else:
        out["decision"]="LICP_HIST_XALT_003_DISCOVERY_NO_EDGE";out["selected_candidate"]=None
    p=Path("research/liquidation_cascade/receipts");p.mkdir(parents=True,exist_ok=True)
    (p/"licp_hist_xalt_003_discovery_v01.json").write_text(json.dumps(out,indent=2,sort_keys=True))
    print(json.dumps(out,indent=2,sort_keys=True))

if __name__=="__main__":main()
