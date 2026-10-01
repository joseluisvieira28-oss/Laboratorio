#!/usr/bin/env python3
from __future__ import annotations
import hashlib,io,json,urllib.request
from collections import Counter
from pathlib import Path

LAB_ID="LICP-HIST-XALT-005"
EVENT_URL="https://raw.githubusercontent.com/edwinyeeshunwan/forced-or-frantic/fe8e96ac2d22bc0fd40fd032f3075f2d47ec4f04/data/event_table_liq.parquet"
BASE="https://data.binance.vision/data/futures/um/monthly/klines/SOLUSDT/1m"
MONTHS=[f"2026-{m:02d}" for m in range(1,10)]
START="2026-01-01T00:00:00Z"
END="2026-10-01T00:00:00Z"
UA={"User-Agent":"CryptoLab-LICP-XALT005-Source/0.1"}
OUT=Path("research/liquidation_cascade/receipts")

def get(url):
    req=urllib.request.Request(url,headers=UA)
    with urllib.request.urlopen(req,timeout=60) as r:
        return r.read(),{"status":int(r.status),"content_length":int(r.headers.get("Content-Length","0") or 0)}

def head(url):
    req=urllib.request.Request(url,method="HEAD",headers=UA)
    try:
        with urllib.request.urlopen(req,timeout=30) as r:
            return {"status":int(r.status),"content_length":int(r.headers.get("Content-Length","0") or 0),"ok":int(r.status)==200 and int(r.headers.get("Content-Length","0") or 0)>0}
    except Exception as e:
        return {"status":None,"content_length":0,"ok":False,"error":type(e).__name__+":"+str(e)}

def main():
    import pandas as pd
    raw,meta=get(EVENT_URL)
    sha=hashlib.sha256(raw).hexdigest()
    df=pd.read_parquet(io.BytesIO(raw),columns=["t0","symbol"])
    df["t0"]=pd.to_datetime(df["t0"],utc=True)
    st=pd.Timestamp(START);en=pd.Timestamp(END)
    btc=df[(df["symbol"].astype(str)=="BTC")&(df["t0"]>=st)&(df["t0"]<en)].copy()
    by_month=Counter(x.strftime("%Y-%m") for x in btc["t0"])
    months_ge5=sorted(m for m,n in by_month.items() if n>=5)
    archives={}
    for m in MONTHS:
        url=f"{BASE}/SOLUSDT-1m-{m}.zip"
        archives[m]={"zip":head(url),"checksum":head(url+".CHECKSUM"),"url":url}
        archives[m]["route_pass"]=archives[m]["zip"]["ok"] and archives[m]["checksum"]["ok"]
    gates={
      "event_table_fetchable":meta["status"]==200 and len(raw)>0,
      "min_80_btc_events":len(btc)>=80,
      "min_6_months_with_5_events":len(months_ge5)>=6,
      "sol_archives_9_of_9":all(archives[m]["route_pass"] for m in MONTHS)
    }
    result={
      "lab_id":LAB_ID,"schema":"LICP_XALT005_SOURCE_GATE_V0.1",
      "classification":"SOURCE_2026_PASS" if all(gates.values()) else ("INSUFFICIENT_2026_EVENT_SAMPLE" if gates["event_table_fetchable"] and gates["sol_archives_9_of_9"] else "SOURCE_2026_BLOCKED"),
      "event_url":EVENT_URL,"event_table_sha256":sha,"event_table_bytes":len(raw),
      "table_min_t0":df["t0"].min().isoformat() if len(df) else None,
      "table_max_t0":df["t0"].max().isoformat() if len(df) else None,
      "confirmatory_start":START,"confirmatory_end":END,
      "btc_event_count":int(len(btc)),
      "btc_events_by_month":dict(sorted(by_month.items())),
      "months_with_5_events":months_ge5,
      "archives":archives,"gates":gates,
      "sol_price_rows_read":False,"outcomes_opened":False,"pnl_computed":False,
      "trading_authority":"NONE"
    }
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"LICP_XALT005_SOURCE_GATE_V0_1.json").write_text(json.dumps(result,indent=2,sort_keys=True))
    print(json.dumps({k:result[k] for k in ["classification","event_table_sha256","table_min_t0","table_max_t0","btc_event_count","btc_events_by_month","months_with_5_events","gates"]},indent=2,sort_keys=True))
    raise SystemExit(0 if result["classification"]=="SOURCE_2026_PASS" else 2)
if __name__=="__main__":main()
