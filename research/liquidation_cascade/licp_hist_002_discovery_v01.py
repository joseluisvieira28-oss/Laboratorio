#!/usr/bin/env python3
import csv, io, json, statistics, urllib.request, zipfile
from collections import defaultdict
from pathlib import Path

EVENT_URL="https://raw.githubusercontent.com/edwinyeeshunwan/forced-or-frantic/fe8e96ac2d22bc0fd40fd032f3075f2d47ec4f04/data/event_table_liq.parquet"
BINANCE_BASE="https://data.binance.vision/data/futures/um/monthly/klines"
DISCOVERY_START="2025-08-10T00:00:00+00:00"
DISCOVERY_END="2025-10-31T23:59:59.999999+00:00"
HORIZONS_MIN=(5,15,30,60)
PRIMARY_DELAY_MIN=6
CEILING_DELAY_MIN=5
TRANSFER_HURDLE_BPS=16.0
UA={"User-Agent":"Crypto-Lab-LICP-HIST-002/0.1"}

def get(url):
    req=urllib.request.Request(url,headers=UA)
    with urllib.request.urlopen(req,timeout=60) as r:
        return r.read()

def load_events():
    import pandas as pd
    raw=get(EVENT_URL)
    # Forbidden external outcome columns are never loaded.
    df=pd.read_parquet(io.BytesIO(raw),columns=["t0","symbol"])
    df["t0"]=pd.to_datetime(df["t0"],utc=True)
    start=pd.Timestamp(DISCOVERY_START)
    end=pd.Timestamp(DISCOVERY_END)
    # Fail closed against holdout leakage.
    if any(df.loc[df["t0"]>end,"t0"] < start):
        raise RuntimeError("PARTITION_LOGIC_ERROR")
    d=df[(df["t0"]>=start)&(df["t0"]<=end)].copy()
    if d.empty: raise RuntimeError("EMPTY_DISCOVERY_EVENTS")
    return [(x.t0.to_pydatetime(),str(x.symbol)) for x in d.itertuples()]

def load_month(symbol,month):
    url=f"{BINANCE_BASE}/{symbol}USDT/1m/{symbol}USDT-1m-{month}.zip"
    raw=get(url)
    z=zipfile.ZipFile(io.BytesIO(raw))
    if z.testzip() is not None: raise RuntimeError(f"CRC_FAIL:{symbol}:{month}")
    names=[n for n in z.namelist() if not n.endswith("/")]
    if len(names)!=1: raise RuntimeError(f"ZIP_MEMBERS:{symbol}:{month}")
    out={}
    with z.open(names[0]) as fh:
        reader=csv.reader(io.TextIOWrapper(fh,encoding="utf-8"))
        for row in reader:
            if not row: continue
            try:
                ts=int(row[0]); op=float(row[1])
            except Exception:
                # tolerate a header row, nothing else
                if str(row[0]).lower() in {"open_time","open time"}: continue
                raise
            out[ts]=op
    if len(out)<40_000: raise RuntimeError(f"INSUFFICIENT_MONTH:{symbol}:{month}:{len(out)}")
    return out

def ts_ms(dt):
    return int(dt.timestamp()*1000)

def directional_short(entry,future):
    return (entry-future)/entry*10000.0

def stat(xs):
    return {
      "n":len(xs),
      "mean_gross_bps":statistics.fmean(xs) if xs else None,
      "median_gross_bps":statistics.median(xs) if xs else None,
      "positive_rate":sum(x>0 for x in xs)/len(xs) if xs else None,
      "mean_transfer_ceiling_net_bps":statistics.fmean(xs)-TRANSFER_HURDLE_BPS if xs else None,
    }

