#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, os, re, subprocess, sys
from pathlib import Path
import pandas as pd

DRIVE_ID="1H1hSTgy1qFVPro1_96pmMU035bvh3WoQ"

def sha256(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def pick_col(cols, names):
    m={re.sub(r"[^a-z0-9]+","_",str(c).lower()).strip("_"):c for c in cols}
    for n in names:
        k=re.sub(r"[^a-z0-9]+","_",n.lower()).strip("_")
        if k in m:return m[k]
    return None

def parse_any(path):
    suf=Path(path).suffix.lower()
    if suf==".csv":
        return pd.read_csv(path,low_memory=False)
    if suf==".rds":
        import pyreadr
        x=pyreadr.read_r(path)
        if not x: raise RuntimeError("empty rds")
        return next(iter(x.values()))
    raise RuntimeError("unsupported "+suf)

def classify(df):
    cols=list(df.columns)
    inst=pick_col(cols,["instrument_name","instrument","symbol"])
    ts=pick_col(cols,["timestamp","time","datetime","date"])
    price=pick_col(cols,["price","trade_price","last_price","instrument_price"])
    qty=pick_col(cols,["amount","quantity","qty","size","trade_amount"])
    bidp=pick_col(cols,["best_bid_price","bid_price","bid"])
    askp=pick_col(cols,["best_ask_price","ask_price","ask"])
    bids=pick_col(cols,["best_bid_amount","best_bid_size","bid_amount","bid_size"])
    asks=pick_col(cols,["best_ask_amount","best_ask_size","ask_amount","ask_size"])

    t=pd.to_datetime(df[ts],utc=True,errors="coerce") if ts else pd.Series(pd.NaT,index=df.index,dtype="datetime64[ns, UTC]")
    # numeric epoch fallback
    if ts and t.notna().sum()==0:
        n=pd.to_numeric(df[ts],errors="coerce")
        v=n.dropna()
        if len(v):
            med=float(v.abs().median()); unit="s"
            if med>1e17:unit="ns"
            elif med>1e14:unit="us"
            elif med>1e11:unit="ms"
            t=pd.to_datetime(n,unit=unit,utc=True,errors="coerce")

    years=(t.max()-t.min()).total_seconds()/31557600 if t.notna().any() else 0
    core=bool(inst and ts and t.notna().any())
    if core and len(df)>=100000 and years>=1.0:
        c="UWA_TRADE_HISTORY_FULL"
    elif core and len(df)>0:
        c="UWA_TRADE_HISTORY_LIMITED"
    else:
        c="UWA_SOURCE_BLOCKED"

    return {
      "classification":c,
      "row_count":int(len(df)),
      "columns":[str(x) for x in cols],
      "instrument_col":inst,"timestamp_col":ts,"trade_price_col":price,"trade_qty_col":qty,
      "best_bid_price_col":bidp,"best_ask_price_col":askp,
      "bid_size_col":bids,"ask_size_col":asks,
      "timestamped_rows":int(t.notna().sum()),
      "timestamp_min_utc":t.min().isoformat() if t.notna().any() else None,
      "timestamp_max_utc":t.max().isoformat() if t.notna().any() else None,
      "span_years":years
    }

def main():
    candidates=[]
    for p in ["uwa_author_data.rds","Deribit_BTC_option_all.rds","Deribit_w_IV.csv"]:
        if Path(p).exists() and Path(p).stat().st_size>1000:candidates.append(p)
    results=[]
    for p in candidates:
        try:
            df=parse_any(p)
            x=classify(df)
            x.update({"file":p,"bytes":Path(p).stat().st_size,"sha256":sha256(p)})
            results.append(x)
        except Exception as e:
            results.append({"file":p,"parse_error":f"{type(e).__name__}:{str(e)[:300]}",
                            "bytes":Path(p).stat().st_size,"sha256":sha256(p)})
    usable=[r for r in results if r.get("classification")]
    if not usable:
        final="UWA_SOURCE_BLOCKED"
        best=None
    else:
        rank={"UWA_TRADE_HISTORY_FULL":2,"UWA_TRADE_HISTORY_LIMITED":1,"UWA_SOURCE_BLOCKED":0}
        best=max(usable,key=lambda r:rank.get(r["classification"],-1))
        final=best["classification"]
    out={
      "source_probe_id":"UWA-DERIBIT-TRADES-SOURCE-001",
      "classification":final,
      "objects":results,
      "best_object":best,
      "cash_spend_usd":0,
      "outcomes_opened":False,
      "returns_computed":False,
      "pnl_computed":False,
      "vrp_computed":False
    }
    Path("uwa_deribit_source_receipt_v01.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps(out,sort_keys=True))
    return 0

if __name__=="__main__": raise SystemExit(main())
