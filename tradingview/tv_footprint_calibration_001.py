#!/usr/bin/env python3
"""TV-FOOTPRINT-CALIBRATION-001 utilities.

Pure-stdlib tooling to:
1) aggregate Binance BTCUSDT aggTrades into UTC 5-minute aggressor-flow bars;
2) normalize TradingView Market Microscope CSV exports;
3) compare TradingView footprint delta with Binance aggressor delta under the
   frozen prospective calibration gate.

No market outcomes, trade signals, PnL, orders, or exchange mutations.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Dict, Optional

BAR_MS = 5 * 60 * 1000
FORWARD_START_MS = int(datetime(2026, 9, 24, 11, 0, tzinfo=timezone.utc).timestamp() * 1000)
MIN_MATCHED_BARS = 2016


def _to_ms(value: str) -> int:
    """Parse epoch or ISO-ish timestamps to milliseconds UTC."""
    s = str(value).strip()
    if not s:
        raise ValueError("empty timestamp")
    try:
        x = float(s)
        ax = abs(x)
        if ax < 1e11:
            return int(round(x * 1000))
        if ax < 1e14:
            return int(round(x))
        if ax < 1e17:
            return int(round(x / 1000))
        return int(round(x / 1_000_000))
    except ValueError:
        pass
    s = s.replace("Z", "+00:00")
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.astimezone(timezone.utc).timestamp() * 1000)


def _bool(v: str) -> bool:
    return str(v).strip().lower() in {"true", "1", "t", "yes", "y"}


def _float(v: str) -> float:
    return float(str(v).strip().replace(",", ""))


def aggregate_binance(paths: Iterable[Path]) -> List[Dict[str, float]]:
    buckets = defaultdict(lambda: {
        "agg_base_volume": 0.0,
        "agg_buy_volume": 0.0,
        "agg_sell_volume": 0.0,
        "agg_trade_count": 0,
    })

    for path in paths:
        with path.open("r", newline="", encoding="utf-8") as fh:
            reader = csv.reader(fh)
            for row in reader:
                if not row:
                    continue
                if not row[0].strip().lstrip("-").isdigit():
                    continue
                if len(row) < 7:
                    raise ValueError(f"{path}: aggTrades row has <7 fields")
                qty = _float(row[2])
                ts = _to_ms(row[5])
                maker = _bool(row[6])
                bar_open = (ts // BAR_MS) * BAR_MS
                b = buckets[bar_open]
                b["agg_base_volume"] += qty
                if maker:
                    b["agg_sell_volume"] += qty
                else:
                    b["agg_buy_volume"] += qty
                b["agg_trade_count"] += 1

    out = []
    for bar_open in sorted(buckets):
        if bar_open + BAR_MS < FORWARD_START_MS:
            continue
        b = buckets[bar_open]
        base = b["agg_base_volume"]
        delta = b["agg_buy_volume"] - b["agg_sell_volume"]
        out.append({
            "bar_open_ms": bar_open,
            "bar_close_ms": bar_open + BAR_MS,
            **b,
            "agg_delta": delta,
            "agg_delta_pct": delta / base if base else math.nan,
        })
    return out


def _pick(row: Dict[str, str], names: Iterable[str]) -> Optional[str]:
    lower = {k.strip().lower(): k for k in row.keys()}
    for name in names:
        key = lower.get(name.lower())
        if key is not None and str(row[key]).strip() != "":
            return row[key]
    return None


def normalize_tv_csv(path: Path) -> List[Dict[str, float]]:
    out = []
    with path.open("r", newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        if not reader.fieldnames:
            raise ValueError("TradingView CSV has no header")
        for row in reader:
            t = _pick(row, ["bar_open_ms", "time", "datetime", "date", "timestamp"])
            if t is None:
                raise ValueError("TradingView CSV missing time/bar_open_ms column")
            bar_open = (_to_ms(t) // BAR_MS) * BAR_MS
            if bar_open + BAR_MS < FORWARD_START_MS:
                continue

            def req(name: str) -> float:
                v = _pick(row, [name])
                if v is None:
                    raise ValueError(f"TradingView CSV missing required column: {name}")
                return _float(v)

            def opt(name: str) -> float:
                v = _pick(row, [name])
                return _float(v) if v is not None else math.nan

            out.append({
                "bar_open_ms": bar_open,
                "bar_close_ms": bar_open + BAR_MS,
                "tv_total_volume": req("TVFP_total_volume"),
                "tv_buy_volume": req("TVFP_buy_volume"),
                "tv_sell_volume": req("TVFP_sell_volume"),
                "tv_delta": req("TVFP_delta"),
                "tv_delta_pct": req("TVFP_delta_pct"),
                "ltf_path_efficiency": opt("LTF_path_efficiency"),
                "ltf_signed_volume_pct": opt("LTF_signed_volume_pct"),
                "volume_z": opt("CTX_volume_z"),
                "bar_return_bps": opt("CTX_bar_return_bps"),
            })
    return out


def write_csv(rows: List[Dict[str, object]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError("refusing to write empty CSV")
    fields = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def read_csv_numeric(path: Path) -> List[Dict[str, float]]:
    rows = []
    with path.open("r", newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            parsed = {}
            for k, v in row.items():
                if k in {"bar_open_ms", "bar_close_ms", "agg_trade_count"}:
                    parsed[k] = int(float(v))
                else:
                    parsed[k] = float(v)
            rows.append(parsed)
    return rows


def _pearson(xs: List[float], ys: List[float]) -> float:
    if len(xs) < 2:
        return math.nan
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    dx = [x - mx for x in xs]
    dy = [y - my for y in ys]
    den = math.sqrt(sum(x*x for x in dx) * sum(y*y for y in dy))
    return sum(x*y for x, y in zip(dx, dy)) / den if den else math.nan


def _ranks(vals: List[float]) -> List[float]:
    order = sorted(range(len(vals)), key=lambda i: vals[i])
    ranks = [0.0] * len(vals)
    i = 0
    while i < len(order):
        j = i + 1
        while j < len(order) and vals[order[j]] == vals[order[i]]:
            j += 1
        avg = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[order[k]] = avg
        i = j
    return ranks


def _spearman(xs: List[float], ys: List[float]) -> float:
    if len(xs) < 2:
        return math.nan
    return _pearson(_ranks(xs), _ranks(ys))


def _median(vals: List[float]) -> float:
    vals = sorted(vals)
    n = len(vals)
    if n == 0:
        return math.nan
    m = n // 2
    return vals[m] if n % 2 else (vals[m - 1] + vals[m]) / 2.0


def calibrate(tv_rows: List[Dict[str, float]], agg_rows: List[Dict[str, float]]) -> Dict[str, object]:
    tv_map = {int(r["bar_open_ms"]): r for r in tv_rows}
    agg_map = {int(r["bar_open_ms"]): r for r in agg_rows}
    if len(tv_map) != len(tv_rows):
        raise ValueError("duplicate TradingView bar_open_ms")
    if len(agg_map) != len(agg_rows):
        raise ValueError("duplicate Binance bar_open_ms")
    if not agg_map:
        raise ValueError("no Binance rows")

    keys = sorted(set(tv_map).intersection(agg_map))
    coverage = len(keys) / len(agg_map)

    rel_errors = []
    tv_delta = []
    agg_delta = []
    sign_hits = 0
    sign_n = 0

    for k in keys:
        t, a = tv_map[k], agg_map[k]
        if a["agg_base_volume"] > 0:
            rel_errors.append(abs(t["tv_total_volume"] - a["agg_base_volume"]) / a["agg_base_volume"])
        if math.isfinite(t["tv_delta"]) and math.isfinite(a["agg_delta"]):
            tv_delta.append(t["tv_delta"])
            agg_delta.append(a["agg_delta"])
            st = (t["tv_delta"] > 0) - (t["tv_delta"] < 0)
            sa = (a["agg_delta"] > 0) - (a["agg_delta"] < 0)
            if st != 0 and sa != 0:
                sign_n += 1
                sign_hits += int(st == sa)

    median_rel = _median(rel_errors)
    sign_agreement = sign_hits / sign_n if sign_n else math.nan
    pearson = _pearson(tv_delta, agg_delta)
    spearman = _spearman(tv_delta, agg_delta)

    min_evidence = len(keys) >= MIN_MATCHED_BARS and coverage >= 0.99
    if not min_evidence:
        classification = "INSUFFICIENT_SAMPLE"
    elif (coverage >= 0.99 and median_rel <= 0.01 and sign_agreement >= 0.70
          and spearman >= 0.65 and pearson >= 0.60):
        classification = "PASS_STRONG"
    elif (coverage >= 0.98 and median_rel <= 0.02 and sign_agreement >= 0.60
          and spearman >= 0.50):
        classification = "PASS_LIMITED"
    else:
        classification = "FAIL_SENSOR"

    return {
        "lab_id": "TV-FOOTPRINT-CALIBRATION-001",
        "forward_start_ms": FORWARD_START_MS,
        "matched_bars": len(keys),
        "tv_bars": len(tv_map),
        "binance_bars": len(agg_map),
        "coverage": coverage,
        "median_abs_relative_total_volume_error": median_rel,
        "delta_sign_comparable_bars": sign_n,
        "delta_sign_agreement": sign_agreement,
        "delta_pearson": pearson,
        "delta_spearman": spearman,
        "minimum_evidence_satisfied": min_evidence,
        "classification": classification,
        "authority": "measurement_only_no_trading_authority",
    }


def _json_dump(obj: Dict[str, object], path: Optional[Path]) -> None:
    txt = json.dumps(obj, indent=2, sort_keys=True, allow_nan=False)
    if path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(txt + "\n", encoding="utf-8")
    print(txt)


def main() -> None:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("aggregate-binance")
    a.add_argument("inputs", nargs="+")
    a.add_argument("--out", required=True)

    n = sub.add_parser("normalize-tv")
    n.add_argument("input")
    n.add_argument("--out", required=True)

    c = sub.add_parser("calibrate")
    c.add_argument("--tv", required=True)
    c.add_argument("--binance", required=True)
    c.add_argument("--out")

    args = p.parse_args()
    if args.cmd == "aggregate-binance":
        rows = aggregate_binance([Path(x) for x in args.inputs])
        write_csv(rows, Path(args.out))
    elif args.cmd == "normalize-tv":
        rows = normalize_tv_csv(Path(args.input))
        write_csv(rows, Path(args.out))
    else:
        report = calibrate(read_csv_numeric(Path(args.tv)), read_csv_numeric(Path(args.binance)))
        _json_dump(report, Path(args.out) if args.out else None)


if __name__ == "__main__":
    main()
