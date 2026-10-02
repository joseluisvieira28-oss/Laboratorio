#!/usr/bin/env python3
"""
MEXC Event Futures Lab V0.3.1
Frozen Min5 standard-futures INDEX-PRICE PROXY study.

Research only. No authenticated requests. No orders. Sep-2026 holdout is not fetched.
"""
import csv
import json
import math
import os
import time
from datetime import datetime, timezone

import requests

BASE = "https://contract.mexc.com"
SYMBOLS = {
    "BTCUSDT": "BTC_USDT",
    "ETHUSDT": "ETH_USDT",
    "NVDAUSDT": "NVIDIA_USDT",
    "MUUSDT": "MUSTOCK_USDT",
    "SPCXUSDT": "SPCXSTOCK_USDT",
}
LOOKBACKS = [5, 15, 60, 240, 1440]
HORIZONS = [10, 30, 60, 1440]
MODES = ["CONTINUATION", "REVERSAL"]
PAYOUTS = [0.70, 0.75, 0.80, 0.85, 0.90]
BREAKEVEN_80 = 1.0 / 1.8
MIN_N = {10: 200, 30: 150, 60: 100, 1440: 60}
Z95 = 1.959963984540054
STEP = 5 * 60

DISC_START = int(datetime(2026, 4, 1, 0, 0, tzinfo=timezone.utc).timestamp())
DISC_END = int(datetime(2026, 8, 1, 0, 0, tzinfo=timezone.utc).timestamp())
OOS_START = DISC_END
OOS_END = int(datetime(2026, 9, 1, 0, 0, tzinfo=timezone.utc).timestamp())

# Need up to 1 day of trailing data before discovery, but NEVER fetch Sep holdout.
FETCH_START = DISC_START - 2 * 24 * 3600
FETCH_END = OOS_END - 2 * STEP

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

def fetch_min5_index(symbol):
    url = f"{BASE}/api/v1/contract/kline/index_price/{symbol}"
    # Five calendar days => <= 1441 Min5 timestamps, below the 2000 point cap.
    chunk = 5 * 24 * 3600
    t = FETCH_START
    rows = {}
    requests_count = 0
    unexpected = []
    while t <= FETCH_END:
        e = min(t + chunk, FETCH_END)
        j = fetch_json(url, {"interval": "Min5", "start": t, "end": e})
        requests_count += 1
        d = j.get("data") or {}
        ts = d.get("time") or []
        closes = d.get("close") or []
        for a, b in zip(ts, closes):
            try:
                a = int(a)
                b = float(b)
            except Exception:
                continue
            # K-line timestamp is treated as bucket start; close becomes observable
            # only at the end of the 5-minute bucket.
            mapped = a + STEP
            if FETCH_START <= mapped < OOS_END:
                rows[mapped] = b
            elif a >= OOS_END:
                unexpected.append(a)
        t = e + STEP
        time.sleep(0.10)
    if unexpected:
        raise RuntimeError(f"holdout-boundary violation: endpoint returned {len(unexpected)} timestamps >= OOS_END")
    return rows, requests_count

def wilson_lower(wins, losses):
    n = wins + losses
    if n <= 0:
        return None
    p = wins / n
    z2 = Z95 * Z95
    center = p + z2 / (2 * n)
    rad = Z95 * math.sqrt((p * (1 - p) + z2 / (4 * n)) / n)
    return (center - rad) / (1 + z2 / n)

def ev_unit(wins, losses, ties, payout):
    n = wins + losses + ties
    return None if n <= 0 else (wins * payout - losses) / n

