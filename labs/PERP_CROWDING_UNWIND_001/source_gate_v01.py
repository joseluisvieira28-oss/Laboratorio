#!/usr/bin/env python3
from __future__ import annotations
import io, json, urllib.request, zipfile
from pathlib import Path
import pandas as pd

DATES=["2021-03-15","2022-06-15","2023-10-15","2024-03-15","2024-11-15"]
BASE="https://data.binance.vision/data/futures/um/daily"

def fetch_zip(url):
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-PCU-SourceGate/0.1"})
    with urllib.request.urlopen(req,timeout=60) as r:
        raw=r.read()
        status=getattr(r,"status",200)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names=z.namelist()
        if not names: raise RuntimeError("empty zip")
        data=z.read(names[0])
    return status,raw,names[0],data

def read_csv(data,header=True):
    return pd.read_csv(io.BytesIO(data),header=0 if header else None)

def normcols(cols):
    return {str(c).strip().lower().replace(" ","_") for c in cols}

def main():
    rows=[]
    all_metrics=all_funding=all_kline=True
    oi_present=False; funding_present=False; timestamps_ok=True
    errors=[]
    for d in DATES:
        routes={
          "metrics":f"{BASE}/metrics/BTCUSDT/BTCUSDT-metrics-{d}.zip",
          "funding":f"{BASE.replace('/daily','/monthly')}/fundingRate/BTCUSDT/BTCUSDT-fundingRate-{d[:7]}.zip",
          "kline":f"{BASE}/klines/BTCUSDT/1h/BTCUSDT-1h-{d}.zip"
        }
        rec={"date":d}
        for kind,url in routes.items():
            try:
                status,raw,name,data=fetch_zip(url)
                rec[kind+"_status"]=status
                rec[kind+"_zip_bytes"]=len(raw)
                rec[kind+"_member"]=name
                if kind=="metrics":
                    df=read_csv(data,True); c=normcols(df.columns)
                    rec["metrics_rows"]=len(df); rec["metrics_columns"]=list(map(str,df.columns))
                    oi=bool({"sum_open_interest","sum_open_interest_value"} & c)
                    oi_present=oi_present or oi
                    tc=[x for x in df.columns if str(x).strip().lower().replace(" ","_") in {"create_time","timestamp","time"}]
                    if tc:
                        t=pd.to_datetime(df[tc[0]],utc=True,errors="coerce")
                        timestamps_ok=timestamps_ok and bool(t.notna().any())
                    else: timestamps_ok=False
                elif kind=="funding":
                    df=read_csv(data,True); c=normcols(df.columns)
                    rec["funding_rows"]=len(df); rec["funding_columns"]=list(map(str,df.columns))
                    # Monthly archive: require the frozen representative date to be present.
                    tc0=[x for x in df.columns if str(x).strip().lower().replace(" ","_") in {"calc_time","fundingtime","timestamp","time"}]
                    date_present=False
                    if tc0:
                        s0=df[tc0[0]]
                        n0=pd.to_numeric(s0,errors="coerce")
                        if n0.notna().any():
                            med0=float(n0.dropna().abs().median()); unit0="ms" if med0>1e11 else "s"
                            tt0=pd.to_datetime(n0,unit=unit0,utc=True,errors="coerce")
                        else:
                            tt0=pd.to_datetime(s0,utc=True,errors="coerce")
                        date_present=bool((tt0.dt.strftime("%Y-%m-%d")==d).any())
                    rec["funding_representative_date_present"]=date_present
                    if not date_present:
                        raise RuntimeError("monthly funding archive missing representative date")
                    fr=bool({"last_funding_rate","fundingrate","funding_rate"} & c)
                    funding_present=funding_present or fr
                    tc=[x for x in df.columns if str(x).strip().lower().replace(" ","_") in {"calc_time","fundingtime","timestamp","time"}]
                    if tc:
                        s=df[tc[0]]
                        n=pd.to_numeric(s,errors="coerce")
                        if n.notna().any():
                            med=float(n.dropna().abs().median()); unit="ms" if med>1e11 else "s"
                            t=pd.to_datetime(n,unit=unit,utc=True,errors="coerce")
                        else:
                            t=pd.to_datetime(s,utc=True,errors="coerce")
                        timestamps_ok=timestamps_ok and bool(t.notna().any())
                    else: timestamps_ok=False
                else:
                    # Binance klines archives are headerless.
                    df=read_csv(data,False)
                    rec["kline_rows"]=len(df); rec["kline_columns"]=len(df.columns)
                    if len(df.columns)<7: timestamps_ok=False
                    else:
                        t=pd.to_datetime(pd.to_numeric(df.iloc[:,0],errors="coerce"),unit="ms",utc=True,errors="coerce")
                        timestamps_ok=timestamps_ok and bool(t.notna().any())
            except Exception as e:
                rec[kind+"_error"]=f"{type(e).__name__}:{str(e)[:300]}"
                errors.append({"date":d,"kind":kind,"error":rec[kind+"_error"]})
                if kind=="metrics": all_metrics=False
                elif kind=="funding": all_funding=False
                else: all_kline=False
        rows.append(rec)

    successes={
      "metrics_dates_ok":sum(1 for r in rows if r.get("metrics_status")==200),
      "funding_dates_ok":sum(1 for r in rows if r.get("funding_status")==200),
      "kline_dates_ok":sum(1 for r in rows if r.get("kline_status")==200)
    }
    full=(successes["metrics_dates_ok"]==len(DATES) and successes["funding_dates_ok"]==len(DATES)
          and successes["kline_dates_ok"]==len(DATES) and oi_present and funding_present and timestamps_ok)
    some=(successes["metrics_dates_ok"]>0 and successes["funding_dates_ok"]>0 and successes["kline_dates_ok"]>0
          and oi_present and funding_present)
    classification="PCU_SOURCE_FULL" if full else ("PCU_SOURCE_LIMITED" if some else "PCU_SOURCE_BLOCKED")
    out={
      "lab_id":"PERP-CROWDING-UNWIND-001",
      "source_gate_id":"PCU-BINANCE-METRICS-FUNDING-001",
      "classification":classification,
      "representative_dates":DATES,
      "successes":successes,
      "open_interest_field_present":oi_present,
      "funding_rate_field_present":funding_present,
      "timestamps_parseable":timestamps_ok,
      "records":rows,
      "errors":errors,
      "authentication_used":False,
      "cash_spend_usd":0,
      "outcomes_opened":False,
      "returns_computed":False,
      "pnl_computed":False,
      "protected_2025_2026_opened":False
    }
    Path("pcu_source_receipt_v01.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
      "classification":classification,
      "successes":successes,
      "open_interest_field_present":oi_present,
      "funding_rate_field_present":funding_present,
      "timestamps_parseable":timestamps_ok,
      "error_count":len(errors)
    },sort_keys=True))
    return 0

if __name__=="__main__": raise SystemExit(main())
