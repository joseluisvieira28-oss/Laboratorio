#!/usr/bin/env python3
"""
MEXC Event Futures Lab V0.4 — frozen technical chart-state hypotheses.

Research only. Public MEXC standard-futures index-price proxy.
No authentication, no orders, no September-2026 holdout.
"""
import csv
import json
import math
import os
import statistics
import time
from bisect import bisect_right
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
CHART_TFS = [5, 15, 60, 240, 1440]
HORIZONS = [10, 30, 60, 1440]
STRATEGIES = [
    "EMA_TREND_9_21",
    "RSI14_EXTREME_REV",
    "DONCHIAN20_BREAKOUT",
    "BOLL20_2_REV",
    "STREAK3_REV",
    "STREAK3_CONT",
    "ROC3_CONT",
    "RANGE20_POSITION_REV",
]
MIN_N = {10: 120, 30: 100, 60: 80, 1440: 40}
P0 = 1.0 / 1.8
PAYOUT = 0.80
Z95 = 1.959963984540054
RAW_STEP = 300
BH_Q = 0.05

DISC_START = int(datetime(2026, 4, 1, tzinfo=timezone.utc).timestamp())
DISC_END = int(datetime(2026, 8, 1, tzinfo=timezone.utc).timestamp())
OOS_START = DISC_END
OOS_END = int(datetime(2026, 9, 1, tzinfo=timezone.utc).timestamp())
FETCH_START = DISC_START - 35 * 24 * 3600
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

def fetch_min5_closes(symbol):
    url = f"{BASE}/api/v1/contract/kline/index_price/{symbol}"
    chunk = 5 * 24 * 3600
    raw_t = FETCH_START - RAW_STEP
    rows = {}
    reqs = 0
    while raw_t <= FETCH_END_RAW:
        e = min(raw_t + chunk, FETCH_END_RAW)
        j = fetch_json(url, {"interval": "Min5", "start": raw_t, "end": e})
        reqs += 1
        d = j.get("data") or {}
        ts = d.get("time") or []
        closes = d.get("close") or []
        for s, p in zip(ts, closes):
            try:
                s = int(s)
                p = float(p)
            except Exception:
                continue
            if s >= OOS_END:
                raise RuntimeError("holdout-boundary violation: raw timestamp >= Sep-2026 boundary")
            mapped = s + RAW_STEP
            if FETCH_START <= mapped < OOS_END:
                rows[mapped] = p
        raw_t = e + RAW_STEP
        time.sleep(0.10)
    return rows, reqs

def chart_series(prices, tf_min):
    sec = tf_min * 60
    ts = sorted(t for t in prices if t % sec == 0)
    vals = [prices[t] for t in ts]
    return ts, vals, {t: i for i, t in enumerate(ts)}

def ema_series(vals, period):
    if not vals:
        return []
    alpha = 2.0 / (period + 1.0)
    out = [vals[0]]
    for x in vals[1:]:
        out.append(alpha * x + (1.0 - alpha) * out[-1])
    return out

def rsi14(vals, i):
    if i < 14:
        return None
    diffs = [vals[k] - vals[k-1] for k in range(i-13, i+1)]
    gains = [max(x, 0.0) for x in diffs]
    losses = [max(-x, 0.0) for x in diffs]
    ag = sum(gains) / 14.0
    al = sum(losses) / 14.0
    if al == 0:
        return None if ag == 0 else 100.0
    rs = ag / al
    return 100.0 - 100.0 / (1.0 + rs)

