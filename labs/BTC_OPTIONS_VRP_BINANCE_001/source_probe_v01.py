#!/usr/bin/env python3
"""Source-only census for Binance public BTC Options EOHSummary archives.

No prices are emitted in the receipt and no economic/strategy outcomes are
computed. The script checks calendar coverage and semantic schema only.
"""
from __future__ import annotations

import csv
import io
import json
import re
import time
import urllib.error
import urllib.request
import zipfile
from datetime import date, timedelta

BASE = "https://data.binance.vision/data/option/daily/EOHSummary/BTCUSDT/"
START = date.fromisoformat("2023-05-18")
END = date.fromisoformat("2023-10-23")
SAMPLES = ["2023-05-18", "2023-07-01", "2023-10-23"]
MIN_AVAILABLE = 100

ALIASES = {
    "point_in_time_timestamp": {"timestamp","time","calc_time","quote_time","date","datetime","snapshot_time","data_time"},
    "option_identity": {"symbol","instrument","instrument_name","contract","contract_name"},
    "expiry": {"expiry","expiration","expiration_time","expiry_date"},
    "strike": {"strike","strike_price"},
    "right": {"side","right","option_type"},
    "bid_price": {"bid_price","bidprice","bid"},
    "ask_price": {"ask_price","askprice","ask"},
    "bid_size": {"bid_qty","bidqty","bid_size","bidsize","bid_amount"},
    "ask_size": {"ask_qty","askqty","ask_size","asksize","ask_amount"},
    "underlying_price": {"underlying_price","underlyingprice","spot_price","index_price"},
    "implied_volatility": {"mark_iv","markiv","iv","implied_volatility"},
}

REQUIRED_CORE = {
    "option_identity","expiry","strike","right",
    "bid_price","ask_price","bid_size","ask_size"
}

def norm(x: str) -> str:
    x = x.strip().strip("[]").lower()
    x = re.sub(r"[^a-z0-9]+", "_", x).strip("_")
    return x

def file_url(ds: str) -> str:
    return f"{BASE}BTCUSDT-EOHSummary-{ds}.zip"

def exists(ds: str) -> tuple[bool, int | None]:
    url = file_url(ds)
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent":"CryptoLab-SourceOnly/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return getattr(r, "status", 200) == 200, int(r.headers.get("Content-Length") or 0)
    except urllib.error.HTTPError as exc:
        if exc.code in (403,405):
            req = urllib.request.Request(url, method="GET", headers={"Range":"bytes=0-0","User-Agent":"CryptoLab-SourceOnly/0.1"})
            try:
                with urllib.request.urlopen(req, timeout=15) as r:
                    return getattr(r, "status", 200) in (200,206), int(r.headers.get("Content-Length") or 0)
            except Exception:
                return False, None
        if exc.code == 404:
            return False, None
        return False, None
    except Exception:
        return False, None

def semantic_map(headers: list[str]) -> dict[str, str | None]:
    normalized = {norm(h): h for h in headers}
    out = {}
    for semantic, aliases in ALIASES.items():
        match = next((normalized[a] for a in aliases if a in normalized), None)
        out[semantic] = match
    return out

def inspect_sample(ds: str) -> dict:
    url = file_url(ds)
    req = urllib.request.Request(url, headers={"User-Agent":"CryptoLab-SourceOnly/0.1"})
    with urllib.request.urlopen(req, timeout=45) as r:
        raw = r.read()
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        names = [n for n in zf.namelist() if not n.endswith("/")]
        if len(names) != 1:
            raise RuntimeError(f"unexpected file count in zip: {len(names)}")
        with zf.open(names[0]) as fh:
            text = io.TextIOWrapper(fh, encoding="utf-8-sig", newline="")
            reader = csv.DictReader(text)
            headers = reader.fieldnames or []
            smap = semantic_map(headers)
            row_count = sum(1 for _ in reader)
    semantic_present = {k: (v is not None) for k, v in smap.items()}
    return {
        "date": ds,
        "zip_bytes": len(raw),
        "csv_filename": names[0],
        "column_count": len(headers),
        "normalized_columns": sorted(norm(h) for h in headers),
        "semantic_present": semantic_present,
        "row_count": row_count,
        "prices_emitted": False,
    }

def main() -> int:
    available = []
    missing = []
    sizes = {}
    d = START
    while d <= END:
        ds = d.isoformat()
        ok, size = exists(ds)
        if ok:
            available.append(ds)
            if size:
                sizes[ds] = size
        else:
            missing.append(ds)
        d += timedelta(days=1)
        time.sleep(0.03)

    samples = []
    sample_errors = []
    for ds in SAMPLES:
        try:
            samples.append(inspect_sample(ds))
        except Exception as exc:
            sample_errors.append({"date":ds,"error_type":type(exc).__name__,"error":str(exc)[:300]})

    fixed_available = all(ds in available for ds in SAMPLES)
    fixed_parsed = len(samples) == len(SAMPLES) and not sample_errors
    semantic_pass = fixed_parsed and all(
        all(s["semantic_present"].get(k, False) for k in REQUIRED_CORE)
        for s in samples
    )

    if len(available) >= MIN_AVAILABLE and fixed_available and semantic_pass:
        classification = "BINANCE_EOH_SOURCE_FEASIBLE"
    elif len(available) > 0 and fixed_parsed and not semantic_pass:
        classification = "BINANCE_EOH_SOURCE_SCHEMA_INSUFFICIENT"
    elif len(available) > 0:
        classification = "BINANCE_EOH_SOURCE_PARTIAL_COVERAGE"
    else:
        classification = "BINANCE_EOH_SOURCE_ACQUISITION_FAILURE"

    receipt = {
        "probe_id":"BOVRP-BINANCE-EOH-SOURCE-001",
        "classification":classification,
        "envelope":{"start":START.isoformat(),"end":END.isoformat()},
        "calendar_days":(END-START).days+1,
        "available_day_count":len(available),
        "missing_day_count":len(missing),
        "first_available":available[0] if available else None,
        "last_available":available[-1] if available else None,
        "missing_dates":missing,
        "fixed_sample_dates":SAMPLES,
        "fixed_samples_available":fixed_available,
        "fixed_samples_parse_pass":fixed_parsed,
        "fixed_samples_semantic_pass":semantic_pass,
        "samples":samples,
        "sample_errors":sample_errors,
        "outcomes_opened":False,
        "returns_computed":False,
        "vrp_computed":False,
        "pnl_computed":False,
        "access_2025":False,
        "access_2026":False,
    }
    with open("binance_eoh_source_receipt_v01.json","w",encoding="utf-8") as f:
        json.dump(receipt,f,indent=2,sort_keys=True)
        f.write("\n")
    print(json.dumps({
        "classification":classification,
        "available_day_count":len(available),
        "missing_day_count":len(missing),
        "fixed_samples_available":fixed_available,
        "fixed_samples_semantic_pass":semantic_pass
    },sort_keys=True))
    return 0 if classification == "BINANCE_EOH_SOURCE_FEASIBLE" else 2

if __name__ == "__main__":
    raise SystemExit(main())
