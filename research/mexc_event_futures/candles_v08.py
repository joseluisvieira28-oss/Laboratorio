#!/usr/bin/env python3
"""
MEXC Event Futures Lab V0.8 — frozen OHLC candle-morphology hypotheses.

Research only. Public MEXC standard-futures index-price K-line proxy.
No authentication, no orders, no September-2026 holdout.
"""
import csv
import json
import math
import os
import statistics
import time
from datetime import datetime, timezone

import requests
from scipy.stats import binomtest

BASE = "https://contract.mexc.com"
SYMBOLS = {
    "BTCUSDT": "BTC_USDT",
    "ETHUSDT": "ETH_USDT",
    "NVDAUSDT": "NVIDIA_USDT",
    "MUUSDT": "MUSTOCK_USDT",
    "SPCXUSDT": "SPCXSTOCK_USDT",
}
CHART_TFS = [5, 15, 60, 240]
HORIZONS = [10, 30, 60, 1440]
STRATEGIES = [
    "BODY_CONT",
    "BODY_REV",
    "CLOSE_LOCATION_CONT",
    "CLOSE_LOCATION_REV",
    "WICK_REJECTION",
    "WICK_FOLLOW",
    "ENGULFING_CONT",
    "LARGE_BODY_CONT",
    "LARGE_BODY_REV",
    "HIGHLOW_BREAKOUT_CONT",
]
MIN_N = {10: 120, 30: 100, 60: 80, 1440: 30}
P0 = 1.0 / 1.8
PAYOUTS = [0.70, 0.75, 0.80, 0.85, 0.90]
BH_Q = 0.05
Z95 = 1.959963984540054
RAW_STEP = 300

DISC_START = int(datetime(2026, 4, 1, tzinfo=timezone.utc).timestamp())
DISC_END = int(datetime(2026, 8, 1, tzinfo=timezone.utc).timestamp())
OOS_START = DISC_END
OOS_END = int(datetime(2026, 9, 1, tzinfo=timezone.utc).timestamp())
FETCH_START = DISC_START - 10 * 24 * 3600
FETCH_END_RAW = OOS_END - 2 * RAW_STEP

def fetch_json(url, params, retries=5):
    last = None
    for i in range(retries):
        try:
            r = requests.get(url, params=params, timeout=30)
            r.raise_for_status()
            j = r.json()
            if isinstance(j, dict) and j.get("success") is True:
                return j
            last = RuntimeError(f"non-success payload: {j}")
        except Exception as e:
            last = e
        time.sleep(0.6 * (i + 1))
    raise last

def fetch_min5_ohlc(symbol):
    url = f"{BASE}/api/v1/contract/kline/index_price/{symbol}"
    chunk = 5 * 24 * 3600
    t = FETCH_START - RAW_STEP
    bars = {}
    reqs = 0
    while t <= FETCH_END_RAW:
        e = min(t + chunk, FETCH_END_RAW)
        j = fetch_json(url, {"interval": "Min5", "start": t, "end": e})
        reqs += 1
        d = j.get("data") or {}
        arrays = [d.get(k) or [] for k in ("time", "open", "high", "low", "close")]
        if not all(arrays):
            raise RuntimeError(f"OHLC_SOURCE_MISSING:{symbol}")
        for s, o, h, l, c in zip(*arrays):
            try:
                s = int(s); o = float(o); h = float(h); l = float(l); c = float(c)
            except Exception:
                continue
            if s >= OOS_END:
                raise RuntimeError("holdout-boundary violation: raw timestamp >= Sep-2026 boundary")
            mapped = s + RAW_STEP
            if FETCH_START <= mapped < OOS_END:
                bars[mapped] = {"open": o, "high": h, "low": l, "close": c}
        t = e + RAW_STEP
        time.sleep(0.10)
    return bars, reqs

