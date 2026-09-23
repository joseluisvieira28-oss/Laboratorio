#!/usr/bin/env python3
"""ARQ-001-MTF-001 Binance 1h source census + normalized export.

Scope:
- official Binance Vision USD-M Futures monthly 1h klines only;
- BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT, XRPUSDT, DOGEUSDT;
- 2023-12 warm-up + 2024 Discovery;
- published CHECKSUM verification;
- no 2025/2026 requests;
- no strategy outcomes/PnL.
"""

from __future__ import annotations

import csv, gzip, hashlib, io, json, math, re, sys, time, urllib.error, urllib.request, zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

BASE="https://data.binance.vision/data/futures/um/monthly/klines"
SYMBOLS=("BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT","DOGEUSDT")
MONTHS=("2023-12",)+tuple(f"2024-{m:02d}" for m in range(1,13))
OUT_CENSUS=Path("arq001_mtf_binance_1h_source_census.json")
OUT_DATA=Path("arq001_mtf_binance_1h_2023_12_2024.csv.gz")
UA="Crypto-Lab-ARQ001-MTF-BinanceSource/0.1"

class GateError(RuntimeError): pass

def req(url:str, attempts:int=5)->bytes:
    last=None
    for i in range(attempts):
        try:
            r=urllib.request.Request(url,headers={"User-Agent":UA})
            with urllib.request.urlopen(r,timeout=90) as x:
                if x.status!=200: raise GateError(f"HTTP_{x.status}:{url}")
                return x.read()
        except Exception as e:
            last=e
            if i+1<attempts: time.sleep(min(8,1.5*(i+1)))
    raise GateError(f"DOWNLOAD_FAILED:{url}:{type(last).__name__}:{last}")

def checksum(url:str)->str:
    raw=req(url+".CHECKSUM").decode("utf-8","replace")
    m=re.search(r"(?i)\b([0-9a-f]{64})\b",raw)
    if not m: raise GateError(f"CHECKSUM_PARSE:{url}")
    return m.group(1).lower()

def month_bounds(ym:str):
    y,m=map(int,ym.split("-"))
    lo=datetime(y,m,1,tzinfo=timezone.utc)
    if m==12: hi=datetime(y+1,1,1,tzinfo=timezone.utc)
    else: hi=datetime(y,m+1,1,tzinfo=timezone.utc)
    return int(lo.timestamp()*1000),int(hi.timestamp()*1000)

def parse_zip(raw:bytes,url:str):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        bad=z.testzip()
        if bad: raise GateError(f"ZIP_CRC:{url}:{bad}")
        names=[n for n in z.namelist() if n.lower().endswith(".csv") and not n.endswith("/")]
        if len(names)!=1: raise GateError(f"CSV_COUNT:{url}:{len(names)}")
        text=z.read(names[0]).decode("utf-8-sig")
    rows=[r for r in csv.reader(io.StringIO(text)) if r]
    if not rows: raise GateError(f"EMPTY:{url}")
    # Binance archives may be headerless or have a header.
    body=rows
    try: int(float(rows[0][0]))
    except Exception: body=rows[1:]
    if not body or any(len(r)<6 for r in body): raise GateError(f"SCHEMA:{url}")
    out=[]
    for r in body:
        ts=int(float(r[0]))
        if ts<10_000_000_000: ts*=1000
        op=float(r[1]); hi=float(r[2]); lo=float(r[3]); cl=float(r[4])
        if not all(math.isfinite(x) and x>0 for x in (op,hi,lo,cl)):
            raise GateError(f"BAD_OHLC:{url}:{ts}")
        out.append((ts,op,hi,lo,cl))
    return out

