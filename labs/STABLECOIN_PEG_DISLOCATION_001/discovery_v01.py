#!/usr/bin/env python3
"""One-shot Discovery runner for STABLECOIN-PEG-DISLOCATION-001.

MVE: SPD-USDCUSDT-CROSS25-H60-001
Research-only. No live trading, orders, exchange mutation, 2025/2026 access,
or post-outcome tuning.
"""
from __future__ import annotations

import concurrent.futures
import csv
import datetime as dt
import hashlib
import io
import json
import math
import os
import random
import re
import shutil
import statistics
import sys
import time
import urllib.error
import urllib.request
import zipfile
from collections import defaultdict
from pathlib import Path

LAB_ID = "STABLECOIN-PEG-DISLOCATION-001"
MVE_ID = "SPD-USDCUSDT-CROSS25-H60-001"
SOURCE_GATE_ID = "SPD-USDCUSDT-SOURCE-002"
SYMBOL = "USDCUSDT"
INTERVAL = "1m"
BASE_URL = f"https://data.binance.vision/data/spot/daily/klines/{SYMBOL}/{INTERVAL}"
SEGMENTS = [
    (dt.date(2021, 1, 1), dt.date(2022, 9, 26)),
    (dt.date(2023, 3, 11), dt.date(2024, 12, 31)),
]
ECONOMIC_EXCLUDED_DATES = {dt.date(2022, 9, 26), dt.date(2023, 3, 11)}
EXPECTED_ACTIVE_DAYS = 1296
PEG = 1.0
LOWER = 0.9975
UPPER = 1.0025
HOLD_MINUTES = 60
BASE_COST_BPS = 20.0
STRESS_COST_BPS = 30.0
MIN_N = 50
MIN_WEEKS = 20
MIN_YEARS = 3
BOOT_REPS = 10_000
BOOT_SEED = 20260916
EXPECTED_SOURCE_ARTIFACT_SHA = "8f406f233bd1a84f215b8377d10abb9c1add206dfc4449d18a28d8b1932234c2"
EXPECTED_SOURCE_MANIFEST_SHA = "020018f4cb2a3392aee6c353a818997b227b4e9917ef8495afce6a2a1100102f"
AUTHORITY_PATH = Path("labs/STABLECOIN_PEG_DISLOCATION_001/DISCOVERY_AUTHORITY_V0.1.json")
OUT = Path("stablecoin_peg_discovery_v01_artifact")
CACHE = Path(".stablecoin_peg_discovery_cache")
OUT.mkdir(parents=True, exist_ok=True)
CACHE.mkdir(parents=True, exist_ok=True)
UA = "CryptoLab-StablecoinPeg-Discovery/1.0 (+research-only)"
CHECKSUM_RE = re.compile(r"^[0-9a-fA-F]{64}$")


class SourceDataError(RuntimeError):
    pass


class SourceTransportError(RuntimeError):
    pass


def daterange(a: dt.date, b: dt.date):
    cur = a
    while cur <= b:
        yield cur
        cur += dt.timedelta(days=1)


