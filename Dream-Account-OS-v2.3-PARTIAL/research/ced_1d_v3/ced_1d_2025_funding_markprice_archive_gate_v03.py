#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import urllib.request
import zipfile
from pathlib import Path

SYMBOLS=("AVAXUSDT","SOLUSDT")
YEAR=2025
START_MS=1735689600000
END_MS=1767225599999
EXPECTED_RECORDS=1095
FUNDING_BASE="https://data.binance.vision/data/futures/um/monthly/fundingRate"
MARK_BASE="https://data.binance.vision/data/futures/um/monthly/markPriceKlines"
UA="CED1D-2025-FUNDING-MARKPRICE-ARCHIVE/0.3"


class SourceError(RuntimeError):
    pass


def canonical(obj):
    return json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()


def fetch(url:str,timeout:int=90)->bytes:
    req=urllib.request.Request(url,headers={"User-Agent":UA})
    try:
        with urllib.request.urlopen(req,timeout=timeout) as r:
            if r.status!=200:
                raise SourceError(f"HTTP_{r.status}:{url}")
            return r.read()
    except Exception as exc:
        if isinstance(exc,SourceError):
            raise
        raise SourceError(f"FETCH_FAIL:{type(exc).__name__}:{exc}:{url}") from exc


def verified_zip(url:str,out:Path)->tuple[bytes,str]:
    raw=fetch(url)
    check=fetch(url+".CHECKSUM").decode("utf-8",errors="replace").strip().split()
    if not check:
        raise SourceError(f"EMPTY_CHECKSUM:{url}")
    expected=check[0].lower()
    actual=hashlib.sha256(raw).hexdigest()
    if actual!=expected:
        raise SourceError(f"CHECKSUM_MISMATCH:{url}:{actual}:{expected}")
    name=url.rsplit("/",1)[-1]
    (out/name).write_bytes(raw)
    (out/(name+".CHECKSUM")).write_text(expected+"  "+name+"\n",encoding="utf-8")
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        bad=zf.testzip()
        if bad is not None:
            raise SourceError(f"ZIP_CRC_FAIL:{url}:{bad}")
    return raw,actual


def normalize_ms(value)->int:
    n=int(value)
    while n>10**14:
        n//=1000
    return n


def one_member_rows(raw:bytes)->list[list[str]]:
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        members=[n for n in zf.namelist() if not n.endswith("/")]
        if len(members)!=1:
            raise SourceError(f"ZIP_MEMBER_COUNT:{len(members)}")
        return list(csv.reader(io.TextIOWrapper(zf.open(members[0]),encoding="utf-8")))


def funding_month(symbol:str,month:int,out:Path)->tuple[list[dict],dict]:
    name=f"{symbol}-fundingRate-{YEAR}-{month:02d}.zip"
    url=f"{FUNDING_BASE}/{symbol}/{name}"
    raw,sha=verified_zip(url,out)
    rows=one_member_rows(raw)
    if not rows:
        raise SourceError(f"FUNDING_EMPTY:{symbol}:{month}")
    header=[str(x).strip() for x in rows[0]]
    required=["calc_time","funding_interval_hours","last_funding_rate"]
    if header[:3]!=required:
        raise SourceError(f"FUNDING_SCHEMA:{symbol}:{month}:{header[:3]}")
    recs=[]
    for row in rows[1:]:
        if not row or all(not str(x).strip() for x in row):
            continue
        if len(row)<3:
            raise SourceError(f"FUNDING_SHORT_ROW:{symbol}:{month}")
        ft=normalize_ms(row[0])
        interval=float(row[1])
        rate=float(row[2])
        if not (START_MS<=ft<=END_MS):
            raise SourceError(f"FUNDING_OUTSIDE_2025:{symbol}:{ft}")
        if not math.isfinite(interval) or interval<=0:
            raise SourceError(f"FUNDING_INTERVAL_INVALID:{symbol}:{ft}")
        if not math.isfinite(rate):
            raise SourceError(f"FUNDING_RATE_INVALID:{symbol}:{ft}")
        recs.append({
            "symbol":symbol,
            "fundingTime":ft,
            "fundingRate":str(row[2]),
            "fundingIntervalHours":interval,
            "providerCalcTimeRaw":str(row[0]),
        })
    return recs,{"file":name,"sha256":sha,"rows":len(recs)}