def main()->int:
    census={
        "lab_id":"ARQ-001-MTF-001",
        "gate":"BINANCE_1H_SOURCE_CENSUS_V0.1",
        "classification":"RUNNING",
        "symbols":list(SYMBOLS),
        "months":list(MONTHS),
        "checksum_verified_objects":0,
        "objects":[],
        "protected_2025_accessed":False,
        "protected_2026_accessed":False,
        "strategy_outcomes_opened":False,
        "pnl_computed":False,
        "errors":[]
    }
    all_rows=[]
    try:
        for s in SYMBOLS:
            seen=set()
            symbol_rows=[]
            for ym in MONTHS:
                url=f"{BASE}/{s}/1h/{s}-1h-{ym}.zip"
                raw=req(url)
                pub=checksum(url)
                actual=hashlib.sha256(raw).hexdigest()
                if actual!=pub: raise GateError(f"CHECKSUM_MISMATCH:{s}:{ym}")
                rows=parse_zip(raw,url)
                lo,hi=month_bounds(ym)
                ts=[x[0] for x in rows]
                expected=list(range(lo,hi,3_600_000))
                if ts!=expected:
                    raise GateError(f"HOURLY_GRID_FAIL:{s}:{ym}:rows={len(ts)}:expected={len(expected)}")
                if any(t in seen for t in ts): raise GateError(f"DUPLICATE_TS:{s}:{ym}")
                seen.update(ts); symbol_rows.extend(rows)
                census["objects"].append({
                    "symbol":s,"month":ym,"sha256":actual,"published_sha256":pub,
                    "checksum_verified":True,"row_count":len(rows),
                    "first_timestamp_utc":datetime.fromtimestamp(ts[0]/1000,tz=timezone.utc).isoformat().replace("+00:00","Z"),
                    "last_timestamp_utc":datetime.fromtimestamp(ts[-1]/1000,tz=timezone.utc).isoformat().replace("+00:00","Z")
                })
                census["checksum_verified_objects"]+=1
            if len(symbol_rows)!=9528:
                raise GateError(f"SYMBOL_TOTAL_ROWS:{s}:{len(symbol_rows)}/9528")
            all_rows.extend((s,*r) for r in symbol_rows)

        census["classification"]="SOURCE_CENSUS_PASS"
        census["total_objects"]=len(census["objects"])
        census["rows_per_symbol"]=9528
        census["total_normalized_rows"]=len(all_rows)
        census["first_timestamp_utc"]="2023-12-01T00:00:00Z"
        census["last_timestamp_utc"]="2024-12-31T23:00:00Z"
        census["census_sha256"]=hashlib.sha256(
            json.dumps(census,sort_keys=True,separators=(",",":")).encode()
        ).hexdigest()
        OUT_CENSUS.write_text(json.dumps(census,indent=2,sort_keys=True)+"\n",encoding="utf-8")

        with gzip.open(OUT_DATA,"wt",newline="",encoding="utf-8") as gz:
            w=csv.writer(gz)
            w.writerow(["symbol","open_time_ms","open","high","low","close"])
            for row in sorted(all_rows,key=lambda x:(x[1],x[0])):
                w.writerow(row)

        print(json.dumps({
            "classification":"SOURCE_CENSUS_PASS",
            "objects":len(census["objects"]),
            "rows_per_symbol":9528,
            "total_rows":len(all_rows),
            "protected_2025_accessed":False,
            "protected_2026_accessed":False,
            "strategy_outcomes_opened":False,
            "pnl_computed":False,
            "census_sha256":census["census_sha256"],
            "normalized_gzip_sha256":hashlib.sha256(OUT_DATA.read_bytes()).hexdigest()
        },sort_keys=True))
        return 0
    except Exception as e:
        census["classification"]="SOURCE_OR_TECHNICAL_FAIL_CLOSED"
        census["errors"].append(f"{type(e).__name__}:{e}")
        OUT_CENSUS.write_text(json.dumps(census,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        print(json.dumps({"classification":census["classification"],"errors":census["errors"]},sort_keys=True))
        return 1

if __name__=="__main__":
    sys.exit(main())
