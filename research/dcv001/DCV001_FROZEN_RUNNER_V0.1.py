#!/usr/bin/env python3
"""DCV-001 frozen full-census + Discovery + conditional 2024 replication runner.

Governance:
* official Binance Vision only;
* full source census before economic parsing;
* Discovery 2021-2023;
* 2024 full acquisition only if every Discovery gate passes;
* 2025/2026 never requested;
* no PnL, trading, orders, wallets or exchange mutation.
"""

from __future__ import annotations

import calendar
import csv
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
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

import numpy as np

BASE = "https://data.binance.vision/data/futures/um"
SYMBOL = "BTCUSDT"
CACHE = Path(".dcv001_cache")
OUT = Path("dcv001_run_receipt.json")
SEED = 140017
BOOT_REPS = 5000
BLOCK = 7
PROTECTED_START = datetime(2025, 1, 1, tzinfo=timezone.utc)
PROTECTED_START_MS = int(PROTECTED_START.timestamp() * 1000)
USER_AGENT = "Crypto-Lab-DCV001-FrozenRunner/0.2"
MARK_DAILY_PATCH_DATES = (
    "2021-07-01",
    "2021-07-24",
    "2021-07-25",
    "2021-07-26",
    "2021-07-27",
    "2022-07-31",
    "2022-10-02",
    "2023-02-24",
)
METRICS_REQUIRED = {
    "create_time",
    "symbol",
    "sum_open_interest",
    "sum_open_interest_value",
    "count_toptrader_long_short_ratio",
    "sum_toptrader_long_short_ratio",
    "count_long_short_ratio",
    "sum_taker_long_short_vol_ratio",
}
FUNDING_TIME_ALIASES = ("calc_time", "fundingTime", "funding_time")
FUNDING_RATE_ALIASES = ("last_funding_rate", "fundingRate", "funding_rate")
COEF_NAMES = ("intercept", "funding_z", "oi_change_z", "rv7_z", "funding_x_oi",
              "funding_x_rv7", "oi_x_rv7", "funding_x_oi_x_rv7")


class RunError(RuntimeError):
    pass


class HttpFailure(RunError):
    def __init__(self, url: str, code: int | None, detail: str):
        self.url = url
        self.code = code
        super().__init__(f"HTTP_FAILURE:{code}:{url}:{detail}")


@dataclass(frozen=True)
class ObjectSpec:
    dataset: str
    key: str
    url: str
    cache_path: Path
    required: bool


@dataclass
class ObjectMeta:
    dataset: str
    key: str
    url: str
    cache_path: str
    sha256: str
    published_sha256: str
    byte_count: int
    raw_row_count: int
    row_count: int
    exact_duplicate_rows_removed: int
    conflicting_duplicate_group_count: int
    first_timestamp_ms: int
    last_timestamp_ms: int
    timestamps_ms: list[int]


@dataclass(frozen=True)
class ModelRow:
    info_day: date
    outcome_day: date
    f: float
    o: float
    v: float
    y: float


def daterange(start: date, end: date) -> Iterable[date]:
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


def monthrange(start_y: int, start_m: int, end_y: int, end_m: int) -> Iterable[tuple[int, int]]:
    y, m = start_y, start_m
    while (y, m) <= (end_y, end_m):
        yield y, m
        if m == 12:
            y, m = y + 1, 1
        else:
            m += 1


def iso_ms(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def to_ms(value: str) -> int:
    v = value.strip()
    if not v:
        raise RunError("EMPTY_TIMESTAMP")
    try:
        x = float(v)
        if x > 1e14:
            return int(x / 1000)
        if x > 1e11:
            return int(x)
        if x > 1e9:
            return int(x * 1000)
    except ValueError:
        pass
    dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def request(url: str, attempts: int = 5, allow_404: bool = False) -> bytes | None:
    last: Exception | None = None
    for i in range(attempts):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=90) as r:
                if r.status != 200:
                    raise HttpFailure(url, r.status, "non-200")
                return r.read()
        except urllib.error.HTTPError as exc:
            if exc.code == 404 and allow_404:
                return None
            last = exc
            if exc.code in (400, 401, 403, 404):
                break
        except Exception as exc:
            last = exc
        if i + 1 < attempts:
            time.sleep(min(8.0, 1.25 * (i + 1)))
    code = getattr(last, "code", None)
    raise HttpFailure(url, code, f"{type(last).__name__}:{last}")


