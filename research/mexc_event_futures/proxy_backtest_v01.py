#!/usr/bin/env python3
"""
MEXC Event Futures V0.1 — frozen directional INDEX-PRICE PROXY test.

IMPORTANT:
- Research only.
- Uses MEXC standard-futures public index-price K-lines as a proxy.
- Does NOT use Event Futures payout history (not identified).
- Does NOT evaluate the locked Sep-2026 historical holdout.
- Does NOT place or prepare orders.
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
LOOKBACKS = [1, 5, 15, 60, 240, 1440]
HORIZONS = [10, 30, 60, 1440]
MODES = ["CONTINUATION", "REVERSAL"]
PAYOUTS = [0.70, 0.75, 0.80, 0.85, 0.90]
BREAKEVEN_80 = 1.0 / 1.8
MIN_N = {10: 200, 30: 150, 60: 100, 1440: 60}
Z95 = 1.959963984540054

DISC_START = int(datetime(2026, 4, 1, tzinfo=timezone.utc).timestamp())
DISC_END = int(datetime(2026, 8, 1, tzinfo=timezone.utc).timestamp())  # exclusive
OOS_START = DISC_END
OOS_END = int(datetime(2026, 9, 1, tzinfo=timezone.utc).timestamp())   # exclusive
FETCH_START = DISC_START - 2 * 24 * 3600
FETCH_END = OOS_END - 60  # never fetch Sep holdout
MIN1 = 60

def fetch_json(url, params, retries=4):
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
        time.sleep(0.5 * (i + 1))
    raise last

def fetch_min1_index(symbol):
    url = f"{BASE}/api/v1/contract/kline/index_price/{symbol}"
    # Keep chunks below the documented max-return envelope.
    chunk = 1800 * 60
    t = FETCH_START
    rows = {}
    requests_count = 0
    while t <= FETCH_END:
        e = min(t + chunk - 60, FETCH_END)
        j = fetch_json(url, {"interval": "Min1", "start": t, "end": e})
        requests_count += 1
        d = j.get("data") or {}
        ts = d.get("time") or []
        closes = d.get("close") or []
        for a, b in zip(ts, closes):
            try:
                rows[int(a)] = float(b)
            except Exception:
                pass
        t = e + 60
        time.sleep(0.12)
    return rows, requests_count

def wilson_lower(wins, losses):
    n = wins + losses
    if n <= 0:
        return None
    p = wins / n
    z2 = Z95 * Z95
    center = p + z2 / (2 * n)
    rad = Z95 * math.sqrt((p * (1 - p) + z2 / (4 * n)) / n)
    denom = 1 + z2 / n
    return (center - rad) / denom

def ev_per_unit(wins, losses, ties, payout):
    n = wins + losses + ties
    if n <= 0:
        return None
    return (wins * payout - losses) / n

def aligned_anchors(start, end, horizon_min):
    step = horizon_min * 60
    first = ((start + step - 1) // step) * step
    t = first
    while t < end:
        yield t
        t += step

def score_cell(prices, start, end, horizon, lookback, mode):
    wins = losses = ties = missing = 0
    thirds = [[0,0,0] for _ in range(3)]  # w,l,t
    span = end - start
    for t in aligned_anchors(start, end, horizon):
        prev_t = t - lookback * MIN1
        fut_t = t + horizon * MIN1
        if fut_t >= end:
            continue
        if prev_t not in prices or t not in prices or fut_t not in prices:
            missing += 1
            continue
        past = prices[t] - prices[prev_t]
        future = prices[fut_t] - prices[t]
        if past == 0 or future == 0:
            ties += 1
            idx = min(2, max(0, int(3 * (t - start) / max(1, span))))
            thirds[idx][2] += 1
            continue
        pred_up = past > 0
        if mode == "REVERSAL":
            pred_up = not pred_up
        actual_up = future > 0
        idx = min(2, max(0, int(3 * (t - start) / max(1, span))))
        if pred_up == actual_up:
            wins += 1
            thirds[idx][0] += 1
        else:
            losses += 1
            thirds[idx][1] += 1

    non_ties = wins + losses
    accuracy = (wins / non_ties) if non_ties else None
    lower = wilson_lower(wins, losses)
    third_acc = []
    for w,l,_ in thirds:
        third_acc.append((w/(w+l)) if (w+l) else None)

    result = {
        "wins": wins, "losses": losses, "ties": ties, "missing": missing,
        "non_ties": non_ties,
        "accuracy": accuracy,
        "wilson95_lower": lower,
        "third_accuracies": third_acc,
    }
    for p in PAYOUTS:
        result[f"ev_payout_{int(p*100)}"] = ev_per_unit(wins, losses, ties, p)
    return result

def discovery_pass(result, horizon):
    if result["non_ties"] < MIN_N[horizon]:
        return False
    if result["wilson95_lower"] is None or result["wilson95_lower"] <= BREAKEVEN_80:
        return False
    if result["ev_payout_80"] is None or result["ev_payout_80"] <= 0:
        return False
    thirds = result["third_accuracies"]
    if any(x is None or x <= 0.50 for x in thirds):
        return False
    return True

def oos_pass(result):
    return (
        result["non_ties"] > 0
        and result["wilson95_lower"] is not None
        and result["wilson95_lower"] > BREAKEVEN_80
        and result["ev_payout_80"] is not None
        and result["ev_payout_80"] > 0
    )

def compact_row(asset, proxy, horizon, lookback, mode, stage, r, gate):
    return {
        "asset": asset, "proxy_symbol": proxy, "stage": stage,
        "horizon_min": horizon, "lookback_min": lookback, "mode": mode,
        "wins": r["wins"], "losses": r["losses"], "ties": r["ties"],
        "missing": r["missing"], "non_ties": r["non_ties"],
        "accuracy": r["accuracy"], "wilson95_lower": r["wilson95_lower"],
        "third1_accuracy": r["third_accuracies"][0],
        "third2_accuracy": r["third_accuracies"][1],
        "third3_accuracy": r["third_accuracies"][2],
        "ev70": r["ev_payout_70"], "ev75": r["ev_payout_75"],
        "ev80": r["ev_payout_80"], "ev85": r["ev_payout_85"], "ev90": r["ev_payout_90"],
        "gate": gate,
    }

def main():
    outdir = "artifacts/mexc_event_futures"
    os.makedirs(outdir, exist_ok=True)
    report = {
        "lab": "MEXC_EVENT_FUTURES_V0.1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "data_role": "MEXC standard-futures INDEX-PRICE PROXY; not exact Event Futures ledger",
        "holdout_sep_2026": "LOCKED_NOT_FETCHED",
        "break_even_accuracy_at_80pct_payout": BREAKEVEN_80,
        "assets": {},
        "discovery_passers": [],
        "oos_survivors": [],
        "exact_product_verdict": "BLOCKED",
    }
    csv_rows = []

    for asset, proxy in SYMBOLS.items():
        asset_report = {"proxy_symbol": proxy}
        try:
            prices, reqs = fetch_min1_index(proxy)
            asset_report["fetch"] = {
                "status": "PASS" if prices else "BLOCKED",
                "rows": len(prices),
                "requests": reqs,
                "first_timestamp": min(prices) if prices else None,
                "last_timestamp": max(prices) if prices else None,
            }
        except Exception as e:
            asset_report["fetch"] = {"status": "BLOCKED", "error": repr(e)}
            report["assets"][asset] = asset_report
            continue

        candidates = []
        for horizon in HORIZONS:
            for lookback in LOOKBACKS:
                for mode in MODES:
                    r = score_cell(prices, DISC_START, DISC_END, horizon, lookback, mode)
                    passed = discovery_pass(r, horizon)
                    gate = "DISCOVERY_PASS" if passed else "DISCOVERY_FAIL"
                    row = compact_row(asset, proxy, horizon, lookback, mode, "DISCOVERY", r, gate)
                    csv_rows.append(row)
                    if passed:
                        key = {
                            "asset": asset, "proxy_symbol": proxy,
                            "horizon_min": horizon, "lookback_min": lookback, "mode": mode,
                        }
                        candidates.append(key)
                        report["discovery_passers"].append({**key, "discovery": r})

        asset_report["discovery_passers"] = len(candidates)
        asset_report["oos_tested"] = 0
        asset_report["oos_survivors"] = 0

        for c in candidates:
            r = score_cell(prices, OOS_START, OOS_END, c["horizon_min"], c["lookback_min"], c["mode"])
            passed = oos_pass(r)
            gate = "OOS_PASS" if passed else "OOS_FAIL"
            csv_rows.append(compact_row(
                asset, proxy, c["horizon_min"], c["lookback_min"], c["mode"], "OOS", r, gate
            ))
            asset_report["oos_tested"] += 1
            if passed:
                asset_report["oos_survivors"] += 1
                report["oos_survivors"].append({**c, "oos": r})

        report["assets"][asset] = asset_report

    report["proxy_verdict"] = (
        "PROXY_CANDIDATES_SURVIVE_OOS" if report["oos_survivors"]
        else "NO_PROXY_SURVIVOR_AT_FROZEN_GATE"
    )
    report["promotion"] = "PROHIBITED_EXACT_EVENT_FUTURES_SOURCE_NOT_PROVEN"
    report["exact_blockers"] = [
        "Historical payout-at-entry series not proven/recovered.",
        "Standard futures index K-line equivalence to Event Futures entry/settlement index not proven.",
        "Minute-close proxy does not prove exact entry-second/rounding semantics.",
        "Event Futures official API trading is unsupported; execution automation is out of scope.",
    ]

    with open(f"{outdir}/proxy_backtest_v01.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, sort_keys=True)

    fields = [
        "asset","proxy_symbol","stage","horizon_min","lookback_min","mode",
        "wins","losses","ties","missing","non_ties","accuracy","wilson95_lower",
        "third1_accuracy","third2_accuracy","third3_accuracy",
        "ev70","ev75","ev80","ev85","ev90","gate",
    ]
    with open(f"{outdir}/proxy_matrix_v01.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in csv_rows:
            w.writerow(row)

    print(json.dumps(report, indent=2, sort_keys=True))
    print(f"WROTE {outdir}/proxy_backtest_v01.json")
    print(f"WROTE {outdir}/proxy_matrix_v01.csv")

if __name__ == "__main__":
    main()
