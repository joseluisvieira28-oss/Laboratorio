#!/usr/bin/env python3
"""
MEXC Event Futures Lab V0.7 — frozen calendar/session directional structure.

Research only. Public MEXC standard-futures index-price Min5 proxy.
No authentication, no orders, no September-2026 holdout.
"""
import csv
import json
import math
import os
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
HORIZONS = [10, 30, 60, 1440]
DIRECTIONS = ["UP", "DOWN"]
MIN_N = {10: 120, 30: 100, 60: 80, 1440: 30}
P0 = 1.0 / 1.8
PAYOUTS = [0.70, 0.75, 0.80, 0.85, 0.90]
BH_Q = 0.05
Z95 = 1.959963984540054
STEP = 300

DISC_START = int(datetime(2026, 4, 1, tzinfo=timezone.utc).timestamp())
DISC_END = int(datetime(2026, 8, 1, tzinfo=timezone.utc).timestamp())
OOS_START = DISC_END
OOS_END = int(datetime(2026, 9, 1, tzinfo=timezone.utc).timestamp())
FETCH_START = DISC_START - STEP
FETCH_END_RAW = OOS_END - 2 * STEP

WEEKDAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]

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

def fetch_prices(symbol):
    url = f"{BASE}/api/v1/contract/kline/index_price/{symbol}"
    chunk = 5 * 24 * 3600
    t = FETCH_START - STEP
    rows = {}
    reqs = 0
    while t <= FETCH_END_RAW:
        e = min(t + chunk, FETCH_END_RAW)
        j = fetch_json(url, {"interval": "Min5", "start": t, "end": e})
        reqs += 1
        d = j.get("data") or {}
        for s, p in zip(d.get("time") or [], d.get("close") or []):
            try:
                s = int(s)
                p = float(p)
            except Exception:
                continue
            if s >= OOS_END:
                raise RuntimeError("holdout-boundary violation: raw timestamp >= Sep-2026 boundary")
            mapped = s + STEP
            if DISC_START <= mapped < OOS_END:
                rows[mapped] = p
        t = e + STEP
        time.sleep(0.10)
    return rows, reqs

def minute_of_day(t):
    dt = datetime.fromtimestamp(t, tz=timezone.utc)
    return dt.hour * 60 + dt.minute

def weekday_idx(t):
    return datetime.fromtimestamp(t, tz=timezone.utc).weekday()

def in_window(t, start_min, end_min):
    m = minute_of_day(t)
    return start_min <= m < end_min

def make_conditions():
    out = []

    # A: UTC 4h blocks
    for start_h in range(0, 24, 4):
        out.append({
            "family": "UTC4H",
            "label": f"{start_h:02d}-{start_h+4:02d}",
            "kind": "window",
            "start_min": start_h * 60,
            "end_min": (start_h + 4) * 60,
        })

    # B: broad sessions
    broad = [
        ("ASIA", 0, 8*60),
        ("EUROPE", 8*60, 13*60+30),
        ("US_CASH", 13*60+30, 20*60),
        ("LATE_US", 20*60, 24*60),
    ]
    for label, a, b in broad:
        out.append({"family": "BROAD_SESSION", "label": label, "kind": "window", "start_min": a, "end_min": b})

    # C: US cash subwindows
    subs = [
        ("US_PREOPEN", 12*60+30, 13*60+30),
        ("US_OPEN_HOUR", 13*60+30, 14*60+30),
        ("US_MORNING", 14*60+30, 16*60),
        ("US_AFTERNOON", 16*60, 20*60),
    ]
    for label, a, b in subs:
        out.append({"family": "US_SUBWINDOW", "label": label, "kind": "window", "start_min": a, "end_min": b})

    # D: weekday
    for i, label in enumerate(WEEKDAYS):
        out.append({"family": "WEEKDAY", "label": label, "kind": "weekday", "weekday": i})

    # E: weekday x broad session
    for i, wd in enumerate(WEEKDAYS):
        for label, a, b in broad:
            out.append({
                "family": "WEEKDAY_X_SESSION",
                "label": f"{wd}_{label}",
                "kind": "weekday_window",
                "weekday": i,
                "start_min": a,
                "end_min": b,
            })
    return out

CONDITIONS = make_conditions()

