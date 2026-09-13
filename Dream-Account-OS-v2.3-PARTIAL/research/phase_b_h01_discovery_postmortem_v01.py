from __future__ import annotations

"""Descriptive-only post-mortem for closed H01 Discovery.

H01 is CLOSED_NO_EDGE. This module may reproduce the exact already-open H01 Discovery
run and describe its trade paths. It MUST NOT retune H01, select a winner, simulate a
new management rule, unlock Validation/2026, access a network, or submit anything.
"""

import argparse
import csv
import json
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from hashlib import sha256
from math import isfinite
from pathlib import Path
from statistics import mean, median
from typing import Any, Callable, Iterable, Mapping

from dream_account.models import Candle
from research.phase_b_h01_discovery_runner_v01 import (
    EFFECTIVE_END_UTC,
    EFFECTIVE_START_UTC,
    _cost_from_p00,
    _freeze_bindings,
    _parameters_from_h01,
    _prefix,
    run_h01_discovery,
)
from research.phase_b_h01_mexc_adapter_audit_v01 import PASS_STATUSES, audit_h01_month
from research.phase_b_h01_mexc_discovery_access_v01 import (
    DEFAULT_AUTHORIZATION_PATH,
    EXPECTED_MONTHS,
    FROZEN_UNIVERSE,
)
from research.phase_b_h01_research_evaluator_v01 import (
    evaluate_h01_symbol,
    evaluate_h01_universe,
)
from research.phase_b_research_evaluator_v01 import ResearchTradeRecord
from research.phase_b_signal_formation_v01 import validate_candles


ROOT = Path(__file__).resolve().parents[1]
CLOSEOUT_PATH = ROOT / "research" / "PHASE_B_H01_DISCOVERY_CLOSEOUT_V0.1.json"
POSTMORTEM_VERSION = "0.1"


@dataclass(frozen=True)
class H01PostMortemReceipt:
    document_type: str
    version: str
    status: str
    hypothesis_id: str
    family_id: str
    stage: str
    closed_classification: str
    reproduction_run_fingerprint: str
    reproduction_decision_fingerprint: str
    effective_start_utc_inclusive: str
    effective_end_utc_exclusive: str
    resolved_trade_count: int
    global_metrics: dict[str, Any]
    geometry_funnel_by_symbol: dict[str, dict[str, Any]]
    by_symbol: dict[str, dict[str, Any]]
    by_exit_reason: dict[str, dict[str, Any]]
    tp1_path: dict[str, Any]
    net_r_distribution: dict[str, Any]
    bars_held_distribution: dict[str, Any]
    by_month_utc: dict[str, dict[str, Any]]
    by_entry_hour_utc: dict[str, dict[str, Any]]
    by_entry_weekday_utc: dict[str, dict[str, Any]]
    volatility_quartiles_descriptive: dict[str, Any]
    stop_distance_quartiles_descriptive: dict[str, Any]
    breakout_excess_quartiles_descriptive: dict[str, Any]
    retest_depth_quartiles_descriptive: dict[str, Any]
    concentration: dict[str, Any]
    governance: dict[str, Any]
    network_access_performed: bool
    exchange_mutation_performed: bool
    validation_2025_09_through_2025_12_access_performed: bool
    holdout_2026_access_performed: bool
    submitted_to_exchange: bool
    fingerprint: str


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {path.name}")
    return value


