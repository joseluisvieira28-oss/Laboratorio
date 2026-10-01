#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import os
import re
import tempfile
import urllib.request
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

LAB_ID = "L2R-CROSSVENUE-001"
PHASE = "BINANCE_TIMESTAMP_CADENCE_PREFLIGHT_V0_1"
DATES = [
    "2024-01-01","2024-01-07","2024-01-13","2024-01-19","2024-01-25",
    "2024-04-01","2024-04-07","2024-04-13","2024-04-19","2024-04-25",
    "2024-07-01","2024-07-07","2024-07-13","2024-07-19","2024-07-25",
    "2024-10-01","2024-10-07","2024-10-13","2024-10-19","2024-10-25",
]
BASE = "https://data.binance.vision/data/spot/daily/aggTrades/BTCUSDT"
CHECK_THRESHOLDS_MS = (50,100,250,500,750,1000,1100,1500,2000,3000,5000,10000)
SHA_RE = re.compile(r"^([0-9a-fA-F]{64})\s+\*?(.+?)\s*$")

def percentile_type7_sorted(a, q):
    if not a:
        return None
    if len(a) == 1:
        return float(a[0])
    pos = (len(a)-1)*q
    lo = int(math.floor(pos)); hi = int(math.ceil(pos))
    if lo == hi:
        return float(a[lo])
    w = pos-lo
    return float(a[lo]*(1-w)+a[hi]*w)

def sha256_file(p: Path) -> str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(8*1024*1024), b""):
            h.update(b)
    return h.hexdigest()

def fetch_text(url: str) -> str:
    with urllib.request.urlopen(url, timeout=60) as r:
        return r.read().decode("utf-8", errors="strict")

def download(url: str, dst: Path):
    req=urllib.request.Request(url, headers={"User-Agent":"crypto-lab-source-preflight/0.1"})
    with urllib.request.urlopen(req, timeout=120) as r, dst.open("wb") as f:
        while True:
            b=r.read(8*1024*1024)
            if not b:
                break
            f.write(b)

def iter_timestamps_from_zip(p: Path, expected_date: str):
    expected_name=f"BTCUSDT-aggTrades-{expected_date}.csv"
    with zipfile.ZipFile(p) as z:
        names=z.namelist()
        if expected_name not in names:
            raise RuntimeError(f"expected CSV absent: {expected_name}; got {names[:5]}")
        with z.open(expected_name, "r") as raw:
            txt=io.TextIOWrapper(raw, encoding="utf-8", newline="")
            reader=csv.reader(txt)
            first=True
            for row in reader:
                if not row:
                    continue
                # Binance spot aggTrades historical CSV:
                # aggregate_trade_id, price, quantity, first_trade_id,
                # last_trade_id, transact_time_ms, is_buyer_maker, best_match
                # This preflight intentionally reads ONLY col 5 (timestamp).
                if first and row[0].lower().startswith("agg"):
                    first=False
                    continue
                first=False
                if len(row) < 6:
                    raise RuntimeError(f"short row on {expected_date}")
                try:
                    ts=int(row[5])
                except Exception as e:
                    raise RuntimeError(f"bad timestamp on {expected_date}: {row[5]!r}") from e
                yield ts

