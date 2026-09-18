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

BASE="https://data.binance.vision/data/futures/um/monthly/fundingRate"
UA="CED1D-2025-FUNDING-ARCHIVE-GATE/0.1"


class FundingArchiveError(RuntimeError):
    pass


def canonical(o):
    return json.dumps(o,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()


def fetch_bytes(url:str)->bytes:
    req=urllib.request.Request(url,headers={"User-Agent":UA})
    try:
        with urllib.request.urlopen(req,timeout=60) as r:
            if r.status!=200:
                raise FundingArchiveError(f"HTTP_{r.status}:{url}")
            return r.read()
    except Exception as exc:
        if isinstance(exc,FundingArchiveError):
            raise
        raise FundingArchiveError(f"FETCH_FAIL:{type(exc).__name__}:{exc}:{url}") from exc


def normalize_time_ms(raw:int)->tuple[int,str]:
    # Public archives may expose provider-native timestamps at ms or us precision.
    if raw > 10**14:
        return raw//1000,"us_to_ms"
    return raw,"ms"


def load_month(symbol:str,year:int,month:int,out:Path)->dict:
    name=f"{symbol}-fundingRate-{year:04d}-{month:02d}.zip"
    url=f"{BASE}/{symbol}/{name}"
    raw=fetch_bytes(url)
    checksum_raw=fetch_bytes(url+".CHECKSUM").decode("utf-8").strip().split()
    if not checksum_raw:
        raise FundingArchiveError(f"EMPTY_CHECKSUM:{name}")
    expected=checksum_raw[0].lower()
    actual=hashlib.sha256(raw).hexdigest()
    if expected!=actual:
        raise FundingArchiveError(f"CHECKSUM_MISMATCH:{name}")
    (out/name).write_bytes(raw)
    (out/(name+".CHECKSUM")).write_text(expected+"  "+name+"\n",encoding="utf-8")

    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        members=[n for n in zf.namelist() if not n.endswith("/")]
        if len(members)!=1:
            raise FundingArchiveError(f"ZIP_MEMBER_COUNT:{name}:{len(members)}")
        text=io.TextIOWrapper(zf.open(members[0]),encoding="utf-8")
        rows=list(csv.reader(text))

    if not rows:
        raise FundingArchiveError(f"EMPTY_CSV:{name}")
    header=[x.strip() for x in rows[0]]
    required=["calc_time","funding_interval_hours","last_funding_rate"]
    if header[:3]!=required:
        raise FundingArchiveError(f"SCHEMA_MISMATCH:{name}:{header[:3]}")
    data=[]
    units=set()
    for row in rows[1:]:
        if not row or all(not str(x).strip() for x in row):
            continue
        if len(row)<3:
            raise FundingArchiveError(f"SHORT_ROW:{name}")
        raw_time=int(row[0])
        ft,unit=normalize_time_ms(raw_time)
        units.add(unit)
        interval=float(row[1])
        rate=float(row[2])
        if not math.isfinite(interval) or interval<=0:
            raise FundingArchiveError(f"BAD_INTERVAL:{name}:{row[1]}")
        if not math.isfinite(rate):
            raise FundingArchiveError(f"BAD_RATE:{name}:{row[2]}")
        data.append({
            "symbol":symbol,
            "fundingTime":ft,
            "fundingRate":str(row[2]),
            "fundingIntervalHours":interval,
            "providerCalcTimeRaw":str(row[0]),
        })
    if not data:
        raise FundingArchiveError(f"NO_RECORDS:{name}")
    if len(units)!=1:
        raise FundingArchiveError(f"MIXED_TIMESTAMP_UNITS:{name}:{sorted(units)}")
    return {
        "name":name,
        "sha256":actual,
        "records":data,
        "timestamp_normalization":next(iter(units)),
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--manifest",required=True)
    ap.add_argument("--output",required=True)
    a=ap.parse_args()

    man=json.loads(Path(a.manifest).read_text())
    if man["access_2026_plus"] or man["price_outcomes_accessed"]:
        raise SystemExit("FUNDING_MANIFEST_FIREWALL_FAIL")
    start=int(man["start_time_ms"])
    end=int(man["end_time_ms"])
    out=Path(a.output)
    out.mkdir(parents=True,exist_ok=True)

    failures=[]
    summaries={}
    canonical_records={}
    for symbol in man["symbols"]:
        records=[]
        archives=[]
        for month in range(1,13):
            try:
                item=load_month(symbol,2025,month,out)
            except Exception as exc:
                failures.append(f"{symbol}:{month:02d}:{type(exc).__name__}:{exc}")
                continue
            archives.append({
                "file":item["name"],
                "sha256":item["sha256"],
                "records":len(item["records"]),
                "timestamp_normalization":item["timestamp_normalization"],
            })
            for r in item["records"]:
                if start<=r["fundingTime"]<=end:
                    records.append(r)

        records.sort(key=lambda x:x["fundingTime"])
        times=[r["fundingTime"] for r in records]
        if len(times)!=len(set(times)):
            failures.append(f"{symbol}:DUPLICATE_TIME")
        if any(times[i]<=times[i-1] for i in range(1,len(times))):
            failures.append(f"{symbol}:NON_ASCENDING")
        if not records:
            failures.append(f"{symbol}:NO_2025_RECORDS")

        canonical_records[symbol]=records
        summaries[symbol]={
            "records":len(records),
            "first_funding_time":records[0]["fundingTime"] if records else None,
            "last_funding_time":records[-1]["fundingTime"] if records else None,
            "archives":archives,
            "canonical_records_sha256":hashlib.sha256(canonical(records)).hexdigest(),
            "ascending_unique":len(times)==len(set(times)) and all(times[i]>times[i-1] for i in range(1,len(times))),
        }

    receipt={
        "document_id":"CED_1D_2025_FUNDING_ARCHIVE_SOURCE_GATE_RECEIPT_V0.1",
        "status":"FUNDING_SOURCE_PASS" if not failures else "FUNDING_SOURCE_FAIL",
        "transport_amendment":"CED_1D_2025_FUNDING_SOURCE_TRANSPORT_AMENDMENT_V0.1",
        "parent_manifest_document_id":man["document_id"],
        "provider":"BINANCE_PUBLIC_DATA_MONTHLY_FUNDINGRATE",
        "interval":{"start_time_ms":start,"end_time_ms":end},
        "symbols":summaries,
        "failures":failures,
        "price_outcomes_computed":False,
        "access_2026_plus":False,
        "orders_created":False,
        "live_capital_enabled":False,
    }
    receipt["fingerprint"]=hashlib.sha256(canonical(receipt)).hexdigest()
    (out/"funding_records_canonical.json").write_text(json.dumps(canonical_records,indent=2,sort_keys=True)+"\n")
    (out/"CED_1D_2025_FUNDING_ARCHIVE_SOURCE_GATE_RECEIPT_V0.1.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":receipt["status"],"summary":summaries,"failures":failures,"fingerprint":receipt["fingerprint"]},indent=2))
    if failures:
        raise SystemExit("FUNDING_SOURCE_FAIL")
    print("FUNDING_SOURCE_PASS")


if __name__=="__main__":
    main()