def _canonical_hash(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return sha256(encoded).hexdigest()


def _with_fingerprint(receipt: H01PostMortemReceipt) -> H01PostMortemReceipt:
    payload = asdict(receipt)
    payload.pop("fingerprint", None)
    return replace(receipt, fingerprint=_canonical_hash(payload))


def _percentile(values: Iterable[float], probability: float) -> float | None:
    ordered = sorted(float(v) for v in values)
    if not ordered:
        return None
    if probability <= 0:
        return ordered[0]
    if probability >= 1:
        return ordered[-1]
    position = (len(ordered) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def _profit_factor(values: Iterable[float]) -> float | None:
    data = [float(v) for v in values]
    gains = sum(v for v in data if v > 0)
    losses = -sum(v for v in data if v < 0)
    return None if losses <= 0 else gains / losses


def _summarize_records(records: Iterable[ResearchTradeRecord]) -> dict[str, Any]:
    rows = list(records)
    resolved = [r for r in rows if r.outcome.net_r is not None]
    values = [float(r.outcome.net_r) for r in resolved]
    bars = [int(r.outcome.bars_held) for r in resolved if r.outcome.bars_held is not None]
    exits = Counter(r.outcome.exit_reason for r in resolved)
    return {
        "trade_count": len(rows),
        "resolved_trade_count": len(resolved),
        "total_net_r": sum(values) if values else 0.0,
        "net_expectancy_r": mean(values) if values else None,
        "median_net_r": median(values) if values else None,
        "profit_factor_r": _profit_factor(values),
        "win_rate": (sum(v > 0 for v in values) / len(values)) if values else None,
        "loss_rate": (sum(v < 0 for v in values) / len(values)) if values else None,
        "zero_rate": (sum(v == 0 for v in values) / len(values)) if values else None,
        "tp1_reach_rate": (sum(r.outcome.tp1_reached for r in resolved) / len(resolved)) if resolved else None,
        "mean_bars_held": mean(bars) if bars else None,
        "median_bars_held": median(bars) if bars else None,
        "exit_reason_counts": dict(sorted(exits.items())),
    }


def _group_records(records: Iterable[ResearchTradeRecord], key_fn: Callable[[ResearchTradeRecord], str]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[ResearchTradeRecord]] = defaultdict(list)
    for record in records:
        grouped[str(key_fn(record))].append(record)
    return {key: _summarize_records(grouped[key]) for key in sorted(grouped)}


def _net_r_distribution(records: list[ResearchTradeRecord]) -> dict[str, Any]:
    values = [float(r.outcome.net_r) for r in records if r.outcome.net_r is not None]
    if not values:
        return {}
    return {
        "min": min(values),
        "q05": _percentile(values, 0.05),
        "q10": _percentile(values, 0.10),
        "q25": _percentile(values, 0.25),
        "q50": _percentile(values, 0.50),
        "q75": _percentile(values, 0.75),
        "q90": _percentile(values, 0.90),
        "q95": _percentile(values, 0.95),
        "max": max(values),
        "mean": mean(values),
        "total": sum(values),
    }


def _bars_held_distribution(records: list[ResearchTradeRecord]) -> dict[str, Any]:
    values = [int(r.outcome.bars_held) for r in records if r.outcome.net_r is not None and r.outcome.bars_held is not None]
    if not values:
        return {}
    return {
        "min": min(values),
        "q25": _percentile(values, 0.25),
        "q50": _percentile(values, 0.50),
        "q75": _percentile(values, 0.75),
        "q90": _percentile(values, 0.90),
        "max": max(values),
        "mean": mean(values),
    }


def _tp1_path(records: list[ResearchTradeRecord]) -> dict[str, Any]:
    resolved = [r for r in records if r.outcome.net_r is not None]
    reached = [r for r in resolved if r.outcome.tp1_reached]
    not_reached = [r for r in resolved if not r.outcome.tp1_reached]
    after_tp1 = Counter(r.outcome.exit_reason for r in reached)
    before_tp1 = Counter(r.outcome.exit_reason for r in not_reached)
    protective_reasons = {
        "PROTECTIVE_STOP",
        "PROTECTIVE_STOP_GAP",
        "PROTECTIVE_STOP_AMBIGUOUS_SAME_BAR",
    }
    protective = [r for r in reached if r.outcome.exit_reason in protective_reasons]
    tp2 = [r for r in reached if r.outcome.exit_reason == "TP2"]
    time_exit = [r for r in reached if r.outcome.exit_reason == "TIME_EXIT_NEXT_OPEN"]
    reached_values = [float(r.outcome.net_r) for r in reached]
    not_reached_values = [float(r.outcome.net_r) for r in not_reached]
    return {
        "resolved_trade_count": len(resolved),
        "tp1_reached_count": len(reached),
        "tp1_not_reached_count": len(not_reached),
        "tp1_reach_rate": len(reached) / len(resolved) if resolved else None,
        "final_exit_after_tp1_counts": dict(sorted(after_tp1.items())),
        "final_exit_without_tp1_counts": dict(sorted(before_tp1.items())),
        "tp1_then_protective_exit_count": len(protective),
        "tp1_then_protective_exit_rate_of_tp1_reached": len(protective) / len(reached) if reached else None,
        "tp1_then_tp2_count": len(tp2),
        "tp1_then_tp2_rate_of_tp1_reached": len(tp2) / len(reached) if reached else None,
        "tp1_then_time_exit_count": len(time_exit),
        "tp1_then_time_exit_rate_of_tp1_reached": len(time_exit) / len(reached) if reached else None,
        "tp1_reached_total_net_r": sum(reached_values),
        "tp1_reached_expectancy_r": mean(reached_values) if reached_values else None,
        "tp1_not_reached_total_net_r": sum(not_reached_values),
        "tp1_not_reached_expectancy_r": mean(not_reached_values) if not_reached_values else None,
        "warning": "Descriptive closed-H01 path accounting only. No partial exit, trailing rule, stop change, or H02 rule is simulated here.",
    }


def _feature_quartiles(
    records: list[ResearchTradeRecord],
    *,
    name: str,
    feature_fn: Callable[[ResearchTradeRecord], float],
) -> dict[str, Any]:
    resolved = [r for r in records if r.outcome.net_r is not None]
    features: list[float] = []
    for record in resolved:
        value = float(feature_fn(record))
        if not isfinite(value):
            raise ValueError(f"non-finite post-mortem feature: {name}")
        features.append(value)
    q25 = _percentile(features, 0.25)
    q50 = _percentile(features, 0.50)
    q75 = _percentile(features, 0.75)
    if q25 is None or q50 is None or q75 is None:
        return {"method": "POSTHOC_DESCRIPTIVE_QUARTILES", "feature": name, "boundaries": None, "groups": {}}

    def bucket(record: ResearchTradeRecord) -> str:
        value = float(feature_fn(record))
        if value <= q25:
            return "Q1_LOW"
        if value <= q50:
            return "Q2"
        if value <= q75:
            return "Q3"
        return "Q4_HIGH"

    return {
        "method": "POSTHOC_DESCRIPTIVE_QUARTILES",
        "feature": name,
        "boundaries": {"q25": q25, "q50": q50, "q75": q75},
        "groups": _group_records(resolved, bucket),
        "warning": "Outcome-opened descriptive buckets only. They cannot filter, rescue, promote, or retune H01 and are not H02 evidence.",
    }


def _concentration(records: list[ResearchTradeRecord]) -> dict[str, Any]:
    resolved = [r for r in records if r.outcome.net_r is not None]
    values = sorted((float(r.outcome.net_r), r.symbol, r.signal.entry_open_time) for r in resolved)
    losses = [item for item in values if item[0] < 0]
    wins = [item for item in values if item[0] > 0]
    total_abs_loss = -sum(item[0] for item in losses)
    total_positive = sum(item[0] for item in wins)
    worst10 = losses[:10]
    best10 = list(reversed(wins[-10:]))
    by_symbol = defaultdict(float)
    by_month = defaultdict(float)
    for value, symbol, entry_ms in values:
        by_symbol[symbol] += value
        month = datetime.fromtimestamp(entry_ms / 1000.0, tz=timezone.utc).strftime("%Y-%m")
        by_month[month] += value
    return {
        "net_r_by_symbol": dict(sorted(by_symbol.items())),
        "net_r_by_month_utc": dict(sorted(by_month.items())),
        "worst_10_trades_abs_loss_share": ((-sum(v for v, _, _ in worst10)) / total_abs_loss) if total_abs_loss > 0 else None,
        "best_10_trades_positive_r_share": (sum(v for v, _, _ in best10) / total_positive) if total_positive > 0 else None,
        "worst_10_trade_net_r": [v for v, _, _ in worst10],
        "best_10_trade_net_r": [v for v, _, _ in best10],
        "warning": "Concentration is explanatory only. No symbol, month, hour, volatility bucket, or trade may be excluded from closed H01 post hoc.",
    }


def _geometry_funnel(candles_by_symbol: Mapping[str, list[Candle]], parameters, costs) -> dict[str, dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    for symbol in FROZEN_UNIVERSE:
        records, diagnostics = evaluate_h01_symbol(symbol, candles_by_symbol[symbol], parameters, costs)
        raw = diagnostics["raw_geometry_count"]
        rejected = diagnostics["net_rr_rejected_count"]
        output[symbol] = {
            "raw_geometry_count": raw,
            "net_rr_rejected_count": rejected,
            "net_rr_rejection_rate_of_raw": rejected / raw if raw else None,
            "overlap_skipped_count": diagnostics["overlap_skipped_count"],
            "selected_trade_count": len(records),
            "resolved_trade_count": sum(r.outcome.net_r is not None for r in records),
            "contiguous_segment_count": diagnostics["contiguous_segment_count"],
            "detected_gap_count": diagnostics["detected_gap_count"],
        }
    return output


def _rebuild_effective_corpus(
    raw_dir: Path,
    output_dir: Path,
    authorization_path: Path,
) -> dict[str, list[Candle]]:
    h01, _p00, start_ms, end_ms = _freeze_bindings()
    if h01.get("hypothesis_id") != "H01_PROTECT_AFTER_TP1_NEXT_BAR":
        raise RuntimeError("H01 freeze binding changed")

    effective: dict[str, list[Candle]] = {}
    canonical_dir = output_dir / "canonical"
    receipt_dir = output_dir / "adapter_receipts"
    for symbol in FROZEN_UNIVERSE:
        candles: list[Candle] = []
        prefix = _prefix(symbol)
        for month in EXPECTED_MONTHS:
            raw_path = raw_dir / f"{prefix}-Min15-{month}-01.csv"
            canonical_path = canonical_dir / f"{raw_path.stem}.canonical.csv"
            adapter_receipt_path = receipt_dir / f"{raw_path.stem}.adapter.json"
            package = audit_h01_month(
                raw_path,
                canonical_path,
                adapter_receipt_path,
                symbol=symbol,
                month=month,
                authorization_path=authorization_path,
            )
            if package.manifest.status not in PASS_STATUSES:
                raise RuntimeError(f"H01 post-mortem corpus audit failed: {symbol}:{month}:{package.manifest.status}")
            candles.extend(package.candles)
        trimmed = [c for c in candles if start_ms <= c.open_time < end_ms]
        effective[symbol] = validate_candles(trimmed, require_regular_spacing=False)
    return effective


def _write_trade_ledger(path: Path, records: list[ResearchTradeRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "symbol",
        "entry_utc",
        "exit_utc",
        "entry_hour_utc",
        "entry_weekday_utc",
        "exit_reason",
        "bars_held",
        "net_r",
        "tp1_reached",
        "stop_distance_pct",
        "atr_pct_entry",
        "breakout_excess_atr",
        "retest_depth_atr",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            signal = record.signal
            outcome = record.outcome
            atr = float(signal.atr_before_breakout)
            entry_dt = datetime.fromtimestamp(signal.entry_open_time / 1000.0, tz=timezone.utc)
            writer.writerow(
                {
                    "symbol": record.symbol,
                    "entry_utc": entry_dt.isoformat(),
                    "exit_utc": datetime.fromtimestamp(outcome.exit_open_time / 1000.0, tz=timezone.utc).isoformat() if outcome.exit_open_time is not None else "",
                    "entry_hour_utc": entry_dt.hour,
                    "entry_weekday_utc": entry_dt.strftime("%A"),
                    "exit_reason": outcome.exit_reason,
                    "bars_held": outcome.bars_held,
                    "net_r": outcome.net_r,
                    "tp1_reached": outcome.tp1_reached,
                    "stop_distance_pct": signal.stop_distance_pct,
                    "atr_pct_entry": atr / signal.entry * 100.0,
                    "breakout_excess_atr": (signal.breakout_close - signal.resistance) / atr if atr > 0 else None,
                    "retest_depth_atr": (signal.zone_high - signal.retest_low) / atr if atr > 0 else None,
                }
            )


def run_postmortem(
    raw_dir: str | Path,
    output_dir: str | Path,
    *,
    authorization_path: str | Path = DEFAULT_AUTHORIZATION_PATH,
    ledger_path: str | Path | None = None,
) -> H01PostMortemReceipt:
    closeout = _load_json(CLOSEOUT_PATH)
    if closeout.get("status") != "CLOSED_NO_EDGE" or closeout.get("classification") != "NO_EDGE":
        raise RuntimeError("H01 closeout is not frozen CLOSED_NO_EDGE")
    governance = closeout.get("governance_closeout", {})
    if governance.get("descriptive_postmortem_on_already_open_discovery_data_allowed") is not True:
        raise RuntimeError("H01 descriptive post-mortem is not authorized")
    if governance.get("reproducibility_rerun_with_identical_frozen_inputs_allowed") is not True:
        raise RuntimeError("H01 identical-input reproduction is not authorized")
    if governance.get("validation_unlock_eligible") is not False or governance.get("2026_may_be_opened") is not False:
        raise RuntimeError("closed H01 future-stage lock changed")

    raw_root = Path(raw_dir)
    output_root = Path(output_dir)
    auth_path = Path(authorization_path)

    reproduction = run_h01_discovery(raw_root, output_root, authorization_path=auth_path)
    decision = reproduction.decision or {}
    if reproduction.status != "H01_DISCOVERY_COMPLETE":
        raise RuntimeError(f"H01 reproducibility preflight failed: {reproduction.status}")
    if reproduction.fingerprint != closeout["run_fingerprint"]:
        raise RuntimeError("closed H01 run fingerprint did not reproduce")
    if decision.get("fingerprint") != closeout["decision_fingerprint"]:
        raise RuntimeError("closed H01 decision fingerprint did not reproduce")
    if decision.get("classification") != "NO_EDGE" or decision.get("validation_unlock_eligible") is not False:
        raise RuntimeError("closed H01 decision changed")
    if reproduction.validation_2025_access_performed or reproduction.holdout_2026_access_performed:
        raise RuntimeError("future-stage access detected during H01 reproduction")
    if reproduction.network_access_performed or reproduction.exchange_mutation_performed or reproduction.submitted_to_exchange:
        raise RuntimeError("forbidden network/exchange activity detected during H01 reproduction")

    effective = _rebuild_effective_corpus(raw_root, output_root, auth_path)
    h01, p00, _start_ms, _end_ms = _freeze_bindings()
    parameters = _parameters_from_h01(h01)
    base_costs = _cost_from_p00(p00, "BASE_SENSITIVITY")
    records, metrics = evaluate_h01_universe(effective, parameters, base_costs)
    resolved = [r for r in records if r.outcome.net_r is not None]

    if len(resolved) != closeout["base_metrics"]["resolved_trade_count"]:
        raise RuntimeError("H01 resolved trade count did not reproduce")
    if abs(float(metrics.net_expectancy_r) - float(closeout["base_metrics"]["net_expectancy_r"])) > 1e-12:
        raise RuntimeError("H01 expectancy did not reproduce")
    if abs(float(metrics.profit_factor_r) - float(closeout["base_metrics"]["profit_factor_r"])) > 1e-12:
        raise RuntimeError("H01 profit factor did not reproduce")

    def entry_dt(record: ResearchTradeRecord) -> datetime:
        return datetime.fromtimestamp(record.signal.entry_open_time / 1000.0, tz=timezone.utc)

    atr_pct = lambda r: float(r.signal.atr_before_breakout / r.signal.entry * 100.0)
    stop_pct = lambda r: float(r.signal.stop_distance_pct)
    breakout_excess = lambda r: float((r.signal.breakout_close - r.signal.resistance) / r.signal.atr_before_breakout)
    retest_depth = lambda r: float((r.signal.zone_high - r.signal.retest_low) / r.signal.atr_before_breakout)

    receipt = H01PostMortemReceipt(
        document_type="PHASE_B_H01_DISCOVERY_POSTMORTEM",
        version=POSTMORTEM_VERSION,
        status="H01_CLOSED_NO_EDGE_POSTMORTEM_COMPLETE",
        hypothesis_id=closeout["hypothesis_id"],
        family_id=closeout["family_id"],
        stage="DISCOVERY_POSTMORTEM_DESCRIPTIVE_ONLY",
        closed_classification="NO_EDGE",
        reproduction_run_fingerprint=reproduction.fingerprint,
        reproduction_decision_fingerprint=str(decision["fingerprint"]),
        effective_start_utc_inclusive=EFFECTIVE_START_UTC,
        effective_end_utc_exclusive=EFFECTIVE_END_UTC,
        resolved_trade_count=len(resolved),
        global_metrics=_summarize_records(records),
        geometry_funnel_by_symbol=_geometry_funnel(effective, parameters, base_costs),
        by_symbol=_group_records(resolved, lambda r: r.symbol),
        by_exit_reason=_group_records(resolved, lambda r: r.outcome.exit_reason),
        tp1_path=_tp1_path(records),
        net_r_distribution=_net_r_distribution(records),
        bars_held_distribution=_bars_held_distribution(records),
        by_month_utc=_group_records(resolved, lambda r: entry_dt(r).strftime("%Y-%m")),
        by_entry_hour_utc=_group_records(resolved, lambda r: f"{entry_dt(r).hour:02d}"),
        by_entry_weekday_utc=_group_records(resolved, lambda r: entry_dt(r).strftime("%A")),
        volatility_quartiles_descriptive=_feature_quartiles(resolved, name="atr_before_breakout / entry * 100", feature_fn=atr_pct),
        stop_distance_quartiles_descriptive=_feature_quartiles(resolved, name="stop_distance_pct", feature_fn=stop_pct),
        breakout_excess_quartiles_descriptive=_feature_quartiles(resolved, name="(breakout_close - resistance) / atr_before_breakout", feature_fn=breakout_excess),
        retest_depth_quartiles_descriptive=_feature_quartiles(resolved, name="(zone_high - retest_low) / atr_before_breakout", feature_fn=retest_depth),
        concentration=_concentration(records),
        governance={
            "h01_remains_closed_no_edge": True,
            "h01_retuning_performed": False,
            "h01_rescue_attempted": False,
            "new_management_rule_simulated": False,
            "partial_exit_counterfactual_simulated": False,
            "trailing_stop_counterfactual_simulated": False,
            "posthoc_filter_applied": False,
            "candidate_selection_performed": False,
            "h02_frozen_or_evaluated": False,
            "validation_unlock_eligible": False,
            "validation_2025_09_through_2025_12_remains_locked": True,
            "holdout_2026_remains_locked": True,
            "descriptive_subgroups_may_not_be_promoted_as_edge": True,
            "next_tradable_candidate_requires_new_hypothesis_id_and_prospective_freeze": True,
        },
        network_access_performed=False,
        exchange_mutation_performed=False,
        validation_2025_09_through_2025_12_access_performed=False,
        holdout_2026_access_performed=False,
        submitted_to_exchange=False,
        fingerprint="",
    )
    receipt = _with_fingerprint(receipt)

    diagnostics_dir = output_root / "h01_postmortem"
    diagnostics_dir.mkdir(parents=True, exist_ok=True)
    receipt_path = diagnostics_dir / "latest_h01_postmortem_receipt.json"
    receipt_path.write_text(json.dumps(asdict(receipt), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    target_ledger = Path(ledger_path) if ledger_path is not None else diagnostics_dir / "latest_h01_trade_ledger.csv"
    _write_trade_ledger(target_ledger, records)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description="Descriptive-only post-mortem for CLOSED_NO_EDGE H01 Discovery")
    parser.add_argument("raw_dir", nargs="?", default=str(ROOT / "research" / "local_data" / "h01_discovery_raw"))
    parser.add_argument("output_dir", nargs="?", default=str(ROOT / "research" / "local_data" / "h01_discovery_output"))
    parser.add_argument("--authorization", default=str(DEFAULT_AUTHORIZATION_PATH))
    parser.add_argument("--ledger", default=None)
    args = parser.parse_args()

    try:
        receipt = run_postmortem(
            args.raw_dir,
            args.output_dir,
            authorization_path=args.authorization,
            ledger_path=args.ledger,
        )
    except Exception as exc:
        print(json.dumps({"status": "H01_POSTMORTEM_BLOCKED", "reason": f"{type(exc).__name__}:{exc}"}, indent=2))
        return 2

    print(json.dumps(asdict(receipt), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
