#!/usr/bin/env python3
"""
MEXC Event Futures Lab V0.9 — frozen volatility-regime directional hypotheses.

Research only. Public MEXC standard-futures index-price Min5 proxy.
No authentication, no orders, no September-2026 holdout.
"""
import csv
import json
import math
import os
import time
from datetime import datetime, timezone

import numpy as np
import pandas as pd
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
LOOKBACKS = [15, 60, 240]
VOL_WINDOWS = [60, 240, 1440]
REGIMES = ["HIGH_VOL", "LOW_VOL"]
MODES = ["CONTINUATION", "REVERSAL"]
HORIZONS = [10, 30, 60, 1440]
MIN_N = {10: 80, 30: 70, 60: 60, 1440: 25}
P0 = 1.0 / 1.8
PAYOUTS = [0.70, 0.75, 0.80, 0.85, 0.90]
BH_Q = 0.05
Z95 = 1.959963984540054
STEP = 300

DISC_START = int(datetime(2026, 4, 1, tzinfo=timezone.utc).timestamp())
DISC_END = int(datetime(2026, 8, 1, tzinfo=timezone.utc).timestamp())
OOS_START = DISC_END
OOS_END = int(datetime(2026, 9, 1, tzinfo=timezone.utc).timestamp())
FETCH_START = DISC_START - 10 * 24 * 3600
FETCH_END_RAW = OOS_END - 2 * STEP
BASELINE_POINTS = 7 * 24 * 12  # 7 calendar days on 5m grid

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
        ts = d.get("time") or []
        closes = d.get("close") or []
        for s, p in zip(ts, closes):
            try:
                s = int(s); p = float(p)
            except Exception:
                continue
            if s >= OOS_END:
                raise RuntimeError("holdout-boundary violation: raw timestamp >= Sep-2026 boundary")
            mapped = s + STEP
            if FETCH_START <= mapped < OOS_END:
                rows[mapped] = p
        t = e + STEP
        time.sleep(0.10)
    return rows, reqs

def build_frame(prices):
    idx = sorted(prices)
    vals = [prices[t] for t in idx]
    df = pd.DataFrame({"price": vals}, index=pd.Index(idx, name="ts"))
    df["logret"] = np.log(df["price"]).diff()

    for w in VOL_WINDOWS:
        n = w // 5
        rv = df["logret"].rolling(n, min_periods=n).std(ddof=0)
        baseline = rv.shift(1).rolling(BASELINE_POINTS, min_periods=BASELINE_POINTS).median()
        ratio = rv / baseline
        df[f"rv_{w}"] = rv
        df[f"rv_base_{w}"] = baseline
        df[f"ratio_{w}"] = ratio
        df[f"high_{w}"] = ratio >= 1.50
        df[f"low_{w}"] = ratio <= 0.67
    return df

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

def score(prices, df, lookback, vol_window, regime, mode, horizon, start, end):
    stride_sec = max(lookback, vol_window, horizon) * 60
    look_sec = lookback * 60
    hor_sec = horizon * 60
    regime_col = f"high_{vol_window}" if regime == "HIGH_VOL" else f"low_{vol_window}"

    last_kept = None
    wins = losses = ties = missing = no_signal = 0
    thirds = [[0,0,0] for _ in range(3)]
    span = end - start

    for t in df.index:
        t = int(t)
        if t < start or t >= end:
            continue
        if last_kept is not None and t < last_kept + stride_sec:
            continue
        try:
            reg = bool(df.at[t, regime_col])
        except Exception:
            reg = False
        if not reg:
            continue

        before = t - look_sec
        after = t + hor_sec
        if after >= end:
            continue
        if before not in prices or t not in prices or after not in prices:
            missing += 1
            continue

        trailing = prices[t] - prices[before]
        if trailing == 0:
            no_signal += 1
            continue

        sig = 1 if trailing > 0 else -1
        if mode == "REVERSAL":
            sig = -sig

        last_kept = t
        future = prices[after] - prices[t]
        third = min(2, max(0, int(3 * (t-start) / max(1, span))))
        if future == 0:
            ties += 1
            thirds[third][2] += 1
        elif (future > 0 and sig > 0) or (future < 0 and sig < 0):
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
        "entry_stride_min": max(lookback, vol_window, horizon),
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