def strategy_signal(name, vals, i, ema9, ema21):
    cur = vals[i]

    if name == "EMA_TREND_9_21":
        if i < 20:
            return None
        if ema9[i] > ema21[i]:
            return 1
        if ema9[i] < ema21[i]:
            return -1
        return None

    if name == "RSI14_EXTREME_REV":
        r = rsi14(vals, i)
        if r is None:
            return None
        if r < 30.0:
            return 1
        if r > 70.0:
            return -1
        return None

    if name in ("DONCHIAN20_BREAKOUT", "BOLL20_2_REV", "RANGE20_POSITION_REV"):
        if i < 20:
            return None
        prior = vals[i-20:i]
        lo, hi = min(prior), max(prior)

        if name == "DONCHIAN20_BREAKOUT":
            if cur > hi:
                return 1
            if cur < lo:
                return -1
            return None

        if name == "BOLL20_2_REV":
            mu = statistics.fmean(prior)
            sd = statistics.pstdev(prior)
            if sd == 0:
                return None
            if cur < mu - 2.0 * sd:
                return 1
            if cur > mu + 2.0 * sd:
                return -1
            return None

        if hi == lo:
            return None
        loc = (cur - lo) / (hi - lo)
        if loc >= 0.80:
            return -1
        if loc <= 0.20:
            return 1
        return None

    if name in ("STREAK3_REV", "STREAK3_CONT"):
        if i < 3:
            return None
        diffs = [vals[k] - vals[k-1] for k in range(i-2, i+1)]
        if all(x > 0 for x in diffs):
            sign = 1
        elif all(x < 0 for x in diffs):
            sign = -1
        else:
            return None
        return -sign if name == "STREAK3_REV" else sign

    if name == "ROC3_CONT":
        if i < 3:
            return None
        d = cur - vals[i-3]
        return 1 if d > 0 else (-1 if d < 0 else None)

    raise ValueError(name)