def active_days():
    days = []
    for a, b in SEGMENTS:
        days.extend(daterange(a, b))
    return days


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def dump_json(name: str, obj) -> Path:
    p = OUT / name
    p.write_text(json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    return p


def urls_for(day: dt.date):
    ds = day.isoformat()
    fn = f"{SYMBOL}-{INTERVAL}-{ds}.zip"
    zurl = f"{BASE_URL}/{fn}"
    return fn, zurl, zurl + ".CHECKSUM"


def http_get(url: str, timeout: int = 60, attempts: int = 5) -> bytes:
    last = None
    for i in range(attempts):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                status = int(getattr(r, "status", 200))
                if status != 200:
                    raise SourceTransportError(f"HTTP_{status}:{url}")
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise SourceDataError(f"HTTP_404:{url}")
            last = e
        except Exception as e:
            last = e
        if i + 1 < attempts:
            time.sleep(min(8.0, 0.5 * (2 ** i)))
    raise SourceTransportError(f"FETCH_FAILED:{url}:{type(last).__name__}:{last}")


def validate_authority():
    if not AUTHORITY_PATH.exists():
        raise RuntimeError("DISCOVERY_AUTHORITY_MISSING")
    raw = AUTHORITY_PATH.read_bytes()
    auth = json.loads(raw.decode("utf-8"))
    checks = [
        auth.get("lab_id") == LAB_ID,
        auth.get("mve_id") == MVE_ID,
        auth.get("status") == "FROZEN_PRE_DISCOVERY",
        auth.get("source_authority", {}).get("source_gate_id") == SOURCE_GATE_ID,
        auth.get("source_authority", {}).get("classification") == "SOURCE_DATA_PASS",
        auth.get("source_authority", {}).get("artifact_sha256") == EXPECTED_SOURCE_ARTIFACT_SHA,
        auth.get("source_authority", {}).get("source_manifest_sha256") == EXPECTED_SOURCE_MANIFEST_SHA,
        float(auth.get("peg_reference")) == PEG,
        float(auth.get("threshold", {}).get("lower")) == LOWER,
        float(auth.get("threshold", {}).get("upper")) == UPPER,
        int(auth.get("execution", {}).get("hold_minutes")) == HOLD_MINUTES,
        float(auth.get("returns", {}).get("base_cost_bps_roundtrip")) == BASE_COST_BPS,
        float(auth.get("returns", {}).get("stress_cost_bps_roundtrip")) == STRESS_COST_BPS,
        int(auth.get("sample_gate", {}).get("min_executable_n")) == MIN_N,
        int(auth.get("sample_gate", {}).get("min_distinct_utc_calendar_weeks")) == MIN_WEEKS,
        int(auth.get("sample_gate", {}).get("min_distinct_calendar_years")) == MIN_YEARS,
        auth.get("protected_periods", {}).get("access_2025") is False,
        auth.get("protected_periods", {}).get("access_2026") is False,
        auth.get("firewalls", {}).get("live_trading") is False,
        auth.get("firewalls", {}).get("post_outcome_tuning") is False,
    ]
    if not all(checks):
        raise RuntimeError("DISCOVERY_AUTHORITY_INVARIANT_MISMATCH")
    return auth, sha256_bytes(raw)


def download_one(day: dt.date):
    if day.year >= 2025:
        raise RuntimeError("PROTECTED_PERIOD_FIREWALL_VIOLATION")
    fn, zurl, curl = urls_for(day)
    checksum_raw = http_get(curl, timeout=30)
    text = checksum_raw.decode("utf-8", "replace").strip()
    toks = text.split()
    if len(toks) < 2 or not CHECKSUM_RE.match(toks[0]) or toks[-1].lstrip("*") != fn:
        raise SourceDataError(f"INVALID_CHECKSUM:{day.isoformat()}")
    expected_sha = toks[0].lower()
    raw = http_get(zurl, timeout=90)
    got_sha = sha256_bytes(raw)
    if got_sha != expected_sha:
        raise SourceDataError(f"CHECKSUM_MISMATCH:{day.isoformat()}:{expected_sha}:{got_sha}")
    p = CACHE / fn
    p.write_bytes(raw)
    return {
        "date": day.isoformat(),
        "filename": fn,
        "zip_sha256": got_sha,
        "bytes": len(raw),
        "checksum_verified": True,
    }


def source_acquisition(authority_sha: str):
    days = active_days()
    if len(days) != EXPECTED_ACTIVE_DAYS or len(set(days)) != EXPECTED_ACTIVE_DAYS:
        raise RuntimeError("ACTIVE_CALENDAR_INVARIANT_FAILED")
    if any(d.year >= 2025 for d in days):
        raise RuntimeError("PROTECTED_PERIOD_FIREWALL_VIOLATION")

    rows = []
    failures = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
        futs = {ex.submit(download_one, d): d for d in days}
        for fut in concurrent.futures.as_completed(futs):
            day = futs[fut]
            try:
                rows.append(fut.result())
            except Exception as e:
                failures.append({
                    "date": day.isoformat(),
                    "error_type": type(e).__name__,
                    "error": str(e),
                })
    rows.sort(key=lambda x: x["date"])
    failures.sort(key=lambda x: x["date"])
    manifest = {
        "lab_id": LAB_ID,
        "mve_id": MVE_ID,
        "source_gate_id": SOURCE_GATE_ID,
        "authority_sha256": authority_sha,
        "expected_active_days": EXPECTED_ACTIVE_DAYS,
        "downloaded_verified_days": len(rows),
        "failures": failures,
        "files": rows,
        "access_2025": False,
        "access_2026": False,
        "prices_parsed": False,
        "economic_outcomes_opened": False,
    }
    mp = dump_json("source_manifest_discovery.json", manifest)
    manifest_sha = sha256_file(mp)

    if failures or len(rows) != EXPECTED_ACTIVE_DAYS:
        any_data = any(f["error_type"] == "SourceDataError" for f in failures)
        classification = "DATA_FAILURE" if any_data else "SOURCE_ACQUISITION_TECHNICAL_FAILURE"
        gate = {
            "classification": classification,
            "expected_active_days": EXPECTED_ACTIVE_DAYS,
            "downloaded_verified_days": len(rows),
            "failure_count": len(failures),
            "source_manifest_sha256": manifest_sha,
            "access_2025": False,
            "access_2026": False,
            "economic_outcomes_opened": False,
        }
        dump_json("source_preoutcome_gate.json", gate)
        return False, classification, manifest_sha

    gate = {
        "classification": "DISCOVERY_SOURCE_BINDING_PASS",
        "expected_active_days": EXPECTED_ACTIVE_DAYS,
        "downloaded_verified_days": EXPECTED_ACTIVE_DAYS,
        "failure_count": 0,
        "source_manifest_sha256": manifest_sha,
        "source_gate_v02_manifest_sha256_lineage": EXPECTED_SOURCE_MANIFEST_SHA,
        "access_2025": False,
        "access_2026": False,
        "economic_outcomes_opened": False,
    }
    dump_json("source_preoutcome_gate.json", gate)
    return True, "DISCOVERY_SOURCE_BINDING_PASS", manifest_sha


def read_day_rows(day: dt.date):
    fn, _, _ = urls_for(day)
    p = CACHE / fn
    if not p.exists():
        raise SourceDataError(f"LOCAL_VERIFIED_ZIP_MISSING:{day.isoformat()}")
    expected_csv = fn[:-4] + ".csv"
    out = []
    with zipfile.ZipFile(p, "r") as zf:
        if zf.testzip() is not None:
            raise SourceDataError(f"ZIP_INTEGRITY_FAIL:{day.isoformat()}")
        if expected_csv not in zf.namelist():
            raise SourceDataError(f"CSV_MEMBER_MISSING:{day.isoformat()}")
        with zf.open(expected_csv, "r") as fb:
            txt = io.TextIOWrapper(fb, encoding="utf-8", newline="")
            reader = csv.reader(txt)
            last_ts = None
            for row in reader:
                if not row:
                    continue
                if len(row) != 12:
                    raise SourceDataError(f"KLINE_SCHEMA_FAIL:{day.isoformat()}:{len(row)}")
                try:
                    ts = int(row[0])
                except ValueError:
                    # Some public-data variants may include a single header row.
                    if last_ts is None:
                        continue
                    raise SourceDataError(f"TIMESTAMP_PARSE_FAIL:{day.isoformat()}")
                if last_ts is not None and ts <= last_ts:
                    raise SourceDataError(f"TIMESTAMP_ORDER_FAIL:{day.isoformat()}")
                d = dt.datetime.fromtimestamp(ts / 1000.0, tz=dt.timezone.utc).date()
                if d != day:
                    raise SourceDataError(f"TIMESTAMP_DATE_FAIL:{day.isoformat()}:{d.isoformat()}")
                try:
                    op = float(row[1])
                    cl = float(row[4])
                except ValueError:
                    raise SourceDataError(f"PRICE_PARSE_FAIL:{day.isoformat()}")
                if not (math.isfinite(op) and math.isfinite(cl) and op > 0 and cl > 0):
                    raise SourceDataError(f"PRICE_VALUE_FAIL:{day.isoformat()}")
                out.append((ts, op, cl))
                last_ts = ts
    return out


def monday_week_start(ts_ms: int) -> str:
    d = dt.datetime.fromtimestamp(ts_ms / 1000.0, tz=dt.timezone.utc).date()
    return (d - dt.timedelta(days=d.weekday())).isoformat()


def month_key(ts_ms: int) -> str:
    d = dt.datetime.fromtimestamp(ts_ms / 1000.0, tz=dt.timezone.utc).date()
    return f"{d.year:04d}-{d.month:02d}"


def detect_events():
    events = []
    exclusions = defaultdict(int)
    prev_ts = None
    prev_close = None
    active = None
    parsed_days = 0
    parsed_rows = 0

    for day in active_days():
        rows = read_day_rows(day)
        parsed_days += 1
        parsed_rows += len(rows)
        if day in ECONOMIC_EXCLUDED_DATES:
            if active is not None:
                exclusions["episode_crosses_excluded_boundary"] += 1
            active = None
            prev_ts = None
            prev_close = None
            continue

        for ts, op, cl in rows:
            if ts >= int(dt.datetime(2025, 1, 1, tzinfo=dt.timezone.utc).timestamp() * 1000):
                raise RuntimeError("PROTECTED_PERIOD_FIREWALL_VIOLATION")

            if prev_ts is not None and ts != prev_ts + 60_000:
                if active is not None:
                    exclusions["episode_broken_by_missing_minute"] += 1
                active = None
                prev_ts = None
                prev_close = None

            if active is not None:
                if active["entry_open"] is None and ts == active["entry_ts"]:
                    active["entry_open"] = op
                if ts == active["exit_ts"]:
                    if active["entry_open"] is None:
                        exclusions["missing_entry_minute"] += 1
                    else:
                        active["exit_open"] = op
                        events.append(active)
                    active = None
                elif ts > active["exit_ts"]:
                    exclusions["missing_exit_minute"] += 1
                    active = None

            if active is None and prev_close is not None and prev_ts is not None and ts == prev_ts + 60_000:
                direction = None
                side = None
                if prev_close > LOWER and cl <= LOWER:
                    direction = 1
                    side = "LOWER_LONG"
                elif prev_close < UPPER and cl >= UPPER:
                    direction = -1
                    side = "UPPER_SHORT_INVENTORY"
                if direction is not None:
                    active = {
                        "signal_ts": ts,
                        "signal_close": cl,
                        "side": side,
                        "direction": direction,
                        "entry_ts": ts + 60_000,
                        "exit_ts": ts + (HOLD_MINUTES + 1) * 60_000,
                        "entry_open": None,
                        "exit_open": None,
                    }

            prev_ts = ts
            prev_close = cl

    if active is not None:
        exclusions["episode_incomplete_at_source_end"] += 1

    for e in events:
        d = dt.datetime.fromtimestamp(e["signal_ts"] / 1000.0, tz=dt.timezone.utc).date()
        e["signal_date"] = d.isoformat()
        e["year"] = d.year
        e["month"] = month_key(e["signal_ts"])
        e["week_start"] = monday_week_start(e["signal_ts"])
    return events, dict(sorted(exclusions.items())), parsed_days, parsed_rows


def percentile(vals, q: float):
    if not vals:
        return None
    s = sorted(vals)
    if len(s) == 1:
        return float(s[0])
    pos = (len(s) - 1) * q
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return float(s[lo])
    w = pos - lo
    return float(s[lo] * (1.0 - w) + s[hi] * w)


def profit_factor(vals):
    pos = sum(x for x in vals if x > 0)
    neg = -sum(x for x in vals if x < 0)
    if neg == 0:
        return None, bool(pos > 0)
    return pos / neg, False


def max_additive_drawdown(vals_bps):
    cum = 0.0
    peak = 0.0
    max_dd = 0.0
    for bps in vals_bps:
        cum += bps / 10_000.0
        peak = max(peak, cum)
        max_dd = min(max_dd, cum - peak)
    return max_dd


def cluster_bootstrap(events, base_vals):
    by_week = defaultdict(list)
    for e, x in zip(events, base_vals):
        by_week[e["week_start"]].append(x)
    weeks = sorted(by_week)
    clusters = [by_week[w] for w in weeks]
    obs = statistics.fmean(base_vals)
    rng = random.Random(BOOT_SEED)
    boot = []
    null_boot = []
    W = len(clusters)
    for _ in range(BOOT_REPS):
        sample = []
        for _j in range(W):
            sample.extend(clusters[rng.randrange(W)])
        m = statistics.fmean(sample)
        boot.append(m)
        null_boot.append(m - obs)
    p = (1 + sum(1 for x in null_boot if x >= obs)) / (BOOT_REPS + 1)
    return {
        "method": "complete_utc_calendar_week_cluster_bootstrap",
        "weeks": W,
        "resamples": BOOT_REPS,
        "seed": BOOT_SEED,
        "observed_mean_base_net_bps": obs,
        "one_sided_p_mean_le_zero": p,
        "percentile_ci95_lower": percentile(boot, 0.025),
        "percentile_ci95_upper": percentile(boot, 0.975),
    }


def write_events_csv(events, include_performance: bool):
    p = OUT / "events.csv"
    base_fields = ["signal_ts", "signal_date", "week_start", "month", "year", "side", "direction", "entry_ts", "exit_ts"]
    perf_fields = ["signal_close", "entry_open", "exit_open", "gross_bps", "base_net_bps", "stress_net_bps"] if include_performance else []
    fields = base_fields + perf_fields
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for e in events:
            w.writerow({k: e.get(k) for k in fields})
    return p


def main():
    access_2025 = False
    access_2026 = False
    try:
        authority, authority_sha = validate_authority()
    except Exception as e:
        result = {
            "lab_id": LAB_ID,
            "mve_id": MVE_ID,
            "classification": "GOVERNANCE_FAIL_CLOSED",
            "error": f"{type(e).__name__}: {e}",
            "performance": None,
            "access_2025": False,
            "access_2026": False,
            "live_trading": False,
            "exchange_mutation": False,
        }
        dump_json("discovery_result.json", result)
        print(json.dumps(result, sort_keys=True))
        return 2

    source_ok, source_class, source_manifest_sha = source_acquisition(authority_sha)
    if not source_ok:
        result = {
            "lab_id": LAB_ID,
            "mve_id": MVE_ID,
            "classification": source_class,
            "authority_sha256": authority_sha,
            "source_manifest_discovery_sha256": source_manifest_sha,
            "economic_outcomes_opened": False,
            "performance": None,
            "access_2025": False,
            "access_2026": False,
            "live_trading": False,
            "exchange_mutation": False,
        }
        dump_json("discovery_result.json", result)
        print(json.dumps(result, sort_keys=True))
        return 2

    # Source binding has passed. Economic Discovery may now open exactly as frozen.
    try:
        events, exclusions, parsed_days, parsed_rows = detect_events()
    except Exception as e:
        result = {
            "lab_id": LAB_ID,
            "mve_id": MVE_ID,
            "classification": "DATA_FAILURE" if isinstance(e, SourceDataError) else "DISCOVERY_TECHNICAL_FAILURE",
            "error": f"{type(e).__name__}: {e}",
            "authority_sha256": authority_sha,
            "source_manifest_discovery_sha256": source_manifest_sha,
            "economic_outcomes_opened": True,
            "performance": None,
            "access_2025": False,
            "access_2026": False,
            "live_trading": False,
            "exchange_mutation": False,
        }
        dump_json("discovery_result.json", result)
        print(json.dumps(result, sort_keys=True))
        return 2

    N = len(events)
    weeks = sorted({e["week_start"] for e in events})
    years = sorted({e["year"] for e in events})
    sample_gate = {
        "min_n": MIN_N,
        "actual_n": N,
        "min_distinct_weeks": MIN_WEEKS,
        "actual_distinct_weeks": len(weeks),
        "min_distinct_years": MIN_YEARS,
        "actual_distinct_years": len(years),
        "years": years,
        "pass": N >= MIN_N and len(weeks) >= MIN_WEEKS and len(years) >= MIN_YEARS,
    }

    if not sample_gate["pass"]:
        write_events_csv(events, include_performance=False)
        result = {
            "lab_id": LAB_ID,
            "mve_id": MVE_ID,
            "classification": "DISCOVERY_INSUFFICIENT_SAMPLE",
            "authority_sha256": authority_sha,
            "source_manifest_discovery_sha256": source_manifest_sha,
            "parsed_verified_source_days": parsed_days,
            "parsed_rows": parsed_rows,
            "sample_gate": sample_gate,
            "exclusions": exclusions,
            "performance": None,
            "economic_outcomes_opened": True,
            "performance_summary_opened": False,
            "access_2025": access_2025,
            "access_2026": access_2026,
            "live_trading": False,
            "exchange_mutation": False,
        }
        dump_json("discovery_result.json", result)
        print(json.dumps({
            "classification": result["classification"],
            "N": N,
            "weeks": len(weeks),
            "years": len(years),
            "performance": None,
            "access_2025": False,
            "access_2026": False,
        }, sort_keys=True))
        shutil.rmtree(CACHE, ignore_errors=True)
        return 0

    gross = []
    base = []
    stress = []
    for e in events:
        g = e["direction"] * (e["exit_open"] / e["entry_open"] - 1.0) * 10_000.0
        b = g - BASE_COST_BPS
        s = g - STRESS_COST_BPS
        e["gross_bps"] = g
        e["base_net_bps"] = b
        e["stress_net_bps"] = s
        gross.append(g)
        base.append(b)
        stress.append(s)

    pf_base, pf_base_inf = profit_factor(base)
    pf_stress, pf_stress_inf = profit_factor(stress)
    boot = cluster_bootstrap(events, base)

    yearly = {}
    by_year = defaultdict(list)
    for e, b in zip(events, base):
        by_year[str(e["year"])].append(b)
    for y in sorted(by_year):
        yearly[y] = {"n": len(by_year[y]), "mean_base_net_bps": statistics.fmean(by_year[y])}

    positive_gross_total = sum(x for x in gross if x > 0)
    by_month_pos = defaultdict(float)
    for e, g in zip(events, gross):
        if g > 0:
            by_month_pos[e["month"]] += g
    if positive_gross_total > 0:
        max_month_share = max(by_month_pos.values(), default=0.0) / positive_gross_total
        max_event_share = max((x for x in gross if x > 0), default=0.0) / positive_gross_total
    else:
        max_month_share = 1.0
        max_event_share = 1.0

    represented_nonnegative_years = sum(1 for v in yearly.values() if v["mean_base_net_bps"] >= 0)
    y2024_ok = "2024" not in yearly or yearly["2024"]["mean_base_net_bps"] >= 0
    calendar_stability = represented_nonnegative_years >= 2 and y2024_ok

    gates = {
        "sample_n": N >= MIN_N,
        "distinct_weeks": len(weeks) >= MIN_WEEKS,
        "distinct_years": len(years) >= MIN_YEARS,
        "mean_base_positive": statistics.fmean(base) > 0,
        "pf_base_gt_1": (pf_base_inf or (pf_base is not None and pf_base > 1.0)),
        "bootstrap_p_lt_005": boot["one_sided_p_mean_le_zero"] < 0.05,
        "bootstrap_lower_gt_0": boot["percentile_ci95_lower"] is not None and boot["percentile_ci95_lower"] > 0,
        "mean_stress_positive": statistics.fmean(stress) > 0,
        "pf_stress_gt_1": (pf_stress_inf or (pf_stress is not None and pf_stress > 1.0)),
        "median_gross_positive": statistics.median(gross) > 0,
        "calendar_stability": calendar_stability,
        "month_positive_gross_concentration_le_040": max_month_share <= 0.40,
        "single_event_positive_gross_concentration_le_015": max_event_share <= 0.15,
        "provenance_and_firewall_clean": not access_2025 and not access_2026,
    }
    classification = "DISCOVERY_PASS_CANDIDATE_REQUIRES_SEPARATE_VALIDATION" if all(gates.values()) else "DISCOVERY_FAIL_NO_PROMOTION"

    perf = {
        "N": N,
        "long_n": sum(1 for e in events if e["direction"] == 1),
        "short_n": sum(1 for e in events if e["direction"] == -1),
        "distinct_event_weeks": len(weeks),
        "distinct_event_years": len(years),
        "mean_gross_bps": statistics.fmean(gross),
        "median_gross_bps": statistics.median(gross),
        "mean_base_net_bps": statistics.fmean(base),
        "median_base_net_bps": statistics.median(base),
        "mean_stress_net_bps": statistics.fmean(stress),
        "median_stress_net_bps": statistics.median(stress),
        "positive_fraction_base": sum(x > 0 for x in base) / N,
        "positive_fraction_stress": sum(x > 0 for x in stress) / N,
        "profit_factor_base": pf_base,
        "profit_factor_base_infinite": pf_base_inf,
        "profit_factor_stress": pf_stress,
        "profit_factor_stress_infinite": pf_stress_inf,
        "cumulative_additive_base_return": sum(base) / 10_000.0,
        "cumulative_additive_stress_return": sum(stress) / 10_000.0,
        "max_additive_drawdown_base": max_additive_drawdown(base),
        "worst_base_episode_bps": min(base),
        "p05_base_episode_bps": percentile(base, 0.05),
        "yearly": yearly,
        "represented_nonnegative_years": represented_nonnegative_years,
        "year_2024_nonnegative_if_represented": y2024_ok,
        "largest_month_positive_gross_share": max_month_share,
        "largest_single_event_positive_gross_share": max_event_share,
        "bootstrap": boot,
        "gates": gates,
    }
    write_events_csv(events, include_performance=True)
    events_sha = sha256_file(OUT / "events.csv")
    result = {
        "lab_id": LAB_ID,
        "mve_id": MVE_ID,
        "classification": classification,
        "authority_sha256": authority_sha,
        "source_manifest_discovery_sha256": source_manifest_sha,
        "events_sha256": events_sha,
        "parsed_verified_source_days": parsed_days,
        "parsed_rows": parsed_rows,
        "sample_gate": sample_gate,
        "exclusions": exclusions,
        "performance": perf,
        "economic_outcomes_opened": True,
        "performance_summary_opened": True,
        "access_2025": access_2025,
        "access_2026": access_2026,
        "live_trading": False,
        "exchange_mutation": False,
        "post_outcome_tuning": False,
    }
    dump_json("discovery_result.json", result)
    print(json.dumps({
        "classification": classification,
        "N": N,
        "mean_base_net_bps": perf["mean_base_net_bps"],
        "mean_stress_net_bps": perf["mean_stress_net_bps"],
        "pf_base": pf_base,
        "bootstrap_p": boot["one_sided_p_mean_le_zero"],
        "bootstrap_lower95": boot["percentile_ci95_lower"],
        "gates_passed": sum(bool(v) for v in gates.values()),
        "gates_total": len(gates),
        "access_2025": False,
        "access_2026": False,
    }, sort_keys=True))
    shutil.rmtree(CACHE, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
