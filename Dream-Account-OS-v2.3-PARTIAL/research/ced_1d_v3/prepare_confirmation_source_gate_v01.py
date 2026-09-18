#!/usr/bin/env python3
"""CED-1D-V1 V3 2025 Confirmation source/provenance gate V0.1.

SOURCE ONLY. Downloads and authenticates the exact AVAXUSDT/SOLUSDT 1m
monthly archives required by the frozen Confirmation plus official Binance
USD-M funding-history rows. It does not compute signals, returns, PnL,
candidate metrics, routing, or promotion.
"""
from __future__ import annotations
import argparse, concurrent.futures, hashlib, json, math, shutil, time, urllib.parse, urllib.request, zipfile
from pathlib import Path

KLINE_BASE = "https://data.binance.vision/data/futures/um/monthly/klines"
FUNDING_API = "https://fapi.binance.com/fapi/v1/fundingRate"
SYMBOLS = ("AVAXUSDT","SOLUSDT")
MONTHS = tuple([f"2024-{m:02d}" for m in range(9,13)] + [f"2025-{m:02d}" for m in range(1,13)])
CONFIRMATION_MONTHS = tuple(f"2025-{m:02d}" for m in range(1,13))
FUNDING_START_MS = 1735689600000
FUNDING_END_MS = 1767225599999
FUNDING_LIMIT = 1000
UA = "CED-1D-V1-V3-CONFIRMATION-SOURCE-GATE/1.0 source-only"

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def sha256_file(p: Path) -> str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1<<20), b""):
            h.update(chunk)
    return h.hexdigest()

