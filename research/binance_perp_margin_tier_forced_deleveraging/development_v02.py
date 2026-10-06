#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
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
from pathlib import Path

import requests

FAMILY = "BINANCE-PERP-MARGIN-TIER-FORCED-DELEVERAGING-001"
SOURCE_REPORT = Path("source_receipt/bpmtfd_v01_source_gate_report.json")
OUT = Path("bpmtfd_v02_development_report.json")
CACHE = Path(".bpmtfd_market_cache")
CACHE.mkdir(exist_ok=True)

PINNED_SOURCE_RUN = 37498232442
PINNED_SOURCE_HEAD = "62b5844d1855bc673f304538e8ff14d7654a59d1"
PINNED_ARTIFACT_ID = 11428188696
PINNED_ARTIFACT_DIGEST = "sha256:01798375ed49565b04275b73f01e2d68e7804c7232f8d6a445b0eba9889eb9ab"
PINNED_EVENTS = 98
PINNED_UNIQUE_CONTRACTS = 89

CONTROLS = ("BTCUSDT", "ETHUSDT", "BNBUSDT")
BASELINE_START_MIN = -120
BASELINE_END_MIN = -60
EVENT_START_MIN = -30
EVENT_END_MIN = 30
MIN_BARS = 54
MIN_RETURNS = 53
VOL_FLOOR = math.log(1.10)
ACT_FLOOR = math.log(1.10)
BOOTSTRAPS = 10_000
SEED = 26061006

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 CryptoLab-BPMTFD-V02/1.0",
    "Accept": "*/*",
})


class DataError(Exception):
    pass


def parse_dt(s: str) -> datetime:
    d = datetime.fromisoformat(s.replace("Z", "+00:00"))
    return d.astimezone(timezone.utc)


def floor_ms(v: int) -> int:
    # Binance public archives may use milliseconds or microseconds depending on dataset vintage.
    if v > 100_000_000_000_000:
        return v // 1000
    return v


def month_key(d: datetime) -> str:
    return d.strftime("%Y-%m")


def months_intersecting(start: datetime, end: datetime) -> list[str]:
    # end is exclusive
    d = datetime(start.year, start.month, 1, tzinfo=timezone.utc)
    z = end - timedelta(microseconds=1)
    last = datetime(z.year, z.month, 1, tzinfo=timezone.utc)
    out = []
    while d <= last:
        out.append(month_key(d))
        if d.month == 12:
            d = datetime(d.year + 1, 1, 1, tzinfo=timezone.utc)
        else:
            d = datetime(d.year, d.month + 1, 1, tzinfo=timezone.utc)
    return out


def archive_url(symbol: str, ym: str) -> str:
    return (
        "https://data.binance.vision/data/futures/um/monthly/klines/"
        f"{symbol}/1m/{symbol}-1m-{ym}.zip"
    )


def download_archive(symbol: str, ym: str) -> Path:
    path = CACHE / f"{symbol}-1m-{ym}.zip"
    if path.exists() and path.stat().st_size > 0:
        return path
    url = archive_url(symbol, ym)
    last = None
    for attempt in range(5):
        try:
            r = SESSION.get(url, timeout=60)
            if r.status_code == 200 and r.content[:2] == b"PK":
                tmp = path.with_suffix(".tmp")
                tmp.write_bytes(r.content)
                os.replace(tmp, path)
                return path
            last = DataError(f"archive_http_{r.status_code}")
            if r.status_code == 404:
                break
        except Exception as e:
            last = e
        time.sleep(min(20, 2 ** attempt))
    raise DataError(f"archive_unavailable:{symbol}:{ym}:{type(last).__name__}:{last}")


