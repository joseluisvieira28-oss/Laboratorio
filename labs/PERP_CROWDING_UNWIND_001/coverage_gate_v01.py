#!/usr/bin/env python3
from __future__ import annotations
import io,json,urllib.request,zipfile
from pathlib import Path
import pandas as pd

START="2021-01"; END="2024-12"
BASE="https://data.binance.vision/data/futures/um/monthly"

def months():
    return pd.period_range(START,END,freq="M").astype(str).tolist()

def fetch(url):
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-PCU/0.1"})
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

def main():
    Path("pcu_cache").mkdir(exist_ok=True)
    rec=[]; metrics=[]; funding=[]; klines=[]
    for m in months():
        row={"month":m}
        routes={
          "metrics":f"{BASE}/metrics/BTCUSDT/BTCUSDT-metrics-{m}.zip",
          "funding":f"{BASE}/fundingRate/BTCUSDT/BTCUSDT-fundingRate-{m}.zip",
          "kline":f"{BASE}/klines/BTCUSDT/1h/BTCUSDT-1h-{m}.zip"
        }
        for kind,u in routes.items():
            try:
                name,data,n=fetch(u)
                row[kind+"_ok"]=True; row[kind+"_zip_bytes"]=n
                if kind=="metrics":
                    d=parse_metrics(data); d["source_month"]=m; metrics.append(d); row["metrics_rows"]=len(d)
                elif kind=="funding":
                    d=parse_funding(data); d["source_month"]=m; funding.append(d); row["funding_rows"]=len(d)
                else:
                    d=parse_klines(data); d["source_month"]=m; klines.append(d); row["kline_rows"]=len(d)
            except Exception as e:
                row[kind+"_ok"]=False; row[kind+"_error"]=f"{type(e).__name__}:{str(e)[:240]}"
        rec.append(row)
    common=[r["month"] for r in rec if r.get("metrics_ok") and r.get("funding_ok") and r.get("kline_ok")]
    yc={str(y):sum(x.startswith(str(y)+"-") for x in common) for y in range(2021,2025)}
    full=(len(common)>=46 and min(yc.values())>=11)
    limited=(len(common)>=36 and min(yc.values())>=8)
    cls="PCU_COVERAGE_FULL" if full else ("PCU_COVERAGE_LIMITED" if limited else "PCU_COVERAGE_BLOCKED")
    if metrics: pd.concat(metrics,ignore_index=True).to_csv("pcu_cache/metrics.csv",index=False)
    if funding: pd.concat(funding,ignore_index=True).to_csv("pcu_cache/funding.csv",index=False)
    if klines: pd.concat(klines,ignore_index=True).to_csv("pcu_cache/klines.csv",index=False)
    out={"classification":cls,"common_month_count":len(common),"common_months":common,"common_months_by_year":yc,"records":rec,"outcomes_opened":False}
    Path("pcu_coverage_receipt_v01.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"classification":cls,"common_month_count":len(common),"common_months_by_year":yc},sort_keys=True))
    if cls=="PCU_COVERAGE_BLOCKED": return 2
    return 0

if __name__=="__main__": raise SystemExit(main())
