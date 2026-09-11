from __future__ import annotations

"""Post-hoc H03 microstructure autopsy on the already-opened Binance corpus.

This module is hypothesis-generation only. It cannot reclassify or rescue H03,
unlock any holdout, access a network, or submit anything to an exchange.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import csv
import hashlib
from io import BytesIO, TextIOWrapper
import json
from math import isfinite
from pathlib import Path
import random
from statistics import mean, median
import sys
from typing import Any
import zipfile

from research.phase_b_h03_binance_daily_manifest_v01 import (
    EXPECTED_ARCHIVE_COUNT,
    expected_h03_daily_objects,
)
from research.phase_b_h03_binance_offline_adapter_v01 import (
    EXPECTED_FIELDS,
    TIMEFRAME_MS,
    adapt_binance_daily_archive_bytes,
)
from research.phase_b_h03_discovery_runner_v01 import BASE_COSTS, PARAMETERS
from research.phase_b_h03_research_evaluator_v01 import evaluate_h03_universe


FREEZE_PATH = Path(__file__).with_name(
    "PHASE_B_H03_MICROSTRUCTURE_POSTMORTEM_FREEZE_V0.1.json"
)
EXPECTED_FREEZE_FINGERPRINT = (
    "192ff38c80df052520969e801de88433dc98b7a1dba31d6cd32dccc7644cce61"
)
EXPECTED_H03_ARCHIVE_SET_FINGERPRINT = (
    "82f72e6c6b480579296c7c7e996e627c0d0b0971dd6b52700eadb5e682e46040"
)
EXPECTED_H03_DISCOVERY_RECEIPT_FINGERPRINT = (
    "14a4bc14a6d95f9c812d697a41fae1079fa222267fe8b650ff99ff93b9edb299"
)
EXPECTED_H03_RESOLVED_TRADES = 151
LOOKBACK_BARS = 96
BOOTSTRAP_REPETITIONS = 5000
BOOTSTRAP_SEED = 230911
BOOTSTRAP_CONFIDENCE = 0.95

NETWORK_ACCESS_PERFORMED = False
EXCHANGE_MUTATION_PERFORMED = False
LIVE_TRADING_PERFORMED = False
MEXC_VALIDATION_2025_ACCESSED = False
HOLDOUT_2026_ACCESSED = False


@dataclass(frozen=True)
class FlowBar:
    open_time: int
    volume: float
    number_of_trades: int
    taker_buy_base_volume: float

    @property
    def flow_imbalance(self) -> float:
        if self.volume <= 0:
            raise ValueError("flow imbalance undefined for zero volume")
        value = (2.0 * self.taker_buy_base_volume - self.volume) / self.volume
        if not isfinite(value) or value < -1.000000000001 or value > 1.000000000001:
            raise ValueError("invalid taker-flow imbalance")
        return max(-1.0, min(1.0, value))

    @property
    def avg_trade_size(self) -> float:
        if self.number_of_trades <= 0:
            raise ValueError("average trade size undefined for non-positive trade count")
        return self.volume / self.number_of_trades


def _canonical_hash(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
    ).hexdigest()


def _load_freeze() -> dict[str, Any]:
    raw = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    supplied = raw.get("fingerprint")
    unsigned = dict(raw)
    unsigned.pop("fingerprint", None)
    recomputed = _canonical_hash(unsigned)
    if supplied != EXPECTED_FREEZE_FINGERPRINT or recomputed != supplied:
        raise PermissionError("microstructure postmortem freeze fingerprint mismatch")
    if raw.get("status") != "FROZEN_POSTHOC_HYPOTHESIS_GENERATION_ONLY":
        raise PermissionError("postmortem freeze status mismatch")
    data = raw.get("data_contract") or {}
    required_false = (
        "new_market_period_authorized",
        "mexc_2025_09_through_2025_12_authorized",
        "holdout_2026_authorized",
    )
    if not data.get("same_h03_corpus_only"):
        raise PermissionError("same-corpus-only guard is not active")
    if not data.get("reacquisition_for_reproducible_postmortem_authorized"):
        raise PermissionError("same-corpus reacquisition is not authorized")
    if any(data.get(key) is not False for key in required_false):
        raise PermissionError("holdout/new-period guard drift")
    governance = raw.get("governance") or {}
    for key in (
        "live_trading_authorized",
        "exchange_mutation_authorized",
        "main_merge_authorized",
        "render_deploy_authorized",
    ):
        if governance.get(key) is not False:
            raise PermissionError(f"governance guard drift: {key}")
    return raw


def _parse_flow_rows(archive_bytes: bytes, archive_filename: str) -> tuple[FlowBar, ...]:
    expected_member = archive_filename[:-4] + ".csv"
    rows: list[FlowBar] = []
    with zipfile.ZipFile(BytesIO(archive_bytes)) as zf:
        infos = zf.infolist()
        if len(infos) != 1 or infos[0].filename != expected_member:
            raise ValueError("unexpected ZIP member set in flow parser")
        with zf.open(infos[0], "r") as binary:
            reader = csv.reader(TextIOWrapper(binary, encoding="utf-8-sig", newline=""))
            first_data_seen = False
            for raw in reader:
                if not raw or all(not cell.strip() for cell in raw):
                    continue
                if not first_data_seen:
                    normalized = tuple(
                        cell.strip().lower().replace(" ", "_") for cell in raw
                    )
                    expected_header = (
                        "open_time", "open", "high", "low", "close", "volume",
                        "close_time", "quote_asset_volume", "number_of_trades",
                        "taker_buy_base_asset_volume",
                        "taker_buy_quote_asset_volume", "ignore",
                    )
                    if normalized == expected_header:
                        first_data_seen = True
                        continue
                first_data_seen = True
                if len(raw) != EXPECTED_FIELDS:
                    raise ValueError("malformed Binance kline field count")
                open_time = int(raw[0])
                volume = float(raw[5])
                number_of_trades = int(raw[8])
                taker_buy_base = float(raw[9])
                if (
                    not isfinite(volume)
                    or not isfinite(taker_buy_base)
                    or volume < 0
                    or number_of_trades < 0
                    or taker_buy_base < -1e-12
                    or taker_buy_base > volume + max(1e-12, abs(volume) * 1e-10)
                ):
                    raise ValueError("invalid Binance trade-flow fields")
                rows.append(
                    FlowBar(
                        open_time=open_time,
                        volume=volume,
                        number_of_trades=number_of_trades,
                        taker_buy_base_volume=taker_buy_base,
                    )
                )
    return tuple(rows)


def _safe_ratio(value: float, baseline: float) -> float:
    if baseline <= 0 or not isfinite(baseline):
        raise ValueError("shock baseline must be positive and finite")
    out = value / baseline
    if not isfinite(out):
        raise ValueError("non-finite shock")
    return out


def _feature_bundle(
    flow_by_time: dict[int, FlowBar],
    sorted_times: list[int],
    time_to_index: dict[int, int],
    target_time: int,
) -> dict[str, float]:
    if target_time not in flow_by_time or target_time not in time_to_index:
        raise ValueError("target flow bar missing")
    idx = time_to_index[target_time]
    if idx < LOOKBACK_BARS:
        raise ValueError("insufficient flow history for frozen 96-bar baseline")
    prior_times = sorted_times[idx - LOOKBACK_BARS : idx]
    expected_start = target_time - LOOKBACK_BARS * TIMEFRAME_MS
    if (
        prior_times[0] != expected_start
        or prior_times[-1] != target_time - TIMEFRAME_MS
        or any(
            right - left != TIMEFRAME_MS
            for left, right in zip(prior_times, prior_times[1:])
        )
    ):
        raise ValueError("96-bar flow baseline is not contiguous")
    target = flow_by_time[target_time]
    prior = [flow_by_time[t] for t in prior_times]
    if target.volume <= 0 or target.number_of_trades <= 0:
        raise ValueError("primary target bar has zero activity")
    if any(bar.volume <= 0 or bar.number_of_trades <= 0 for bar in prior):
        raise ValueError("96-bar flow baseline contains zero activity")
    med_volume = median(bar.volume for bar in prior)
    med_trades = median(bar.number_of_trades for bar in prior)
    med_avg_size = median(bar.avg_trade_size for bar in prior)
    return {
        "flow_imbalance": target.flow_imbalance,
        "volume_shock": _safe_ratio(target.volume, med_volume),
        "trade_count_shock": _safe_ratio(float(target.number_of_trades), float(med_trades)),
        "avg_trade_size_shock": _safe_ratio(target.avg_trade_size, med_avg_size),
    }


def _quantile(values: list[float], q: float) -> float:
    if not values:
        raise ValueError("quantile on empty values")
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    pos = q * (len(ordered) - 1)
    lo = int(pos)
    hi = min(lo + 1, len(ordered) - 1)
    frac = pos - lo
    return ordered[lo] * (1.0 - frac) + ordered[hi] * frac


def _rate_difference(rows: list[dict[str, Any]]) -> float | None:
    persistent = [row for row in rows if row["flow_persistent"]]
    other = [row for row in rows if not row["flow_persistent"]]
    if not persistent or not other:
        return None
    return (
        mean(float(row["tp1_reached"]) for row in persistent)
        - mean(float(row["tp1_reached"]) for row in other)
    )


def _day_block_bootstrap(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_day: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_day.setdefault(row["entry_day_utc"], []).append(row)
    days = sorted(by_day)
    point = _rate_difference(rows)
    if point is None or not days:
        return {
            "method": "UTC_CALENDAR_DAY_BLOCK_BOOTSTRAP_OF_TP1_RATE_DIFFERENCE",
            "repetitions": BOOTSTRAP_REPETITIONS,
            "valid_repetitions": 0,
            "seed": BOOTSTRAP_SEED,
            "confidence": BOOTSTRAP_CONFIDENCE,
            "point_estimate": point,
            "lower": None,
            "upper": None,
        }
    rng = random.Random(BOOTSTRAP_SEED)
    draws: list[float] = []
    for _ in range(BOOTSTRAP_REPETITIONS):
        sample: list[dict[str, Any]] = []
        for _ in range(len(days)):
            sample.extend(by_day[rng.choice(days)])
        diff = _rate_difference(sample)
        if diff is not None:
            draws.append(diff)
    alpha = 1.0 - BOOTSTRAP_CONFIDENCE
    return {
        "method": "UTC_CALENDAR_DAY_BLOCK_BOOTSTRAP_OF_TP1_RATE_DIFFERENCE",
        "repetitions": BOOTSTRAP_REPETITIONS,
        "valid_repetitions": len(draws),
        "sample_days": len(days),
        "seed": BOOTSTRAP_SEED,
        "confidence": BOOTSTRAP_CONFIDENCE,
        "point_estimate": point,
        "lower": _quantile(draws, alpha / 2.0) if draws else None,
        "upper": _quantile(draws, 1.0 - alpha / 2.0) if draws else None,
    }


def _odds_ratio(rows: list[dict[str, Any]]) -> dict[str, Any]:
    a = sum(row["flow_persistent"] and row["tp1_reached"] for row in rows)
    b = sum(row["flow_persistent"] and not row["tp1_reached"] for row in rows)
    c = sum((not row["flow_persistent"]) and row["tp1_reached"] for row in rows)
    d = sum((not row["flow_persistent"]) and (not row["tp1_reached"]) for row in rows)
    corrected = 0 in (a, b, c, d)
    if corrected:
        odds = ((a + 0.5) * (d + 0.5)) / ((b + 0.5) * (c + 0.5))
    else:
        odds = (a * d) / (b * c)
    return {
        "tp1_and_persistent": a,
        "failed_and_persistent": b,
        "tp1_and_nonpersistent": c,
        "failed_and_nonpersistent": d,
        "odds_ratio": odds,
        "haldane_anscombe_correction_used": corrected,
    }


def _group_summary(rows: list[dict[str, Any]], field: str) -> dict[str, Any]:
    tp1 = [float(row[field]) for row in rows if row["tp1_reached"]]
    failed = [float(row[field]) for row in rows if not row["tp1_reached"]]
    return {
        "tp1_reached": {
            "n": len(tp1),
            "mean": mean(tp1) if tp1 else None,
            "median": median(tp1) if tp1 else None,
        },
        "tp1_not_reached": {
            "n": len(failed),
            "mean": mean(failed) if failed else None,
            "median": median(failed) if failed else None,
        },
        "mean_difference_tp1_minus_failed": (
            mean(tp1) - mean(failed) if tp1 and failed else None
        ),
    }


def run_postmortem(raw_root: Path, output_path: Path) -> dict[str, Any]:
    freeze = _load_freeze()
    objects = expected_h03_daily_objects()
    if len(objects) != EXPECTED_ARCHIVE_COUNT:
        raise RuntimeError("H03 manifest cardinality drift")

    candles_by_symbol: dict[str, list[Any]] = {
        symbol: [] for symbol in freeze["data_contract"]["symbols"]
    }
    flow_by_symbol: dict[str, dict[int, FlowBar]] = {
        symbol: {} for symbol in freeze["data_contract"]["symbols"]
    }
    archive_sha256: dict[str, str] = {}

    for item in objects:
        symbol = item["symbol"]
        archive_path = raw_root / symbol / item["archive_filename"]
        checksum_path = raw_root / symbol / (item["archive_filename"] + ".CHECKSUM")
        if not archive_path.is_file() or not checksum_path.is_file():
            raise FileNotFoundError(f"missing exact H03 corpus object: {archive_path}")
        archive_bytes = archive_path.read_bytes()
        checksum_text = checksum_path.read_text(encoding="utf-8")
        adapted = adapt_binance_daily_archive_bytes(
            symbol=symbol,
            day=item["date_utc"],
            archive_filename=item["archive_filename"],
            archive_bytes=archive_bytes,
            checksum_text=checksum_text,
        )
        if not adapted.status.startswith("PASS_BINANCE_DAILY"):
            raise RuntimeError(
                f"H03 corpus integrity failure {symbol} {item['date_utc']}: "
                f"{adapted.status} {adapted.reasons}"
            )
        candles_by_symbol[symbol].extend(adapted.candles)
        archive_sha256[f"{symbol}/{item['archive_filename']}"] = adapted.archive_sha256
        for bar in _parse_flow_rows(archive_bytes, item["archive_filename"]):
            if bar.open_time in flow_by_symbol[symbol]:
                raise ValueError("duplicate flow open_time across daily archives")
            flow_by_symbol[symbol][bar.open_time] = bar

    archive_set_fingerprint = _canonical_hash(archive_sha256)
    if archive_set_fingerprint != EXPECTED_H03_ARCHIVE_SET_FINGERPRINT:
        raise PermissionError("postmortem corpus does not match closed H03 archive set")

    records, metrics, _ = evaluate_h03_universe(
        candles_by_symbol, PARAMETERS, BASE_COSTS
    )
    resolved = [record for record in records if record.outcome.net_r is not None]
    if len(resolved) != EXPECTED_H03_RESOLVED_TRADES:
        raise RuntimeError("H03 resolved-trade reproduction mismatch")

    index_cache: dict[str, tuple[list[int], dict[int, int]]] = {}
    for symbol, values in flow_by_symbol.items():
        times = sorted(values)
        index_cache[symbol] = (times, {value: index for index, value in enumerate(times)})

    rows: list[dict[str, Any]] = []
    for record in resolved:
        symbol = record.symbol
        times, time_to_index = index_cache[symbol]
        breakout = _feature_bundle(
            flow_by_symbol[symbol], times, time_to_index, record.signal.breakout_open_time
        )
        retest = _feature_bundle(
            flow_by_symbol[symbol], times, time_to_index, record.signal.retest_open_time
        )
        persistent = (
            breakout["flow_imbalance"] > 0.0
            and retest["flow_imbalance"] > 0.0
        )
        entry_day = datetime.fromtimestamp(
            record.signal.entry_open_time / 1000.0, tz=timezone.utc
        ).date().isoformat()
        rows.append(
            {
                "entry_day_utc": entry_day,
                "tp1_reached": bool(record.outcome.tp1_reached),
                "flow_persistent": persistent,
                "breakout_flow_imbalance": breakout["flow_imbalance"],
                "retest_flow_imbalance": retest["flow_imbalance"],
                "retest_minus_breakout_flow_imbalance": (
                    retest["flow_imbalance"] - breakout["flow_imbalance"]
                ),
                "breakout_volume_shock_vs_prior_96_bar_median": breakout["volume_shock"],
                "retest_volume_shock_vs_prior_96_bar_median": retest["volume_shock"],
                "breakout_trade_count_shock_vs_prior_96_bar_median": breakout["trade_count_shock"],
                "retest_trade_count_shock_vs_prior_96_bar_median": retest["trade_count_shock"],
                "breakout_avg_trade_size_shock_vs_prior_96_bar_median": breakout["avg_trade_size_shock"],
                "retest_avg_trade_size_shock_vs_prior_96_bar_median": retest["avg_trade_size_shock"],
            }
        )

    persistent_rows = [row for row in rows if row["flow_persistent"]]
    nonpersistent_rows = [row for row in rows if not row["flow_persistent"]]
    primary = {
        "n_total": len(rows),
        "n_persistent": len(persistent_rows),
        "n_nonpersistent": len(nonpersistent_rows),
        "tp1_rate_persistent": (
            mean(float(row["tp1_reached"]) for row in persistent_rows)
            if persistent_rows else None
        ),
        "tp1_rate_nonpersistent": (
            mean(float(row["tp1_reached"]) for row in nonpersistent_rows)
            if nonpersistent_rows else None
        ),
        "tp1_rate_difference": _rate_difference(rows),
        "odds_table": _odds_ratio(rows),
    }

    secondary_fields = list(freeze["secondary_descriptive_features"]["features"])
    secondary = {field: _group_summary(rows, field) for field in secondary_fields}

    body = {
        "document_type": "PHASE_B_H03_MICROSTRUCTURE_POSTMORTEM_RECEIPT",
        "version": "0.1",
        "status": "POSTHOC_DIAGNOSTIC_COMPLETE",
        "authority": "HYPOTHESIS_GENERATION_ONLY_NO_CLASSIFICATION_AUTHORITY",
        "freeze_fingerprint": EXPECTED_FREEZE_FINGERPRINT,
        "h03_discovery_receipt_fingerprint": EXPECTED_H03_DISCOVERY_RECEIPT_FINGERPRINT,
        "archive_set_fingerprint": archive_set_fingerprint,
        "h03_reproduction": {
            "resolved_trade_count": metrics.resolved_trade_count,
            "net_expectancy_r": metrics.net_expectancy_r,
            "profit_factor_r": metrics.profit_factor_r,
            "tp1_reach_rate": metrics.tp1_reach_rate,
        },
        "primary_feature": freeze["primary_feature"],
        "primary_diagnostic": primary,
        "bootstrap": _day_block_bootstrap(rows),
        "secondary_descriptive": secondary,
        "guards": {
            "no_threshold_search_performed": true,
            "no_symbol_subgroup_search_performed": true,
            "no_time_subgroup_search_performed": true,
            "h03_reclassified": false,
            "h03_rescued": false,
            "mexc_validation_2025_accessed": false,
            "holdout_2026_accessed": false,
            "network_access_performed_by_module": false,
            "exchange_mutation_performed": false,
            "live_trading_performed": false
        }
    }
    body["fingerprint"] = _canonical_hash(body)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return body


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 2:
        print(
            "usage: python -m research.phase_b_h03_microstructure_postmortem_v01 "
            "<raw_root> <output_receipt>"
        )
        return 2
    try:
        receipt = run_postmortem(Path(args[0]), Path(args[1]))
    except Exception as exc:
        print(f"H03_FLOW_POSTMORTEM_FATAL: {type(exc).__name__}: {exc}")
        return 2
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
