#!/usr/bin/env python3
"""
BTC-CONVEX-TREND-CAPTURE-001
Activation-boundary forensic probe V0.1

NON-ADJUDICATING diagnostic.
Downloads public Binance USD-M BTCUSDT monthly klines for six frozen
boundary trades and compares intratrade high/close behavior.

This script does NOT optimize thresholds and creates ZERO promotion credit.
"""
from __future__ import annotations

import csv
import io
import json
import math
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

LAB = Path(__file__).resolve().parent
EVIDENCE = LAB / "evidence"
EVIDENCE.mkdir(parents=True, exist_ok=True)

CASES = [
    {
        "id": "5m_min_normal_winner",
        "tf": "5m",
        "kind": "WINNER",
        "trade_no": 127,
        "entry": "2023-02-14T01:35:00Z",
        "exit": "2023-03-03T01:30:00Z",
        "entry_price": 21678.9,
        "exit_price": 22305.8,
        "tv_mfe_pct": 16.81,
    },
    {
        "id": "5m_max_mfe_loser",
        "tf": "5m",
        "kind": "LOSER",
        "trade_no": 42,
        "entry": "2021-01-13T09:45:00Z",
        "exit": "2021-01-21T09:10:00Z",
        "entry_price": 34340.0,
        "exit_price": 32966.4,
        "tv_mfe_pct": 16.92,
    },
    {
        "id": "15m_min_normal_winner",
        "tf": "15m",
        "kind": "WINNER",
        "trade_no": 16,
        "entry": "2020-03-31T11:15:00Z",
        "exit": "2020-04-13T00:30:00Z",
        "entry_price": 6360.2,
        "exit_price": 6562.1,
        "tv_mfe_pct": 17.13,
    },
    {
        "id": "15m_max_mfe_loser",
        "tf": "15m",
        "kind": "LOSER",
        "trade_no": 131,
        "entry": "2024-08-06T22:30:00Z",
        "exit": "2024-09-06T15:15:00Z",
        "entry_price": 56028.0,
        "exit_price": 53786.8,
        "tv_mfe_pct": 16.21,
    },
    {
        "id": "4h_min_normal_winner",
        "tf": "4h",
        "kind": "WINNER",
        "trade_no": 37,
        "entry": "2023-02-09T16:00:00Z",
        "exit": "2023-03-03T00:00:00Z",
        "entry_price": 21862.1,
        "exit_price": 22305.8,
        "tv_mfe_pct": 15.83,
    },
    {
        "id": "4h_max_mfe_loser",
        "tf": "4h",
        "kind": "LOSER",
        "trade_no": 21,
        "entry": "2021-02-23T16:00:00Z",
        "exit": "2021-02-28T12:00:00Z",
        "entry_price": 45500.0,
        "exit_price": 43680.0,
        "tv_mfe_pct": 14.47,
    },
]

THRESHOLDS_PCT = [12.0, 13.0, 14.0, 15.0, 16.0, 17.0]