def main():
    events=load_events()
    months=sorted(set(t.strftime("%Y-%m") for t,_ in events))
    if any(m not in {"2025-08","2025-09","2025-10"} for m in months):
        raise RuntimeError(f"HOLDOUT_MONTH_REQUESTED:{months}")

    prices={}
    for sym in ("BTC","ETH"):
        for m in months:
            prices[(sym,m)]=load_month(sym,m)

    result={
      "status":"LICP_HIST_002_DISCOVERY",
      "event_source_commit":"fe8e96ac2d22bc0fd40fd032f3075f2d47ec4f04",
      "discovery_start":DISCOVERY_START,
      "discovery_end":DISCOVERY_END,
      "holdout_opened":False,
      "events_loaded":len(events),
      "primary_delay_min":PRIMARY_DELAY_MIN,
      "ceiling_delay_min":CEILING_DELAY_MIN,
      "transfer_hurdle_bps":TRANSFER_HURDLE_BPS,
      "primary":{},
      "optimistic_ceiling":{},
    }

    def evaluate(delay):
        by_h={h:[] for h in HORIZONS_MIN}
        by_asset={h:defaultdict(list) for h in HORIZONS_MIN}
        by_month={h:defaultdict(list) for h in HORIZONS_MIN}
        missing=0
        rows=[]
        for t,sym in events:
            month=t.strftime("%Y-%m")
            book=prices[(sym,month)]
            entry_t=ts_ms(t)+delay*60_000
            entry=book.get(entry_t)
            if entry is None:
                missing+=1;continue
            rec={"t0":t.isoformat(),"symbol":sym,"entry_time_ms":entry_t}
            for h in HORIZONS_MIN:
                fut=book.get(entry_t+h*60_000)
                if fut is None:
                    missing+=1;continue
                g=directional_short(entry,fut)
                by_h[h].append(g);by_asset[h][sym].append(g);by_month[h][month].append(g)
                rec[str(h)]={"gross_directional_bps":g,
                             "transfer_ceiling_net_bps":g-TRANSFER_HURDLE_BPS}
            rows.append(rec)
        summary={}
        for h in HORIZONS_MIN:
            summary[str(h)]={
              "pooled":stat(by_h[h]),
              "by_asset":{a:stat(xs) for a,xs in sorted(by_asset[h].items())},
              "by_month":{m:stat(xs) for m,xs in sorted(by_month[h].items())},
            }
        return summary,missing,rows

    primary,pmiss,prows=evaluate(PRIMARY_DELAY_MIN)
    ceiling,cmiss,crows=evaluate(CEILING_DELAY_MIN)
    result["primary"]=primary
    result["optimistic_ceiling"]=ceiling
    result["primary_missing_points"]=pmiss
    result["ceiling_missing_points"]=cmiss

    survivors=[]
    for h in HORIZONS_MIN:
        x=primary[str(h)]
        pooled=x["pooled"]
        btc=x["by_asset"].get("BTC",{"n":0})
        eth=x["by_asset"].get("ETH",{"n":0})
        positive_months=sum(1 for r in x["by_month"].values()
                            if r["n"]>0 and r["mean_gross_bps"]>0)
        ok=(
          pooled["n"]>=50 and
          btc.get("n",0)>=15 and
          eth.get("n",0)>=15 and
          pooled["mean_gross_bps"]>16.0 and
          pooled["median_gross_bps"]>0 and
          positive_months>=2
        )
        if ok:
            survivors.append({
              "horizon_min":h,
              "n":pooled["n"],
              "mean_gross_bps":pooled["mean_gross_bps"],
              "median_gross_bps":pooled["median_gross_bps"],
              "mean_transfer_ceiling_net_bps":pooled["mean_transfer_ceiling_net_bps"],
              "positive_months":positive_months,
              "btc_n":btc.get("n",0),"eth_n":eth.get("n",0)
            })

    result["survivors"]=survivors
    if survivors:
        selected=max(survivors,key=lambda x:(x["mean_transfer_ceiling_net_bps"],-x["horizon_min"]))
        result["decision"]="DISCOVERY_SURVIVOR_EXISTS"
        result["selected_candidate"]=selected
    else:
        result["decision"]="LICP_HIST_002_DISCOVERY_NO_EDGE"
        result["selected_candidate"]=None

    # Do not persist event-level rows to reduce accidental holdout/process misuse.
    out=Path("research/liquidation_cascade/receipts");out.mkdir(parents=True,exist_ok=True)
    (out/"licp_hist_002_discovery_v01.json").write_text(
      json.dumps(result,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__=="__main__":main()
