#!/usr/bin/env python3
from __future__ import annotations
import json, urllib.parse, urllib.request
from pathlib import Path
import pandas as pd

BASE="https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"
PARAMS={
  "assets":"eth",
  "metrics":"FeeTotNtv,SplyCur",
  "frequency":"1d",
  "start_time":"2022-12-01",
  "end_time":"2024-12-31",
  "page_size":"10000"
}

def main():
    url=BASE+"?"+urllib.parse.urlencode(PARAMS)
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-EDFF-SourceGate/0.2"})
    with urllib.request.urlopen(req,timeout=60) as r:
        payload=json.loads(r.read().decode("utf-8"))
    rows=payload.get("data",[])
    if payload.get("next_page_token"):
        raise SystemExit("unexpected pagination: frozen page_size should cover bounded interval")
    df=pd.DataFrame(rows)
    required={"time","FeeTotNtv","SplyCur"}
    if not required.issubset(df.columns):
        out={"classification":"EDFF_SOURCE_BLOCKED","reason":"missing required fields","columns":list(df.columns),
             "outcomes_opened":False,"requested_end_time":"2024-12-31"}
        Path("edff_source_receipt_v02.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
        print(json.dumps(out,sort_keys=True)); return 2
    df["time"]=pd.to_datetime(df["time"],utc=True,errors="coerce")
    df["FeeTotNtv"]=pd.to_numeric(df["FeeTotNtv"],errors="coerce")
    df["SplyCur"]=pd.to_numeric(df["SplyCur"],errors="coerce")
    n=len(df)
    valid_t=df["time"].notna()
    mn=df.loc[valid_t,"time"].min(); mx=df.loc[valid_t,"time"].max()
    fee_nonnull=float(df["FeeTotNtv"].notna().mean()) if n else 0
    supply_nonnull=float(df["SplyCur"].notna().mean()) if n else 0
    positive_fee=float((df["FeeTotNtv"]>0).mean()) if n else 0
    supply_floor=float(df["SplyCur"].min()) if df["SplyCur"].notna().any() else None
    dencun=pd.Timestamp("2024-03-13",tz="UTC")
    post=int(((df["time"]>=dencun)&(df["time"]<=pd.Timestamp("2024-12-31",tz="UTC"))).sum())
    checks={
      "rows_gte_750":n>=750,
      "max_time_lte_2024_12_31":bool(mx is not pd.NaT and mx<=pd.Timestamp("2024-12-31T23:59:59Z")),
      "min_time_lte_2022_12_02":bool(mn is not pd.NaT and mn<=pd.Timestamp("2022-12-02T00:00:00Z")),
      "fee_nonnull_gte_0_98":fee_nonnull>=.98,
      "supply_nonnull_gte_0_98":supply_nonnull>=.98,
      "positive_fee_gte_0_98":positive_fee>=.98,
      "supply_floor_gt_100m":bool(supply_floor is not None and supply_floor>100_000_000),
      "dencun_date_present":bool((df["time"].dt.strftime("%Y-%m-%d")=="2024-03-13").any()),
      "post_dencun_days_gte_290":post>=290
    }
    if all(checks.values()):
        cls="EDFF_SOURCE_FULL"
    elif n>=600 and checks["max_time_lte_2024_12_31"] and fee_nonnull>=.9 and supply_nonnull>=.9 and post>=250:
        cls="EDFF_SOURCE_LIMITED"
    else:
        cls="EDFF_SOURCE_BLOCKED"
    out={
      "lab_id":"ETH-DEMAND-FEE-FLOW-001","source_gate_id":"EDFF-COINMETRICS-COMMUNITY-001",
      "classification":cls,"request_url_without_credentials":url,
      "row_count":n,"time_min":mn.isoformat() if pd.notna(mn) else None,
      "time_max":mx.isoformat() if pd.notna(mx) else None,
      "fee_nonnull_fraction":fee_nonnull,"supply_nonnull_fraction":supply_nonnull,
      "positive_fee_fraction":positive_fee,"supply_min_eth":supply_floor,
      "post_dencun_day_count":post,"checks":checks,
      "next_page_token_present":bool(payload.get("next_page_token")),
      "credentials_used":False,"cash_spend_usd":0,
      "outcomes_opened":False,"returns_computed":False,
      "protected_2025_2026_requested":False
    }
    Path("edff_source_receipt_v02.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    df[["time","FeeTotNtv","SplyCur"]].to_csv("edff_fee_supply_bounded_v02.csv",index=False)
    print(json.dumps(out,sort_keys=True))
    return 0 if cls!="EDFF_SOURCE_BLOCKED" else 2

if __name__=="__main__": raise SystemExit(main())