def condition_matches(t, c):
    if c["kind"] == "window":
        return in_window(t, c["start_min"], c["end_min"])
    if c["kind"] == "weekday":
        return weekday_idx(t) == c["weekday"]
    if c["kind"] == "weekday_window":
        return weekday_idx(t) == c["weekday"] and in_window(t, c["start_min"], c["end_min"])
    raise ValueError(c["kind"])

def sample_entries(prices, start, end, horizon_min, condition):
    horizon_sec = horizon_min * 60
    last_kept = None
    for t in sorted(k for k in prices if start <= k < end):
        after = t + horizon_sec
        if after >= end or after not in prices:
            continue
        if not condition_matches(t, condition):
            continue
        if last_kept is not None and t < last_kept + horizon_sec:
            continue
        last_kept = t
        yield t, after

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

def score(prices, start, end, horizon, condition, direction):
    wins = losses = ties = 0
    thirds = [[0, 0, 0] for _ in range(3)]
    span = end - start

    for t, after in sample_entries(prices, start, end, horizon, condition):
        move = prices[after] - prices[t]
        third = min(2, max(0, int(3 * (t - start) / max(1, span))))
        if move == 0:
            ties += 1
            thirds[third][2] += 1
            continue
        actual_up = move > 0
        pred_up = direction == "UP"
        if actual_up == pred_up:
            wins += 1
            thirds[third][0] += 1
        else:
            losses += 1
            thirds[third][1] += 1

    n = wins + losses
    acc = wins / n if n else None
    third_acc = [(w/(w+l) if w+l else None) for w,l,_ in thirds]
    out = {
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "non_ties": n,
        "accuracy": acc,
        "wilson95_lower": wilson_lower(wins, losses),
        "p_value_vs_be80": exact_p(wins, losses),
        "third_accuracies": third_acc,
    }
    denom = wins + losses + ties
    for p in PAYOUTS:
        out[f"ev{int(p*100)}"] = ((wins*p - losses)/denom) if denom else None
    out["required_payout_for_ev0"] = (losses / wins) if wins else None
    return out

def discovery_eligible(r, horizon):
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

def flat(asset, stage, horizon, condition, direction, r, gate):
    return {
        "asset": asset,
        "stage": stage,
        "horizon_min": horizon,
        "family": condition["family"],
        "condition": condition["label"],
        "direction": direction,
        "wins": r["wins"],
        "losses": r["losses"],
        "ties": r["ties"],
        "non_ties": r["non_ties"],
        "accuracy": r["accuracy"],
        "wilson95_lower": r["wilson95_lower"],
        "p_value_vs_be80": r["p_value_vs_be80"],
        "third1_accuracy": r["third_accuracies"][0],
        "third2_accuracy": r["third_accuracies"][1],
        "third3_accuracy": r["third_accuracies"][2],
        "ev70": r["ev70"],
        "ev75": r["ev75"],
        "ev80": r["ev80"],
        "ev85": r["ev85"],
        "ev90": r["ev90"],
        "required_payout_for_ev0": r["required_payout_for_ev0"],
        "gate": gate,
    }

def coverage(prices, start, end):
    vals = [t for t in prices if start <= t < end]
    return {"rows": len(vals), "first": min(vals) if vals else None, "last": max(vals) if vals else None}