def mark_month(symbol:str,month:int,needed:set[int],out:Path)->tuple[dict[int,float],dict]:
    name=f"{symbol}-1m-{YEAR}-{month:02d}.zip"
    url=f"{MARK_BASE}/{symbol}/1m/{name}"
    raw,sha=verified_zip(url,out)
    rows=one_member_rows(raw)
    if not rows:
        raise SourceError(f"MARK_EMPTY:{symbol}:{month}")
    start=0
    if rows[0] and str(rows[0][0]).strip().lower() in {"open_time","open time"}:
        start=1
    found={}
    duplicates=set()
    parsed=0
    for row in rows[start:]:
        if not row or all(not str(x).strip() for x in row):
            continue
        if len(row)<5:
            raise SourceError(f"MARK_SHORT_ROW:{symbol}:{month}")
        ot=normalize_ms(row[0])
        op=float(row[1])
        if not math.isfinite(op) or op<=0:
            raise SourceError(f"MARK_OPEN_INVALID:{symbol}:{ot}")
        parsed+=1
        if ot in needed:
            if ot in found:
                duplicates.add(ot)
            found[ot]=op
    if duplicates:
        raise SourceError(f"MARK_DUPLICATE_SETTLEMENT_TIME:{symbol}:{month}:{sorted(duplicates)[:5]}")
    return found,{"file":name,"sha256":sha,"rows_parsed":parsed,"settlement_matches":len(found)}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",required=True)
    args=ap.parse_args()
    out=Path(args.output)
    out.mkdir(parents=True,exist_ok=True)

    failures=[]
    summaries={}
    all_rows={}
    for symbol in SYMBOLS:
        funding=[]
        funding_files=[]
        mark_files=[]
        for month in range(1,13):
            try:
                rows,meta=funding_month(symbol,month,out)
                funding.extend(rows)
                funding_files.append(meta)
            except Exception as exc:
                failures.append(f"{symbol}:FUNDING:{month:02d}:{type(exc).__name__}:{exc}")

        funding.sort(key=lambda x:x["fundingTime"])
        times=[r["fundingTime"] for r in funding]
        if len(funding)!=EXPECTED_RECORDS:
            failures.append(f"{symbol}:FUNDING_RECORD_COUNT:{len(funding)}:{EXPECTED_RECORDS}")
        if len(times)!=len(set(times)):
            failures.append(f"{symbol}:FUNDING_DUPLICATE_TIMES")
        if any(times[i]<=times[i-1] for i in range(1,len(times))):
            failures.append(f"{symbol}:FUNDING_NON_ASCENDING")

        mark_by_time={}
        by_month={}
        for r in funding:
            from datetime import datetime,timezone
            m=datetime.fromtimestamp(r["fundingTime"]/1000,tz=timezone.utc).month
            by_month.setdefault(m,set()).add(r["fundingTime"])
        for month in range(1,13):
            needed=by_month.get(month,set())
            try:
                matches,meta=mark_month(symbol,month,needed,out)
                overlap=set(mark_by_time).intersection(matches)
                if overlap:
                    failures.append(f"{symbol}:MARK_CROSS_MONTH_DUPLICATE:{sorted(overlap)[:5]}")
                mark_by_time.update(matches)
                mark_files.append(meta)
            except Exception as exc:
                failures.append(f"{symbol}:MARK:{month:02d}:{type(exc).__name__}:{exc}")

        missing=sorted(set(times)-set(mark_by_time))
        extra=sorted(set(mark_by_time)-set(times))
        if missing:
            failures.append(f"{symbol}:MARK_MISSING:{len(missing)}:{missing[:10]}")
        if extra:
            failures.append(f"{symbol}:MARK_EXTRA:{len(extra)}:{extra[:10]}")

        paired=[]
        if not missing and not extra:
            for r in funding:
                mp=mark_by_time[r["fundingTime"]]
                paired.append({**r,"markPrice":format(mp,".16g")})
        all_rows[symbol]=paired
        summaries[symbol]={
            "funding_records":len(funding),
            "paired_records":len(paired),
            "first_funding_time":times[0] if times else None,
            "last_funding_time":times[-1] if times else None,
            "funding_files":funding_files,
            "markprice_files":mark_files,
            "paired_sha256":hashlib.sha256(canonical(paired)).hexdigest(),
        }

    receipt={
        "document_id":"CED_1D_2025_FUNDING_MARKPRICE_ARCHIVE_SOURCE_GATE_RECEIPT_V0.3",
        "status":"FUNDING_MARKPRICE_SOURCE_PASS" if not failures else "FUNDING_MARKPRICE_SOURCE_FAIL",
        "amendment":"CED_1D_2025_FUNDING_MARKPRICE_ARCHIVE_AMENDMENT_V0.3",
        "provider":"BINANCE_PUBLIC_DATA_ARCHIVES",
        "symbols":summaries,
        "failures":failures,
        "outcomes_computed":False,
        "signals_computed":False,
        "returns_computed":False,
        "pnl_computed":False,
        "promotion_computed":False,
        "year_2026_accessed":False,
        "orders_created":False,
        "live_capital_enabled":False,
    }
    receipt["fingerprint"]=hashlib.sha256(canonical(receipt)).hexdigest()
    (out/"funding_markprice_paired_2025.json").write_text(json.dumps(all_rows,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (out/"CED_1D_2025_FUNDING_MARKPRICE_ARCHIVE_SOURCE_GATE_RECEIPT_V0.3.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"status":receipt["status"],"summaries":summaries,"failures":failures,"fingerprint":receipt["fingerprint"]},indent=2))
    if failures:
        raise SystemExit("FUNDING_MARKPRICE_SOURCE_FAIL")
    print("FUNDING_MARKPRICE_SOURCE_PASS")


if __name__=="__main__":
    main()