def parse_archive_window(path: Path, start_ms: int, end_ms: int) -> dict[int, dict]:
    rows: dict[int, dict] = {}
    try:
        with zipfile.ZipFile(path) as zf:
            names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
            if len(names) != 1:
                raise DataError(f"unexpected_zip_members:{len(names)}")
            with zf.open(names[0]) as raw:
                txt = io.TextIOWrapper(raw, encoding="utf-8", newline="")
                reader = csv.reader(txt)
                for row in reader:
                    if not row:
                        continue
                    try:
                        ot = floor_ms(int(row[0]))
                    except Exception:
                        # Header row.
                        continue
                    if ot < start_ms or ot >= end_ms:
                        continue
                    if len(row) < 9:
                        raise DataError("short_kline_row")
                    if ot in rows:
                        raise DataError(f"duplicate_open_time:{ot}")
                    try:
                        rows[ot] = {
                            "open": float(row[1]),
                            "high": float(row[2]),
                            "low": float(row[3]),
                            "close": float(row[4]),
                            "quote_volume": float(row[7]),
                            "trades": float(row[8]),
                        }
                    except Exception as e:
                        raise DataError(f"bad_numeric_row:{type(e).__name__}")
    except zipfile.BadZipFile as e:
        raise DataError(f"bad_zip:{path.name}") from e
    return rows


def load_window(symbol: str, start: datetime, end: datetime) -> dict[int, dict]:
    start_ms = int(start.timestamp() * 1000)
    end_ms = int(end.timestamp() * 1000)
    out: dict[int, dict] = {}
    for ym in months_intersecting(start, end):
        p = download_archive(symbol, ym)
        part = parse_archive_window(p, start_ms, end_ms)
        overlap = set(out).intersection(part)
        if overlap:
            raise DataError(f"duplicate_across_archives:{symbol}:{ym}")
        out.update(part)
    return out


