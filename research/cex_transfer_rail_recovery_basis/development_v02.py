#!/usr/bin/env python3
"""
CEX-TRANSFER-RAIL-RECOVERY-BASIS-001
V0.2 ONE-SHOT DEVELOPMENT

Scientific rules are frozen in:
CTRRB_V02_PRE_OUTCOME_ANALYSIS_FREEZE_2026-10-06.md

This runner opens 2022-2025 historical market outcomes.
2026 is forbidden.
No authenticated/private endpoints. No trading/account actions.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import math
import os
import random
import statistics
import time
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple

import numpy as np
import requests

REPO = "joseluisvieira28-oss/Laboratorio"
SOURCE_RUN_ID = 37487514764
SOURCE_ARTIFACT_ID = 11424097342
SOURCE_ARTIFACT_DIGEST = "sha256:464c3d35924ac525e15ec08dc2a620ad111cbf6c49254294f98afd1307dab54d"
SOURCE_HEAD_SHA = "e28223e0beb9f3613e735eeb350e20164dc11b55"

CB_API = "https://api.exchange.coinbase.com"
BN_VISION = "https://data.binance.vision/data/spot/monthly/klines"

LIQ_WINDOW_START_MIN = -120
LIQ_WINDOW_END_MIN = -60
LIQ_COMPLETENESS = 0.90
LIQ_MIN_NOTIONAL = 25_000.0
POINT_TOLERANCE_MIN = 2
CLUSTER_GAP_MIN = 60
PRIMARY_EFFECT_MIN_BPS = 5.0
FRICTION_BPS = 60.0
BOOTSTRAP_N = 10_000
BOOTSTRAP_SEED = 26061006

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "CryptoLab-CTRRB-Development/0.2 research-only"})

# Binance month cache: (symbol, YYYY-MM) -> dict[minute_epoch_s] = (close, quote_volume)
BN_CACHE: Dict[Tuple[str, str], Dict[int, Tuple[float, float]]] = {}


def dt(s: str) -> datetime:
    x = datetime.fromisoformat(s)
    return x.astimezone(timezone.utc)


def floor_minute(x: datetime) -> datetime:
    return x.astimezone(timezone.utc).replace(second=0, microsecond=0)


def epoch_minute(x: datetime) -> int:
    return int(floor_minute(x).timestamp())


def iso(x: datetime) -> str:
    return x.astimezone(timezone.utc).isoformat()


def http_get(url, *, params=None, timeout=30, binary=False):
    last = None
    for i in range(6):
        try:
            r = SESSION.get(url, params=params, timeout=timeout)
            last = r
            if r.status_code == 200:
                return r.content if binary else r
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(min(8, 0.7 * (2 ** i)))
                continue
            return r.content if binary else r
        except Exception:
            time.sleep(min(8, 0.7 * (2 ** i)))
    if last is not None:
        return last.content if binary else last
    raise RuntimeError(f"HTTP failed: {url}")


def fetch_coinbase(symbol: str, start: datetime, end: datetime) -> Dict[int, Tuple[float, float]]:
    """Return minute -> (close, quote_notional). Public endpoint, <=300 bars per call."""
    product = f"{symbol}-USD"
    params = {
        "granularity": 60,
        "start": start.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "end": end.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    r = http_get(f"{CB_API}/products/{product}/candles", params=params, timeout=30)
    if not hasattr(r, "status_code") or r.status_code != 200:
        return {}
    try:
        rows = r.json()
    except Exception:
        return {}
    out = {}
    if not isinstance(rows, list):
        return out
    for row in rows:
        try:
            # Coinbase: [time, low, high, open, close, volume]
            ts = int(row[0])
            close = float(row[4])
            base_vol = float(row[5])
            if close > 0 and base_vol >= 0 and math.isfinite(close) and math.isfinite(base_vol):
                out[(ts // 60) * 60] = (close, close * base_vol)
        except Exception:
            continue
    return out


def month_keys_between(start: datetime, end: datetime) -> List[str]:
    y, m = start.year, start.month
    out = []
    while (y, m) <= (end.year, end.month):
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m == 13:
            y += 1
            m = 1
    return out


def normalize_binance_ts(v: int) -> int:
    # Binance archives may use ms or us depending on vintage.
    if v > 10**15:
        sec = v / 1_000_000.0
    elif v > 10**12:
        sec = v / 1_000.0
    else:
        sec = float(v)
    return (int(sec) // 60) * 60


def load_binance_month(symbol: str, ym: str) -> Dict[int, Tuple[float, float]]:
    key = (symbol, ym)
    if key in BN_CACHE:
        return BN_CACHE[key]
    pair = f"{symbol}USDT"
    url = f"{BN_VISION}/{pair}/1m/{pair}-1m-{ym}.zip"
    try:
        b = http_get(url, timeout=60, binary=True)
        if not isinstance(b, (bytes, bytearray)) or len(b) < 100:
            BN_CACHE[key] = {}
            return {}
        z = zipfile.ZipFile(io.BytesIO(b))
        name = z.namelist()[0]
        out = {}
        with z.open(name) as fh:
            text = io.TextIOWrapper(fh, encoding="utf-8")
            for row in csv.reader(text):
                if len(row) < 8:
                    continue
                try:
                    ts = normalize_binance_ts(int(row[0]))
                    close = float(row[4])
                    quote_vol = float(row[7])
                    if close > 0 and quote_vol >= 0 and math.isfinite(close) and math.isfinite(quote_vol):
                        out[ts] = (close, quote_vol)
                except Exception:
                    continue
        BN_CACHE[key] = out
        return out
    except Exception:
        BN_CACHE[key] = {}
        return {}


def fetch_binance(symbol: str, start: datetime, end: datetime) -> Dict[int, Tuple[float, float]]:
    out = {}
    for ym in month_keys_between(start, end):
        m = load_binance_month(symbol, ym)
        lo, hi = int(start.timestamp()), int(end.timestamp())
        for ts, val in m.items():
            if lo <= ts <= hi:
                out[ts] = val
    return out


def synchronized_anchor(cb, bn, target: datetime):
    tgt = epoch_minute(target)
    common = sorted(set(cb) & set(bn))
    cand = [t for t in common if tgt - 120 <= t <= tgt]
    if not cand:
        return None
    return max(cand)


def synchronized_nearest(cb, bn, target: datetime):
    tgt = epoch_minute(target)
    common = set(cb) & set(bn)
    cand = [t for t in common if abs(t - tgt) <= POINT_TOLERANCE_MIN * 60]
    if not cand:
        return None
    return min(cand, key=lambda t: (abs(t - tgt), t))


def median_notional(series, start: datetime, end: datetime):
    lo, hi = epoch_minute(start), epoch_minute(end)
    expected = int((hi - lo) / 60) + 1
    vals = [notional for ts, (_, notional) in series.items() if lo <= ts <= hi and math.isfinite(notional)]
    completeness = len(vals) / expected if expected > 0 else 0.0
    med = statistics.median(vals) if vals else None
    return {"bars": len(vals), "expected": expected, "completeness": completeness, "median_notional": med}


def basis_bps(cb, bn, anchor_ts: int, t: int):
    pcb0 = cb[anchor_ts][0]
    pbn0 = bn[anchor_ts][0]
    pcb = cb[t][0]
    pbn = bn[t][0]
    return 10_000.0 * (math.log(pcb / pcb0) - math.log(pbn / pbn0))


def exact_one_sided_sign_p(values: List[float]) -> Tuple[int, int, float]:
    n = len(values)
    s = sum(v > 0 for v in values)
    # zeros count as non-positive/failures, exactly as frozen.
    p = sum(math.comb(n, k) for k in range(s, n + 1)) / (2 ** n) if n else 1.0
    return s, n, p


def bootstrap_median_ci(values: List[float]):
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    a = np.asarray(values, dtype=float)
    meds = np.empty(BOOTSTRAP_N, dtype=float)
    n = len(a)
    for i in range(BOOTSTRAP_N):
        meds[i] = np.median(rng.choice(a, size=n, replace=True))
    lo, hi = np.percentile(meds, [2.5, 97.5])
    return float(lo), float(hi)


def create_recovery_clusters(events):
    ev = sorted(events, key=lambda x: x["recovery_epoch"])
    clusters = []
    cur = []
    prev = None
    for x in ev:
        t = x["recovery_epoch"]
        if prev is None or t - prev <= CLUSTER_GAP_MIN * 60:
            cur.append(x)
        else:
            clusters.append(cur)
            cur = [x]
        prev = t
    if cur:
        clusters.append(cur)
    out = []
    for i, group in enumerate(clusters, 1):
        out.append({
            "cluster_id": i,
            "n_events": len(group),
            "start_recovery_utc": min(x["T_recovery"] for x in group),
            "end_recovery_utc": max(x["T_recovery"] for x in group),
            "symbols": sorted(set(x["symbol"] for x in group)),
            "codes": [x["code"] for x in group],
            "A_bps": float(statistics.median(x["A_bps"] for x in group)),
            "C_post_bps": float(statistics.median(x["C_post_bps"] for x in group)),
            "C_pre_bps": float(statistics.median(x["C_pre_bps"] for x in group)),
        })
    return out


def spearman_simple(xs, ys):
    if len(xs) < 3:
        return None
    def ranks(a):
        order = sorted(range(len(a)), key=lambda i: a[i])
        r = [0.0] * len(a)
        i = 0
        while i < len(a):
            j = i
            while j + 1 < len(a) and a[order[j + 1]] == a[order[i]]:
                j += 1
            rank = (i + j) / 2 + 1
            for k in range(i, j + 1):
                r[order[k]] = rank
            i = j + 1
        return r
    rx, ry = ranks(xs), ranks(ys)
    mx, my = statistics.mean(rx), statistics.mean(ry)
    num = sum((a-mx)*(b-my) for a,b in zip(rx,ry))
    den = math.sqrt(sum((a-mx)**2 for a in rx) * sum((b-my)**2 for b in ry))
    return num/den if den else None


def process_event(e):
    symbol = e["symbol"]
    tis = dt(e["start_utc"])
    trec = dt(e["end_utc"])
    if trec.year == 2026 or tis.year == 2026:
        return None, {"code": e["code"], "reason": "2026_FORBIDDEN"}

    # Coinbase: two separate <=300-candle windows.
    cb_anchor = fetch_coinbase(symbol, tis - timedelta(minutes=4), tis + timedelta(minutes=1))
    cb_rec = fetch_coinbase(symbol, trec - timedelta(minutes=130), trec + timedelta(minutes=70))
    cb = {**cb_anchor, **cb_rec}

    bn_anchor = fetch_binance(symbol, tis - timedelta(minutes=4), tis + timedelta(minutes=1))
    bn_rec = fetch_binance(symbol, trec - timedelta(minutes=130), trec + timedelta(minutes=70))
    bn = {**bn_anchor, **bn_rec}

    anchor = synchronized_anchor(cb, bn, tis - timedelta(minutes=1))
    if anchor is None:
        return None, {"code": e["code"], "symbol": symbol, "reason": "MISSING_ANCHOR"}

    targets = {
        "pre30": trec - timedelta(minutes=31),
        "pre1": trec - timedelta(minutes=1),
        "post5": trec + timedelta(minutes=5),
        "post15": trec + timedelta(minutes=15),
        "post30": trec + timedelta(minutes=30),
        "post60": trec + timedelta(minutes=60),
    }
    ts = {k: synchronized_nearest(cb, bn, v) for k,v in targets.items()}
    required = ["pre30", "pre1", "post30"]
    if any(ts[k] is None for k in required):
        return None, {"code": e["code"], "symbol": symbol, "reason": "MISSING_REQUIRED_POINT", "missing": [k for k in required if ts[k] is None]}

    liq_a = trec + timedelta(minutes=LIQ_WINDOW_START_MIN)
    liq_b = trec + timedelta(minutes=LIQ_WINDOW_END_MIN)
    cb_liq = median_notional(cb, liq_a, liq_b)
    bn_liq = median_notional(bn, liq_a, liq_b)
    if cb_liq["completeness"] < LIQ_COMPLETENESS or bn_liq["completeness"] < LIQ_COMPLETENESS:
        return None, {"code": e["code"], "symbol": symbol, "reason": "LIQUIDITY_COMPLETENESS_FAIL", "cb_liq": cb_liq, "bn_liq": bn_liq}
    if cb_liq["median_notional"] is None or bn_liq["median_notional"] is None or cb_liq["median_notional"] < LIQ_MIN_NOTIONAL or bn_liq["median_notional"] < LIQ_MIN_NOTIONAL:
        return None, {"code": e["code"], "symbol": symbol, "reason": "LIQUIDITY_NOTIONAL_FAIL", "cb_liq": cb_liq, "bn_liq": bn_liq}

    bvals = {k: basis_bps(cb, bn, anchor, t) for k,t in ts.items() if t is not None}
    C_pre = abs(bvals["pre30"]) - abs(bvals["pre1"])
    C_post = abs(bvals["pre1"]) - abs(bvals["post30"])
    A = C_post - C_pre

    duration_h = (trec - tis).total_seconds() / 3600.0
    row = {
        "code": e["code"],
        "name": e["name"],
        "symbol": symbol,
        "T_isolation": iso(tis),
        "T_recovery": iso(trec),
        "recovery_epoch": int(trec.timestamp()),
        "year": trec.year,
        "duration_hours": duration_h,
        "anchor_utc": datetime.fromtimestamp(anchor, tz=timezone.utc).isoformat(),
        "point_timestamps_utc": {k: (datetime.fromtimestamp(v,tz=timezone.utc).isoformat() if v is not None else None) for k,v in ts.items()},
        "basis_bps": bvals,
        "C_pre_bps": C_pre,
        "C_post_bps": C_post,
        "A_bps": A,
        "net_C_post_60_bps": C_post - FRICTION_BPS,
        "coinbase_pre_liquidity": cb_liq,
        "binance_pre_liquidity": bn_liq,
    }
    for h in ("post5","post15","post60"):
        row[f"C_{h}_bps"] = abs(bvals["pre1"]) - abs(bvals[h]) if h in bvals else None
    return row, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-report", required=True)
    ap.add_argument("--out", default="ctrrb_v02_development_report.json")
    ap.add_argument("--events-csv", default="ctrrb_v02_event_metrics.csv")
    args = ap.parse_args()

    source = json.load(open(args.source_report, encoding="utf-8"))
    assert source["verdict"] == "SOURCE_GATE_PASS"
    events = source["eligible_events"]
    assert len(events) == 136
    assert all(int(e["year"]) <= 2025 for e in events)

    analyzable = []
    excluded = []
    for idx, e in enumerate(events, 1):
        row, ex = process_event(e)
        if row is not None:
            analyzable.append(row)
        else:
            excluded.append(ex)
        print(f"EVENT_PROGRESS={idx}/{len(events)} code={e['code']} analyzable={row is not None}")
        time.sleep(0.08)

    counts = Counter(x["symbol"] for x in analyzable)
    years = Counter(x["year"] for x in analyzable)
    nraw = len(analyzable)
    max_asset = max(counts.values())/nraw if nraw else 1.0
    max_year = max(years.values())/nraw if nraw else 1.0

    clusters = create_recovery_clusters(analyzable)
    Acl = [x["A_bps"] for x in clusters]
    Cpostcl = [x["C_post_bps"] for x in clusters]

    successes, ncl, sign_p = exact_one_sided_sign_p(Acl)
    medA = statistics.median(Acl) if Acl else None
    medCpost = statistics.median(Cpostcl) if Cpostcl else None
    if Acl:
        ci_lo, ci_hi = bootstrap_median_ci(Acl)
    else:
        ci_lo, ci_hi = None, None

    sample_gates = {
        "clusters_ge_12": ncl >= 12,
        "unique_assets_ge_4": len(counts) >= 4,
        "asset_concentration_le_40pct": max_asset <= 0.40,
        "year_concentration_le_70pct": max_year <= 0.70,
    }
    primary_gates = {
        "median_A_gt_0": medA is not None and medA > 0,
        "median_A_ge_5bps": medA is not None and medA >= PRIMARY_EFFECT_MIN_BPS,
        "sign_test_p_lt_0_05": sign_p < 0.05,
        "bootstrap_ci_lower_gt_0": ci_lo is not None and ci_lo > 0,
        "median_C_post_gt_0": medCpost is not None and medCpost > 0,
    }
    survives = all(sample_gates.values()) and all(primary_gates.values())
    verdict = "SURVIVES_RAIL_RECOVERY_DISCOVERY" if survives else "NO_EDGE_DISCOVERY"

    # Non-rescuing diagnostics.
    loo_cluster_medians = []
    for i in range(len(Acl)):
        vals = Acl[:i] + Acl[i+1:]
        loo_cluster_medians.append(statistics.median(vals) if vals else None)

    asset_loo = {}
    for sym, cnt in sorted(counts.items()):
        if cnt >= 5:
            vals = [x["A_bps"] for x in analyzable if x["symbol"] != sym]
            asset_loo[sym] = statistics.median(vals) if vals else None

    per_year = {}
    for y in sorted(years):
        vals = [x["A_bps"] for x in analyzable if x["year"] == y]
        per_year[str(y)] = {"n": len(vals), "median_A_bps": statistics.median(vals) if vals else None}

    secondary = {}
    for key in ("C_post5_bps","C_post15_bps","C_post60_bps"):
        vals = [x[key] for x in analyzable if x.get(key) is not None]
        secondary[key] = {"n": len(vals), "median_bps": statistics.median(vals) if vals else None}

    netvals = [x["net_C_post_60_bps"] for x in analyzable]
    pre_basis_abs = [abs(x["basis_bps"]["pre1"]) for x in analyzable]
    duration = [x["duration_hours"] for x in analyzable]
    avec = [x["A_bps"] for x in analyzable]

    exclusion_counts = Counter(x.get("reason","UNKNOWN") for x in excluded)

    report = {
        "family": "CEX-TRANSFER-RAIL-RECOVERY-BASIS-001",
        "development_version": "V0.2",
        "source_pin": {
            "run_id": SOURCE_RUN_ID,
            "artifact_id": SOURCE_ARTIFACT_ID,
            "artifact_digest": SOURCE_ARTIFACT_DIGEST,
            "head_sha": SOURCE_HEAD_SHA,
            "source_events": len(events),
        },
        "governance": {
            "development_run_count_authorized": 1,
            "calendar": "2022-2025",
            "2026_opened": False,
            "trading_actions": False,
            "authenticated_exchange_endpoints": False,
        },
        "frozen_parameters": {
            "liquidity_min_median_quote_notional_per_minute": LIQ_MIN_NOTIONAL,
            "liquidity_completeness": LIQ_COMPLETENESS,
            "point_tolerance_minutes": POINT_TOLERANCE_MIN,
            "cluster_gap_minutes": CLUSTER_GAP_MIN,
            "primary_horizon_minutes": 30,
            "primary_min_effect_bps": PRIMARY_EFFECT_MIN_BPS,
            "friction_diagnostic_bps": FRICTION_BPS,
            "bootstrap_resamples": BOOTSTRAP_N,
            "bootstrap_seed": BOOTSTRAP_SEED,
        },
        "sample": {
            "source_events": len(events),
            "analyzable_raw_events": nraw,
            "excluded_events": len(excluded),
            "exclusion_counts": dict(exclusion_counts),
            "unique_assets": len(counts),
            "asset_counts": dict(sorted(counts.items())),
            "year_counts": {str(k):v for k,v in sorted(years.items())},
            "max_asset_concentration": max_asset,
            "max_year_concentration": max_year,
            "recovery_clusters": ncl,
        },
        "sample_gates": sample_gates,
        "primary": {
            "cluster_successes_A_gt_0": successes,
            "cluster_n": ncl,
            "sign_test_one_sided_p": sign_p,
            "median_cluster_A_bps": medA,
            "bootstrap_95pct_median_A_bps": [ci_lo, ci_hi],
            "median_cluster_C_post_bps": medCpost,
            "primary_gates": primary_gates,
        },
        "non_rescuing_diagnostics": {
            "secondary_horizons": secondary,
            "leave_one_cluster_out_median_A_bps": loo_cluster_medians,
            "leave_one_asset_out_median_A_bps": asset_loo,
            "per_year": per_year,
            "median_abs_basis_at_recovery_pre1_bps": statistics.median(pre_basis_abs) if pre_basis_abs else None,
            "incident_duration_vs_A_spearman": spearman_simple(duration, avec),
            "friction_60bps": {
                "median_net_C_post_bps": statistics.median(netvals) if netvals else None,
                "fraction_net_positive": sum(v > 0 for v in netvals)/len(netvals) if netvals else None,
            },
        },
        "verdict": verdict,
        "clusters": clusters,
        "event_metrics": analyzable,
        "excluded": excluded,
    }

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, sort_keys=True)

    # CSV is an audit convenience only.
    fields = ["code","name","symbol","T_isolation","T_recovery","year","duration_hours",
              "C_pre_bps","C_post_bps","A_bps","C_post5_bps","C_post15_bps","C_post60_bps",
              "net_C_post_60_bps"]
    with open(args.events_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for x in analyzable:
            w.writerow({k:x.get(k) for k in fields})

    print("CTRRB_V02_VERDICT="+verdict)
    print("SOURCE_EVENTS="+str(len(events)))
    print("ANALYZABLE_RAW_EVENTS="+str(nraw))
    print("EXCLUDED_EVENTS="+str(len(excluded)))
    print("EXCLUSION_COUNTS="+json.dumps(dict(exclusion_counts),sort_keys=True))
    print("UNIQUE_ASSETS="+str(len(counts)))
    print("ASSET_COUNTS="+json.dumps(dict(sorted(counts.items())),sort_keys=True))
    print("YEAR_COUNTS="+json.dumps({str(k):v for k,v in sorted(years.items())},sort_keys=True))
    print("MAX_ASSET_CONCENTRATION="+str(max_asset))
    print("MAX_YEAR_CONCENTRATION="+str(max_year))
    print("RECOVERY_CLUSTERS="+str(ncl))
    print("CLUSTER_SUCCESSES_A_GT_0="+str(successes))
    print("SIGN_TEST_P="+str(sign_p))
    print("MEDIAN_CLUSTER_A_BPS="+str(medA))
    print("BOOTSTRAP_MEDIAN_A_95CI="+json.dumps([ci_lo,ci_hi]))
    print("MEDIAN_CLUSTER_C_POST_BPS="+str(medCpost))
    print("SAMPLE_GATES="+json.dumps(sample_gates,sort_keys=True))
    print("PRIMARY_GATES="+json.dumps(primary_gates,sort_keys=True))
    print("FRICTION_MEDIAN_NET_C_POST_BPS="+str(report["non_rescuing_diagnostics"]["friction_60bps"]["median_net_C_post_bps"]))
    print("FRICTION_FRACTION_NET_POSITIVE="+str(report["non_rescuing_diagnostics"]["friction_60bps"]["fraction_net_positive"]))
    print("2026_OPENED=False")
    print("TRADING_ACTIONS=False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
