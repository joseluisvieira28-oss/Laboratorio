#!/usr/bin/env python3
"""Source-only test: exact Binance Vision historical aggTrades 2026-04-01 BTC, ETH."""
import csv
import datetime as dt
import gzip
import hashlib
import io
import json
import math
import pathlib
import re
import sys
import tempfile
import urllib.request
import zipfile
from collections import defaultdict

DATE="2026-04-01"
SYMBOLS=("BTCUSDT","ETHUSDT")
START=int(dt.datetime(2026,4,1,tzinfo=dt.timezone.utc).timestamp()*1000)
END=START+86_400_000
ROOT="https://data.binance.vision/data/futures/um/daily/aggTrades"
OUT=pathlib.Path("artifacts/event_futures_ati_source_v01")
OUT.mkdir(parents=True,exist_ok=True)

def sign(px,qty,buyer_maker):
    if not math.isfinite(px) or not math.isfinite(qty) or px<=0 or qty<=0:
        raise ValueError("BAD_PRICE_OR_QTY")
    k=str(buyer_maker).strip().lower()
    if k not in ("true","false"):
        raise ValueError("INVALID_AGGRESSOR_FLAG")
    return (-1 if k=="true" else 1)*px*qty

def selftest():
    assert sign(100,2,"true")==-200
    assert sign(100,2,"false")==200
    try: sign(100,2,"invalid")
    except ValueError: pass
    else: raise AssertionError("BAD_MAKER_FLAG_ACCEPTED")
    print("SYNTHETIC_SIGN_GUARDS_PASS")

def get(url,path=None,limit=140_000_000):
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-ReadOnlySourceGate/0.1"})
    hasher=hashlib.sha256()
    total=0
    with urllib.request.urlopen(req,timeout=60) as resp:
        if resp.status!=200: raise RuntimeError("SOURCE_HTTP_NOT_200")
        with open(path,"wb") if path else tempfile.TemporaryFile() as handle:
            while True:
                piece=resp.read(1024*1024)
                if not piece: break
                total+=len(piece)
                if total>limit: raise RuntimeError("SOURCE_TOO_LARGE")
                hasher.update(piece)
                handle.write(piece)
            handle.seek(0)
            payload=handle.read() if not path else None
    return hasher.hexdigest(),total,payload

def one(symbol,folder):
    name=symbol+"-aggTrades-"+DATE+".zip"
    url=ROOT+"/"+symbol+"/"+name
    _,_,check=get(url+".CHECKSUM",limit=2000)
    text=check.decode("utf-8")
    match=re.search(r"(?i)\b([0-9a-f]{64})\b\s+\*?(\S+)",text)
    if not match or match.group(2).rsplit("/",1)[-1]!=name:
        raise RuntimeError("MISSING_OR_INVALID_PUBLISHER_CHECKSUM")
    expected=match.group(1).lower()
    p=pathlib.Path(folder)/name
    sha,bytesize,_=get(url,path=p)
    if sha!=expected: raise RuntimeError("PUBLISHER_SHA256_MISMATCH")
    bins=defaultdict(lambda:[0.0,0.0,0])
    rows=0
    prev_ts=None
    prev_id=None
    first=None
    last=None
    with zipfile.ZipFile(p) as archive:
        entries=[e for e in archive.infolist() if not e.is_dir()]
        if len(entries)!=1 or not entries[0].filename.endswith(".csv"):
            raise RuntimeError("BAD_ZIP_STRUCTURE")
        if entries[0].file_size>1_400_000_000:
            raise RuntimeError("UNCOMPRESSED_LIMIT")
        with archive.open(entries[0]) as binary:
            reader=csv.reader(io.TextIOWrapper(binary,encoding="utf-8-sig",newline=""))
            for row in reader:
                if rows==0 and row and row[0].lower().startswith("agg_trade"):
                    continue
                if len(row)<7: raise RuntimeError("SCHEMA_CHANGED")
                try:
                    id_=int(row[0]);px=float(row[1]);qty=float(row[2]);t=int(row[5])
                    notional=sign(px,qty,row[6])
                except ValueError as exc: raise RuntimeError("INVALID_SOURCE_ROW") from exc
                if not START<=t<END: raise RuntimeError("OUT_OF_SCOPE_TIMESTAMP")
                if prev_ts is not None and t<prev_ts: raise RuntimeError("TIME_REVERSED")
                if prev_id is not None and id_<=prev_id: raise RuntimeError("ID_REVERSED")
                prev_ts=t;prev_id=id_
                if first is None: first=t
                last=t
                bucket=t//60000*60000
                acc=bins[bucket]
                if notional>0: acc[0]+=notional
                else: acc[1]+=-notional
                acc[2]+=1
                rows+=1
                if rows>12_000_000:raise RuntimeError("TOO_MANY_ROWS")
    if rows<1000 or len(bins)<600:raise RuntimeError("COVERAGE_LOW")
    path=OUT/(symbol+"_minute_source_only.csv.gz")
    with gzip.open(path,"wt",newline="",encoding="utf-8") as f:
        writer=csv.writer(f)
        writer.writerow(["minute_start_utc_ms","taker_buy_notional","taker_sell_notional","aggtrade_count"])
        for m,(b,s,n) in sorted(bins.items()):
            writer.writerow([m,f"{b:.8f}",f"{s:.8f}",n])
    return dict(symbol=symbol,archive_url=url,publisher_checksum_url=url+".CHECKSUM",
                archive_sha256=sha,publisher_sha256=expected,zip_bytes=bytesize,
                rows=rows,active_minutes=len(bins),first_ms=first,last_ms=last,
                derived_filename=path.name,
                derived_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                exchange_receive_timestamps_known=False)

def main():
    selftest()
    if "--self-test" in sys.argv:return
    report=dict(study="EVENT_FUTURES_ATI_SOURCE_V01",scope="SOURCE_ONLY",
      day=DATE,symbols=list(SYMBOLS),gate="STARTING",records=[],
      no_market_outcomes_opened=True,holdout_2026_09_accessed=False,
      payouts_observed=0,model_activated=False,orders=0,account_access=0)
    try:
        with tempfile.TemporaryDirectory() as folder:
            for symbol in SYMBOLS:
                report["records"].append(one(symbol,folder))
        report["gate"]="HISTORICAL_AGGRESSOR_SOURCE_PASS"
    except Exception as e:
        report["gate"]="SOURCE_BLOCKED"
        report["block_reason"]=str(e)
        raise
    finally:
        (OUT/"receipt.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
        print(json.dumps(report,indent=2,sort_keys=True))

if __name__=="__main__": main()
