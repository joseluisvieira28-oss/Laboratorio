#!/usr/bin/env python3
from __future__ import annotations
import calendar, concurrent.futures, io, json, urllib.request, zipfile
from pathlib import Path
import pandas as pd

START="2022-01"; END="2024-12"
MONTHLY="https://data.binance.vision/data/futures/um/monthly"
DAILY="https://data.binance.vision/data/futures/um/daily"
SYMBOL="ETHUSDT"

def months():
    return pd.period_range(START,END,freq="M").astype(str).tolist()

def fetch(url):
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-PCU-ETH/0.1"})
    with urllib.request.urlopen(req,timeout=60) as r: raw=r.read()
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        n=z.namelist()[0]; data=z.read(n)
    return n,data,len(raw)

def parse_metrics(data):
    df=pd.read_csv(io.BytesIO(data))
    keep=[c for c in ["create_time","symbol","sum_open_interest","sum_open_interest_value"] if c in df.columns]
    if "create_time" not in keep or "sum_open_interest" not in keep: raise RuntimeError("metrics schema")
    return df[keep]

def parse_funding(data):
    df=pd.read_csv(io.BytesIO(data))
    if not {"calc_time","last_funding_rate"}.issubset(df.columns): raise RuntimeError("funding schema")
    return df[["calc_time","last_funding_rate"]]

def parse_klines(data):
    df=pd.read_csv(io.BytesIO(data),header=None)
    if df.shape[1]<7: raise RuntimeError("kline schema")
    df=df.iloc[:,:12].copy()
    df.columns=["open_time","open","high","low","close","volume","close_time","quote_volume","trades","taker_base","taker_quote","ignore"]
    return df[["open_time","open","close"]]

def fetch_metric_day(ds):
    u=f"{DAILY}/metrics/{SYMBOL}/{SYMBOL}-metrics-{ds}.zip"
    try:
        _,data,n=fetch(u)
        d=parse_metrics(data); d["source_date"]=ds
        return ds,d,n,None
    except Exception as e:
        return ds,None,0,f"{type(e).__name__}:{str(e)[:180]}"

def metric_month(m):
    y,mo=map(int,m.split("-")); nd=calendar.monthrange(y,mo)[1]
    dates=[f"{y:04d}-{mo:02d}-{d:02d}" for d in range(1,nd+1)]
    out=[]; errs=[]; total_bytes=0
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
        for ds,d,n,e in ex.map(fetch_metric_day,dates):
            if d is not None:
                out.append(d); total_bytes+=n
            else: errs.append({"date":ds,"error":e})
    ok=len(out); ratio=ok/nd
    df=pd.concat(out,ignore_index=True) if out else None
    return df,{"metric_days_ok":ok,"calendar_days":nd,"metric_day_ratio":ratio,
               "metrics_full":ratio>=0.95,"metrics_usable":ratio>=0.80,
               "metric_errors":errs,"metrics_zip_bytes_total":total_bytes}

def main():
    Path("pcu_eth_cache").mkdir(exist_ok=True)
    rec=[]; metrics=[]; funding=[]; klines=[]
    for m in months():
        row={"month":m}
        md,mstat=metric_month(m); row.update(mstat)
        if md is not None:
            md["source_month"]=m; metrics.append(md); row["metrics_rows"]=len(md)
        routes={
          "funding":f"{MONTHLY}/fundingRate/{SYMBOL}/{SYMBOL}-fundingRate-{m}.zip",
          "kline":f"{MONTHLY}/klines/{SYMBOL}/1h/{SYMBOL}-1h-{m}.zip"
        }
        for kind,u in routes.items():
            try:
                _,data,n=fetch(u)
                row[kind+"_ok"]=True; row[kind+"_zip_bytes"]=n
                if kind=="funding":
                    d=parse_funding(data); d["source_month"]=m; funding.append(d); row["funding_rows"]=len(d)
                else:
                    d=parse_klines(data); d["source_month"]=m; klines.append(d); row["kline_rows"]=len(d)
            except Exception as e:
                row[kind+"_ok"]=False; row[kind+"_error"]=f"{type(e).__name__}:{str(e)[:240]}"
        rec.append(row)

    full_months=[r["month"] for r in rec if r.get("metrics_full") and r.get("funding_ok") and r.get("kline_ok")]
    usable_months=[r["month"] for r in rec if r.get("metrics_usable") and r.get("funding_ok") and r.get("kline_ok")]
    fy={str(y):sum(x.startswith(str(y)+"-") for x in full_months) for y in range(2022,2025)}
    uy={str(y):sum(x.startswith(str(y)+"-") for x in usable_months) for y in range(2022,2025)}
    full=(len(full_months)>=35 and min(fy.values())>=11)
    limited=(len(usable_months)>=30 and min(uy.values())>=8)
    cls="PCU_ETH_COVERAGE_FULL" if full else ("PCU_ETH_COVERAGE_LIMITED" if limited else "PCU_ETH_COVERAGE_BLOCKED")
    if metrics: pd.concat(metrics,ignore_index=True).to_csv("pcu_eth_cache/metrics.csv",index=False)
    if funding: pd.concat(funding,ignore_index=True).to_csv("pcu_eth_cache/funding.csv",index=False)
    if klines: pd.concat(klines,ignore_index=True).to_csv("pcu_eth_cache/klines.csv",index=False)
    out={"classification":cls,"full_month_count":len(full_months),"usable_month_count":len(usable_months),
         "full_months_by_year":fy,"usable_months_by_year":uy,"records":rec,"outcomes_opened":False}
    Path("pcu_eth_coverage_receipt_v01.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"classification":cls,"full_month_count":len(full_months),"usable_month_count":len(usable_months),
                      "full_months_by_year":fy,"usable_months_by_year":uy},sort_keys=True))
    if cls=="PCU_ETH_COVERAGE_BLOCKED": return 2
    return 0

if __name__=="__main__": raise SystemExit(main())
