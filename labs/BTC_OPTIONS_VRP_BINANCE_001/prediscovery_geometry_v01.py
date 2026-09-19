#!/usr/bin/env python3
"""Source-geometry census for free Binance BTC options EOH archives.

No option prices, returns, IV outcomes, realized variance, VRP or PnL are
emitted. The census measures only whether an executable 24h paired-option
geometry exists often enough to justify a later prospectively frozen MVE.
"""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import io
import json
import re
import time
import urllib.error
import urllib.request
import zipfile
from collections import defaultdict
from pathlib import Path

BASE = "https://data.binance.vision/data/option/daily/EOHSummary/BTCUSDT/"
START = dt.date.fromisoformat("2023-05-18")
END = dt.date.fromisoformat("2023-10-23")
DECISION_HOUR = 8

DTE_BINS = [
    ("DTE_1_2", 1.0, 2.0),
    ("DTE_2_4", 2.0, 4.0),
    ("DTE_4_8", 4.0, 8.0),
    ("DTE_8_15", 8.0, 15.0),
    ("DTE_15_31", 15.0, 31.0),
]

def url_for(ds: str) -> str:
    return f"{BASE}BTCUSDT-EOHSummary-{ds}.zip"

def norm(x: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", x.strip().strip("[]").lower()).strip("_")

def parse_expiry(symbol: str) -> dt.datetime | None:
    m = re.search(r"(?:^|-)(\d{6})(?:-|$)", symbol)
    if not m:
        return None
    try:
        d = dt.datetime.strptime(m.group(1), "%y%m%d").replace(tzinfo=dt.timezone.utc)
        return d.replace(hour=8)
    except ValueError:
        return None

def parse_hour(v: str) -> int | None:
    s = str(v).strip()
    if not s:
        return None
    try:
        f = float(s)
        if 0 <= f < 24:
            return int(f)
    except ValueError:
        pass
    m = re.search(r"(\d{1,2})", s)
    if m:
        h = int(m.group(1))
        if 0 <= h < 24:
            return h
    return None

def nonempty(v) -> bool:
    return v is not None and str(v).strip() not in {"", "nan", "NaN", "null", "None"}

def download_day(ds: str) -> bytes | None:
    req = urllib.request.Request(url_for(ds), headers={"User-Agent":"CryptoLab-SourceGeometry/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.read()
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise

def load_0800(ds: str, raw: bytes) -> tuple[dict[str, dict], dict]:
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        names = [n for n in zf.namelist() if not n.endswith("/")]
        if len(names) != 1:
            raise RuntimeError(f"{ds}: unexpected zip member count {len(names)}")
        with zf.open(names[0]) as fh:
            reader = csv.DictReader(io.TextIOWrapper(fh, encoding="utf-8-sig", newline=""))
            headers = reader.fieldnames or []
            by = {norm(h): h for h in headers}
            required = [
                "date","hour","symbol","type","strike","delta",
                "best_bid_price","best_bid_qty","best_ask_price","best_ask_qty"
            ]
            missing = [x for x in required if x not in by]
            if missing:
                raise RuntimeError(f"{ds}: missing structural fields {missing}")

            snap = {}
            total_08 = 0
            complete_08 = 0
            for row in reader:
                if parse_hour(row.get(by["hour"], "")) != DECISION_HOUR:
                    continue
                total_08 += 1
                symbol = str(row.get(by["symbol"], "")).strip()
                expiry = parse_expiry(symbol)
                if not symbol or expiry is None:
                    continue
                typ = str(row.get(by["type"], "")).strip().upper()
                if typ in {"CALL","C"}:
                    right = "C"
                elif typ in {"PUT","P"}:
                    right = "P"
                else:
                    continue
                try:
                    strike = float(row.get(by["strike"], ""))
                    delta = float(row.get(by["delta"], ""))
                except Exception:
                    continue
                bbo_ok = all(nonempty(row.get(by[k])) for k in (
                    "best_bid_price","best_bid_qty","best_ask_price","best_ask_qty"
                ))
                if not bbo_ok:
                    continue
                complete_08 += 1
                snapshot_dt = dt.datetime.fromisoformat(ds).replace(hour=8,tzinfo=dt.timezone.utc)
                dte = (expiry - snapshot_dt).total_seconds() / 86400.0
                snap[symbol] = {
                    "expiry": expiry.date().isoformat(),
                    "strike": strike,
                    "right": right,
                    "delta_present": True,
                    "dte": dte,
                    "bbo_complete": True,
                }

    meta = {
        "source_date": ds,
        "zip_sha256": hashlib.sha256(raw).hexdigest(),
        "zip_bytes": len(raw),
        "rows_08utc": total_08,
        "complete_structural_rows_08utc": complete_08,
        "prices_emitted": False,
    }
    return snap, meta

def bin_id(dte: float) -> str | None:
    for name, lo, hi in DTE_BINS:
        if lo <= dte < hi:
            return name
    return None

def main() -> int:
    snapshots = {}
    manifests = []
    missing_dates = []
    d = START
    while d <= END:
        ds = d.isoformat()
        raw = download_day(ds)
        if raw is None:
            missing_dates.append(ds)
        else:
            snap, meta = load_0800(ds, raw)
            snapshots[ds] = snap
            manifests.append(meta)
        d += dt.timedelta(days=1)
        time.sleep(0.025)

    episodes_by_bin = defaultdict(set)
    pair_counts_by_bin = defaultdict(int)
    persistent_instruments_by_bin = defaultdict(int)
    months_by_bin = defaultdict(set)

    sorted_dates = sorted(snapshots)
    for ds in sorted_dates:
        d0 = dt.date.fromisoformat(ds)
        ds1 = (d0 + dt.timedelta(days=1)).isoformat()
        if ds1 not in snapshots:
            continue
        s0 = snapshots[ds]
        s1 = snapshots[ds1]

        persistent = {sym for sym in s0 if sym in s1 and s0[sym]["bbo_complete"] and s1[sym]["bbo_complete"]}

        paired = defaultdict(set)
        for sym in persistent:
            r = s0[sym]
            b = bin_id(r["dte"])
            if b is None:
                continue
            persistent_instruments_by_bin[b] += 1
            key = (b, r["expiry"], r["strike"])
            paired[key].add(r["right"])

        per_bin_pairs_today = defaultdict(int)
        for (b, expiry, strike), rights in paired.items():
            if {"C","P"}.issubset(rights):
                per_bin_pairs_today[b] += 1

        for b, n in per_bin_pairs_today.items():
            if n > 0:
                episodes_by_bin[b].add(ds)
                months_by_bin[b].add(ds[:7])
                pair_counts_by_bin[b] += n

    bins = {}
    for name, lo, hi in DTE_BINS:
        eps = sorted(episodes_by_bin[name])
        bins[name] = {
            "dte_min_inclusive": lo,
            "dte_max_exclusive": hi,
            "distinct_24h_episode_starts": len(eps),
            "calendar_month_count": len(months_by_bin[name]),
            "paired_strike_count_total": pair_counts_by_bin[name],
            "persistent_instrument_count_total": persistent_instruments_by_bin[name],
            "first_episode_start": eps[0] if eps else None,
            "last_episode_start": eps[-1] if eps else None,
        }

    qualifying = [
        name for name, x in bins.items()
        if x["distinct_24h_episode_starts"] >= 80 and x["calendar_month_count"] >= 4
    ]
    classification = "PREDISCOVERY_GEOMETRY_PASS" if qualifying else "PREDISCOVERY_GEOMETRY_INSUFFICIENT"

    receipt = {
        "census_id":"BOVRP-BINANCE-PREDISCOVERY-GEOMETRY-001",
        "classification":classification,
        "source_dates_loaded":len(snapshots),
        "missing_date_count":len(missing_dates),
        "missing_dates":missing_dates,
        "decision_hour_utc":DECISION_HOUR,
        "hold_geometry_hours":24,
        "bins":bins,
        "qualifying_bins":qualifying,
        "manifest_count":len(manifests),
        "source_manifest":manifests,
        "outcomes_opened":False,
        "option_prices_emitted":False,
        "returns_computed":False,
        "realized_variance_computed":False,
        "vrp_computed":False,
        "pnl_computed":False,
        "access_2025":False,
        "access_2026":False,
    }
    Path("binance_prediscovery_geometry_receipt_v01.json").write_text(
        json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8"
    )
    print(json.dumps({
        "classification":classification,
        "source_dates_loaded":len(snapshots),
        "qualifying_bins":qualifying,
        "episode_counts":{k:v["distinct_24h_episode_starts"] for k,v in bins.items()}
    },sort_keys=True))
    return 0 if classification == "PREDISCOVERY_GEOMETRY_PASS" else 2

if __name__ == "__main__":
    raise SystemExit(main())
