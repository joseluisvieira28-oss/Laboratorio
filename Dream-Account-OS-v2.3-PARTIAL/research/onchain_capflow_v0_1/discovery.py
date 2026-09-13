#!/usr/bin/env python3
"""
ONCHAIN-CAPFLOW-001 V0.1A — frozen Discovery implementation.

This program computes outcomes for Discovery 2021–2024 only.
It is intentionally offline: it reads only the byte-identical audited raw snapshot.
It cannot download data and it rejects any input-manifest mismatch.

2025 holdout: LOCKED.
2026+: LOCKED.
No live trading. No exchange mutation.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import math
import random
import statistics
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Sequence

UTC = dt.timezone.utc
LAB_ID = "ONCHAIN-CAPFLOW-001"
VERSION = "V0.1A"

PROTOCOL_SHA256 = "1c6c66b7188694bcc2d62cb83ee050a023fba7f97388bc87933ed668d3392b65"
CONTRACT_SHA256 = "564110a73e013031e08f9b86af7c130e0b6247a5489cce9f540f7bc5b4c0a1c4"
RAW_MANIFEST_SHA256 = "a45ceb4248c9438dfafc6580627fc399fccfafb0ec208cb87024412ca8f08794"

WARMUP_START = dt.date(2020, 1, 1)
DISCOVERY_START = dt.date(2021, 1, 1)
DISCOVERY_END = dt.date(2024, 12, 31)
HOLDOUT_START = dt.date(2025, 1, 1)

TRAILING_WEEKS = 52
LONG_THRESHOLD = 0.75
SHORT_THRESHOLD = 0.25
BASE_COST = 0.001
STRESS_COST = 0.002

NW_LAG = 4
BOOTSTRAP_BLOCK = 4
BOOTSTRAP_RESAMPLES = 10_000
BOOTSTRAP_SEED = 20260913

YEAR_DOMINANCE_MAX = 0.60
SINGLE_WEEK_DOMINANCE_MAX = 0.25
STRESS_SPREAD_MIN = -0.001


class DiscoveryBlocked(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_json_sha256(obj: Any) -> str:
    payload = json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def safe_child(root: Path, relative_path: str) -> Path:
    candidate = (root / relative_path).resolve()
    root_resolved = root.resolve()
    try:
        candidate.relative_to(root_resolved)
    except ValueError as exc:
        raise DiscoveryBlocked(
            f"manifest path escapes data root: {relative_path}"
        ) from exc
    return candidate


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise DiscoveryBlocked(f"cannot read JSON {path}: {exc}") from exc


def verify_contract(contract_path: Path) -> dict[str, Any]:
    contract = load_json(contract_path)
    actual = canonical_json_sha256(contract)
    if actual != CONTRACT_SHA256:
        raise DiscoveryBlocked(
            f"Discovery contract hash mismatch: expected {CONTRACT_SHA256}, got {actual}"
        )
    if contract.get("scientific_protocol_sha256") != PROTOCOL_SHA256:
        raise DiscoveryBlocked("Discovery contract protocol hash mismatch")
    if contract.get("required_raw_manifest_sha256") != RAW_MANIFEST_SHA256:
        raise DiscoveryBlocked("Discovery contract raw-manifest authority mismatch")
    if contract.get("holdout_2025_access") is not False:
        raise DiscoveryBlocked("contract does not keep 2025 holdout closed")
    if contract.get("locked_2026_access") is not False:
        raise DiscoveryBlocked("contract does not keep 2026 closed")
    return contract


def verify_snapshot(data_root: Path) -> dict[str, Any]:
    manifest_path = data_root / "raw_manifest.json"
    if not manifest_path.exists():
        raise DiscoveryBlocked("raw_manifest.json missing")

    actual_manifest_hash = sha256_file(manifest_path)
    if actual_manifest_hash != RAW_MANIFEST_SHA256:
        raise DiscoveryBlocked(
            "raw snapshot identity mismatch: "
            f"expected {RAW_MANIFEST_SHA256}, got {actual_manifest_hash}"
        )

    manifest = load_json(manifest_path)
    if manifest.get("protocol_sha256") != PROTOCOL_SHA256:
        raise DiscoveryBlocked("raw manifest protocol hash mismatch")
    if manifest.get("holdout_accessed") is not False:
        raise DiscoveryBlocked("raw manifest says holdout was accessed")
    if manifest.get("locked_2026_accessed") is not False:
        raise DiscoveryBlocked("raw manifest says 2026 was accessed")
    if manifest.get("allowed_period") != "2020-01-01/2024-12-31":
        raise DiscoveryBlocked("unexpected raw-manifest allowed period")

    entries = manifest.get("entries")
    if not isinstance(entries, list) or len(entries) != 121:
        raise DiscoveryBlocked(
            f"expected exactly 121 raw entries, got "
            f"{len(entries) if isinstance(entries, list) else 'non-list'}"
        )

    for entry in entries:
        if not isinstance(entry, dict):
            raise DiscoveryBlocked("malformed raw-manifest entry")
        rel = entry.get("relative_path")
        expected = entry.get("sha256")
        if not isinstance(rel, str) or not isinstance(expected, str):
            raise DiscoveryBlocked("raw-manifest entry missing path/hash")
        path = safe_child(data_root, rel)
        if not path.exists():
            raise DiscoveryBlocked(f"raw file missing: {rel}")
        actual = sha256_file(path)
        if actual != expected:
            raise DiscoveryBlocked(
                f"raw file hash mismatch: {rel}: expected {expected}, got {actual}"
            )

    gate = load_json(data_root / "data_gate_status.json")
    if gate.get("status") != "PASS":
        raise DiscoveryBlocked("data source gate is not PASS")
    if gate.get("holdout_accessed") is not False:
        raise DiscoveryBlocked("data source gate says holdout accessed")
    if gate.get("locked_2026_accessed") is not False:
        raise DiscoveryBlocked("data source gate says 2026 accessed")

    audit = load_json(data_root / "data_audit_report.json")
    if audit.get("status") != "PASS":
        raise DiscoveryBlocked("data audit is not PASS")
    if audit.get("outcome_metrics_computed") is not False:
        raise DiscoveryBlocked("data audit unexpectedly computed outcomes")
    if audit.get("holdout_accessed") is not False:
        raise DiscoveryBlocked("data audit says holdout accessed")
    if audit.get("locked_2026_accessed") is not False:
        raise DiscoveryBlocked("data audit says 2026 accessed")

    return manifest


def parse_iso_date(value: str) -> dt.date:
    text = value.replace("Z", "+00:00")
    parsed = dt.datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    parsed = parsed.astimezone(UTC)
    if parsed.time() != dt.time(0, 0):
        raise DiscoveryBlocked(f"non-midnight Coin Metrics timestamp: {value}")
    return parsed.date()


def parse_stablecoin_supply(data_root: Path) -> dict[dt.date, float]:
    pages = sorted(
        (data_root / "raw/coinmetrics").glob("stablecoin_supply_page_*.json")
    )
    if not pages:
        raise DiscoveryBlocked("no Coin Metrics pages found")

    by_asset: dict[str, dict[dt.date, float]] = {"usdt": {}, "usdc": {}}
    for page in pages:
        obj = load_json(page)
        rows = obj.get("data")
        if not isinstance(rows, list):
            raise DiscoveryBlocked(f"{page}: missing data[]")
        for row in rows:
            if not isinstance(row, dict):
                continue
            asset = str(row.get("asset", "")).lower()
            if asset not in by_asset:
                continue
            t_raw = row.get("time")
            v_raw = row.get("SplyCur")
            if not isinstance(t_raw, str) or v_raw is None:
                raise DiscoveryBlocked(f"{page}: malformed {asset} supply row")
            date = parse_iso_date(t_raw)
            if date >= HOLDOUT_START:
                raise DiscoveryBlocked(f"holdout supply timestamp encountered: {date}")
            try:
                value = float(v_raw)
            except Exception as exc:
                raise DiscoveryBlocked(
                    f"{page}: invalid {asset} supply value {v_raw!r}"
                ) from exc
            if not math.isfinite(value) or value <= 0:
                raise DiscoveryBlocked(f"{page}: non-positive {asset} supply")
            if date in by_asset[asset]:
                raise DiscoveryBlocked(f"duplicate {asset} supply date {date}")
            by_asset[asset][date] = value

    combined: dict[dt.date, float] = {}
    all_dates = sorted(set(by_asset["usdt"]) | set(by_asset["usdc"]))
    for date in all_dates:
        if date not in by_asset["usdt"] or date not in by_asset["usdc"]:
            raise DiscoveryBlocked(f"supply asset date mismatch at {date}")
        combined[date] = by_asset["usdt"][date] + by_asset["usdc"][date]
    return combined


def parse_binance_zip(path: Path) -> list[tuple[dt.date, float]]:
    out: list[tuple[dt.date, float]] = []
    with zipfile.ZipFile(path) as zf:
        names = [name for name in zf.namelist() if not name.endswith("/")]
        if len(names) != 1:
            raise DiscoveryBlocked(
                f"{path}: expected one CSV member, found {len(names)}"
            )
        with zf.open(names[0]) as raw:
            text = io.TextIOWrapper(raw, encoding="utf-8", newline="")
            reader = csv.reader(text)
            for row in reader:
                if not row:
                    continue
                try:
                    open_ms = int(row[0])
                    open_px = float(row[1])
                except (ValueError, IndexError):
                    if row and row[0].lower().startswith("open"):
                        continue
                    raise DiscoveryBlocked(f"{path}: malformed Binance row")
                stamp = dt.datetime.fromtimestamp(open_ms / 1000.0, tz=UTC)
                if stamp.time() != dt.time(0, 0):
                    raise DiscoveryBlocked(
                        f"{path}: non-midnight daily open {stamp.isoformat()}"
                    )
                if stamp.date() >= HOLDOUT_START:
                    raise DiscoveryBlocked(
                        f"{path}: holdout price timestamp encountered {stamp.date()}"
                    )
                if not math.isfinite(open_px) or open_px <= 0:
                    raise DiscoveryBlocked(f"{path}: invalid open price")
                out.append((stamp.date(), open_px))
    return out


def parse_price_series(data_root: Path, symbol: str) -> dict[dt.date, float]:
    files = sorted(
        (data_root / f"raw/binance/{symbol}").glob(f"{symbol}-1d-*.zip")
    )
    if len(files) != 60:
        raise DiscoveryBlocked(
            f"{symbol}: expected 60 monthly archives, got {len(files)}"
        )

    out: dict[dt.date, float] = {}
    for path in files:
        for date, price in parse_binance_zip(path):
            if date in out:
                raise DiscoveryBlocked(f"{symbol}: duplicate daily open {date}")
            out[date] = price
    return out


def saturday_dates(start: dt.date, end: dt.date) -> Iterable[dt.date]:
    date = start
    while date.weekday() != 5:
        date += dt.timedelta(days=1)
    while date <= end:
        yield date
        date += dt.timedelta(days=7)


def build_growth_series(supply: dict[dt.date, float]) -> dict[dt.date, float]:
    growth: dict[dt.date, float] = {}
    saturdays = list(saturday_dates(WARMUP_START, DISCOVERY_END))
    for sat in saturdays:
        prior = sat - dt.timedelta(days=7)
        if prior < WARMUP_START:
            continue
        if sat not in supply or prior not in supply:
            raise DiscoveryBlocked(
                f"missing exact supply date required for weekly signal: {sat} or {prior}"
            )
        ratio = supply[sat] / supply[prior]
        if not math.isfinite(ratio) or ratio <= 0:
            raise DiscoveryBlocked(f"invalid supply ratio at {sat}")
        growth[sat] = math.log(ratio)
    return growth


def percentile_midrank(current: float, history: Sequence[float]) -> float:
    if len(history) != TRAILING_WEEKS:
        raise DiscoveryBlocked(
            f"percentile history must have {TRAILING_WEEKS} values"
        )
    less = sum(1 for value in history if value < current)
    equal = sum(1 for value in history if value == current)
    return (less + 0.5 * equal) / TRAILING_WEEKS


def classify(percentile: float) -> str:
    if percentile >= LONG_THRESHOLD:
        return "LONG"
    if percentile <= SHORT_THRESHOLD:
        return "SHORT"
    return "FLAT"


def build_weekly_records(
    growth: dict[dt.date, float],
    btc: dict[dt.date, float],
    eth: dict[dt.date, float],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []

    for sat in saturday_dates(WARMUP_START, DISCOVERY_END):
        if sat not in growth:
            continue

        prior_sats = [
            sat - dt.timedelta(days=7 * k)
            for k in range(TRAILING_WEEKS, 0, -1)
        ]
        if any(prior not in growth for prior in prior_sats):
            continue

        history = [growth[prior] for prior in prior_sats]
        pct = percentile_midrank(growth[sat], history)
        state = classify(pct)

        entry = sat + dt.timedelta(days=2)
        exit_ = entry + dt.timedelta(days=7)

        if entry < DISCOVERY_START:
            continue
        if exit_ > DISCOVERY_END:
            # Deliberately exclude before any price lookup. 2025 remains unopened.
            continue
        if entry >= HOLDOUT_START or exit_ >= HOLDOUT_START:
            raise DiscoveryBlocked("holdout boundary crossed before price lookup")

        for symbol, prices in (("BTCUSDT", btc), ("ETHUSDT", eth)):
            if entry not in prices or exit_ not in prices:
                raise DiscoveryBlocked(
                    f"{symbol}: missing exact Monday open {entry} or {exit_}"
                )

        btc_return = btc[exit_] / btc[entry] - 1.0
        eth_return = eth[exit_] / eth[entry] - 1.0

        records.append(
            {
                "signal_saturday": sat,
                "entry_monday": entry,
                "exit_monday": exit_,
                "growth": growth[sat],
                "percentile": pct,
                "state": state,
                "btc_return": btc_return,
                "eth_return": eth_return,
            }
        )

    if not records:
        raise DiscoveryBlocked("no Discovery records were generated")
    if records[0]["entry_monday"] < DISCOVERY_START:
        raise DiscoveryBlocked("Discovery begins before 2021")
    if records[-1]["exit_monday"] > DISCOVERY_END:
        raise DiscoveryBlocked("Discovery touches 2025")
    return records


def mean(values: Sequence[float]) -> float:
    if not values:
        return float("nan")
    return statistics.fmean(values)


def median(values: Sequence[float]) -> float:
    if not values:
        return float("nan")
    return statistics.median(values)


def top_bottom_spread(
    records: Sequence[dict[str, Any]],
    asset_key: str,
    cost_per_leg: float,
) -> float:
    top = [float(r[asset_key]) for r in records if r["state"] == "LONG"]
    bottom = [float(r[asset_key]) for r in records if r["state"] == "SHORT"]
    if not top or not bottom:
        return float("nan")
    return mean(top) - mean(bottom) - 2.0 * cost_per_leg


def directional_net_returns(
    records: Sequence[dict[str, Any]],
    asset_key: str,
    cost: float,
) -> list[tuple[dt.date, float]]:
    out: list[tuple[dt.date, float]] = []
    for row in records:
        state = row["state"]
        if state == "FLAT":
            continue
        raw = float(row[asset_key])
        directional = raw if state == "LONG" else -raw
        out.append((row["entry_monday"], directional - cost))
    return out


def profit_factor(values: Sequence[float]) -> float | str | None:
    pos = sum(v for v in values if v > 0)
    neg = -sum(v for v in values if v < 0)
    if neg == 0:
        return "Infinity" if pos > 0 else None
    return pos / neg


def max_drawdown(values: Sequence[float]) -> float:
    equity = 1.0
    peak = 1.0
    worst = 0.0
    for value in values:
        equity *= 1.0 + value
        if equity > peak:
            peak = equity
        if peak != 0:
            drawdown = equity / peak - 1.0
            worst = min(worst, drawdown)
    return worst


def newey_west_tstat(values: Sequence[float], lag: int) -> float:
    n = len(values)
    if n < 3:
        return float("nan")
    xbar = mean(values)
    centered = [x - xbar for x in values]
    gamma0 = sum(x * x for x in centered) / n
    long_run = gamma0
    max_lag = min(lag, n - 1)
    for ell in range(1, max_lag + 1):
        gamma = (
            sum(centered[t] * centered[t - ell] for t in range(ell, n)) / n
        )
        weight = 1.0 - ell / (lag + 1.0)
        long_run += 2.0 * weight * gamma
    if long_run <= 0:
        return float("nan")
    se_mean = math.sqrt(long_run / n)
    if se_mean == 0:
        return float("nan")
    return xbar / se_mean


def quantile(values: Sequence[float], q: float) -> float:
    if not values:
        return float("nan")
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    pos = q * (len(ordered) - 1)
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return ordered[lo]
    frac = pos - lo
    return ordered[lo] * (1 - frac) + ordered[hi] * frac


def circular_block_bootstrap_spread(
    records: Sequence[dict[str, Any]],
    asset_key: str,
    cost_per_leg: float,
) -> dict[str, Any]:
    n = len(records)
    if n < BOOTSTRAP_BLOCK:
        return {"samples": 0, "ci95": [None, None]}

    rng = random.Random(BOOTSTRAP_SEED)
    samples: list[float] = []
    for _ in range(BOOTSTRAP_RESAMPLES):
        resampled: list[dict[str, Any]] = []
        while len(resampled) < n:
            start = rng.randrange(n)
            for offset in range(BOOTSTRAP_BLOCK):
                resampled.append(records[(start + offset) % n])
                if len(resampled) == n:
                    break
        spread = top_bottom_spread(resampled, asset_key, cost_per_leg)
        if math.isfinite(spread):
            samples.append(spread)

    if len(samples) != BOOTSTRAP_RESAMPLES:
        raise DiscoveryBlocked(
            "bootstrap produced an invalid sample without both LONG and SHORT buckets"
        )
    return {
        "samples": len(samples),
        "seed": BOOTSTRAP_SEED,
        "block_length_weeks": BOOTSTRAP_BLOCK,
        "ci95": [quantile(samples, 0.025), quantile(samples, 0.975)],
    }


def dominance_metrics(
    active: Sequence[tuple[dt.date, float]],
) -> dict[str, Any]:
    yearly: dict[int, float] = defaultdict(float)
    for date, value in active:
        yearly[date.year] += value

    positive_years = [value for value in yearly.values() if value > 0]
    positive_year_total = sum(positive_years)
    year_ratio = (
        max(positive_years) / positive_year_total
        if positive_year_total > 0
        else float("inf")
    )

    positive_weeks = [value for _, value in active if value > 0]
    positive_week_total = sum(positive_weeks)
    week_ratio = (
        max(positive_weeks) / positive_week_total
        if positive_week_total > 0
        else float("inf")
    )

    return {
        "yearly_cumulative_base_net_directional_pnl": {
            str(year): yearly.get(year, 0.0)
            for year in range(2021, 2025)
        },
        "year_dominance_ratio": year_ratio,
        "single_week_dominance_ratio": week_ratio,
    }


def annual_spreads(
    records: Sequence[dict[str, Any]],
    asset_key: str,
) -> dict[str, float | None]:
    out: dict[str, float | None] = {}
    for year in range(2021, 2025):
        subset = [r for r in records if r["entry_monday"].year == year]
        value = top_bottom_spread(subset, asset_key, BASE_COST)
        out[str(year)] = value if math.isfinite(value) else None
    return out


def asset_summary(
    records: Sequence[dict[str, Any]],
    asset_key: str,
    include_bootstrap: bool,
) -> dict[str, Any]:
    gross_spread = top_bottom_spread(records, asset_key, 0.0)
    base_spread = top_bottom_spread(records, asset_key, BASE_COST)
    stress_spread = top_bottom_spread(records, asset_key, STRESS_COST)

    active_base = directional_net_returns(records, asset_key, BASE_COST)
    active_stress = directional_net_returns(records, asset_key, STRESS_COST)
    base_values = [value for _, value in active_base]
    stress_values = [value for _, value in active_stress]

    if not base_values:
        raise DiscoveryBlocked(f"{asset_key}: no active trades")

    annual = annual_spreads(records, asset_key)
    dominance = dominance_metrics(active_base)
    summary: dict[str, Any] = {
        "top_minus_bottom_gross_spread": gross_spread,
        "top_minus_bottom_base_net_spread": base_spread,
        "top_minus_bottom_stress_net_spread": stress_spread,
        "active_trade_count": len(base_values),
        "mean_base_net_directional_return": mean(base_values),
        "median_base_net_directional_return": median(base_values),
        "mean_stress_net_directional_return": mean(stress_values),
        "profit_factor_base": profit_factor(base_values),
        "max_drawdown_base": max_drawdown(base_values),
        "newey_west_tstat_base_mean": newey_west_tstat(base_values, NW_LAG),
        "newey_west_lag": NW_LAG,
        "win_rate_base": sum(v > 0 for v in base_values) / len(base_values),
        "annual_base_net_spreads": annual,
        **dominance,
    }
    if include_bootstrap:
        summary["block_bootstrap_base_spread"] = circular_block_bootstrap_spread(
            records, asset_key, BASE_COST
        )
    return summary


def finite_or_none(value: Any) -> Any:
    if isinstance(value, float):
        if math.isfinite(value):
            return value
        if value == float("inf"):
            return "Infinity"
        if value == float("-inf"):
            return "-Infinity"
        return None
    if isinstance(value, dict):
        return {k: finite_or_none(v) for k, v in value.items()}
    if isinstance(value, list):
        return [finite_or_none(v) for v in value]
    return value


def write_weekly_csv(path: Path, records: Sequence[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "signal_saturday",
        "entry_monday",
        "exit_monday",
        "growth",
        "percentile",
        "state",
        "btc_return",
        "eth_return",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in records:
            writer.writerow(
                {
                    key: row[key].isoformat()
                    if isinstance(row[key], dt.date)
                    else row[key]
                    for key in fields
                }
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="./data")
    parser.add_argument("--output", default="./discovery_output")
    parser.add_argument(
        "--i-understand-this-computes-outcomes",
        action="store_true",
        help="Required explicit guardrail. This program computes Discovery outcomes.",
    )
    args = parser.parse_args()

    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    report_path = output / "discovery_report.json"

    if not args.i_understand_this_computes_outcomes:
        report_path.write_text(
            json.dumps(
                {
                    "lab_id": LAB_ID,
                    "version": VERSION,
                    "status": "DISCOVERY_NOT_AUTHORIZED_BY_CLI_GUARD",
                    "holdout_2025_accessed": False,
                    "locked_2026_accessed": False,
                },
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        print("STOP: explicit Discovery-outcome guard flag not supplied.")
        return 5

    data_root = Path(args.data).resolve()
    contract_path = Path(__file__).with_name("DISCOVERY_CONTRACT.json")

    try:
        verify_contract(contract_path)
        manifest = verify_snapshot(data_root)

        supply = parse_stablecoin_supply(data_root)
        btc = parse_price_series(data_root, "BTCUSDT")
        eth = parse_price_series(data_root, "ETHUSDT")
        growth = build_growth_series(supply)
        records = build_weekly_records(growth, btc, eth)

        state_counts = Counter(row["state"] for row in records)
        if state_counts["LONG"] == 0 or state_counts["SHORT"] == 0:
            raise DiscoveryBlocked("Discovery has no LONG or no SHORT bucket")

        btc_summary = asset_summary(
            records, "btc_return", include_bootstrap=True
        )
        eth_summary = asset_summary(
            records, "eth_return", include_bootstrap=False
        )

        annual_values = btc_summary["annual_base_net_spreads"]
        year_nonnegative = sum(
            value is not None and value >= 0
            for value in annual_values.values()
        )

        gates = {
            "raw_snapshot_hash_exact": True,
            "base_net_top_bottom_spread_gt_0":
                btc_summary["top_minus_bottom_base_net_spread"] > 0,
            "at_least_3_of_4_years_non_negative_base_net_spread":
                year_nonnegative >= 3,
            "year_dominance_le_0_60":
                btc_summary["year_dominance_ratio"] <= YEAR_DOMINANCE_MAX,
            "single_week_dominance_le_0_25":
                btc_summary["single_week_dominance_ratio"]
                <= SINGLE_WEEK_DOMINANCE_MAX,
            "stress_net_top_bottom_spread_ge_minus_10bps":
                btc_summary["top_minus_bottom_stress_net_spread"]
                >= STRESS_SPREAD_MIN,
            "provenance_timestamp_leakage_failure_absent": True,
            "holdout_2025_unopened": True,
            "locked_2026_unopened": True,
        }
        mve0_pass = all(gates.values())

        report = {
            "lab_id": LAB_ID,
            "version": VERSION,
            "stage": "DISCOVERY_2021_2024",
            "status": "MVE0_PASS" if mve0_pass else "MVE0_FAIL",
            "scientific_protocol_sha256": PROTOCOL_SHA256,
            "discovery_contract_sha256": CONTRACT_SHA256,
            "raw_manifest_sha256": RAW_MANIFEST_SHA256,
            "raw_entry_count": len(manifest["entries"]),
            "period": {
                "discovery_start": DISCOVERY_START.isoformat(),
                "discovery_end": DISCOVERY_END.isoformat(),
                "first_entry": records[0]["entry_monday"].isoformat(),
                "last_exit": records[-1]["exit_monday"].isoformat(),
            },
            "weekly_record_count": len(records),
            "state_counts": dict(state_counts),
            "turnover_active_week_fraction":
                (state_counts["LONG"] + state_counts["SHORT"]) / len(records),
            "btc_primary": btc_summary,
            "eth_confirmation_only": eth_summary,
            "mve0_gates": gates,
            "mve0_pass": mve0_pass,
            "holdout_2025_accessed": False,
            "locked_2026_accessed": False,
            "live_trading_authorized": False,
            "exchange_mutation_authorized": False,
            "next_step": (
                "Write Discovery closeout and freeze decision in Drive before "
                "any 2025 holdout access."
            ),
        }

        write_weekly_csv(output / "weekly_records.csv", records)
        report = finite_or_none(report)
        report_path.write_text(
            json.dumps(report, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        print(f"{report['status']}: wrote {report_path}")
        print("2025 holdout remains unopened. 2026 remains locked.")
        return 0

    except Exception as exc:
        blocked = {
            "lab_id": LAB_ID,
            "version": VERSION,
            "stage": "DISCOVERY_2021_2024",
            "status": "DISCOVERY_BLOCKED",
            "error": str(exc),
            "holdout_2025_accessed": False,
            "locked_2026_accessed": False,
            "live_trading_authorized": False,
            "exchange_mutation_authorized": False,
        }
        report_path.write_text(
            json.dumps(blocked, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        print(f"DISCOVERY_BLOCKED: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
