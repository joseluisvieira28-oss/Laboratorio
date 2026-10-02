#!/usr/bin/env python3
"""
MEXC Event Futures Lab V0.7 — frozen calendar/session directional-bias study.

Research only. Public MEXC standard-futures index-price Min5 proxy.
No authentication, no orders, no September-2026 holdout.
"""
import csv
import json
import math
import os
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

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
DIRECTIONS = ["ALWAYS_UP", "ALWAYS_DOWN"]
MIN_N = {10: 120, 30: 100, 60: 80, 1440: 20}
P0 = 1.0 / 1.8
PAYOUT = 0.80
BH_Q = 0.05
Z95 = 1.959963984540054
STEP = 300

DISC_START = int(datetime(2026, 4, 1, tzinfo=timezone.utc).timestamp())
DISC_END = int(datetime(2026, 8, 1, tzinfo=timezone.utc).timestamp())
OOS_START = DISC_END
OOS_END = int(datetime(2026, 9, 1, tzinfo=timezone.utc).timestamp())
FETCH_START = DISC_START
FETCH_END_RAW = OOS_END - 2 * STEP
NY = ZoneInfo("America/New_York")

CONTEXTS = {
    "UTC4H": ["UTC00_04", "UTC04_08", "UTC08_12", "UTC12_16", "UTC16_20", "UTC20_24"],
    "WEEKDAY": ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"],
    "BROAD_SESSION": ["ASIA", "EUROPE", "US", "LATE"],
    "US_CASH_WINDOW": ["US_OPEN_HOUR", "US_MIDDAY", "US_CLOSE_HOUR", "US_OFF_HOURS"],
}

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
    out = {}
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
                raise RuntimeError("holdout-boundary violation")
            mapped = s + STEP
            if FETCH_START <= mapped < OOS_END:
                out[mapped] = p
        t = e + STEP
        time.sleep(0.10)
    return out, reqs

def context_label(family, t):
    dt = datetime.fromtimestamp(t, tz=timezone.utc)
    h = dt.hour

    if family == "UTC4H":
        starts = [0, 4, 8, 12, 16, 20]
        labels = CONTEXTS[family]
        for i, s in enumerate(starts):
            if s <= h < s + 4:
                return labels[i]

    if family == "WEEKDAY":
        return CONTEXTS[family][dt.weekday()]

    if family == "BROAD_SESSION":
        if 0 <= h < 8:
            return "ASIA"
        if 8 <= h < 13:
            return "EUROPE"
        if 13 <= h < 21:
            return "US"
        return "LATE"

    if family == "US_CASH_WINDOW":
        ny = dt.astimezone(NY)
        minutes = ny.hour * 60 + ny.minute
        if 9 * 60 + 30 <= minutes < 10 * 60 + 30:
            return "US_OPEN_HOUR"
        if 11 * 60 + 30 <= minutes < 14 * 60 + 30:
            return "US_MIDDAY"
        if 15 * 60 <= minutes < 16 * 60:
            return "US_CLOSE_HOUR"
        return "US_OFF_HOURS"

    raise ValueError(family)