def published_checksum(url: str) -> str:
    raw = request(url + ".CHECKSUM", allow_404=False)
    assert raw is not None
    text = raw.decode("utf-8", "replace")
    m = re.search(r"(?i)\b([0-9a-f]{64})\b", text)
    if not m:
        raise RunError(f"CHECKSUM_PARSE_FAILED:{url}")
    return m.group(1).lower()


def get_verified(spec: ObjectSpec) -> tuple[ObjectSpec, str, str, int] | None:
    spec.cache_path.parent.mkdir(parents=True, exist_ok=True)
    raw = request(spec.url, allow_404=not spec.required)
    if raw is None:
        return None
    pub = published_checksum(spec.url)
    actual = hashlib.sha256(raw).hexdigest()
    if actual != pub:
        raise RunError(f"CHECKSUM_MISMATCH:{spec.key}:{actual}:{pub}")
    spec.cache_path.write_bytes(raw)
    return spec, actual, pub, len(raw)


def one_csv(path: Path) -> tuple[str, bytes]:
    with zipfile.ZipFile(path, "r") as z:
        bad = z.testzip()
        if bad is not None:
            raise RunError(f"ZIP_CRC_FAIL:{path}:{bad}")
        names = [n for n in z.namelist() if n.lower().endswith(".csv") and not n.endswith("/")]
        if len(names) != 1:
            raise RunError(f"ZIP_CSV_COUNT:{path}:{len(names)}")
        return names[0], z.read(names[0])


def decode_rows(path: Path) -> list[list[str]]:
    _, raw = one_csv(path)
    text = raw.decode("utf-8-sig", "strict")
    return [r for r in csv.reader(io.StringIO(text)) if r and any(x.strip() for x in r)]


def find_alias(header: list[str], aliases: tuple[str, ...], label: str, key: str) -> int:
    for a in aliases:
        if a in header:
            return header.index(a)
    raise RunError(f"{label}_COLUMN_MISSING:{key}:{header}")


def assert_pre2025(ts: list[int], key: str) -> None:
    if any(x >= PROTECTED_START_MS for x in ts):
        raise RunError(f"PROTECTED_TIMESTAMP:{key}")


def dedupe_exact_metrics_rows(body: list[list[str]], ti: int, key: str) -> tuple[list[list[str]], int, int]:
    """Collapse only exact full-row duplicates sharing create_time.

    Amendment B: conflicting duplicate timestamp groups fail closed.
    No numeric economic field is interpreted by this structural normalization.
    """
    groups: dict[int, list[list[str]]] = {}
    for r in body:
        if len(r) <= ti:
            raise RunError(f"METRICS_WIDTH:{key}")
        groups.setdefault(to_ms(r[ti]), []).append(r)

    deduped: list[list[str]] = []
    removed = 0
    conflicting = 0
    for ts in sorted(groups):
        rows_at_ts = groups[ts]
        unique_rows = {tuple(r) for r in rows_at_ts}
        if len(unique_rows) != 1:
            conflicting += 1
            raise RunError(f"SOURCE_PROVENANCE_CONFLICT:{key}:{iso_ms(ts)}:{len(unique_rows)}")
        deduped.append(rows_at_ts[0])
        removed += len(rows_at_ts) - 1
    return deduped, removed, conflicting


