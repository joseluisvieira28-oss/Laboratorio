"""V0.4.3 outcome-blind semantic + Binance mark timestamp provenance probe.

Reads narrowly authorized Hyperliquid funding values internally only to determine
field scale/formula semantics. Never emits raw funding/premium values, signs,
means, spreads, carry, APR/APY, PnL, or rankings.

Binance markPriceKlines values remain opaque: only archive checksums and 1-minute
open-time coverage are inspected.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import os
import time
import urllib.error
import urllib.request
import zipfile
from calendar import monthrange
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, getcontext
from pathlib import Path
from typing import Any

getcontext().prec = 40

LAB_ID = "CROSS_VENUE_FUNDING_BASIS_LAB_V01"
AMENDMENT_ID = "CROSS_VENUE_FUNDING_BASIS_SEMANTIC_AND_BASIS_PROVENANCE_AMENDMENT_V043"
HL_INFO = "https://api.hyperliquid.xyz/info"
BINANCE_BASE = "https://data.binance.vision/data/futures/um/monthly/markPriceKlines"
TOL = Decimal("1e-12")
INTEREST_8H = Decimal("0.0001")
CANDIDATE_CLAMPS = (Decimal("0.0003"), Decimal("0.0005"))

carry_computed = False
apr_apy_computed = False
pnl_computed = False
signals_computed = False
cross_venue_rate_comparison_computed = False
price_values_output = False


class ProbeFailure(RuntimeError):
    pass


def _require(ok: bool, msg: str) -> None:
    if not ok:
        raise ProbeFailure(msg)


def _ms(iso: str) -> int:
    return int(datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp() * 1000)


def _post_json(url: str, body: dict[str, Any], timeout: int = 30) -> Any:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _fetch_hl_window(coin: str, start_iso: str, end_iso: str) -> list[dict[str, Any]]:
    rows = _post_json(HL_INFO, {
        "type": "fundingHistory",
        "coin": coin,
        "startTime": _ms(start_iso),
        "endTime": _ms(end_iso),
    })
    _require(isinstance(rows, list), f"Hyperliquid {coin}: non-list response")
    return rows


def _dec(x: Any) -> Decimal | None:
    try:
        d = Decimal(str(x))
    except (InvalidOperation, ValueError):
        return None
    if not d.is_finite():
        return None
    return d


def _clamp(x: Decimal, c: Decimal) -> Decimal:
    return min(max(x, -c), c)


def _expected(premium: Decimal, clamp_bound: Decimal, divisor: int) -> Decimal:
    f8 = premium + _clamp(INTEREST_8H - premium, clamp_bound)
    return f8 / Decimal(divisor)


def _semantic_matches(rows: list[dict[str, Any]], clamp_bound: Decimal, divisor: int) -> tuple[int, int]:
    finite = 0
    matches = 0
    for row in rows:
        p = _dec(row.get("premium"))
        f = _dec(row.get("fundingRate"))
        if p is None or f is None:
            continue
        finite += 1
        if abs(f - _expected(p, clamp_bound, divisor)) <= TOL:
            matches += 1
    return matches, finite


def _discriminating_clamp_counts(rows: list[dict[str, Any]], divisor: int = 8) -> dict[str, int]:
    old_c, new_c = CANDIDATE_CLAMPS
    out = {"discriminating_rows": 0, "old_clamp_matches": 0, "new_clamp_matches": 0, "neither_matches": 0}
    for row in rows:
        p = _dec(row.get("premium"))
        f = _dec(row.get("fundingRate"))
        if p is None or f is None:
            continue
        e_old = _expected(p, old_c, divisor)
        e_new = _expected(p, new_c, divisor)
        if abs(e_old - e_new) <= TOL:
            continue
        out["discriminating_rows"] += 1
        old_match = abs(f - e_old) <= TOL
        new_match = abs(f - e_new) <= TOL
        if old_match:
            out["old_clamp_matches"] += 1
        if new_match:
            out["new_clamp_matches"] += 1
        if not old_match and not new_match:
            out["neither_matches"] += 1
    return out


def _ratio(n: int, d: int) -> float:
    return 0.0 if d == 0 else n / d


def run_hyperliquid_semantic_probe() -> dict[str, Any]:
    windows = {
        "hourly_scale_check": ("2023-09-01T00:00:00Z", "2023-09-07T23:59:59Z"),
        "early_clamp_check": ("2023-12-01T00:00:00Z", "2023-12-11T22:59:59Z"),
        "late_clamp_check": ("2023-12-11T23:00:00Z", "2023-12-22T23:59:59Z"),
    }
    fetched: dict[str, list[dict[str, Any]]] = {}
    per_asset_counts: dict[str, dict[str, int]] = {}
    for name, (start, end) in windows.items():
        all_rows: list[dict[str, Any]] = []
        per_asset_counts[name] = {}
        for coin in ("BTC", "ETH"):
            rows = _fetch_hl_window(coin, start, end)
            per_asset_counts[name][coin] = len(rows)
            all_rows.extend(rows)
            time.sleep(0.4)
        fetched[name] = all_rows

    scale_rows = fetched["hourly_scale_check"]
    scale_candidates: dict[str, dict[str, Any]] = {}
    for c in CANDIDATE_CLAMPS:
        for divisor in (1, 8):
            matches, finite = _semantic_matches(scale_rows, c, divisor)
            key = f"clamp_{c}_divisor_{divisor}"
            scale_candidates[key] = {
                "matches": matches,
                "finite_rows": finite,
                "match_ratio": _ratio(matches, finite),
            }
    best_div8 = max(v["match_ratio"] for k, v in scale_candidates.items() if k.endswith("divisor_8"))
    best_div1 = max(v["match_ratio"] for k, v in scale_candidates.items() if k.endswith("divisor_1"))
    hourly_scale_pass = best_div8 >= 0.95 and best_div8 >= best_div1 + 0.50

    early = _discriminating_clamp_counts(fetched["early_clamp_check"])
    late = _discriminating_clamp_counts(fetched["late_clamp_check"])
    early_ratio = _ratio(early["old_clamp_matches"], early["discriminating_rows"])
    late_ratio = _ratio(late["new_clamp_matches"], late["discriminating_rows"])
    clamp_transition_pass = (
        early["discriminating_rows"] >= 10
        and late["discriminating_rows"] >= 10
        and early_ratio >= 0.75
        and late_ratio >= 0.75
        and early["old_clamp_matches"] > early["new_clamp_matches"]
        and late["new_clamp_matches"] > late["old_clamp_matches"]
    )

    return {
        "classification": "SEMANTIC_PROBE_ONLY_NOT_STRATEGY_ECONOMICS",
        "fixed_windows": windows,
        "row_counts_by_asset": per_asset_counts,
        "scale_candidate_match_summary": scale_candidates,
        "detected_scale_label": "HOURLY_ONE_EIGHTH_OF_8H_FORMULA" if hourly_scale_pass else "UNRESOLVED",
        "early_clamp_discriminating_summary": early,
        "late_clamp_discriminating_summary": late,
        "early_clamp_match_ratio": early_ratio,
        "late_clamp_match_ratio": late_ratio,
        "detected_clamp_regime": "0.0003_BEFORE_2023-12-11T23Z__0.0005_AT_AND_AFTER" if clamp_transition_pass else "UNRESOLVED",
        "semantic_probe_pass": hourly_scale_pass and clamp_transition_pass,
        "raw_values_output": False,
        "cross_venue_comparison_performed": False,
    }


def _month_keys(start: str = "2023-09", end: str = "2025-12") -> list[str]:
    sy, sm = map(int, start.split("-"))
    ey, em = map(int, end.split("-"))
    out: list[str] = []
    y, m = sy, sm
    while (y, m) <= (ey, em):
        out.append(f"{y:04d}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def _http_bytes(url: str, timeout: int = 60) -> bytes | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "research-provenance-v043"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise


def _month_bounds_ms(month: str) -> tuple[int, int]:
    y, m = map(int, month.split("-"))
    start = datetime(y, m, 1, tzinfo=timezone.utc)
    ny, nm = (y + 1, 1) if m == 12 else (y, m + 1)
    end = datetime(ny, nm, 1, tzinfo=timezone.utc)
    return int(start.timestamp() * 1000), int(end.timestamp() * 1000)


def _parse_checksum(text: str) -> str:
    token = text.strip().split()[0].lower()
    _require(len(token) == 64 and all(c in "0123456789abcdef" for c in token), "invalid CHECKSUM sidecar")
    return token


def _timestamp_coverage_from_zip(raw_zip: bytes, month: str) -> dict[str, Any]:
    with zipfile.ZipFile(io.BytesIO(raw_zip)) as zf:
        names = [n for n in zf.namelist() if not n.endswith("/")]
        _require(len(names) == 1, f"{month}: unexpected zip members {names}")
        with zf.open(names[0]) as fh:
            text = io.TextIOWrapper(fh, encoding="utf-8", newline="")
            reader = csv.reader(text)
            timestamps: list[int] = []
            for row in reader:
                if not row:
                    continue
                try:
                    ts = int(row[0])
                except ValueError:
                    continue
                timestamps.append(ts)
    start, end = _month_bounds_ms(month)
    expected = set(range(start, end, 60_000))
    observed = [ts for ts in timestamps if start <= ts < end]
    observed_set = set(observed)
    missing = sorted(expected - observed_set)
    extra = sorted(observed_set - expected)
    duplicates = len(observed) - len(observed_set)
    return {
        "row_count_in_month": len(observed),
        "unique_minute_count": len(observed_set),
        "expected_minute_count": len(expected),
        "missing_minute_count": len(missing),
        "missing_open_time_ms": missing,
        "extra_off_grid_count": len(extra),
        "extra_open_time_ms": extra,
        "duplicate_open_time_count": duplicates,
        "full_month_timestamp_coverage": not missing and not extra and duplicates == 0,
    }


def run_binance_mark_timestamp_probe() -> dict[str, Any]:
    months = _month_keys()
    series: dict[str, Any] = {}
    common_full = set(months)
    for symbol in ("BTCUSDT", "ETHUSDT"):
        monthly: dict[str, Any] = {}
        full_for_symbol: set[str] = set()
        for month in months:
            filename = f"{symbol}-1m-{month}.zip"
            url = f"{BINANCE_BASE}/{symbol}/1m/{filename}"
            checksum_url = url + ".CHECKSUM"
            checksum_raw = _http_bytes(checksum_url)
            zip_raw = _http_bytes(url)
            if checksum_raw is None or zip_raw is None:
                monthly[month] = {
                    "archive_available": False,
                    "checksum_available": checksum_raw is not None,
                    "full_month_timestamp_coverage": False,
                }
                continue
            expected_hash = _parse_checksum(checksum_raw.decode("utf-8", errors="strict"))
            actual_hash = hashlib.sha256(zip_raw).hexdigest()
            _require(actual_hash == expected_hash, f"{symbol} {month}: archive checksum mismatch")
            coverage = _timestamp_coverage_from_zip(zip_raw, month)
            coverage.update({
                "archive_available": True,
                "checksum_available": True,
                "archive_sha256": actual_hash,
                "price_values_parsed": False,
            })
            monthly[month] = coverage
            if coverage["full_month_timestamp_coverage"]:
                full_for_symbol.add(month)
            time.sleep(0.05)
        common_full &= full_for_symbol
        series[symbol] = {
            "monthly": monthly,
            "full_months": sorted(full_for_symbol),
            "full_month_count": len(full_for_symbol),
        }
    return {
        "classification": "BINANCE_MARK_TIMESTAMP_PROVENANCE_ONLY",
        "dataset": "USD-M markPriceKlines 1m",
        "candidate_months": months,
        "series": series,
        "common_full_mark_months": sorted(common_full),
        "common_full_mark_month_count": len(common_full),
        "price_values_parsed": False,
        "price_values_output": False,
    }


def run() -> dict[str, Any]:
    hl = run_hyperliquid_semantic_probe()
    bn = run_binance_mark_timestamp_probe()
    return {
        "schema_version": "0.1",
        "lab_id": LAB_ID,
        "amendment_id": AMENDMENT_ID,
        "status": "PASS_PARTIAL_PREFREEZE" if hl["semantic_probe_pass"] else "FAIL_CLOSED_SEMANTICS_UNRESOLVED",
        "hyperliquid_funding_semantics": hl,
        "binance_mark_timestamp_provenance": bn,
        "gate_interpretation": {
            "G03": "PASS_SEMANTIC_COMPONENT_PENDING_V042_CADENCE_RECEIPT" if hl["semantic_probe_pass"] else "FAIL_CLOSED",
            "G04": "PARTIAL_BINANCE_MARK_AUDITED_HYPERLIQUID_ASSET_CTX_PENDING",
            "G10": "PROVISIONAL_ONLY_NOT_MATERIALIZED",
            "G12": "BLOCKED",
        },
        "locked_2026_accessed": False,
        "mexc_accessed": False,
        "authenticated_account_data_used": False,
        "exchange_mutation_used": False,
        "carry_computed": False,
        "apr_apy_computed": False,
        "pnl_computed": False,
        "signals_computed": False,
        "cross_venue_rate_comparison_computed": False,
        "price_values_output": False,
        "discovery_authorized": False,
        "trading_authorized": False,
    }


def main() -> int:
    path = Path(os.environ.get("PREFREEZE_V043_RECEIPT", "CROSS_VENUE_FUNDING_BASIS_V043_RECEIPT.json"))
    result = run()
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "hl_semantics": result["hyperliquid_funding_semantics"]["semantic_probe_pass"],
        "binance_common_full_mark_months": result["binance_mark_timestamp_provenance"]["common_full_mark_month_count"],
        "receipt": str(path),
    }, sort_keys=True))
    return 0 if result["status"].startswith("PASS") else 2


if __name__ == "__main__":
    raise SystemExit(main())
