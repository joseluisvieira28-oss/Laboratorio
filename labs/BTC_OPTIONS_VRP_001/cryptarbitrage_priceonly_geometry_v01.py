#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, math, re, sys
from pathlib import Path
import pandas as pd

P=Path(sys.argv[1] if len(sys.argv)>1 else "btc_option_data_toshare.parquet")

def parse_ts(s):
    return pd.to_datetime(s,utc=True,errors="coerce")

def parse_expiry(df):
    x=pd.to_datetime(df.get("expiry_date"),utc=True,errors="coerce") if "expiry_date" in df else pd.Series(pd.NaT,index=df.index,dtype="datetime64[ns, UTC]")
    if x.notna().any(): return x
    tok=df["instrument_name"].astype(str).str.extract(r"(\d{1,2}[A-Z]{3}\d{2})",expand=False)
    return pd.to_datetime(tok,format="%d%b%y",utc=True,errors="coerce")

def main():
    raw=P.read_bytes()
    df=pd.read_parquet(P)
    required=["snapshot_time","instrument_name","bid_price","ask_price"]
    missing=[c for c in required if c not in df.columns]
    if missing: raise SystemExit("missing required columns: "+repr(missing))

    ts=parse_ts(df["snapshot_time"])
    expiry=parse_expiry(df)
    inst=df["instrument_name"].astype(str)
    parts=inst.str.extract(r"^[^-]+-(\d{1,2}[A-Z]{3}\d{2})-([0-9]+(?:\.[0-9]+)?)-([CP])$",expand=True)
    strike=pd.to_numeric(parts[1],errors="coerce")
    right=parts[2]
    bid=pd.to_numeric(df["bid_price"],errors="coerce")
    ask=pd.to_numeric(df["ask_price"],errors="coerce")
    bbo=(bid>0)&(ask>0)&(ask>=bid)
    dte=(expiry-ts).dt.total_seconds()/86400.0
    band=bbo & ts.notna() & expiry.notna() & strike.notna() & right.isin(["C","P"]) & (dte>=25.0) & (dte<=35.0)

    sub=pd.DataFrame({
        "hour":ts[band].dt.floor("h"),
        "date":ts[band].dt.date,
        "expiry":expiry[band].dt.date,
        "strike":strike[band],
        "right":right[band]
    })
    paired=0
    if len(sub):
        g=sub.groupby(["hour","expiry","strike"])["right"].nunique()
        paired=int((g>=2).sum())

    oi_present=0
    vol_present=0
    if "open_interest" in df:
        oi=pd.to_numeric(df["open_interest"],errors="coerce")
        oi_present=int((band & oi.notna()).sum())
    if "volume" in df:
        vol=pd.to_numeric(df["volume"],errors="coerce")
        vol_present=int((band & vol.notna()).sum())

    dates=int(sub["date"].nunique()) if len(sub) else 0
    hours=int(sub["hour"].nunique()) if len(sub) else 0
    rows=int(band.sum())

    if rows==0:
        classification="PRICE_ONLY_GEOMETRY_UNUSABLE"
    elif hours>=120 and dates>=90 and paired>=120:
        classification="PRICE_ONLY_GEOMETRY_RICH_EXECUTION_SIZE_BLOCKED"
    else:
        classification="PRICE_ONLY_GEOMETRY_SPARSE_EXECUTION_SIZE_BLOCKED"

    out={
      "diagnostic_id":"OVRP-CRYPTARBITRAGE-PRICEONLY-GEOMETRY-001",
      "classification":classification,
      "file_bytes":len(raw),
      "sha256":hashlib.sha256(raw).hexdigest(),
      "row_count":int(len(df)),
      "timestamped_rows":int(ts.notna().sum()),
      "instrument_identity_parse_rows":int(strike.notna().sum()),
      "positive_bbo_price_rows":int(bbo.sum()),
      "price_only_25_35_dte_rows":rows,
      "distinct_25_35_dte_dates":dates,
      "distinct_25_35_dte_hours":hours,
      "paired_call_put_snapshot_keys":paired,
      "open_interest_nonnull_rows_in_band":oi_present,
      "volume_nonnull_rows_in_band":vol_present,
      "bid_size_column_present":False,
      "ask_size_column_present":False,
      "execution_source_gate_reopened":False,
      "outcomes_opened":False,
      "returns_computed":False,
      "vrp_computed":False,
      "pnl_computed":False
    }
    Path("cryptarbitrage_priceonly_geometry_receipt_v01.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps(out,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