def parse_meta(spec: ObjectSpec, sha: str, pub: str, size: int) -> ObjectMeta:
    rows = decode_rows(spec.cache_path)
    if not rows:
        raise RunError(f"EMPTY_CSV:{spec.key}")

    if spec.dataset == "metrics":
        header = [x.strip() for x in rows[0]]
        missing = METRICS_REQUIRED.difference(header)
        if missing:
            raise RunError(f"METRICS_SCHEMA_MISSING:{spec.key}:{sorted(missing)}")
        ti = header.index("create_time")
        si = header.index("symbol")
        raw_body = rows[1:]
        if not raw_body:
            raise RunError(f"METRICS_NO_BODY:{spec.key}")
        body, exact_duplicate_rows_removed, conflicting_duplicate_group_count = dedupe_exact_metrics_rows(
            raw_body, ti, spec.key
        )
        ts = []
        for r in body:
            if len(r) <= max(ti, si):
                raise RunError(f"METRICS_WIDTH:{spec.key}")
            if r[si].strip() != SYMBOL:
                raise RunError(f"METRICS_SYMBOL:{spec.key}")
            ts.append(to_ms(r[ti]))

        requested = date.fromisoformat(spec.key)
        lo = int(datetime.combine(requested, datetime.min.time(), tzinfo=timezone.utc).timestamp() * 1000)
        hi = lo + 86_400_000
        if min(ts) < lo or max(ts) >= hi:
            raise RunError(f"METRICS_DATE_SCOPE:{spec.key}:{iso_ms(min(ts))}:{iso_ms(max(ts))}")

    elif spec.dataset == "funding":
        exact_duplicate_rows_removed = 0
        conflicting_duplicate_group_count = 0
        raw_body = rows[1:]
        header = [x.strip() for x in rows[0]]
        ti = find_alias(header, FUNDING_TIME_ALIASES, "FUNDING_TIME", spec.key)
        find_alias(header, FUNDING_RATE_ALIASES, "FUNDING_RATE", spec.key)
        body = rows[1:]
        if not body:
            raise RunError(f"FUNDING_NO_BODY:{spec.key}")
        ts = [to_ms(r[ti]) for r in body if len(r) > ti]
        if len(ts) != len(body):
            raise RunError(f"FUNDING_WIDTH:{spec.key}")

    elif spec.dataset in ("mark", "mark_patch"):
        exact_duplicate_rows_removed = 0
        conflicting_duplicate_group_count = 0
        raw_body = rows
        body = rows
        try:
            to_ms(rows[0][0])
        except Exception:
            body = rows[1:]
        if not body or any(len(r) < 6 for r in body):
            raise RunError(f"MARK_SCHEMA:{spec.key}")
        ts = [to_ms(r[0]) for r in body]
        if spec.dataset == "mark_patch":
            requested = date.fromisoformat(spec.key)
            lo = int(datetime.combine(requested, datetime.min.time(), tzinfo=timezone.utc).timestamp() * 1000)
            hi = lo + 86_400_000
            if len(ts) != 24 or sorted(ts) != [lo + i * 3_600_000 for i in range(24)]:
                raise RunError(f"MARK_PATCH_DAY_GRID_INVALID:{spec.key}")

    else:
        raise RunError(f"UNKNOWN_DATASET:{spec.dataset}")

    if not ts:
        raise RunError(f"NO_TIMESTAMPS:{spec.key}")
    assert_pre2025(ts, spec.key)
    if len(ts) != len(set(ts)):
        raise RunError(f"DUPLICATE_TIMESTAMP_INSIDE_OBJECT:{spec.key}")

    if spec.dataset != "metrics":
        raw_body = body

    return ObjectMeta(
        dataset=spec.dataset,
        key=spec.key,
        url=spec.url,
        cache_path=str(spec.cache_path),
        sha256=sha,
        published_sha256=pub,
        byte_count=size,
        raw_row_count=len(raw_body),
        row_count=len(body),
        exact_duplicate_rows_removed=exact_duplicate_rows_removed,
        conflicting_duplicate_group_count=conflicting_duplicate_group_count,
        first_timestamp_ms=min(ts),
        last_timestamp_ms=max(ts),
        timestamps_ms=ts,
    )


def build_specs(year_start: int, year_end: int) -> list[ObjectSpec]:
    specs: list[ObjectSpec] = []
    for d in daterange(date(year_start, 1, 1), date(year_end, 12, 31)):
        ds = d.isoformat()
        url = f"{BASE}/daily/metrics/{SYMBOL}/{SYMBOL}-metrics-{ds}.zip"
        specs.append(ObjectSpec("metrics", ds, url, CACHE / f"metrics/{SYMBOL}-metrics-{ds}.zip", False))

    for y, m in monthrange(year_start, 1, year_end, 12):
        ym = f"{y:04d}-{m:02d}"
        f_url = f"{BASE}/monthly/fundingRate/{SYMBOL}/{SYMBOL}-fundingRate-{ym}.zip"
        p_url = f"{BASE}/monthly/markPriceKlines/{SYMBOL}/1h/{SYMBOL}-1h-{ym}.zip"
        specs.append(ObjectSpec("funding", ym, f_url, CACHE / f"funding/{SYMBOL}-fundingRate-{ym}.zip", True))
        specs.append(ObjectSpec("mark", ym, p_url, CACHE / f"mark/{SYMBOL}-1h-{ym}.zip", True))

    for ds in MARK_DAILY_PATCH_DATES:
        d = date.fromisoformat(ds)
        if year_start <= d.year <= year_end:
            p_url = f"{BASE}/daily/markPriceKlines/{SYMBOL}/1h/{SYMBOL}-1h-{ds}.zip"
            specs.append(ObjectSpec("mark_patch", ds, p_url, CACHE / f"mark_patch/{SYMBOL}-1h-{ds}.zip", True))
    return specs


