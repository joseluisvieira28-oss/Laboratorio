#!/usr/bin/env python3
import io,json,urllib.request
from pathlib import Path

URL="https://raw.githubusercontent.com/edwinyeeshunwan/forced-or-frantic/fe8e96ac2d22bc0fd40fd032f3075f2d47ec4f04/data/event_table_liq.parquet"

def main():
    import pandas as pd
    req=urllib.request.Request(URL,headers={"User-Agent":"Crypto-Lab-LICP-HIST/0.2"})
    with urllib.request.urlopen(req,timeout=30) as r:
        raw=r.read()
    df=pd.read_parquet(io.BytesIO(raw),columns=["t0","symbol"])
    df["t0"]=pd.to_datetime(df["t0"],utc=True)
    if df.empty: raise RuntimeError("EMPTY_EVENT_TABLE")
    months=df["t0"].dt.strftime("%Y-%m").value_counts().sort_index().to_dict()
    symbols=df["symbol"].astype(str).value_counts().sort_index().to_dict()
    out={
      "purpose":"PINNED EXTERNAL EVENT TIME SOURCE ONLY",
      "pinned_url":URL,
      "bytes":len(raw),
      "rows":int(len(df)),
      "t0_min":df["t0"].min().isoformat(),
      "t0_max":df["t0"].max().isoformat(),
      "symbol_counts":{str(k):int(v) for k,v in symbols.items()},
      "month_counts":{str(k):int(v) for k,v in months.items()},
      "allowed_columns":["t0","symbol"]
    }
    good=(
      len(df)>=100 and
      set(df["symbol"].astype(str).unique()).issubset({"BTC","ETH"}) and
      df["t0"].min().isoformat()[:10]>="2025-08-10" and
      df["t0"].max().isoformat()[:10]<="2025-12-31"
    )
    out["gate"]="PASS_SAMPLE" if good else "BLOCKED"
    p=Path("research/liquidation_cascade/receipts");p.mkdir(parents=True,exist_ok=True)
    (p/"licp_hist_002_external_event_source_v02.json").write_text(
      json.dumps(out,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps(out,indent=2,sort_keys=True))
    raise SystemExit(0 if good else 2)

if __name__=="__main__":main()