def aligned(start, end, horizon_min):
    step = horizon_min * 60
    t = ((start + step - 1) // step) * step
    while t < end:
        yield t
        t += step

def wilson_lower(w, l):
    n = w + l
    if not n:
        return None
    p = w / n
    z2 = Z95 * Z95
    return (p + z2/(2*n) - Z95*math.sqrt((p*(1-p) + z2/(4*n))/n)) / (1 + z2/n)

def exact_p(w, l):
    n = w + l
    return None if not n else float(binomtest(w, n, P0, alternative="greater").pvalue)

def score(prices, family, label, horizon, direction, start, end):
    w = l = ties = missing = outside = 0
    thirds = [[0, 0, 0] for _ in range(3)]
    span = end - start

    for t in aligned(start, end, horizon):
        if context_label(family, t) != label:
            outside += 1
            continue
        after = t + horizon * 60
        if after >= end:
            continue
        if t not in prices or after not in prices:
            missing += 1
            continue
        d = prices[after] - prices[t]
        third = min(2, max(0, int(3 * (t - start) / max(1, span))))
        if d == 0:
            ties += 1
            thirds[third][2] += 1
            continue
        actual_up = d > 0
        pred_up = direction == "ALWAYS_UP"
        if actual_up == pred_up:
            w += 1
            thirds[third][0] += 1
        else:
            l += 1
            thirds[third][1] += 1

    n = w + l
    acc = w / n if n else None
    thirds_acc = [(a/(a+b) if a+b else None) for a,b,_ in thirds]
    ev = ((w * PAYOUT - l) / (w + l + ties)) if (w + l + ties) else None
    required = (l / w) if w else None
    return {
        "wins": w,
        "losses": l,
        "ties": ties,
        "missing": missing,
        "outside_context": outside,
        "non_ties": n,
        "accuracy": acc,
        "wilson95_lower": wilson_lower(w, l),
        "p_value_vs_be80": exact_p(w, l),
        "third_accuracies": thirds_acc,
        "ev80": ev,
        "required_payout_for_ev0": required,
        "entry_stride_min": horizon,
    }

def eligible(r, h):
    return (
        r["non_ties"] >= MIN_N[h]
        and r["accuracy"] is not None and r["accuracy"] > P0
        and r["wilson95_lower"] is not None and r["wilson95_lower"] > 0.50
        and all(x is not None and x > 0.50 for x in r["third_accuracies"])
        and r["p_value_vs_be80"] is not None
    )

def bh_select(cells):
    e = [x for x in cells if x["eligible"]]
    e.sort(key=lambda x: x["discovery"]["p_value_vs_be80"])
    m = len(e)
    cutoff = None
    for rank, x in enumerate(e, 1):
        if x["discovery"]["p_value_vs_be80"] <= (rank / m) * BH_Q:
            cutoff = x["discovery"]["p_value_vs_be80"]
    return ([] if cutoff is None else [x for x in e if x["discovery"]["p_value_vs_be80"] <= cutoff]), m, cutoff

def oos_pass(r):
    return (
        r["non_ties"] > 0
        and r["accuracy"] is not None and r["accuracy"] > P0
        and r["wilson95_lower"] is not None and r["wilson95_lower"] > 0.50
        and r["p_value_vs_be80"] is not None and r["p_value_vs_be80"] < 0.05
        and r["ev80"] is not None and r["ev80"] > 0
    )

def flat(stage, asset, family, label, h, direction, r, gate):
    return {
        "stage": stage,
        "asset": asset,
        "family": family,
        "context": label,
        "horizon_min": h,
        "direction": direction,
        "entry_stride_min": r["entry_stride_min"],
        "wins": r["wins"],
        "losses": r["losses"],
        "ties": r["ties"],
        "missing": r["missing"],
        "outside_context": r["outside_context"],
        "non_ties": r["non_ties"],
        "accuracy": r["accuracy"],
        "wilson95_lower": r["wilson95_lower"],
        "p_value_vs_be80": r["p_value_vs_be80"],
        "third1_accuracy": r["third_accuracies"][0],
        "third2_accuracy": r["third_accuracies"][1],
        "third3_accuracy": r["third_accuracies"][2],
        "ev80": r["ev80"],
        "required_payout_for_ev0": r["required_payout_for_ev0"],
        "gate": gate,
    }

def coverage(p, start, end):
    a = [t for t in p if start <= t < end]
    return {"rows": len(a), "first": min(a) if a else None, "last": max(a) if a else None}

def main():
    outdir = "artifacts/mexc_event_futures"
    os.makedirs(outdir, exist_ok=True)

    prices = {}
    assets = {}
    for asset, symbol in SYMBOLS.items():
        try:
            p, reqs = fetch_prices(symbol)
            prices[asset] = p
            assets[asset] = {
                "proxy_symbol": symbol,
                "requests": reqs,
                "total_rows": len(p),
                "discovery_coverage": coverage(p, DISC_START, DISC_END),
                "oos_coverage": coverage(p, OOS_START, OOS_END),
            }
            assets[asset]["source_status"] = (
                "SOURCE_AVAILABLE"
                if assets[asset]["discovery_coverage"]["rows"] and assets[asset]["oos_coverage"]["rows"]
                else "SOURCE_BLOCKED"
            )
        except Exception as e:
            assets[asset] = {"proxy_symbol": symbol, "source_status": "SOURCE_BLOCKED", "error": repr(e)}

    available = [a for a,v in assets.items() if v["source_status"] == "SOURCE_AVAILABLE"]
    cells = []
    rows = []

    for asset in available:
        for family, labels in CONTEXTS.items():
            for label in labels:
                for h in HORIZONS:
                    for direction in DIRECTIONS:
                        r = score(prices[asset], family, label, h, direction, DISC_START, DISC_END)
                        ok = eligible(r, h)
                        c = {
                            "asset": asset,
                            "family": family,
                            "context": label,
                            "horizon_min": h,
                            "direction": direction,
                            "eligible": ok,
                            "discovery": r,
                        }
                        cells.append(c)
                        rows.append(flat(
                            "DISCOVERY", asset, family, label, h, direction, r,
                            "DISCOVERY_ELIGIBLE" if ok else "DISCOVERY_FAIL"
                        ))

    selected, m, cutoff = bh_select(cells)
    survivors = []
    for c in selected:
        r = score(
            prices[c["asset"]], c["family"], c["context"], c["horizon_min"], c["direction"],
            OOS_START, OOS_END
        )
        passed = oos_pass(r)
        rows.append(flat(
            "OOS", c["asset"], c["family"], c["context"], c["horizon_min"], c["direction"], r,
            "OOS_PASS" if passed else "OOS_FAIL"
        ))
        if passed:
            survivors.append({
                "asset": c["asset"],
                "family": c["family"],
                "context": c["context"],
                "horizon_min": c["horizon_min"],
                "direction": c["direction"],
                "discovery": c["discovery"],
                "oos": r,
            })

    report = {
        "lab": "MEXC_EVENT_FUTURES_SESSION_CALENDAR_V0.7",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "MEXC_STANDARD_FUTURES_INDEX_PRICE_MIN5_PROXY_CLOSE_AT_BUCKET_END",
        "historical_holdout_sep_2026": "LOCKED_NOT_FETCHED",
        "exact_event_futures": "NOT_PROVEN",
        "reference_payout": PAYOUT,
        "reference_break_even_accuracy": P0,
        "discovery_multiple_testing": "BENJAMINI_HOCHBERG_FDR_Q_0.05",
        "contexts": CONTEXTS,
        "assets": assets,
        "source_available_assets": available,
        "source_blocked_assets": [a for a,v in assets.items() if v["source_status"] != "SOURCE_AVAILABLE"],
        "discovery_cells": cells,
        "bh_eligible_count": m,
        "bh_cutoff_p": cutoff,
        "bh_selected": [{k:v for k,v in c.items() if k != "eligible"} for c in selected],
        "oos_survivors": survivors,
        "verdict": "PROXY_CANDIDATES_SURVIVE_OOS" if survivors else "NO_PROXY_SURVIVOR_AT_FROZEN_V07_GATE",
        "promotion_status": "NO_EXACT_EVENT_FUTURES_PROMOTION",
    }

    jp = f"{outdir}/session_calendar_v07.json"
    cp = f"{outdir}/session_calendar_matrix_v07.csv"
    with open(jp, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, sort_keys=True)

    fields = list(rows[0].keys()) if rows else []
    with open(cp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    compact = {
        "verdict": report["verdict"],
        "source_available_assets": available,
        "source_blocked_assets": report["source_blocked_assets"],
        "discovery_cells": len(cells),
        "bh_eligible_count": m,
        "bh_selected_count": len(selected),
        "bh_cutoff_p": cutoff,
        "oos_survivor_count": len(survivors),
        "oos_survivors": [{
            "asset": x["asset"],
            "family": x["family"],
            "context": x["context"],
            "horizon_min": x["horizon_min"],
            "direction": x["direction"],
            "disc_n": x["discovery"]["non_ties"],
            "disc_acc": x["discovery"]["accuracy"],
            "disc_p": x["discovery"]["p_value_vs_be80"],
            "oos_n": x["oos"]["non_ties"],
            "oos_acc": x["oos"]["accuracy"],
            "oos_p": x["oos"]["p_value_vs_be80"],
            "oos_ev80": x["oos"]["ev80"],
            "required_payout_for_ev0": x["oos"]["required_payout_for_ev0"],
        } for x in survivors],
        "holdout": report["historical_holdout_sep_2026"],
        "exact_event_futures": report["exact_event_futures"],
    }
    print(json.dumps(compact, indent=2, sort_keys=True))
    print("WROTE", jp)
    print("WROTE", cp)

if __name__ == "__main__":
    main()