def acquire_and_census(year_start: int, year_end: int, label: str) -> tuple[dict, dict[str, ObjectMeta]]:
    specs = build_specs(year_start, year_end)
    metas: dict[str, ObjectMeta] = {}
    missing_metrics: list[str] = []
    errors: list[str] = []

    # Bounded concurrency: official public archive, no credentials.
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(get_verified, spec): spec for spec in specs}
        for fut in as_completed(futures):
            spec = futures[fut]
            try:
                got = fut.result()
                if got is None:
                    if spec.dataset == "metrics":
                        missing_metrics.append(spec.key)
                        continue
                    raise RunError(f"REQUIRED_OBJECT_MISSING:{spec.key}")
                s, sha, pub, size = got
                meta = parse_meta(s, sha, pub, size)
                metas[f"{s.dataset}:{s.key}"] = meta
            except Exception as exc:
                errors.append(f"{type(exc).__name__}:{exc}")

    if errors:
        raise RunError("SOURCE_OBJECT_FAILURES:" + " | ".join(errors[:20]))

    requested_metrics = (date(year_end, 12, 31) - date(year_start, 1, 1)).days + 1
    metric_metas = sorted((m for m in metas.values() if m.dataset == "metrics"), key=lambda x: x.key)
    funding_metas = sorted((m for m in metas.values() if m.dataset == "funding"), key=lambda x: x.key)
    mark_metas = sorted((m for m in metas.values() if m.dataset == "mark"), key=lambda x: x.key)
    mark_patch_metas = sorted((m for m in metas.values() if m.dataset == "mark_patch"), key=lambda x: x.key)

    metrics_coverage = len(metric_metas) / requested_metrics
    if metrics_coverage < 0.99:
        raise RunError(f"METRICS_COVERAGE_LT_99PCT:{len(metric_metas)}/{requested_metrics}")

    expected_months = (year_end - year_start + 1) * 12
    if len(funding_metas) != expected_months:
        raise RunError(f"FUNDING_MONTH_COUNT:{len(funding_metas)}/{expected_months}")
    if len(mark_metas) != expected_months:
        raise RunError(f"MARK_MONTH_COUNT:{len(mark_metas)}/{expected_months}")

    def combined_ts(ms: list[ObjectMeta]) -> list[int]:
        arr = [x for meta in ms for x in meta.timestamps_ms]
        if len(arr) != len(set(arr)):
            raise RunError(f"GLOBAL_DUPLICATE_TIMESTAMP:{ms[0].dataset if ms else 'none'}")
        return sorted(arr)

    metric_ts = combined_ts(metric_metas)
    funding_ts = combined_ts(funding_metas)
    monthly_mark_ts = combined_ts(mark_metas)
    patch_mark_ts = combined_ts(mark_patch_metas) if mark_patch_metas else []
    monthly_mark_set = set(monthly_mark_ts)
    overlap = sorted(monthly_mark_set.intersection(patch_mark_ts))
    if overlap:
        raise RunError(f"MARK_PATCH_OVERLAP_WITH_MONTHLY:{len(overlap)}:{iso_ms(overlap[0])}")
    mark_ts = sorted(monthly_mark_ts + patch_mark_ts)

    # Funding continuity: no gap greater than 12 hours.
    funding_gaps = [(b - a) / 3_600_000 for a, b in zip(funding_ts, funding_ts[1:])]
    max_funding_gap_h = max(funding_gaps) if funding_gaps else math.inf
    if max_funding_gap_h > 12.0:
        raise RunError(f"FUNDING_GAP_GT_12H:{max_funding_gap_h}")

    expected_hours = requested_metrics * 24
    mark_coverage = len(mark_ts) / expected_hours
    if mark_coverage < 0.995:
        raise RunError(f"MARK_COVERAGE_LT_99_5PCT:{len(mark_ts)}/{expected_hours}")
    mark_missing_runs = [max(0, round((b - a) / 3_600_000) - 1) for a, b in zip(mark_ts, mark_ts[1:])]
    max_mark_missing_run = max(mark_missing_runs) if mark_missing_runs else expected_hours
    if max_mark_missing_run > 3:
        raise RunError(f"MARK_GAP_GT_3_CONSECUTIVE_HOURS:{max_mark_missing_run}")

    manifest = []
    for meta in sorted(metas.values(), key=lambda x: (x.dataset, x.key)):
        manifest.append({
            "dataset": meta.dataset,
            "key": meta.key,
            "sha256": meta.sha256,
            "published_sha256": meta.published_sha256,
            "checksum_verified": meta.sha256 == meta.published_sha256,
            "byte_count": meta.byte_count,
            "raw_row_count": meta.raw_row_count,
            "row_count_after_exact_dedupe": meta.row_count,
            "exact_duplicate_rows_removed": meta.exact_duplicate_rows_removed,
            "conflicting_duplicate_group_count": meta.conflicting_duplicate_group_count,
            "first_timestamp_utc": iso_ms(meta.first_timestamp_ms),
            "last_timestamp_utc": iso_ms(meta.last_timestamp_ms),
        })

    census = {
        "label": label,
        "classification": "SOURCE_CENSUS_PASS",
        "years": [year_start, year_end],
        "metrics_requested_days": requested_metrics,
        "metrics_present_days": len(metric_metas),
        "metrics_missing_days": sorted(missing_metrics),
        "metrics_coverage_fraction": metrics_coverage,
        "metrics_exact_duplicate_rows_removed": sum(m.exact_duplicate_rows_removed for m in metric_metas),
        "metrics_conflicting_duplicate_group_count": sum(m.conflicting_duplicate_group_count for m in metric_metas),
        "funding_months": len(funding_metas),
        "funding_max_gap_hours": max_funding_gap_h,
        "mark_months": len(mark_metas),
        "mark_daily_patch_objects": len(mark_patch_metas),
        "mark_daily_patch_hours": len(patch_mark_ts),
        "mark_hour_rows": len(mark_ts),
        "mark_expected_hours": expected_hours,
        "mark_coverage_fraction": mark_coverage,
        "mark_max_consecutive_missing_hours": max_mark_missing_run,
        "checksum_verified_objects": len(metas),
        "protected_2025_accessed": False,
        "protected_2026_accessed": False,
        "economic_values_opened_during_census": False,
        "manifest": manifest,
    }
    census["census_sha256"] = hashlib.sha256(
        json.dumps(census, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return census, metas


def read_metrics_values(metas: dict[str, ObjectMeta]) -> dict[date, float]:
    out: dict[date, float] = {}
    for meta in sorted((m for m in metas.values() if m.dataset == "metrics"), key=lambda x: x.key):
        rows = decode_rows(Path(meta.cache_path))
        header = [x.strip() for x in rows[0]]
        ti, oi = header.index("create_time"), header.index("sum_open_interest")
        body, _, _ = dedupe_exact_metrics_rows(rows[1:], ti, meta.key)
        candidates: list[tuple[int, float]] = []
        for r in body:
            ts = to_ms(r[ti])
            val = float(r[oi])
            if not math.isfinite(val) or val <= 0:
                raise RunError(f"INVALID_OI_VALUE:{meta.key}")
            candidates.append((ts, val))
        if not candidates:
            raise RunError(f"NO_VALID_OI:{meta.key}")
        candidates.sort(key=lambda x: x[0])
        last_ts, last_val = candidates[-1]
        d = datetime.fromtimestamp(last_ts / 1000, tz=timezone.utc).date()
        expected = date.fromisoformat(meta.key)
        if d != expected:
            raise RunError(f"METRICS_EOD_DATE_MISMATCH:{meta.key}:{d}")
        if d in out:
            raise RunError(f"DUPLICATE_OI_DAY:{d}")
        out[d] = last_val
    return out


def read_funding_values(metas: dict[str, ObjectMeta]) -> dict[date, float]:
    by_day: dict[date, list[float]] = {}
    for meta in sorted((m for m in metas.values() if m.dataset == "funding"), key=lambda x: x.key):
        rows = decode_rows(Path(meta.cache_path))
        header = [x.strip() for x in rows[0]]
        ti = find_alias(header, FUNDING_TIME_ALIASES, "FUNDING_TIME", meta.key)
        ri = find_alias(header, FUNDING_RATE_ALIASES, "FUNDING_RATE", meta.key)
        for r in rows[1:]:
            ts = to_ms(r[ti])
            val = float(r[ri])
            if not math.isfinite(val):
                raise RunError(f"INVALID_FUNDING_VALUE:{meta.key}")
            d = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).date()
            by_day.setdefault(d, []).append(val)
    return {d: float(sum(vs)) for d, vs in by_day.items() if vs}


def read_mark_values(metas: dict[str, ObjectMeta]) -> dict[int, float]:
    out: dict[int, float] = {}
    ordered = sorted((m for m in metas.values() if m.dataset == "mark"), key=lambda x: x.key)
    ordered += sorted((m for m in metas.values() if m.dataset == "mark_patch"), key=lambda x: x.key)
    for meta in ordered:
        rows = decode_rows(Path(meta.cache_path))
        body = rows
        try:
            to_ms(rows[0][0])
        except Exception:
            body = rows[1:]
        for r in body:
            ts = to_ms(r[0])
            close = float(r[4])
            if not math.isfinite(close) or close <= 0:
                raise RunError(f"INVALID_MARK_CLOSE:{meta.key}")
            if ts in out:
                raise RunError(f"DUPLICATE_MARK_VALUE_TS:{ts}")
            out[ts] = close
    return out


def raw_features(
    oi: dict[date, float],
    funding: dict[date, float],
    mark: dict[int, float],
    start: date,
    end: date,
) -> dict[date, tuple[float, float, float, float]]:
    """Returns D -> (funding_D, oi_change_D, rv7_D, mark_close_D)."""
    out: dict[date, tuple[float, float, float, float]] = {}
    hour_ms = 3_600_000

    for d in daterange(start, end):
        prev_d = d - timedelta(days=1)
        if d not in oi or prev_d not in oi or d not in funding:
            continue
        oi_change = math.log(oi[d] / oi[prev_d])

        # Exactly 169 closes produce 168 one-hour returns:
        # D-7 23:00 through D 23:00 inclusive.
        first_dt = datetime.combine(d - timedelta(days=7), datetime.min.time(), tzinfo=timezone.utc) + timedelta(hours=23)
        first_ts = int(first_dt.timestamp() * 1000)
        times = [first_ts + i * hour_ms for i in range(169)]
        if any(ts not in mark for ts in times):
            continue
        closes = [mark[ts] for ts in times]
        rets = [math.log(closes[i] / closes[i - 1]) for i in range(1, len(closes))]
        if len(rets) != 168:
            raise RunError("RV_RETURN_COUNT_INVARIANT")
        rv7 = math.sqrt(sum(x * x for x in rets))
        if not (math.isfinite(rv7) and rv7 > 0):
            continue
        mark_close = closes[-1]  # exact D 23:00
        out[d] = (funding[d], oi_change, rv7, mark_close)
    return out


def sample_std(xs: list[float]) -> float:
    if len(xs) < 2:
        return math.nan
    return statistics.stdev(xs)


def clipped_z(x: float, history: list[float]) -> float | None:
    if len(history) != 90:
        return None
    mu = statistics.fmean(history)
    sd = sample_std(history)
    if not math.isfinite(sd) or sd <= 0:
        return None
    z = (x - mu) / sd
    if not math.isfinite(z):
        return None
    return max(-5.0, min(5.0, z))


def build_model_rows(
    raw: dict[date, tuple[float, float, float, float]],
    outcome_start: date,
    outcome_end: date,
) -> list[ModelRow]:
    raw_days = sorted(raw)
    rows: list[ModelRow] = []

    for i, d in enumerate(raw_days):
        if i < 90:
            continue
        hist_days = raw_days[i - 90:i]
        f_hist = [raw[h][0] for h in hist_days]
        o_hist = [raw[h][1] for h in hist_days]
        v_hist = [raw[h][2] for h in hist_days]
        fz = clipped_z(raw[d][0], f_hist)
        oz = clipped_z(raw[d][1], o_hist)
        vz = clipped_z(raw[d][2], v_hist)
        if fz is None or oz is None or vz is None:
            continue

        next_d = d + timedelta(days=1)
        if not (outcome_start <= next_d <= outcome_end):
            continue
        if next_d not in raw:
            # Need the exact next-day 23:00 close. raw[next_d] guarantees it.
            continue
        c0 = raw[d][3]
        c1 = raw[next_d][3]
        y = math.log(c1 / c0)
        if not math.isfinite(y):
            continue
        rows.append(ModelRow(d, next_d, fz, oz, vz, y))
    return rows


def design(rows: list[ModelRow]) -> tuple[np.ndarray, np.ndarray]:
    f = np.array([r.f for r in rows], dtype=float)
    o = np.array([r.o for r in rows], dtype=float)
    v = np.array([r.v for r in rows], dtype=float)
    y = np.array([r.y for r in rows], dtype=float)
    X = np.column_stack([
        np.ones(len(rows)),
        f, o, v,
        f * o,
        f * v,
        o * v,
        f * o * v,
    ])
    return X, y


def fit(rows: list[ModelRow]) -> tuple[np.ndarray, int]:
    X, y = design(rows)
    beta, _, rank, _ = np.linalg.lstsq(X, y, rcond=None)
    return beta, int(rank)


def bootstrap_bfov(rows: list[ModelRow], ci_low: float, ci_high: float) -> dict:
    n = len(rows)
    if n < BLOCK:
        raise RunError("BOOTSTRAP_SAMPLE_TOO_SMALL")
    rng = np.random.default_rng(SEED)
    vals: list[float] = []
    singular = 0
    max_start = n - BLOCK

    for _ in range(BOOT_REPS):
        idx: list[int] = []
        while len(idx) < n:
            s = int(rng.integers(0, max_start + 1))
            idx.extend(range(s, s + BLOCK))
        sample = [rows[i] for i in idx[:n]]
        b, rank = fit(sample)
        if rank != 8 or not np.isfinite(b[-1]):
            singular += 1
            continue
        vals.append(float(b[-1]))

    if len(vals) < 4750:
        raise RunError(f"INFERENCE_TECHNICAL_FAIL:valid={len(vals)}:singular={singular}")
    arr = np.array(vals)
    return {
        "valid_bootstrap_estimates": len(vals),
        "singular_bootstrap_samples": singular,
        "block_length": BLOCK,
        "seed": SEED,
        "repetitions_requested": BOOT_REPS,
        "ci_low": float(np.percentile(arr, ci_low * 100)),
        "ci_high": float(np.percentile(arr, ci_high * 100)),
        "mean": float(np.mean(arr)),
    }


def evaluate_discovery(rows: list[ModelRow]) -> dict:
    beta, rank = fit(rows)
    yearly: dict[str, dict] = {}
    neg_years = 0
    for yr in (2021, 2022, 2023):
        yr_rows = [r for r in rows if r.info_day.year == yr]
        if len(yr_rows) >= 8:
            b, rnk = fit(yr_rows)
            val = float(b[-1]) if rnk == 8 else None
        else:
            rnk, val = 0, None
        if val is not None and val < 0:
            neg_years += 1
        yearly[str(yr)] = {"n": len(yr_rows), "rank": rnk, "bFOV": val}

    boot = bootstrap_bfov(rows, 0.025, 0.975)
    gates = {
        "eligible_n_gte_900": len(rows) >= 900,
        "design_rank_eq_8": rank == 8,
        "bFOV_lt_0": float(beta[-1]) < 0,
        "bootstrap_95_upper_lt_0": boot["ci_high"] < 0,
        "negative_bFOV_years_gte_2_of_3": neg_years >= 2,
    }
    passed = all(gates.values())
    return {
        "classification": "DISCOVERY_MECHANISM_PASS" if passed else "DISCOVERY_FAIL_NO_PROMOTION",
        "eligible_n": len(rows),
        "design_rank": rank,
        "coefficients": {name: float(beta[i]) for i, name in enumerate(COEF_NAMES)},
        "primary_bFOV": float(beta[-1]),
        "bootstrap_95": boot,
        "calendar_years": yearly,
        "negative_bFOV_year_count": neg_years,
        "gates": gates,
        "all_gates_pass": passed,
    }


def evaluate_replication(rows: list[ModelRow]) -> dict:
    beta, rank = fit(rows)
    boot = bootstrap_bfov(rows, 0.05, 0.95)
    gates = {
        "eligible_n_gte_300": len(rows) >= 300,
        "design_rank_eq_8": rank == 8,
        "bFOV_lt_0": float(beta[-1]) < 0,
        "bootstrap_90_upper_lt_0": boot["ci_high"] < 0,
    }
    passed = all(gates.values())
    return {
        "classification": "MECHANISM_REPLICATION_PASS_CANDIDATE" if passed else "REPLICATION_FAIL_NO_PROMOTION",
        "eligible_n": len(rows),
        "design_rank": rank,
        "coefficients": {name: float(beta[i]) for i, name in enumerate(COEF_NAMES)},
        "primary_bFOV": float(beta[-1]),
        "bootstrap_90": boot,
        "gates": gates,
        "all_gates_pass": passed,
    }


def merge_metas(*groups: dict[str, ObjectMeta]) -> dict[str, ObjectMeta]:
    out: dict[str, ObjectMeta] = {}
    for g in groups:
        for k, v in g.items():
            if k in out:
                raise RunError(f"DUPLICATE_META_KEY:{k}")
            out[k] = v
    return out


def safe_write(receipt: dict) -> None:
    receipt["receipt_sha256"] = hashlib.sha256(
        json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    shutil.rmtree(CACHE, ignore_errors=True)
    CACHE.mkdir(parents=True, exist_ok=True)

    receipt: dict = {
        "lab_id": "DCV-001",
        "authority": "DCV001_PREOUTCOME_AUTHORITY_V0.1.md + AMENDMENT_A_V0.1 + AMENDMENT_B_V0.1 + DAILY_MARK_REMEDIATION_AUTHORITY_V0.2",
        "classification": "RUNNING",
        "live_trading": False,
        "orders_created": False,
        "exchange_mutation": False,
        "wallet_access": False,
        "protected_2025_accessed": False,
        "protected_2026_accessed": False,
        "replication_2024_full_source_accessed": False,
        "pnl_computed": False,
        "errors": [],
    }

    try:
        census_21_23, metas_21_23 = acquire_and_census(2021, 2023, "DISCOVERY_SOURCE_2021_2023")
        receipt["source_census_2021_2023"] = census_21_23

        # Only now, after SOURCE_CENSUS_PASS, open economic source values.
        oi = read_metrics_values(metas_21_23)
        funding = read_funding_values(metas_21_23)
        mark = read_mark_values(metas_21_23)
        raw = raw_features(oi, funding, mark, date(2021, 1, 1), date(2023, 12, 31))
        discovery_rows = build_model_rows(raw, date(2021, 1, 1), date(2023, 12, 31))
        discovery = evaluate_discovery(discovery_rows)
        receipt["discovery"] = discovery

        if not discovery["all_gates_pass"]:
            receipt["classification"] = "DISCOVERY_FAIL_NO_PROMOTION"
            receipt["replication_2024_full_source_accessed"] = False
            safe_write(receipt)
            print(json.dumps({
                "lab_id": "DCV-001",
                "classification": receipt["classification"],
                "source_census": census_21_23["classification"],
                "eligible_n": discovery["eligible_n"],
                "primary_bFOV": discovery["primary_bFOV"],
                "bootstrap_95": discovery["bootstrap_95"],
                "negative_years": discovery["negative_bFOV_year_count"],
                "replication_2024_full_source_accessed": False,
                "protected_2025_accessed": False,
                "protected_2026_accessed": False,
                "receipt_sha256": receipt["receipt_sha256"],
            }, sort_keys=True))
            return 0

        # Discovery PASS is the only release condition for full 2024 acquisition.
        census_2024, metas_2024 = acquire_and_census(2024, 2024, "REPLICATION_SOURCE_2024")
        receipt["replication_2024_full_source_accessed"] = True
        receipt["source_census_2024"] = census_2024

        all_metas = merge_metas(metas_21_23, metas_2024)
        oi_all = read_metrics_values(all_metas)
        funding_all = read_funding_values(all_metas)
        mark_all = read_mark_values(all_metas)
        # Build 2023-2024 raw set so 2024 January normalization can use 2023 history.
        raw_all = raw_features(oi_all, funding_all, mark_all, date(2023, 1, 1), date(2024, 12, 31))
        rep_rows = build_model_rows(raw_all, date(2024, 1, 1), date(2024, 12, 31))
        replication = evaluate_replication(rep_rows)
        receipt["replication_2024"] = replication
        receipt["classification"] = replication["classification"]
        safe_write(receipt)
        print(json.dumps({
            "lab_id": "DCV-001",
            "classification": receipt["classification"],
            "discovery": discovery["classification"],
            "discovery_n": discovery["eligible_n"],
            "discovery_bFOV": discovery["primary_bFOV"],
            "replication_n": replication["eligible_n"],
            "replication_bFOV": replication["primary_bFOV"],
            "replication_2024_full_source_accessed": True,
            "protected_2025_accessed": False,
            "protected_2026_accessed": False,
            "receipt_sha256": receipt["receipt_sha256"],
        }, sort_keys=True))
        return 0

    except Exception as exc:
        receipt["classification"] = "TECHNICAL_OR_SOURCE_FAIL_CLOSED"
        receipt["errors"].append(f"{type(exc).__name__}:{exc}")
        safe_write(receipt)
        print(json.dumps({
            "lab_id": "DCV-001",
            "classification": receipt["classification"],
            "errors": receipt["errors"],
            "replication_2024_full_source_accessed": receipt["replication_2024_full_source_accessed"],
            "protected_2025_accessed": False,
            "protected_2026_accessed": False,
            "receipt_sha256": receipt["receipt_sha256"],
        }, sort_keys=True))
        return 1
    finally:
        shutil.rmtree(CACHE, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