def aligned_anchors(start, end, horizon_min):
    step = horizon_min * 60
    first = ((start + step - 1) // step) * step
    t = first
    while t < end:
        yield t
        t += step

def score(prices, start, end, horizon, lookback, mode):
    wins = losses = ties = missing = 0
    thirds = [[0, 0, 0] for _ in range(3)]
    span = end - start

    for t in aligned_anchors(start, end, horizon):
        before = t - lookback * 60
        after = t + horizon * 60
        if after >= end:
            continue
        if before not in prices or t not in prices or after not in prices:
            missing += 1
            continue

        past = prices[t] - prices[before]
        future = prices[after] - prices[t]
        third = min(2, max(0, int(3 * (t - start) / max(1, span))))

        if past == 0 or future == 0:
            ties += 1
            thirds[third][2] += 1
            continue

        pred_up = past > 0
        if mode == "REVERSAL":
            pred_up = not pred_up
        actual_up = future > 0

        if pred_up == actual_up:
            wins += 1
            thirds[third][0] += 1
        else:
            losses += 1
            thirds[third][1] += 1

    non_ties = wins + losses
    acc = wins / non_ties if non_ties else None
    third_acc = []
    for w, l, _ in thirds:
        third_acc.append(w / (w + l) if (w + l) else None)

    out = {
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "missing": missing,
        "non_ties": non_ties,
        "accuracy": acc,
        "wilson95_lower": wilson_lower(wins, losses),
        "third_accuracies": third_acc,
    }
    for p in PAYOUTS:
        out[f"ev_payout_{int(p * 100)}"] = ev_unit(wins, losses, ties, p)
    return out

def discovery_pass(r, horizon):
    return (
        r["non_ties"] >= MIN_N[horizon]
        and r["wilson95_lower"] is not None
        and r["wilson95_lower"] > BREAKEVEN_80
        and r["ev_payout_80"] is not None
        and r["ev_payout_80"] > 0
        and all(x is not None and x > 0.50 for x in r["third_accuracies"])
    )

def oos_pass(r):
    return (
        r["non_ties"] > 0
        and r["wilson95_lower"] is not None
        and r["wilson95_lower"] > BREAKEVEN_80
        and r["ev_payout_80"] is not None
        and r["ev_payout_80"] > 0
    )

def row(asset, proxy, stage, horizon, lookback, mode, r, gate):
    return {
        "asset": asset,
        "proxy_symbol": proxy,
        "stage": stage,
        "horizon_min": horizon,
        "lookback_min": lookback,
        "mode": mode,
        "wins": r["wins"],
        "losses": r["losses"],
        "ties": r["ties"],
        "missing": r["missing"],
        "non_ties": r["non_ties"],
        "accuracy": r["accuracy"],
        "wilson95_lower": r["wilson95_lower"],
        "third1_accuracy": r["third_accuracies"][0],
        "third2_accuracy": r["third_accuracies"][1],
        "third3_accuracy": r["third_accuracies"][2],
        "ev70": r["ev_payout_70"],
        "ev75": r["ev_payout_75"],
        "ev80": r["ev_payout_80"],
        "ev85": r["ev_payout_85"],
        "ev90": r["ev_payout_90"],
        "gate": gate,
    }

def coverage(prices, start, end):
    vals = [t for t in prices if start <= t < end]
    return {
        "rows": len(vals),
        "first": min(vals) if vals else None,
        "last": max(vals) if vals else None,
    }

def main():
    outdir = "artifacts/mexc_event_futures"
    os.makedirs(outdir, exist_ok=True)
    report = {
        "lab": "MEXC_EVENT_FUTURES_PROXY_V0.3.1_CLOCKFIX",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "MEXC_STANDARD_FUTURES_INDEX_PRICE_MIN5_PROXY_CLOSE_MAPPED_TO_BUCKET_END",
        "exact_event_futures": "NOT_PROVEN",
        "historical_holdout_sep_2026": "LOCKED_NOT_FETCHED",
        "unobservable_chart_lookbacks": [1],
        "break_even_reference_80pct": BREAKEVEN_80,
        "assets": {},
        "discovery_passers": [],
        "oos_survivors": [],
    }
    matrix = []

    for asset, proxy in SYMBOLS.items():
        a = {"proxy_symbol": proxy}
        try:
            prices, reqs = fetch_min5_index(proxy)
            a["fetch_requests"] = reqs
            a["total_rows"] = len(prices)
            a["discovery_coverage"] = coverage(prices, DISC_START, DISC_END)
            a["oos_coverage"] = coverage(prices, OOS_START, OOS_END)
        except Exception as e:
            a["source_status"] = "SOURCE_BLOCKED"
            a["error"] = repr(e)
            report["assets"][asset] = a
            continue

        if a["discovery_coverage"]["rows"] == 0 or a["oos_coverage"]["rows"] == 0:
            a["source_status"] = "SOURCE_BLOCKED"
            a["discovery_passers"] = 0
            a["oos_tested"] = 0
            a["oos_survivors"] = 0
            report["assets"][asset] = a
            continue

        a["source_status"] = "SOURCE_AVAILABLE"
        candidates = []
        for horizon in HORIZONS:
            for lookback in LOOKBACKS:
                for mode in MODES:
                    r = score(prices, DISC_START, DISC_END, horizon, lookback, mode)
                    passed = discovery_pass(r, horizon)
                    matrix.append(row(
                        asset, proxy, "DISCOVERY", horizon, lookback, mode, r,
                        "DISCOVERY_PASS" if passed else "DISCOVERY_FAIL"
                    ))
                    if passed:
                        c = {
                            "asset": asset,
                            "proxy_symbol": proxy,
                            "horizon_min": horizon,
                            "lookback_min": lookback,
                            "mode": mode,
                            "discovery": r,
                        }
                        candidates.append(c)
                        report["discovery_passers"].append(c)

        a["discovery_passers"] = len(candidates)
        a["oos_tested"] = 0
        a["oos_survivors"] = 0
        for c in candidates:
            r = score(prices, OOS_START, OOS_END, c["horizon_min"], c["lookback_min"], c["mode"])
            passed = oos_pass(r)
            matrix.append(row(
                asset, proxy, "OOS", c["horizon_min"], c["lookback_min"], c["mode"], r,
                "OOS_PASS" if passed else "OOS_FAIL"
            ))
            a["oos_tested"] += 1
            if passed:
                a["oos_survivors"] += 1
                report["oos_survivors"].append({
                    "asset": asset,
                    "proxy_symbol": proxy,
                    "horizon_min": c["horizon_min"],
                    "lookback_min": c["lookback_min"],
                    "mode": c["mode"],
                    "discovery": c["discovery"],
                    "oos": r,
                })

        report["assets"][asset] = a

    available = [k for k, v in report["assets"].items() if v.get("source_status") == "SOURCE_AVAILABLE"]
    blocked = [k for k, v in report["assets"].items() if v.get("source_status") != "SOURCE_AVAILABLE"]
    report["source_available_assets"] = available
    report["source_blocked_assets"] = blocked
    report["proxy_verdict"] = (
        "PROXY_CANDIDATES_SURVIVE_OOS"
        if report["oos_survivors"]
        else "NO_PROXY_SURVIVOR_AT_FROZEN_GATE"
    )
    report["promotion_status"] = "NO_EXACT_EVENT_FUTURES_PROMOTION"
    report["exact_product_blockers"] = [
        "Historical Event Futures payout-at-entry series not recovered.",
        "Equivalence between standard-futures index K-lines and Event Futures settlement index not proven.",
        "Exact Event Futures entry/expiry timestamp and rounding semantics not reconstructed.",
        "Official Event Futures API trading support is absent.",
    ]

    with open(f"{outdir}/proxy_backtest_v031.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, sort_keys=True)

    fields = [
        "asset","proxy_symbol","stage","horizon_min","lookback_min","mode",
        "wins","losses","ties","missing","non_ties","accuracy","wilson95_lower",
        "third1_accuracy","third2_accuracy","third3_accuracy",
        "ev70","ev75","ev80","ev85","ev90","gate",
    ]
    with open(f"{outdir}/proxy_matrix_v031.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(matrix)

    compact = {
        "proxy_verdict": report["proxy_verdict"],
        "source_available_assets": available,
        "source_blocked_assets": blocked,
        "discovery_passers": len(report["discovery_passers"]),
        "oos_survivors": len(report["oos_survivors"]),
        "survivors": [
            {
                "asset": x["asset"],
                "horizon_min": x["horizon_min"],
                "lookback_min": x["lookback_min"],
                "mode": x["mode"],
                "disc_accuracy": x["discovery"]["accuracy"],
                "disc_wilson_low": x["discovery"]["wilson95_lower"],
                "disc_n": x["discovery"]["non_ties"],
                "oos_accuracy": x["oos"]["accuracy"],
                "oos_wilson_low": x["oos"]["wilson95_lower"],
                "oos_n": x["oos"]["non_ties"],
                "oos_ev80": x["oos"]["ev_payout_80"],
            }
            for x in report["oos_survivors"]
        ],
        "holdout": report["historical_holdout_sep_2026"],
        "exact_event_futures": report["exact_event_futures"],
    }
    print(json.dumps(compact, indent=2, sort_keys=True))
    print(f"WROTE {outdir}/proxy_backtest_v031.json")
    print(f"WROTE {outdir}/proxy_matrix_v031.csv")

if __name__ == "__main__":
    main()
