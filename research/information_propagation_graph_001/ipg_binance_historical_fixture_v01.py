#!/usr/bin/env python3
from __future__ import annotations
import csv,hashlib,io,json,urllib.request,zipfile
from datetime import datetime,timezone
from pathlib import Path

OUT=Path("artifacts/ipg001_binance_historical_fixture_v01.json")
DATE="2024-01-01"
START=int(datetime(2024,1,1,tzinfo=timezone.utc).timestamp()*1000)
END=int(datetime(2024,1,2,tzinfo=timezone.utc).timestamp()*1000)-1
BASE="https://data.binance.vision/data"
SETS=[
 ("spot",f"{BASE}/spot/daily/aggTrades/BTCUSDT/BTCUSDT-aggTrades-{DATE}.zip",8,5),
 ("usd_m_futures",f"{BASE}/futures/um/daily/aggTrades/BTCUSDT/BTCUSDT-aggTrades-{DATE}.zip",7,5),
]

def get(url):
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-IPG-BinanceArchive/0.1"})
    with urllib.request.urlopen(req,timeout=120) as r:return r.read()

rows_out=[];overall=True
for name,url,mincols,tsidx in SETS:
    row={"name":name,"url":url}
    try:
        raw=get(url);digest=hashlib.sha256(raw).hexdigest()
        chk=get(url+".CHECKSUM").decode().strip().split()[0].lower()
        row["zip_sha256"]=digest;row["checksum_expected"]=chk;row["checksum_pass"]=digest==chk
        z=zipfile.ZipFile(io.BytesIO(raw))
        names=z.namelist()
        if len(names)!=1:raise RuntimeError(f"ZIP_MEMBER_COUNT:{len(names)}")
        count=0;first_ts=None;last_ts=None;prev_ts=None;prev_id=None
        id_nondec=True;ts_nondec=True;outside=0;header_detected=False
        with z.open(names[0]) as fh:
            text=io.TextIOWrapper(fh,encoding="utf-8",newline="")
            reader=csv.reader(text)
            for rec in reader:
                if not rec:continue
                try:
                    aid=int(rec[0]);ts=int(rec[tsidx])
                except Exception:
                    if count==0 and not header_detected:
                        header_detected=True;continue
                    raise
                if len(rec)<mincols:raise RuntimeError(f"SHORT_ROW:{len(rec)}")
                count+=1
                if first_ts is None:first_ts=ts
                last_ts=ts
                if prev_id is not None and aid<prev_id:id_nondec=False
                if prev_ts is not None and ts<prev_ts:ts_nondec=False
                if not (START<=ts<=END):outside+=1
                prev_id=aid;prev_ts=ts
        passed=row["checksum_pass"] and count>0 and id_nondec and ts_nondec and outside==0
        row.update({"csv_member":names[0],"rows":count,"header_detected":header_detected,
                    "first_timestamp_ms":first_ts,"last_timestamp_ms":last_ts,
                    "aggregate_trade_id_nondecreasing":id_nondec,
                    "timestamp_nondecreasing":ts_nondec,"rows_outside_fixture_day":outside,
                    "pass":passed})
    except Exception as e:
        row.update({"pass":False,"error":f"{type(e).__name__}:{str(e)[:500]}"})
    overall=overall and row["pass"];rows_out.append(row)
receipt={
 "lab_id":"INFORMATION-PROPAGATION-GRAPH-001","stage":"BINANCE_HISTORICAL_ARCHIVE_FIXTURE_V0.1",
 "captured_at_utc":datetime.now(timezone.utc).isoformat(),"fixture_date":DATE,
 "classification":"BINANCE_HISTORICAL_ARCHIVE_FIXTURE_PASS" if overall else "BINANCE_HISTORICAL_ARCHIVE_FIXTURE_BLOCKED",
 "datasets":rows_out,
 "price_quantity_values_retained":False,"predictive_analysis_performed":False,
 "market_returns_computed":False,"pnl_opened":False,"mutation":False,
}
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2))
if not overall:raise SystemExit(2)