def fetch_bytes(url: str, timeout=180) -> bytes:
    last=None
    for i in range(5):
        try:
            req=urllib.request.Request(url, headers={"User-Agent":UA,"Accept":"application/json,*/*"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:
            last=e
            time.sleep(1.5*(i+1))
    raise RuntimeError(f"FETCH_FAILED:{url}:{type(last).__name__}:{last}")

def fetch_file(url: str, dest: Path):
    dest.parent.mkdir(parents=True,exist_ok=True)
    b=fetch_bytes(url)
    dest.write_bytes(b)

def check_zip(p: Path):
    with zipfile.ZipFile(p) as zf:
        bad=zf.testzip()
        if bad is not None:
            raise RuntimeError(f"ZIP_CRC_FAIL:{p}:{bad}")
        csvs=[x for x in zf.infolist() if x.filename.lower().endswith(".csv")]
        if len(csvs)!=1:
            raise RuntimeError(f"ZIP_CSV_MEMBER_COUNT_INVALID:{p}:{len(csvs)}")

def load_registry(path: Path):
    rows=json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(rows,list) or len(rows)!=600:
        raise RuntimeError(f"CANONICAL_REGISTRY_600_REQUIRED:{len(rows) if isinstance(rows,list) else 'NON_LIST'}")
    return {(str(x["symbol"]),str(x["month"])):x for x in rows}

def kline_one(reg, root: Path, symbol: str, month: str):
    key=(symbol,month)
    rr=reg.get(key)
    if rr is None:
        raise RuntimeError(f"REGISTRY_SLOT_MISSING:{symbol}:{month}")
    if rr.get("status")!="PASS" or rr.get("classification")!="PASS" or rr.get("provider_checksum_match") is not True:
        raise RuntimeError(f"REGISTRY_NOT_PASS:{symbol}:{month}")
    if rr.get("provenance")!="RECONSTRUCTED_FROM_RAW":
        raise RuntimeError(f"REGISTRY_PROVENANCE_UNEXPECTED:{symbol}:{month}:{rr.get('provenance')}")
    expected=str(rr["provider_sha256"]).lower()
    if expected != str(rr["local_sha256"]).lower() or expected != str(rr["zip_sha256"]).lower():
        raise RuntimeError(f"REGISTRY_SHA_DISAGREEMENT:{symbol}:{month}")
    name=f"{symbol}-1m-{month}.zip"
    url=f"{KLINE_BASE}/{symbol}/1m/{name}"
    dest=root/"klines"/symbol/name
    fetch_file(url,dest)
    got=sha256_file(dest)
    if got!=expected:
        raise RuntimeError(f"KLINE_BYTE_HASH_MISMATCH:{symbol}:{month}:{got}:{expected}")
    check_zip(dest)
    return {
        "symbol":symbol,"month":month,"source":"BINANCE_PUBLIC_DATA_MONTHLY_1M",
        "url":url,"sha256":got,"expected_sha256":expected,"status":"PASS",
        "confirmation_2025":month in CONFIRMATION_MONTHS
    }

def canonical_funding_hash(rows):
    b=(json.dumps(rows,sort_keys=True,separators=(",",":"))+"\n").encode()
    return sha256_bytes(b),b

def funding_symbol(root: Path, symbol: str):
    rawdir=root/"funding_raw"/symbol
    rawdir.mkdir(parents=True,exist_ok=True)
    start=FUNDING_START_MS
    pages=[]
    normalized=[]
    page_no=0
    while start<=FUNDING_END_MS:
        q=urllib.parse.urlencode({
            "symbol":symbol,"startTime":start,"endTime":FUNDING_END_MS,"limit":FUNDING_LIMIT
        })
        url=f"{FUNDING_API}?{q}"
        raw=fetch_bytes(url)
        page_no+=1
        p=rawdir/f"page_{page_no:03d}.json"
        p.write_bytes(raw)
        try:
            data=json.loads(raw.decode("utf-8"))
        except Exception as e:
            raise RuntimeError(f"FUNDING_JSON_PARSE_FAIL:{symbol}:{page_no}:{e}")
        if not isinstance(data,list):
            raise RuntimeError(f"FUNDING_RESPONSE_NOT_LIST:{symbol}:{page_no}:{data}")
        pages.append({
            "page":page_no,"url":url,"raw_sha256":sha256_bytes(raw),"row_count":len(data)
        })
        if not data:
            break
        last=None
        for row in data:
            if str(row.get("symbol"))!=symbol:
                raise RuntimeError(f"FUNDING_SYMBOL_DRIFT:{symbol}:{row}")
            if "fundingTime" not in row or "fundingRate" not in row or "markPrice" not in row:
                raise RuntimeError(f"FUNDING_REQUIRED_FIELD_MISSING:{symbol}:{row}")
            ft=int(row["fundingTime"])
            if not (FUNDING_START_MS<=ft<=FUNDING_END_MS):
                raise RuntimeError(f"FUNDING_TIME_OUTSIDE_2025:{symbol}:{ft}")
            try:
                rate=float(row["fundingRate"]); mark=float(row["markPrice"])
            except Exception:
                raise RuntimeError(f"FUNDING_NUMERIC_PARSE_FAIL:{symbol}:{row}")
            if not math.isfinite(rate) or not math.isfinite(mark) or mark<=0:
                raise RuntimeError(f"FUNDING_NUMERIC_INVALID:{symbol}:{row}")
            normalized.append({
                "symbol":symbol,
                "fundingTime":ft,
                "fundingRate":str(row["fundingRate"]),
                "markPrice":str(row["markPrice"])
            })
            last=ft
        if len(data)<FUNDING_LIMIT:
            break
        if last is None or last < start:
            raise RuntimeError(f"FUNDING_PAGINATION_STALL:{symbol}:{start}:{last}")
        start=last+1
    times=[x["fundingTime"] for x in normalized]
    if times!=sorted(times):
        raise RuntimeError(f"FUNDING_NOT_ASCENDING:{symbol}")
    if len(times)!=len(set(times)):
        raise RuntimeError(f"FUNDING_DUPLICATE_TIME:{symbol}")
    if not normalized:
        raise RuntimeError(f"FUNDING_EMPTY:{symbol}")
    ch,cb=canonical_funding_hash(normalized)
    (root/"funding_normalized").mkdir(parents=True,exist_ok=True)
    (root/"funding_normalized"/f"{symbol}_2025.json").write_bytes(cb)
    return {
        "symbol":symbol,
        "status":"PASS",
        "endpoint":FUNDING_API,
        "query_start_ms":FUNDING_START_MS,
        "query_end_ms":FUNDING_END_MS,
        "row_count":len(normalized),
        "first_funding_time":times[0],
        "last_funding_time":times[-1],
        "page_count":len(pages),
        "canonical_sha256":ch,
        "pages":pages,
        "rate_summaries_computed":False,
        "funding_pnl_computed":False
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--registry",required=True)
    ap.add_argument("--output",required=True)
    ap.add_argument("--workers",type=int,default=8)
    a=ap.parse_args()
    out=Path(a.output)
    if out.exists():
        raise RuntimeError("OUTPUT_ALREADY_EXISTS")
    out.mkdir(parents=True)
    reg=load_registry(Path(a.registry))

    jobs=[(s,m) for s in SYMBOLS for m in MONTHS]
    kline_records=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs=[ex.submit(kline_one,reg,out,s,m) for s,m in jobs]
        for f in concurrent.futures.as_completed(futs):
            kline_records.append(f.result())
    if len(kline_records)!=32:
        raise RuntimeError(f"KLINE_COUNT_NOT_32:{len(kline_records)}")
    if sum(bool(x["confirmation_2025"]) for x in kline_records)!=24:
        raise RuntimeError("CONFIRMATION_KLINE_COUNT_NOT_24")

    funding_records=[funding_symbol(out,s) for s in SYMBOLS]

    receipt={
        "status":"CED1D_V3_2025_SOURCE_GATE_PASS",
        "stage":"SOURCE_PROVENANCE_ONLY",
        "symbols":list(SYMBOLS),
        "kline_months":"2024-09_through_2025-12",
        "kline_files":len(kline_records),
        "confirmation_2025_kline_files":24,
        "funding_symbols":len(funding_records),
        "funding_source":"BINANCE_USD_M_FAPI_FUNDING_RATE_HISTORY",
        "outcomes_computed":False,
        "signals_computed":False,
        "returns_computed":False,
        "pnl_computed":False,
        "promotion_computed":False,
        "year_2025_source_accessed":True,
        "year_2025_outcomes_accessed":False,
        "year_2026_accessed":False,
        "live_trading_authorized":False,
        "exchange_mutation_authorized":False,
        "kline_records":sorted(kline_records,key=lambda x:(x["symbol"],x["month"])),
        "funding_records":funding_records
    }
    (out/"SOURCE_GATE_RECEIPT.json").write_text(
        json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8",newline="\n"
    )
    print(receipt["status"])

if __name__=="__main__":
    main()