def validate_rows(rows: dict[int, dict], expected_start: datetime, expected_end: datetime) -> None:
    expected = int((expected_end - expected_start).total_seconds() // 60)
    if expected != 60:
        raise DataError(f"window_not_60:{expected}")
    if len(rows) < MIN_BARS:
        raise DataError(f"bars_lt_{MIN_BARS}:{len(rows)}")
    for ot, x in rows.items():
        vals = (x["open"], x["high"], x["low"], x["close"])
        if not all(math.isfinite(v) and v > 0 for v in vals):
            raise DataError(f"invalid_ohlc:{ot}")
        if not (math.isfinite(x["quote_volume"]) and x["quote_volume"] >= 0):
            raise DataError(f"invalid_quote_volume:{ot}")
        if not (math.isfinite(x["trades"]) and x["trades"] >= 0):
            raise DataError(f"invalid_trades:{ot}")


def window_metrics(rows: dict[int, dict]) -> dict:
    ts = sorted(rows)
    rets = []
    for a, b in zip(ts, ts[1:]):
        if b - a != 60_000:
            continue
        ca = rows[a]["close"]
        cb = rows[b]["close"]
        rets.append(math.log(cb / ca))
    if len(rets) < MIN_RETURNS:
        raise DataError(f"returns_lt_{MIN_RETURNS}:{len(rets)}")
    rv = sum(r * r for r in rets)
    if not math.isfinite(rv) or rv <= 0:
        raise DataError("rv_nonpositive")
    qv = statistics.fmean(x["quote_volume"] for x in rows.values())
    if not math.isfinite(qv) or qv <= 0:
        raise DataError("qv_nonpositive")
    tr = statistics.fmean(x["trades"] for x in rows.values())
    return {"rv": rv, "qv": qv, "trades": tr, "bars": len(rows), "returns": len(rets)}


def symbol_effect(symbol: str, t: datetime) -> dict:
    b0 = t + timedelta(minutes=BASELINE_START_MIN)
    b1 = t + timedelta(minutes=BASELINE_END_MIN)
    e0 = t + timedelta(minutes=EVENT_START_MIN)
    e1 = t + timedelta(minutes=EVENT_END_MIN)
    br = load_window(symbol, b0, b1)
    er = load_window(symbol, e0, e1)
    validate_rows(br, b0, b1)
    validate_rows(er, e0, e1)
    bm = window_metrics(br)
    em = window_metrics(er)
    vraw = math.log(em["rv"] / bm["rv"])
    araw = math.log(em["qv"] / bm["qv"])
    traw = math.log((em["trades"] + 1e-12) / (bm["trades"] + 1e-12))
    return {
        "v_raw": vraw,
        "a_raw": araw,
        "trades_raw": traw,
        "baseline": bm,
        "event": em,
    }


def median(xs):
    return statistics.median(xs)


def exact_sign_p(values: list[float]) -> dict:
    n = len(values)
    k = sum(1 for x in values if x > 0)
    p = sum(math.comb(n, i) for i in range(k, n + 1)) / (2 ** n)
    return {"n": n, "successes": k, "failures_including_zero": n - k, "p_one_sided": p}


def percentile(sorted_values: list[float], q: float) -> float:
    if not sorted_values:
        return float("nan")
    if len(sorted_values) == 1:
        return sorted_values[0]
    h = (len(sorted_values) - 1) * q
    lo = math.floor(h)
    hi = math.ceil(h)
    if lo == hi:
        return sorted_values[lo]
    w = h - lo
    return sorted_values[lo] * (1 - w) + sorted_values[hi] * w


def bootstrap_median_ci(values: list[float]) -> list[float]:
    rng = random.Random(SEED)
    n = len(values)
    sims = []
    for _ in range(BOOTSTRAPS):
        sample = [values[rng.randrange(n)] for _ in range(n)]
        sims.append(median(sample))
    sims.sort()
    return [percentile(sims, 0.025), percentile(sims, 0.975)]


def main() -> int:
    src_bytes = SOURCE_REPORT.read_bytes()
    src_hash = hashlib.sha256(src_bytes).hexdigest()
    src = json.loads(src_bytes)

    assert src["family"] == FAMILY
    assert src["verdict"] == "SOURCE_GATE_PASS"
    assert src["outcome_access"] == "NONE"
    assert src["eligible_asset_events"] == PINNED_EVENTS
    assert src["unique_contracts"] == PINNED_UNIQUE_CONTRACTS
    assert src["years"] == [2023, 2024, 2025]
    assert all(datetime.fromisoformat(e["effective_utc"].replace("Z", "+00:00")).year <= 2025 for e in src["eligible_events"])

    events = src["eligible_events"]
    clusters = defaultdict(list)
    for e in events:
        key = e["article_code"] + "@" + e["effective_utc"]
        clusters[key].append(e)

    event_results = []
    excluded = []
    cluster_results = []

    for ci, (cluster_key, evs) in enumerate(sorted(clusters.items()), start=1):
        t_values = {e["effective_utc"] for e in evs}
        if len(t_values) != 1:
            raise RuntimeError(f"cluster_timestamp_conflict:{cluster_key}")
        t = parse_dt(next(iter(t_values)))
        if t.second != 0 or t.microsecond != 0:
            for e in evs:
                excluded.append({
                    "cluster": cluster_key,
                    "symbol": e["symbol"],
                    "reason": "effective_timestamp_not_minute_aligned",
                })
            continue

        treated_symbols = {e["symbol"] for e in evs}
        control_symbols = [c for c in CONTROLS if c not in treated_symbols]
        control_effects = {}
        control_errors = {}
        for c in control_symbols:
            try:
                control_effects[c] = symbol_effect(c, t)
            except Exception as ex:
                control_errors[c] = f"{type(ex).__name__}:{ex}"

        valid_controls = sorted(control_effects)
        if len(valid_controls) < 2:
            for e in evs:
                excluded.append({
                    "cluster": cluster_key,
                    "symbol": e["symbol"],
                    "reason": "fewer_than_two_valid_controls",
                    "control_errors": control_errors,
                })
            print(f"CLUSTER_PROGRESS={ci}/{len(clusters)} key={cluster_key} analyzable=0 reason=controls")
            continue

        cv = median([control_effects[c]["v_raw"] for c in valid_controls])
        ca = median([control_effects[c]["a_raw"] for c in valid_controls])
        ct = median([control_effects[c]["trades_raw"] for c in valid_controls])

        cres = []
        for e in sorted(evs, key=lambda z: z["symbol"]):
            s = e["symbol"]
            try:
                te = symbol_effect(s, t)
                ve = te["v_raw"] - cv
                ae = te["a_raw"] - ca
                trde = te["trades_raw"] - ct
                rec = {
                    "cluster": cluster_key,
                    "article_code": e["article_code"],
                    "effective_utc": e["effective_utc"],
                    "symbol": s,
                    "controls": valid_controls,
                    "V_e": ve,
                    "A_e": ae,
                    "trades_e_descriptive": trde,
                    "treated_raw": te,
                    "control_median_raw": {
                        "v_raw": cv,
                        "a_raw": ca,
                        "trades_raw": ct,
                    },
                }
                event_results.append(rec)
                cres.append(rec)
            except Exception as ex:
                excluded.append({
                    "cluster": cluster_key,
                    "symbol": s,
                    "reason": f"{type(ex).__name__}:{ex}",
                })

        if cres:
            vk = median([x["V_e"] for x in cres])
            ak = median([x["A_e"] for x in cres])
            jk = min(vk, ak)
            cluster_results.append({
                "cluster": cluster_key,
                "article_code": evs[0]["article_code"],
                "effective_utc": evs[0]["effective_utc"],
                "year": t.year,
                "analyzable_events": len(cres),
                "symbols": sorted(x["symbol"] for x in cres),
                "V_k": vk,
                "A_k": ak,
                "J_k": jk,
            })
        print(f"CLUSTER_PROGRESS={ci}/{len(clusters)} key={cluster_key} analyzable={len(cres)}")

    n_events = len(event_results)
    n_clusters = len(cluster_results)
    unique_contracts = sorted({x["symbol"] for x in event_results})
    years = sorted({x["year"] for x in cluster_results})
    max_cluster_events = max((x["analyzable_events"] for x in cluster_results), default=0)
    max_cluster_conc = max_cluster_events / n_events if n_events else 1.0
    yc = Counter(x["year"] for x in cluster_results)
    max_year_conc = max(yc.values(), default=0) / n_clusters if n_clusters else 1.0

    sample_gates = {
        "clusters_ge_12": n_clusters >= 12,
        "asset_events_ge_20": n_events >= 20,
        "unique_contracts_ge_8": len(unique_contracts) >= 8,
        "years_ge_2": len(years) >= 2,
        "max_cluster_le_35pct": max_cluster_conc <= 0.35,
        "max_year_le_70pct": max_year_conc <= 0.70,
    }

    if cluster_results:
        vs = [x["V_k"] for x in cluster_results]
        ass = [x["A_k"] for x in cluster_results]
        js = [x["J_k"] for x in cluster_results]
        med_v = median(vs)
        med_a = median(ass)
        med_j = median(js)
        sign = exact_sign_p(js)
        boot = bootstrap_median_ci(js)
    else:
        med_v = med_a = med_j = float("nan")
        sign = {"n": 0, "successes": 0, "failures_including_zero": 0, "p_one_sided": 1.0}
        boot = [float("nan"), float("nan")]

    primary_gates = {
        "median_V_ge_ln1p10": math.isfinite(med_v) and med_v >= VOL_FLOOR,
        "median_A_ge_ln1p10": math.isfinite(med_a) and med_a >= ACT_FLOOR,
        "median_J_gt_0": math.isfinite(med_j) and med_j > 0,
        "sign_test_p_lt_0_05": sign["p_one_sided"] < 0.05,
        "bootstrap_ci_lower_gt_0": math.isfinite(boot[0]) and boot[0] > 0,
    }

    survives = all(sample_gates.values()) and all(primary_gates.values())
    verdict = "SURVIVES_MARGIN_TIER_DISCOVERY" if survives else "NO_EDGE_DISCOVERY"

    raw_rv_ratios = []
    raw_qv_ratios = []
    for x in event_results:
        tr = x["treated_raw"]
        raw_rv_ratios.append(tr["event"]["rv"] / tr["baseline"]["rv"])
        raw_qv_ratios.append(tr["event"]["qv"] / tr["baseline"]["qv"])

    report = {
        "family": FAMILY,
        "stage": "V0.2_ONE_SHOT_DEVELOPMENT",
        "verdict": verdict,
        "source_pin": {
            "workflow_run": PINNED_SOURCE_RUN,
            "head_sha": PINNED_SOURCE_HEAD,
            "artifact_id": PINNED_ARTIFACT_ID,
            "artifact_digest": PINNED_ARTIFACT_DIGEST,
            "source_report_sha256": src_hash,
            "eligible_events_expected": PINNED_EVENTS,
        },
        "governance": {
            "calendar": "2023-2025",
            "year_2026_opened": False,
            "authenticated_endpoint_used": False,
            "private_endpoint_used": False,
            "trading_or_order_mutation": False,
            "main_modified": False,
            "post_outcome_tuning": False,
        },
        "windows": {
            "baseline": "[-120m,-60m)",
            "primary_event": "[-30m,+30m)",
            "min_bars_each_window": MIN_BARS,
            "min_consecutive_returns": MIN_RETURNS,
        },
        "controls": list(CONTROLS),
        "source_events": len(events),
        "source_clusters": len(clusters),
        "analyzable_asset_events": n_events,
        "excluded_asset_events": len(excluded),
        "analyzable_clusters": n_clusters,
        "unique_analyzable_contracts": len(unique_contracts),
        "analyzable_years": years,
        "max_cluster_concentration": max_cluster_conc,
        "max_year_cluster_concentration": max_year_conc,
        "sample_gates": sample_gates,
        "primary_metrics": {
            "median_V_k": med_v,
            "median_A_k": med_a,
            "median_J_k": med_j,
            "volatility_floor_ln1p10": VOL_FLOOR,
            "activity_floor_ln1p10": ACT_FLOOR,
            "sign_test": sign,
            "bootstrap_median_J_95ci": boot,
            "bootstrap_resamples": BOOTSTRAPS,
            "bootstrap_seed": SEED,
        },
        "primary_gates": primary_gates,
        "descriptive": {
            "median_treated_raw_rv_event_over_baseline": median(raw_rv_ratios) if raw_rv_ratios else None,
            "median_treated_raw_qv_event_over_baseline": median(raw_qv_ratios) if raw_qv_ratios else None,
            "exclusion_reasons": dict(Counter(x["reason"].split(":", 1)[0] for x in excluded)),
        },
        "cluster_results": cluster_results,
        "event_results": event_results,
        "excluded": excluded,
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")

    print("BPMTFD_V02_VERDICT=" + verdict)
    print("SOURCE_EVENTS=" + str(len(events)))
    print("SOURCE_CLUSTERS=" + str(len(clusters)))
    print("ANALYZABLE_RAW_EVENTS=" + str(n_events))
    print("EXCLUDED_EVENTS=" + str(len(excluded)))
    print("ANALYZABLE_CLUSTERS=" + str(n_clusters))
    print("UNIQUE_CONTRACTS=" + str(len(unique_contracts)))
    print("YEARS=" + json.dumps(years))
    print("MAX_CLUSTER_CONCENTRATION=" + str(max_cluster_conc))
    print("MAX_YEAR_CLUSTER_CONCENTRATION=" + str(max_year_conc))
    print("MEDIAN_V_K=" + str(med_v))
    print("MEDIAN_A_K=" + str(med_a))
    print("MEDIAN_J_K=" + str(med_j))
    print("SIGN_TEST=" + json.dumps(sign, sort_keys=True))
    print("BOOTSTRAP_MEDIAN_J_95CI=" + json.dumps(boot))
    print("SAMPLE_GATES=" + json.dumps(sample_gates, sort_keys=True))
    print("PRIMARY_GATES=" + json.dumps(primary_gates, sort_keys=True))
    print("GOVERNANCE: research-only; 2026 closed; no trading/private endpoints/main mutation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
