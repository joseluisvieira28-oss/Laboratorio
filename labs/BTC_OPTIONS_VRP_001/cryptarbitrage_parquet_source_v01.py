#!/usr/bin/env python3
"""Source-only validator for the free Cryptarbitrage 2024H1 Deribit parquet."""
from __future__ import annotations
import hashlib, json, math, re, sys
from pathlib import Path
import pandas as pd

PATH=Path(sys.argv[1] if len(sys.argv)>1 else "btc_option_data_toshare.parquet")

ALIASES={
 "timestamp":["timestamp","time","datetime","date_time","snapshot_time","creation_timestamp"],
 "symbol":["symbol","instrument_name","instrument"],
 "expiry":["expiration","expiry","expiration_timestamp","expiry_timestamp"],
 "strike":["strike","strike_price"],
 "right":["type","option_type","right"],
 "bid_price":["best_bid_price","bid_price","bid"],
 "ask_price":["best_ask_price","ask_price","ask"],
 "bid_size":["best_bid_amount","best_bid_size","bid_amount","bid_size","bid_qty"],
 "ask_size":["best_ask_amount","best_ask_size","ask_amount","ask_size","ask_qty"],
 "underlying":["index_price","underlying_price","spot_price","underlying"]
}

def norm(x):
    return re.sub(r"[^a-z0-9]+","_",str(x).strip().lower()).strip("_")

def find_col(cols,names):
    by={norm(c):c for c in cols}
    for n in names:
        if norm(n) in by:return by[norm(n)]
    return None

def to_utc(series):
    # Support datetime, epoch ns/us/ms/s, and strings.
    if pd.api.types.is_datetime64_any_dtype(series):
        return pd.to_datetime(series,utc=True,errors="coerce")
    num=pd.to_numeric(series,errors="coerce")
    valid=num.dropna()
    if len(valid):
        med=float(valid.abs().median())
        unit="s"
        if med>1e17: unit="ns"
        elif med>1e14: unit="us"
        elif med>1e11: unit="ms"
        return pd.to_datetime(num,unit=unit,utc=True,errors="coerce")
    return pd.to_datetime(series,utc=True,errors="coerce")

def parse_expiry(series,symbol_series=None):
    if series is not None:
        if pd.api.types.is_datetime64_any_dtype(series):
            x=pd.to_datetime(series,utc=True,errors="coerce")
        else:
            num=pd.to_numeric(series,errors="coerce")
            valid=num.dropna()
            if len(valid):
                med=float(valid.abs().median())
                unit="s"
                if med>1e17: unit="ns"
                elif med>1e14: unit="us"
                elif med>1e11: unit="ms"
                x=pd.to_datetime(num,unit=unit,utc=True,errors="coerce")
            else:
                x=pd.to_datetime(series,utc=True,errors="coerce")
        if x.notna().any(): return x
    if symbol_series is None:
        return pd.Series(pd.NaT,index=series.index if series is not None else [],dtype="datetime64[ns, UTC]")
    tok=symbol_series.astype(str).str.extract(r"(?:^|-)(\d{1,2}[A-Z]{3}\d{2}|\d{6})(?:-|$)",expand=False)
    out=[]
    for v in tok:
        try:
            if pd.isna(v): out.append(pd.NaT)
            elif re.fullmatch(r"\d{6}",str(v)):
                out.append(pd.Timestamp.strptime(str(v),"%y%m%d").tz_localize("UTC"))
            else:
                out.append(pd.to_datetime(str(v),format="%d%b%y",utc=True))
        except Exception: out.append(pd.NaT)
    return pd.Series(out,index=symbol_series.index,dtype="datetime64[ns, UTC]")

def main():
    raw=PATH.read_bytes()
    sha=hashlib.sha256(raw).hexdigest()
    magic=(raw[:4]==b"PAR1" and raw[-4:]==b"PAR1")
    df=pd.read_parquet(PATH)
    cols=list(df.columns)
    c={k:find_col(cols,v) for k,v in ALIASES.items()}

    ts=to_utc(df[c["timestamp"]]) if c["timestamp"] else pd.Series(pd.NaT,index=df.index,dtype="datetime64[ns, UTC]")
    expiry=parse_expiry(df[c["expiry"]] if c["expiry"] else None,df[c["symbol"]] if c["symbol"] else None)

    def numeric(name):
        return pd.to_numeric(df[c[name]],errors="coerce") if c[name] else pd.Series(float("nan"),index=df.index)

    bid=numeric("bid_price"); ask=numeric("ask_price"); bs=numeric("bid_size"); az=numeric("ask_size")
    complete=(bid>0)&(ask>0)&(bs>0)&(az>0)&(ask>=bid)&ts.notna()&expiry.notna()

    dte=(expiry-ts).dt.total_seconds()/86400.0
    band=complete&(dte>=25.0)&(dte<=35.0)

    receipt={
      "source_probe_id":"OVRP-CRYPTARBITRAGE-2024H1-PARQUET-001",
      "classification":None,
      "file_name":PATH.name,
      "file_bytes":len(raw),
      "sha256":sha,
      "parquet_magic_pass":magic,
      "row_count":int(len(df)),
      "column_count":int(len(cols)),
      "columns":[str(x) for x in cols],
      "semantic_columns":c,
      "timestamped_rows":int(ts.notna().sum()),
      "timestamp_min_utc":ts.min().isoformat() if ts.notna().any() else None,
      "timestamp_max_utc":ts.max().isoformat() if ts.notna().any() else None,
      "distinct_utc_dates":int(ts.dt.date.nunique()) if ts.notna().any() else 0,
      "distinct_utc_hours":int(ts.dt.floor("h").nunique()) if ts.notna().any() else 0,
      "expiry_parse_rows":int(expiry.notna().sum()),
      "complete_bbo_rows":int(complete.sum()),
      "complete_bbo_25_35_dte_rows":int(band.sum()),
      "distinct_25_35_dte_dates":int(ts[band].dt.date.nunique()) if band.any() else 0,
      "outcomes_opened":False,
      "returns_computed":False,
      "pnl_computed":False
    }
    passed=(
      magic and receipt["timestamped_rows"]>0 and
      receipt["complete_bbo_rows"]>0 and
      receipt["complete_bbo_25_35_dte_rows"]>0 and
      receipt["distinct_25_35_dte_dates"]>=30
    )
    receipt["classification"]="CRYPTARBITRAGE_2024H1_SOURCE_FEASIBLE" if passed else "CRYPTARBITRAGE_2024H1_SOURCE_INSUFFICIENT"
    Path("cryptarbitrage_2024h1_source_receipt_v01.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
      "classification":receipt["classification"],
      "row_count":receipt["row_count"],
      "timestamp_min_utc":receipt["timestamp_min_utc"],
      "timestamp_max_utc":receipt["timestamp_max_utc"],
      "complete_bbo_rows":receipt["complete_bbo_rows"],
      "complete_bbo_25_35_dte_rows":receipt["complete_bbo_25_35_dte_rows"],
      "distinct_25_35_dte_dates":receipt["distinct_25_35_dte_dates"],
      "sha256":sha
    },sort_keys=True))
    return 0 if passed else 2

if __name__=="__main__":
    raise SystemExit(main())