def dt(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def months_between(a: datetime, b: datetime):
    y, m = a.year, a.month
    while (y, m) <= (b.year, b.month):
        yield y, m
        m += 1
        if m == 13:
            y += 1
            m = 1


def url_for(tf: str, year: int, month: int) -> str:
    ym = f"{year:04d}-{month:02d}"
    return (
        "https://data.binance.vision/data/futures/um/monthly/klines/"
        f"BTCUSDT/{tf}/BTCUSDT-{tf}-{ym}.zip"
    )


def fetch_month(tf: str, year: int, month: int):
    url = url_for(tf, year, month)
    req = urllib.request.Request(url, headers={"User-Agent": "CryptoLab/1.0"})
    with urllib.request.urlopen(req, timeout=45) as r:
        body = r.read()
    with zipfile.ZipFile(io.BytesIO(body)) as zf:
        names = zf.namelist()
        if len(names) != 1:
            raise RuntimeError(f"unexpected ZIP members for {url}: {names}")
        raw = zf.read(names[0]).decode("utf-8")
    rows = []
    reader = csv.reader(io.StringIO(raw))
    for r in reader:
        if not r:
            continue
        try:
            open_time = int(r[0])
        except ValueError:
            continue  # optional header
        # Historical files used here are milliseconds.
        if open_time > 10**14:
            open_time //= 1000
        rows.append(
            {
                "open_time_ms": open_time,
                "open": float(r[1]),
                "high": float(r[2]),
                "low": float(r[3]),
                "close": float(r[4]),
            }
        )
    return url, rows


def run_case(case):
    start, end = dt(case["entry"]), dt(case["exit"])
    start_ms = int(start.timestamp() * 1000)
    end_ms = int(end.timestamp() * 1000)
    rows = []
    urls = []
    for y, m in months_between(start, end):
        url, part = fetch_month(case["tf"], y, m)
        urls.append(url)
        rows.extend(part)
    inside = [r for r in rows if start_ms <= r["open_time_ms"] <= end_ms]
    if not inside:
        raise RuntimeError(f"no Binance bars for {case['id']}")

    entry = case["entry_price"]
    max_high = max(r["high"] for r in inside)
    max_close = max(r["close"] for r in inside)
    max_open = max(r["open"] for r in inside)
    min_low = min(r["low"] for r in inside)

    high_ret = (max_high / entry - 1.0) * 100.0
    close_ret = (max_close / entry - 1.0) * 100.0
    open_ret = (max_open / entry - 1.0) * 100.0
    low_ret = (min_low / entry - 1.0) * 100.0

    expected_exit_from_12pct_trail = max_high * 0.88
    trail_error_pct_of_actual = (
        (case["exit_price"] / expected_exit_from_12pct_trail - 1.0) * 100.0
    )

    crossed = {}
    for th in THRESHOLDS_PCT:
        crossed[f"{th:g}"] = {
            "high": high_ret >= th,
            "close": close_ret >= th,
            "open": open_ret >= th,
        }

    return {
        **case,
        "source_urls": urls,
        "bar_count": len(inside),
        "binance_max_high": max_high,
        "binance_max_close": max_close,
        "binance_max_open": max_open,
        "binance_min_low": min_low,
        "binance_max_high_return_pct": high_ret,
        "binance_max_close_return_pct": close_ret,
        "binance_max_open_return_pct": open_ret,
        "binance_min_low_return_pct": low_ret,
        "tv_vs_binance_mfe_diff_pct_points": high_ret - case["tv_mfe_pct"],
        "expected_exit_if_exact_12pct_trail": expected_exit_from_12pct_trail,
        "actual_exit_vs_12pct_trail_error_pct": trail_error_pct_of_actual,
        "threshold_crossings": crossed,
    }


def main():
    results = [run_case(c) for c in CASES]

    by_tf = {}
    for tf in ["5m", "15m", "4h"]:
        winner = next(r for r in results if r["tf"] == tf and r["kind"] == "WINNER")
        loser = next(r for r in results if r["tf"] == tf and r["kind"] == "LOSER")
        by_tf[tf] = {
            "winner_max_close_return_pct": winner["binance_max_close_return_pct"],
            "loser_max_close_return_pct": loser["binance_max_close_return_pct"],
            "close_boundary_interval_if_ordered": (
                [
                    loser["binance_max_close_return_pct"],
                    winner["binance_max_close_return_pct"],
                ]
                if loser["binance_max_close_return_pct"]
                < winner["binance_max_close_return_pct"]
                else None
            ),
            "note": "diagnostic interval only; no threshold selection or promotion credit",
        }

    out = {
        "lab": "BTC-CONVEX-TREND-CAPTURE-001",
        "probe": "ACTIVATION_BOUNDARY_PROBE_V0.1",
        "scientific_role": "NON_ADJUDICATING_FORENSIC_DIAGNOSTIC",
        "threshold_selection_authorized": False,
        "promotion_credit": 0,
        "results": results,
        "boundary_summary": by_tf,
    }
    path = EVIDENCE / "ACTIVATION_BOUNDARY_PROBE_V0.1.json"
    path.write_text(json.dumps(out, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(out["boundary_summary"], indent=2))
    print(f"WROTE {path}")


if __name__ == "__main__":
    main()
