#!/usr/bin/env python3
"""DCV-001 official daily mark archive remediation probe — source only."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import urllib.request
import zipfile
from datetime import date, datetime, timezone, timedelta

BASE="https://data.binance.vision/data/futures/um/daily/markPriceKlines/BTCUSDT/1h"
DATES=(
    "2021-07-01",
    "2021-07-24",
    "2021-07-25",
    "2021-07-26",
    "2021-07-27",
    "2022-07-31",
    "2022-10-02",
    "2023-02-24",
)
UA="Crypto-Lab-DCV001-DailyMarkRemediation/0.2"
PROTECTED=int(datetime(2025,1,1,tzinfo=timezone.utc).timestamp()*1000)

def req(url:str)->bytes:
    r=urllib.request.Request(url,headers={"User-Agent":UA})
    with urllib.request.urlopen(r,timeout=60) as x:
        if x.status!=200:
            raise RuntimeError(f"HTTP_{x.status}:{url}")
        return x.read()

def checksum(url:str)->str:
    txt=req(url+".CHECKSUM").decode("utf-8","replace")
    m=re.search(r"(?i)\b([0-9a-f]{64})\b",txt)
    if not m:
        raise RuntimeError(f"CHECKSUM_PARSE:{url}")
    return m.group(1).lower()

def to_ms(v:str)->int:
    x=float(v.strip())
    if x>1e14:return int(x/1000)
    if x>1e11:return int(x)
    if x>1e9:return int(x*1000)
    raise RuntimeError(f"BAD_TS:{v}")

def iso(ms:int)->str:
    return datetime.fromtimestamp(ms/1000,tz=timezone.utc).isoformat().replace("+00:00","Z")

out={
    "lab_id":"DCV-001",
    "gate":"DAILY_MARK_REMEDIATION_SOURCE_V0.2",
    "classification":"RUNNING",
    "economic_values_reported":False,
    "outcomes_opened":False,
    "protected_2025_accessed":False,
    "protected_2026_accessed":False,
    "days":[],
    "errors":[],
}

try:
    for ds in DATES:
        url=f"{BASE}/BTCUSDT-1h-{ds}.zip"
        raw=req(url)
        actual=hashlib.sha256(raw).hexdigest()
        published=checksum(url)
        if actual!=published:
            raise RuntimeError(f"CHECKSUM_MISMATCH:{ds}")

        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            bad=z.testzip()
            if bad is not None:
                raise RuntimeError(f"ZIP_CRC_FAIL:{ds}:{bad}")
            names=[n for n in z.namelist() if n.lower().endswith(".csv") and not n.endswith("/")]
            if len(names)!=1:
                raise RuntimeError(f"CSV_COUNT:{ds}:{len(names)}")
            rows=[r for r in csv.reader(io.StringIO(z.read(names[0]).decode("utf-8-sig"))) if r]

        body=rows
        try:
            to_ms(rows[0][0])
        except Exception:
            body=rows[1:]

        if len(body)!=24:
            raise RuntimeError(f"ROW_COUNT_NOT_24:{ds}:{len(body)}")
        if any(len(r)<6 for r in body):
            raise RuntimeError(f"SCHEMA_LT_6:{ds}")

        ts=[to_ms(r[0]) for r in body]
        if len(set(ts))!=24:
            raise RuntimeError(f"DUPLICATE_TS:{ds}")
        if any(x>=PROTECTED for x in ts):
            raise RuntimeError(f"PROTECTED_TS:{ds}")

        d=date.fromisoformat(ds)
        start=int(datetime(d.year,d.month,d.day,tzinfo=timezone.utc).timestamp()*1000)
        expected=[start+i*3600000 for i in range(24)]
        if sorted(ts)!=expected:
            raise RuntimeError(f"TIMESTAMP_GRID_MISMATCH:{ds}")

        out["days"].append({
            "date":ds,
            "sha256":actual,
            "checksum_verified":True,
            "row_count":24,
            "unique_hour_count":24,
            "first_timestamp_utc":iso(min(ts)),
            "last_timestamp_utc":iso(max(ts)),
            "economic_values_reported":False,
        })

    if len(out["days"])!=len(DATES):
        raise RuntimeError("DAY_COUNT_MISMATCH")
    out["classification"]="DAILY_REMEDIATION_SOURCE_PASS"
except Exception as exc:
    out["classification"]="DAILY_REMEDIATION_SOURCE_FAIL"
    out["errors"].append(f"{type(exc).__name__}:{exc}")

print(json.dumps(out,sort_keys=True))
raise SystemExit(0 if out["classification"]=="DAILY_REMEDIATION_SOURCE_PASS" else 1)