def aligned_anchors(start, end, stride_min):
    step = stride_min * 60
    t = ((start + step - 1) // step) * step
    while t < end:
        yield t
        t += step

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

def score(prices, tf_min, horizon_min, strategy, start, end):
    cts, vals, idx = chart_series(prices, tf_min)
    ema9 = ema_series(vals, 9)
    ema21 = ema_series(vals, 21)
    stride = max(tf_min, horizon_min)

    wins = losses = ties = missing = no_signal = 0
    thirds = [[0,0,0] for _ in range(3)]
    span = end - start

    for t in aligned_anchors(start, end, stride):
        after = t + horizon_min * 60
        if after >= end:
            continue
        if t not in prices or after not in prices:
            missing += 1
            continue
        i = idx.get(t)
        if i is None:
            missing += 1
            continue

        sig = strategy_signal(strategy, vals, i, ema9, ema21)
        if sig is None:
            no_signal += 1
            continue

        future = prices[after] - prices[t]
        third = min(2, max(0, int(3 * (t - start) / max(1, span))))
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
    thirds_acc = [(w/(w+l) if w+l else None) for w,l,_ in thirds]
    ev80 = ((wins*PAYOUT - losses)/(wins+losses+ties)) if (wins+losses+ties) else None
    required_payout = (losses/wins) if wins > 0 else None
    return {
        "wins":wins, "losses":losses, "ties":ties, "missing":missing, "no_signal":no_signal,
        "non_ties":n, "accuracy":acc, "wilson95_lower":wilson_lower(wins,losses),
        "p_value_vs_be80":exact_p(wins,losses), "third_accuracies":thirds_acc,
        "ev80":ev80, "required_payout_for_ev0":required_payout,
        "entry_stride_min":stride,
    }

def discovery_eligible(r, horizon):
    return (
        r["non_ties"] >= MIN_N[horizon]
        and r["accuracy"] is not None and r["accuracy"] > P0
        and r["wilson95_lower"] is not None and r["wilson95_lower"] > 0.50
        and all(x is not None and x > 0.50 for x in r["third_accuracies"])
        and r["p_value_vs_be80"] is not None
    )

def bh_select(cells, q=BH_Q):
    eligible = [c for c in cells if c["eligible"]]
    eligible.sort(key=lambda x: x["discovery"]["p_value_vs_be80"])
    m = len(eligible)
    cutoff = None
    for rank, c in enumerate(eligible, start=1):
        if c["discovery"]["p_value_vs_be80"] <= (rank/m)*q:
            cutoff = c["discovery"]["p_value_vs_be80"]
    selected = []
    if cutoff is not None:
        selected = [c for c in eligible if c["discovery"]["p_value_vs_be80"] <= cutoff]
    return selected, m, cutoff

def oos_pass(r):
    return (
        r["non_ties"] > 0
        and r["accuracy"] is not None and r["accuracy"] > P0
        and r["wilson95_lower"] is not None and r["wilson95_lower"] > 0.50
        and r["p_value_vs_be80"] is not None and r["p_value_vs_be80"] < 0.05
        and r["ev80"] is not None and r["ev80"] > 0
    )

def flat(asset, proxy, stage, tf, h, strategy, r, gate):
    return {
        "asset":asset, "proxy_symbol":proxy, "stage":stage,
        "chart_tf_min":tf, "horizon_min":h, "strategy":strategy,
        "entry_stride_min":r["entry_stride_min"],
        "wins":r["wins"], "losses":r["losses"], "ties":r["ties"],
        "missing":r["missing"], "no_signal":r["no_signal"], "non_ties":r["non_ties"],
        "accuracy":r["accuracy"], "wilson95_lower":r["wilson95_lower"],
        "p_value_vs_be80":r["p_value_vs_be80"],
        "third1_accuracy":r["third_accuracies"][0],
        "third2_accuracy":r["third_accuracies"][1],
        "third3_accuracy":r["third_accuracies"][2],
        "ev80":r["ev80"], "required_payout_for_ev0":r["required_payout_for_ev0"],
        "gate":gate,
    }

def coverage(prices, start, end):
    a=[t for t in prices if start <= t < end]
    return {"rows":len(a),"first":min(a) if a else None,"last":max(a) if a else None}

def main():
    outdir="artifacts/mexc_event_futures"
    os.makedirs(outdir, exist_ok=True)
    report={
        "lab":"MEXC_EVENT_FUTURES_TECHSIGNALS_V0.4",
        "generated_at_utc":datetime.now(timezone.utc).isoformat(),
        "source":"MEXC_STANDARD_FUTURES_INDEX_PRICE_MIN5_PROXY_CLOSE_AT_BUCKET_END",
        "historical_holdout_sep_2026":"LOCKED_NOT_FETCHED",
        "exact_event_futures":"NOT_PROVEN",
        "discovery_multiple_testing":"BENJAMINI_HOCHBERG_FDR_Q_0.05",
        "reference_payout":0.80,
        "reference_break_even_accuracy":P0,
        "assets":{},
        "discovery_cells":[],
        "bh_selected":[],
        "oos_survivors":[],
    }
    csv_rows=[]

    for asset,proxy in SYMBOLS.items():
        a={"proxy_symbol":proxy}
        try:
            prices,reqs=fetch_min5_closes(proxy)
            a["requests"]=reqs
            a["total_rows"]=len(prices)
            a["discovery_coverage"]=coverage(prices,DISC_START,DISC_END)
            a["oos_coverage"]=coverage(prices,OOS_START,OOS_END)
            a["source_status"]="SOURCE_AVAILABLE" if a["discovery_coverage"]["rows"] and a["oos_coverage"]["rows"] else "SOURCE_BLOCKED"
        except Exception as e:
            a["source_status"]="SOURCE_BLOCKED"
            a["error"]=repr(e)
            report["assets"][asset]=a
            continue

        if a["source_status"]!="SOURCE_AVAILABLE":
            report["assets"][asset]=a
            continue

        local=[]
        for tf in CHART_TFS:
            for h in HORIZONS:
                for s in STRATEGIES:
                    r=score(prices,tf,h,s,DISC_START,DISC_END)
                    eligible=discovery_eligible(r,h)
                    c={
                        "asset":asset,"proxy_symbol":proxy,"chart_tf_min":tf,
                        "horizon_min":h,"strategy":s,"eligible":eligible,"discovery":r,
                    }
                    local.append(c)
                    report["discovery_cells"].append(c)
                    csv_rows.append(flat(asset,proxy,"DISCOVERY",tf,h,s,r,
                                         "DISCOVERY_ELIGIBLE" if eligible else "DISCOVERY_FAIL"))
        report["assets"][asset]=a

    selected,m,cutoff=bh_select(report["discovery_cells"])
    report["bh_eligible_count"]=m
    report["bh_cutoff_p"]=cutoff
    report["bh_selected"]=[
        {k:v for k,v in c.items() if k!="eligible"} for c in selected
    ]

    # Re-fetch per asset only for selected cells, preserving exact same public source.
    by_asset={}
    for c in selected:
        by_asset.setdefault(c["asset"],[]).append(c)

    for asset,cells in by_asset.items():
        proxy=SYMBOLS[asset]
        prices,_=fetch_min5_closes(proxy)
        for c in cells:
            r=score(prices,c["chart_tf_min"],c["horizon_min"],c["strategy"],OOS_START,OOS_END)
            passed=oos_pass(r)
            csv_rows.append(flat(asset,proxy,"OOS",c["chart_tf_min"],c["horizon_min"],c["strategy"],r,
                                 "OOS_PASS" if passed else "OOS_FAIL"))
            if passed:
                report["oos_survivors"].append({
                    "asset":asset,"proxy_symbol":proxy,
                    "chart_tf_min":c["chart_tf_min"],"horizon_min":c["horizon_min"],
                    "strategy":c["strategy"],"discovery":c["discovery"],"oos":r,
                })

    report["source_available_assets"]=[k for k,v in report["assets"].items() if v.get("source_status")=="SOURCE_AVAILABLE"]
    report["source_blocked_assets"]=[k for k,v in report["assets"].items() if v.get("source_status")!="SOURCE_AVAILABLE"]
    report["verdict"]="PROXY_CANDIDATES_SURVIVE_OOS" if report["oos_survivors"] else "NO_PROXY_SURVIVOR_AT_FROZEN_V04_GATE"
    report["promotion_status"]="NO_EXACT_EVENT_FUTURES_PROMOTION"

    jpath=f"{outdir}/techsignals_v04.json"
    cpath=f"{outdir}/techsignals_matrix_v04.csv"
    with open(jpath,"w",encoding="utf-8") as f:
        json.dump(report,f,indent=2,sort_keys=True)

    fields=[
        "asset","proxy_symbol","stage","chart_tf_min","horizon_min","strategy","entry_stride_min",
        "wins","losses","ties","missing","no_signal","non_ties","accuracy","wilson95_lower",
        "p_value_vs_be80","third1_accuracy","third2_accuracy","third3_accuracy",
        "ev80","required_payout_for_ev0","gate",
    ]
    with open(cpath,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields)
        w.writeheader(); w.writerows(csv_rows)

    compact={
        "verdict":report["verdict"],
        "source_available_assets":report["source_available_assets"],
        "source_blocked_assets":report["source_blocked_assets"],
        "discovery_cells":len(report["discovery_cells"]),
        "bh_eligible_count":m,
        "bh_selected_count":len(selected),
        "bh_cutoff_p":cutoff,
        "oos_survivor_count":len(report["oos_survivors"]),
        "oos_survivors":[{
            "asset":x["asset"],"chart_tf_min":x["chart_tf_min"],"horizon_min":x["horizon_min"],
            "strategy":x["strategy"],
            "disc_n":x["discovery"]["non_ties"],"disc_acc":x["discovery"]["accuracy"],
            "disc_p":x["discovery"]["p_value_vs_be80"],
            "oos_n":x["oos"]["non_ties"],"oos_acc":x["oos"]["accuracy"],
            "oos_p":x["oos"]["p_value_vs_be80"],"oos_ev80":x["oos"]["ev80"],
            "required_payout_for_ev0":x["oos"]["required_payout_for_ev0"],
        } for x in report["oos_survivors"]],
        "holdout":report["historical_holdout_sep_2026"],
        "exact_event_futures":report["exact_event_futures"],
    }
    print(json.dumps(compact,indent=2,sort_keys=True))
    print("WROTE",jpath)
    print("WROTE",cpath)

if __name__=="__main__":
    main()