def flat(asset, stage, lookback, vol_window, regime, mode, horizon, r, gate):
    return {
        "asset": asset, "stage": stage,
        "lookback_min": lookback, "vol_window_min": vol_window,
        "regime": regime, "mode": mode, "horizon_min": horizon,
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

def coverage(prices, start, end):
    vals = [t for t in prices if start <= t < end]
    return {"rows":len(vals), "first":min(vals) if vals else None, "last":max(vals) if vals else None}

def main():
    outdir = "artifacts/mexc_event_futures"
    os.makedirs(outdir, exist_ok=True)
    report = {
        "lab": "MEXC_EVENT_FUTURES_VOLREGIME_V0.9",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "MEXC_STANDARD_FUTURES_INDEX_PRICE_MIN5_PROXY_CLOSE_AT_BUCKET_END",
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
    prices_by_asset = {}
    frames = {}
    rows = []

    for asset, proxy in SYMBOLS.items():
        info = {"proxy_symbol": proxy}
        try:
            prices, reqs = fetch_prices(proxy)
            info["requests"] = reqs
            info["total_rows"] = len(prices)
            info["discovery_coverage"] = coverage(prices, DISC_START, DISC_END)
            info["oos_coverage"] = coverage(prices, OOS_START, OOS_END)
            if info["discovery_coverage"]["rows"] and info["oos_coverage"]["rows"]:
                info["source_status"] = "SOURCE_AVAILABLE"
                prices_by_asset[asset] = prices
                frames[asset] = build_frame(prices)
            else:
                info["source_status"] = "SOURCE_BLOCKED"
        except Exception as e:
            info["source_status"] = "SOURCE_BLOCKED"
            info["error"] = repr(e)
        report["assets"][asset] = info

    available = [a for a,v in report["assets"].items() if v.get("source_status") == "SOURCE_AVAILABLE"]

    for asset in available:
        prices = prices_by_asset[asset]
        df = frames[asset]
        for lookback in LOOKBACKS:
            for vol_window in VOL_WINDOWS:
                for regime in REGIMES:
                    for mode in MODES:
                        for horizon in HORIZONS:
                            r = score(prices, df, lookback, vol_window, regime, mode, horizon, DISC_START, DISC_END)
                            ok = eligible(r, horizon)
                            c = {
                                "asset": asset, "lookback_min": lookback,
                                "vol_window_min": vol_window, "regime": regime,
                                "mode": mode, "horizon_min": horizon,
                                "eligible": ok, "discovery": r,
                            }
                            report["discovery_cells"].append(c)
                            rows.append(flat(
                                asset, "DISCOVERY", lookback, vol_window, regime, mode, horizon, r,
                                "DISCOVERY_ELIGIBLE" if ok else "DISCOVERY_FAIL"
                            ))

    selected, m, cutoff = bh_select(report["discovery_cells"])
    report["bh_eligible_count"] = m
    report["bh_cutoff_p"] = cutoff
    report["bh_selected"] = [{k:v for k,v in c.items() if k != "eligible"} for c in selected]

    for c in selected:
        asset = c["asset"]
        r = score(
            prices_by_asset[asset], frames[asset],
            c["lookback_min"], c["vol_window_min"], c["regime"],
            c["mode"], c["horizon_min"], OOS_START, OOS_END
        )
        passed = oos_pass(r)
        rows.append(flat(
            asset, "OOS", c["lookback_min"], c["vol_window_min"], c["regime"],
            c["mode"], c["horizon_min"], r,
            "OOS_PASS" if passed else "OOS_FAIL"
        ))
        if passed:
            report["oos_survivors"].append({
                "asset": asset, "lookback_min": c["lookback_min"],
                "vol_window_min": c["vol_window_min"], "regime": c["regime"],
                "mode": c["mode"], "horizon_min": c["horizon_min"],
                "discovery": c["discovery"], "oos": r,
            })

    report["source_available_assets"] = available
    report["source_blocked_assets"] = [a for a,v in report["assets"].items() if v.get("source_status") != "SOURCE_AVAILABLE"]
    report["verdict"] = (
        "PROXY_CANDIDATES_SURVIVE_OOS"
        if report["oos_survivors"]
        else "NO_PROXY_SURVIVOR_AT_FROZEN_V09_GATE"
    )
    report["promotion_status"] = "NO_EXACT_EVENT_FUTURES_PROMOTION"

    jp = f"{outdir}/volregime_v09.json"
    cp = f"{outdir}/volregime_matrix_v09.csv"
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
                "asset": x["asset"], "lookback_min": x["lookback_min"],
                "vol_window_min": x["vol_window_min"], "regime": x["regime"],
                "mode": x["mode"], "horizon_min": x["horizon_min"],
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