def resample(raw, tf_min):
    if tf_min == 5:
        return dict(raw)
    tf_sec = tf_min * 60
    need = tf_min // 5
    grouped = {}
    for t in sorted(raw):
        end = ((t + tf_sec - 1) // tf_sec) * tf_sec
        grouped.setdefault(end, []).append((t, raw[t]))
    out = {}
    for end, rows in grouped.items():
        rows.sort(key=lambda x: x[0])
        if len(rows) != need:
            continue
        times = [x[0] for x in rows]
        expected = list(range(end - tf_sec + RAW_STEP, end + 1, RAW_STEP))
        if times != expected:
            continue
        vals = [x[1] for x in rows]
        out[end] = {
            "open": vals[0]["open"],
            "high": max(x["high"] for x in vals),
            "low": min(x["low"] for x in vals),
            "close": vals[-1]["close"],
        }
    return out

def body_direction(bar):
    if bar["close"] > bar["open"]:
        return 1
    if bar["close"] < bar["open"]:
        return -1
    return None

def signal(name, series_times, bars, i):
    t = series_times[i]
    b = bars[t]
    o, h, l, c = b["open"], b["high"], b["low"], b["close"]
    rng = h - l
    body = abs(c - o)
    direction = body_direction(b)

    if name == "BODY_CONT":
        return direction
    if name == "BODY_REV":
        return None if direction is None else -direction

    if name in ("CLOSE_LOCATION_CONT", "CLOSE_LOCATION_REV"):
        if rng <= 0:
            return None
        loc = (c - l) / rng
        sig = 1 if loc >= 0.80 else (-1 if loc <= 0.20 else None)
        if sig is None:
            return None
        return sig if name == "CLOSE_LOCATION_CONT" else -sig

    if name in ("WICK_REJECTION", "WICK_FOLLOW"):
        upper = h - max(o, c)
        lower = min(o, c) - l
        sig = None
        if lower >= 2.0 * upper and lower > body:
            sig = 1
        elif upper >= 2.0 * lower and upper > body:
            sig = -1
        if sig is None:
            return None
        return sig if name == "WICK_REJECTION" else -sig

    if name == "ENGULFING_CONT":
        if i < 1:
            return None
        p = bars[series_times[i-1]]
        curr_lo, curr_hi = min(o, c), max(o, c)
        prev_lo, prev_hi = min(p["open"], p["close"]), max(p["open"], p["close"])
        if curr_lo <= prev_lo and curr_hi >= prev_hi and direction is not None:
            return direction
        return None

    if name in ("LARGE_BODY_CONT", "LARGE_BODY_REV"):
        if i < 20 or rng <= 0 or direction is None:
            return None
        prior_ranges = [
            bars[series_times[k]]["high"] - bars[series_times[k]]["low"]
            for k in range(i-20, i)
        ]
        med = statistics.median(prior_ranges)
        if med <= 0:
            return None
        if body / rng >= 0.70 and rng >= 1.5 * med:
            return direction if name == "LARGE_BODY_CONT" else -direction
        return None

    if name == "HIGHLOW_BREAKOUT_CONT":
        if i < 20:
            return None
        prior = [bars[series_times[k]] for k in range(i-20, i)]
        hi20 = max(x["high"] for x in prior)
        lo20 = min(x["low"] for x in prior)
        if c > hi20:
            return 1
        if c < lo20:
            return -1
        return None

    raise ValueError(name)

def wilson_lower(wins, losses):
    n = wins + losses
    if n <= 0:
        return None
    p = wins / n
    z2 = Z95 * Z95
    center = p + z2 / (2*n)
    rad = Z95 * math.sqrt((p*(1-p) + z2/(4*n))/n)
    return (center - rad) / (1 + z2/n)

def exact_p(wins, losses):
    n = wins + losses
    if n <= 0:
        return None
    return float(binomtest(wins, n, P0, alternative="greater").pvalue)

def score(raw, chart_bars, tf_min, horizon, strategy, start, end):
    times = sorted(t for t in chart_bars if t < end)
    idx = {t:i for i,t in enumerate(times)}
    stride = max(tf_min, horizon) * 60
    last_kept = None
    wins = losses = ties = missing = no_signal = 0
    thirds = [[0,0,0] for _ in range(3)]
    span = end - start

    for t in times:
        if not (start <= t < end):
            continue
        after = t + horizon * 60
        if after >= end:
            continue
        if last_kept is not None and t < last_kept + stride:
            continue
        if t not in raw or after not in raw:
            missing += 1
            continue

        i = idx[t]
        sig = signal(strategy, times, chart_bars, i)
        if sig is None:
            no_signal += 1
            continue

        # Only accepted signal entries consume the non-overlap stride.
        last_kept = t
        move = raw[after]["close"] - raw[t]["close"]
        third = min(2, max(0, int(3 * (t-start) / max(1, span))))
        if move == 0:
            ties += 1
            thirds[third][2] += 1
        elif (move > 0 and sig > 0) or (move < 0 and sig < 0):
            wins += 1
            thirds[third][0] += 1
        else:
            losses += 1
            thirds[third][1] += 1

    n = wins + losses
    acc = wins/n if n else None
    third_acc = [(w/(w+l) if w+l else None) for w,l,_ in thirds]
    denom = wins + losses + ties
    out = {
        "wins": wins, "losses": losses, "ties": ties,
        "missing": missing, "no_signal": no_signal,
        "non_ties": n, "accuracy": acc,
        "wilson95_lower": wilson_lower(wins, losses),
        "p_value_vs_be80": exact_p(wins, losses),
        "third_accuracies": third_acc,
        "entry_stride_min": max(tf_min, horizon),
        "required_payout_for_ev0": (losses/wins) if wins else None,
    }
    for p in PAYOUTS:
        out[f"ev{int(p*100)}"] = ((wins*p-losses)/denom) if denom else None
    return out

def eligible(r, horizon):
    return (
        r["non_ties"] >= MIN_N[horizon]
        and r["accuracy"] is not None and r["accuracy"] > P0
        and r["wilson95_lower"] is not None and r["wilson95_lower"] > 0.50
        and all(x is not None and x > 0.50 for x in r["third_accuracies"])
        and r["p_value_vs_be80"] is not None
    )

def bh_select(cells):
    e = [c for c in cells if c["eligible"]]
    e.sort(key=lambda x: x["discovery"]["p_value_vs_be80"])
    m = len(e)
    cutoff = None
    for rank, c in enumerate(e, 1):
        if c["discovery"]["p_value_vs_be80"] <= (rank/m) * BH_Q:
            cutoff = c["discovery"]["p_value_vs_be80"]
    selected = [] if cutoff is None else [c for c in e if c["discovery"]["p_value_vs_be80"] <= cutoff]
    return selected, m, cutoff

def oos_pass(r):
    return (
        r["non_ties"] > 0
        and r["accuracy"] is not None and r["accuracy"] > P0
        and r["wilson95_lower"] is not None and r["wilson95_lower"] > 0.50
        and r["p_value_vs_be80"] is not None and r["p_value_vs_be80"] < 0.05
        and r["ev80"] is not None and r["ev80"] > 0
    )

def flat(asset, stage, tf, horizon, strategy, r, gate):
    return {
        "asset": asset, "stage": stage, "chart_tf_min": tf,
        "horizon_min": horizon, "strategy": strategy,
        "entry_stride_min": r["entry_stride_min"],
        "wins": r["wins"], "losses": r["losses"], "ties": r["ties"],
        "missing": r["missing"], "no_signal": r["no_signal"],
        "non_ties": r["non_ties"], "accuracy": r["accuracy"],
        "wilson95_lower": r["wilson95_lower"],
        "p_value_vs_be80": r["p_value_vs_be80"],
        "third1_accuracy": r["third_accuracies"][0],
        "third2_accuracy": r["third_accuracies"][1],
        "third3_accuracy": r["third_accuracies"][2],
        "ev70": r["ev70"], "ev75": r["ev75"], "ev80": r["ev80"],
        "ev85": r["ev85"], "ev90": r["ev90"],
        "required_payout_for_ev0": r["required_payout_for_ev0"],
        "gate": gate,
    }

def coverage(raw, start, end):
    vals = [t for t in raw if start <= t < end]
    return {"rows":len(vals), "first":min(vals) if vals else None, "last":max(vals) if vals else None}

def main():
    outdir = "artifacts/mexc_event_futures"
    os.makedirs(outdir, exist_ok=True)
    report = {
        "lab": "MEXC_EVENT_FUTURES_CANDLE_V0.8",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "MEXC_STANDARD_FUTURES_INDEX_PRICE_MIN5_OHLC_PROXY_CLOSE_AT_BUCKET_END",
        "historical_holdout_sep_2026": "LOCKED_NOT_FETCHED",
        "exact_event_futures": "NOT_PROVEN",
        "reference_payout": 0.80,
        "reference_break_even_accuracy": P0,
        "multiple_testing": "BENJAMINI_HOCHBERG_FDR_Q_0.05",
        "assets": {},
        "discovery_cells": [],
        "bh_selected": [],
        "oos_survivors": [],
    }
    raw_by_asset = {}
    charts_by_asset = {}
    rows = []

    for asset, proxy in SYMBOLS.items():
        info = {"proxy_symbol": proxy}
        try:
            raw, reqs = fetch_min5_ohlc(proxy)
            info["requests"] = reqs
            info["total_raw_bars"] = len(raw)
            info["discovery_coverage"] = coverage(raw, DISC_START, DISC_END)
            info["oos_coverage"] = coverage(raw, OOS_START, OOS_END)
            if not info["discovery_coverage"]["rows"] or not info["oos_coverage"]["rows"]:
                info["source_status"] = "SOURCE_BLOCKED"
            else:
                info["source_status"] = "SOURCE_AVAILABLE"
                raw_by_asset[asset] = raw
                charts_by_asset[asset] = {tf: resample(raw, tf) for tf in CHART_TFS}
                info["chart_bar_counts"] = {str(tf): len(charts_by_asset[asset][tf]) for tf in CHART_TFS}
        except Exception as e:
            info["source_status"] = "SOURCE_BLOCKED"
            info["error"] = repr(e)
        report["assets"][asset] = info

    available = [a for a,v in report["assets"].items() if v.get("source_status") == "SOURCE_AVAILABLE"]

    for asset in available:
        raw = raw_by_asset[asset]
        for tf in CHART_TFS:
            chart = charts_by_asset[asset][tf]
            for horizon in HORIZONS:
                for strategy in STRATEGIES:
                    r = score(raw, chart, tf, horizon, strategy, DISC_START, DISC_END)
                    ok = eligible(r, horizon)
                    c = {
                        "asset": asset, "chart_tf_min": tf,
                        "horizon_min": horizon, "strategy": strategy,
                        "eligible": ok, "discovery": r,
                    }
                    report["discovery_cells"].append(c)
                    rows.append(flat(
                        asset, "DISCOVERY", tf, horizon, strategy, r,
                        "DISCOVERY_ELIGIBLE" if ok else "DISCOVERY_FAIL"
                    ))

    selected, m, cutoff = bh_select(report["discovery_cells"])
    report["bh_eligible_count"] = m
    report["bh_cutoff_p"] = cutoff
    report["bh_selected"] = [{k:v for k,v in c.items() if k != "eligible"} for c in selected]

    for c in selected:
        raw = raw_by_asset[c["asset"]]
        chart = charts_by_asset[c["asset"]][c["chart_tf_min"]]
        r = score(raw, chart, c["chart_tf_min"], c["horizon_min"], c["strategy"], OOS_START, OOS_END)
        passed = oos_pass(r)
        rows.append(flat(
            c["asset"], "OOS", c["chart_tf_min"], c["horizon_min"], c["strategy"], r,
            "OOS_PASS" if passed else "OOS_FAIL"
        ))
        if passed:
            report["oos_survivors"].append({
                "asset": c["asset"], "chart_tf_min": c["chart_tf_min"],
                "horizon_min": c["horizon_min"], "strategy": c["strategy"],
                "discovery": c["discovery"], "oos": r,
            })

    report["source_available_assets"] = available
    report["source_blocked_assets"] = [a for a,v in report["assets"].items() if v.get("source_status") != "SOURCE_AVAILABLE"]
    report["verdict"] = (
        "PROXY_CANDIDATES_SURVIVE_OOS"
        if report["oos_survivors"]
        else "NO_PROXY_SURVIVOR_AT_FROZEN_V08_GATE"
    )
    report["promotion_status"] = "NO_EXACT_EVENT_FUTURES_PROMOTION"

    jp = f"{outdir}/candles_v08.json"
    cp = f"{outdir}/candles_matrix_v08.csv"
    with open(jp, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, sort_keys=True)
    fields = list(rows[0].keys()) if rows else []
    with open(cp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    compact = {
        "verdict": report["verdict"],
        "source_available_assets": report["source_available_assets"],
        "source_blocked_assets": report["source_blocked_assets"],
        "discovery_cells": len(report["discovery_cells"]),
        "bh_eligible_count": m,
        "bh_selected_count": len(selected),
        "bh_cutoff_p": cutoff,
        "oos_survivor_count": len(report["oos_survivors"]),
        "oos_survivors": [
            {
                "asset": x["asset"], "chart_tf_min": x["chart_tf_min"],
                "horizon_min": x["horizon_min"], "strategy": x["strategy"],
                "disc_n": x["discovery"]["non_ties"], "disc_acc": x["discovery"]["accuracy"],
                "disc_p": x["discovery"]["p_value_vs_be80"],
                "oos_n": x["oos"]["non_ties"], "oos_acc": x["oos"]["accuracy"],
                "oos_p": x["oos"]["p_value_vs_be80"], "oos_ev80": x["oos"]["ev80"],
                "required_payout_for_ev0": x["oos"]["required_payout_for_ev0"],
            }
            for x in report["oos_survivors"]
        ],
        "holdout": report["historical_holdout_sep_2026"],
        "exact_event_futures": report["exact_event_futures"],
    }
    print(json.dumps(compact, indent=2, sort_keys=True))
    print("WROTE", jp)
    print("WROTE", cp)

if __name__ == "__main__":
    main()