def main():
    assert len(DATES)==20 and len(set(DATES))==20
    assert all(d.startswith("2024-") for d in DATES)

    all_gaps=[]
    day_rows=[]
    totals=Counter()
    with tempfile.TemporaryDirectory(prefix="l2r_cv_cadence_") as td:
        td=Path(td)
        for d in DATES:
            fn=f"BTCUSDT-aggTrades-{d}.zip"
            url=f"{BASE}/{fn}"
            checksum_url=url+".CHECKSUM"
            dst=td/fn

            checksum_txt=fetch_text(checksum_url).strip()
            m=SHA_RE.match(checksum_txt)
            if not m:
                raise RuntimeError(f"unparseable checksum for {d}: {checksum_txt[:200]!r}")
            expected_sha=m.group(1).lower()
            expected_file=m.group(2).strip()
            if expected_file != fn:
                raise RuntimeError(f"checksum filename mismatch {d}: {expected_file} != {fn}")

            download(url,dst)
            actual_sha=sha256_file(dst)
            if actual_sha != expected_sha:
                raise RuntimeError(f"SHA256 mismatch {d}: {actual_sha} != {expected_sha}")

            ts=list(iter_timestamps_from_zip(dst,d))
            if len(ts)<2:
                raise RuntimeError(f"insufficient timestamps on {d}: {len(ts)}")
            if any(ts[i] < ts[i-1] for i in range(1,len(ts))):
                raise RuntimeError(f"timestamp regression on {d}")

            start_ms=int(datetime.fromisoformat(d).replace(tzinfo=timezone.utc).timestamp()*1000)
            end_ms=start_ms+86_400_000
            if ts[0] < start_ms or ts[-1] >= end_ms:
                raise RuntimeError(f"timestamp outside UTC date on {d}: {ts[0]}..{ts[-1]}")

            gaps=[ts[i]-ts[i-1] for i in range(1,len(ts))]
            all_gaps.extend(gaps)
            s=sorted(gaps)
            day_rows.append({
                "date":d,
                "rows":len(ts),
                "first_ts_ms":ts[0],
                "last_ts_ms":ts[-1],
                "zip_sha256":actual_sha,
                "gap_p50_ms":percentile_type7_sorted(s,0.50),
                "gap_p90_ms":percentile_type7_sorted(s,0.90),
                "gap_p95_ms":percentile_type7_sorted(s,0.95),
                "gap_p99_ms":percentile_type7_sorted(s,0.99),
                "gap_p999_ms":percentile_type7_sorted(s,0.999),
                "gap_max_ms":max(gaps),
            })
            totals["rows"] += len(ts)
            totals["gaps"] += len(gaps)
            print(f"DATE_PASS {d} rows={len(ts)} p99_ms={day_rows[-1]['gap_p99_ms']} max_ms={max(gaps)}", flush=True)

    def hist_quantile(q):
        if totals["gaps"] <= 0:
            return None
        pos=(totals["gaps"]-1)*q
        lo=int(math.floor(pos)); hi=int(math.ceil(pos))
        def value_at(rank):
            seen=0
            for gap,count in sorted(gap_hist.items()):
                if seen+count > rank:
                    return gap
                seen += count
            raise RuntimeError("histogram rank overflow")
        vlo=value_at(lo); vhi=value_at(hi)
        if lo==hi:
            return float(vlo)
        w=pos-lo
        return float(vlo*(1-w)+vhi*w)

    threshold_coverage={}
    n=totals["gaps"]
    sorted_hist=sorted(gap_hist.items())
    for t in CHECK_THRESHOLDS_MS:
        # proportion of observed inter-aggTrade gaps <= t; source cadence only.
        count_le=sum(count for gap,count in sorted_hist if gap<=t)
        threshold_coverage[str(t)]={"count":count_le,"pct":100.0*count_le/n}

    receipt={
        "schema_version":"0.1",
        "lab_id":LAB_ID,
        "phase":PHASE,
        "classification":"BINANCE_TIMESTAMP_CADENCE_PREFLIGHT_PASS",
        "source":"Binance official public historical spot aggTrades / data.binance.vision",
        "symbol":"BTCUSDT",
        "market":"spot",
        "frozen_dates":DATES,
        "days_verified":len(day_rows),
        "rows_total":totals["rows"],
        "gaps_total":totals["gaps"],
        "cadence_ms":{
            "p50":hist_quantile(0.50),
            "p90":hist_quantile(0.90),
            "p95":hist_quantile(0.95),
            "p99":hist_quantile(0.99),
            "p999":hist_quantile(0.999),
            "max":max(gap_hist),
        },
        "threshold_gap_coverage":threshold_coverage,
        "per_day":day_rows,
        "outcome_blind":{
            "price_column_parsed":False,
            "returns_computed":False,
            "signed_response_computed":False,
            "weak_strong_crossvenue_contrast_computed":False,
            "pnl_computed":False,
            "fees_computed":False,
        },
        "firewalls":{
            "access_2025":False,
            "access_2026":False,
            "live_trading":False,
            "orders":False,
            "exchange_mutation":False,
            "main_merge":False,
        },
        "next_gate":"Freeze external lookup tolerance prospectively from timestamp cadence only; parent anchors remain separately required before any Discovery outcome.",
    }
    blob=json.dumps(receipt,sort_keys=True,separators=(",",":")).encode()
    receipt["receipt_sha256_pretty_independent_payload"]=hashlib.sha256(blob).hexdigest()
    out=Path("L2R_CROSSVENUE_001_BINANCE_TIMESTAMP_CADENCE_PREFLIGHT_V0_1.json")
    out.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("CADENCE_RECEIPT="+str(out))
    print("CADENCE_JSON="+json.dumps(receipt,sort_keys=True))
    print("CADENCE_CLASSIFICATION="+receipt["classification"])

if __name__=="__main__":
    main()