def main():
    outdir = "artifacts/mexc_event_futures"
    os.makedirs(outdir, exist_ok=True)

    report = {
        "lab": "MEXC_EVENT_FUTURES_SESSION_V0.7",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "MEXC_STANDARD_FUTURES_INDEX_PRICE_MIN5_PROXY_CLOSE_AT_BUCKET_END",
        "historical_holdout_sep_2026": "LOCKED_NOT_FETCHED",
        "exact_event_futures": "NOT_PROVEN",
        "reference_payout": 0.80,
        "reference_break_even_accuracy": P0,
        "multiple_testing": "BENJAMINI_HOCHBERG_FDR_Q_0.05",
        "condition_count": len(CONDITIONS),
        "assets": {},
        "discovery_cells": [],
        "bh_selected": [],
        "oos_survivors": [],
    }
    prices_by_asset = {}
    rows = []

    for asset, proxy in SYMBOLS.items():
        info = {"proxy_symbol": proxy}
        try:
            prices, reqs = fetch_prices(proxy)
            prices_by_asset[asset] = prices
            info["requests"] = reqs
            info["total_rows"] = len(prices)
            info["discovery_coverage"] = coverage(prices, DISC_START, DISC_END)
            info["oos_coverage"] = coverage(prices, OOS_START, OOS_END)
            info["source_status"] = (
                "SOURCE_AVAILABLE"
                if info["discovery_coverage"]["rows"] and info["oos_coverage"]["rows"]
                else "SOURCE_BLOCKED"
            )
        except Exception as e:
            info["source_status"] = "SOURCE_BLOCKED"
            info["error"] = repr(e)
        report["assets"][asset] = info

    available = [a for a,v in report["assets"].items() if v.get("source_status") == "SOURCE_AVAILABLE"]

    for asset in available:
        prices = prices_by_asset[asset]
        for horizon in HORIZONS:
            for condition in CONDITIONS:
                for direction in DIRECTIONS:
                    r = score(prices, DISC_START, DISC_END, horizon, condition, direction)
                    ok = discovery_eligible(r, horizon)
                    c = {
                        "asset": asset,
                        "horizon_min": horizon,
                        "family": condition["family"],
                        "condition": condition["label"],
                        "direction": direction,
                        "eligible": ok,
                        "discovery": r,
                    }
                    report["discovery_cells"].append(c)
                    rows.append(flat(
                        asset, "DISCOVERY", horizon, condition, direction, r,
                        "DISCOVERY_ELIGIBLE" if ok else "DISCOVERY_FAIL"
                    ))

    selected, m, cutoff = bh_select(report["discovery_cells"])
    report["bh_eligible_count"] = m
    report["bh_cutoff_p"] = cutoff
    report["bh_selected"] = [{k:v for k,v in c.items() if k != "eligible"} for c in selected]

    condition_lookup = {(c["family"], c["label"]): c for c in CONDITIONS}
    for c in selected:
        condition = condition_lookup[(c["family"], c["condition"])]
        r = score(
            prices_by_asset[c["asset"]],
            OOS_START, OOS_END,
            c["horizon_min"],
            condition,
            c["direction"],
        )
        passed = oos_pass(r)
        rows.append(flat(
            c["asset"], "OOS", c["horizon_min"], condition, c["direction"], r,
            "OOS_PASS" if passed else "OOS_FAIL"
        ))
        if passed:
            report["oos_survivors"].append({
                "asset": c["asset"],
                "horizon_min": c["horizon_min"],
                "family": c["family"],
                "condition": c["condition"],
                "direction": c["direction"],
                "discovery": c["discovery"],
                "oos": r,
            })

    report["source_available_assets"] = available
    report["source_blocked_assets"] = [a for a,v in report["assets"].items() if v.get("source_status") != "SOURCE_AVAILABLE"]
    report["verdict"] = (
        "PROXY_CANDIDATES_SURVIVE_OOS"
        if report["oos_survivors"]
        else "NO_PROXY_SURVIVOR_AT_FROZEN_V07_GATE"
    )
    report["promotion_status"] = "NO_EXACT_EVENT_FUTURES_PROMOTION"

    jp = f"{outdir}/session_v07.json"
    cp = f"{outdir}/session_matrix_v07.csv"
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
        "condition_count": len(CONDITIONS),
        "discovery_cells": len(report["discovery_cells"]),
        "bh_eligible_count": m,
        "bh_selected_count": len(selected),
        "bh_cutoff_p": cutoff,
        "oos_survivor_count": len(report["oos_survivors"]),
        "oos_survivors": [
            {
                "asset": x["asset"],
                "horizon_min": x["horizon_min"],
                "family": x["family"],
                "condition": x["condition"],
                "direction": x["direction"],
                "disc_n": x["discovery"]["non_ties"],
                "disc_acc": x["discovery"]["accuracy"],
                "disc_p": x["discovery"]["p_value_vs_be80"],
                "oos_n": x["oos"]["non_ties"],
                "oos_acc": x["oos"]["accuracy"],
                "oos_p": x["oos"]["p_value_vs_be80"],
                "oos_ev80": x["oos"]["ev80"],
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
