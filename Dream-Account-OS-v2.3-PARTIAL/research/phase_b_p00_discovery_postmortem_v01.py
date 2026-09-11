from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
from math import isfinite
from pathlib import Path
from statistics import mean, median
from typing import Any, Iterable, Mapping

from dream_account.models import Candle
from research.phase_b_p00_discovery_runner_v01 import (
    END_MONTH,
    FROZEN_UNIVERSE,
    START_MONTH,
    _cost_from_freeze,
    _freeze_bindings,
    _load_canonical_window,
    _month_sequence,
    _parameters_from_freeze,
    _prefix,
    run_p00_discovery,
)
from research.phase_b_research_evaluator_v01 import (
    ResearchTradeRecord,
    evaluate_symbol,
    evaluate_universe,
    split_contiguous_segments,
)
from research.phase_b_signal_formation_v01 import derive_signal_geometries


ROOT = Path(__file__).resolve().parents[1]
CLOSEOUT_PATH = ROOT / "research" / "PHASE_B_P00_DISCOVERY_CLOSEOUT_V0.1.json"
POSTMORTEM_VERSION = "0.1"


@dataclass(frozen=True)
class PostMortemReceipt:
    document_type: str
    version: str
    status: str
    profile_id: str
    setup_id: str
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
    by_year: dict[str, dict[str, Any]]
    by_month_utc: dict[str, dict[str, Any]]
    by_entry_hour_utc: dict[str, dict[str, Any]]
    volatility_quartiles_descriptive: dict[str, Any]
    concentration: dict[str, Any]
    governance: dict[str, Any]
    network_access_performed: bool
    exchange_mutation_performed: bool
    validation_2025_access_performed: bool
    holdout_2026_access_performed: bool
    submitted_to_exchange: bool
    fingerprint: str


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _canonical_hash(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return sha256(encoded).hexdigest()


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
    exits = Counter(r.outcome.exit_reason for r in resolved)
    stops = [float(r.signal.stop_distance_pct) for r in resolved]
    atr_pct = [float(r.signal.atr_before_breakout / r.signal.entry * 100.0) for r in resolved]
    return {
        "trade_count": len(rows),
        "resolved_trade_count": len(resolved),
        "total_net_r": sum(values) if values else 0.0,
        "net_expectancy_r": mean(values) if values else None,
        "median_net_r": median(values) if values else None,
        "profit_factor_r": _profit_factor(values),
        "win_rate": (sum(v > 0 for v in values) / len(values)) if values else None,
        "loss_rate": (sum(v < 0 for v in values) / len(values)) if values else None,
        "tp1_reach_rate": (sum(r.outcome.tp1_reached for r in resolved) / len(resolved)) if resolved else None,
        "mean_bars_held": mean([r.outcome.bars_held for r in resolved if r.outcome.bars_held is not None]) if resolved else None,
        "exit_reason_counts": dict(sorted(exits.items())),
        "stop_distance_pct": {
            "median": median(stops) if stops else None,
            "q25": _percentile(stops, 0.25),
            "q75": _percentile(stops, 0.75),
        },
        "atr_pct_entry": {
            "median": median(atr_pct) if atr_pct else None,
            "q25": _percentile(atr_pct, 0.25),
            "q75": _percentile(atr_pct, 0.75),
        },
    }


def _group_records(records: Iterable[ResearchTradeRecord], key_fn) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[ResearchTradeRecord]] = defaultdict(list)
    for record in records:
        grouped[str(key_fn(record))].append(record)
    return {key: _summarize_records(grouped[key]) for key in sorted(grouped)}


def _volatility_quartiles(records: list[ResearchTradeRecord]) -> dict[str, Any]:
    resolved = [r for r in records if r.outcome.net_r is not None]
    features = [float(r.signal.atr_before_breakout / r.signal.entry * 100.0) for r in resolved]
    q25 = _percentile(features, 0.25)
    q50 = _percentile(features, 0.50)
    q75 = _percentile(features, 0.75)
    if q25 is None or q50 is None or q75 is None:
        return {"method": "POSTHOC_DESCRIPTIVE_ATR_PCT_QUARTILES", "boundaries": None, "groups": {}}

    def bucket(record: ResearchTradeRecord) -> str:
        value = float(record.signal.atr_before_breakout / record.signal.entry * 100.0)
        if value <= q25:
            return "Q1_LOW"
        if value <= q50:
            return "Q2"
        if value <= q75:
            return "Q3"
        return "Q4_HIGH"

    return {
        "method": "POSTHOC_DESCRIPTIVE_ATR_PCT_QUARTILES",
        "feature": "atr_before_breakout / entry * 100",
        "boundaries_pct": {"q25": q25, "q50": q50, "q75": q75},
        "groups": _group_records(resolved, bucket),
        "warning": "Descriptive post-mortem only. These outcome-opened buckets cannot rescue P00 or define a trade filter.",
    }


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


def _tp1_path(records: list[ResearchTradeRecord]) -> dict[str, Any]:
    resolved = [r for r in records if r.outcome.net_r is not None]
    reached = [r for r in resolved if r.outcome.tp1_reached]
    not_reached = [r for r in resolved if not r.outcome.tp1_reached]
    after_tp1 = Counter(r.outcome.exit_reason for r in reached)
    stop_like = {"STOP", "STOP_GAP", "STOP_AMBIGUOUS_SAME_BAR"}
    tp1_then_stop = sum(count for reason, count in after_tp1.items() if reason in stop_like)
    return {
        "resolved_trade_count": len(resolved),
        "tp1_reached_count": len(reached),
        "tp1_not_reached_count": len(not_reached),
        "tp1_reach_rate": len(reached) / len(resolved) if resolved else None,
        "final_exit_after_tp1_counts": dict(sorted(after_tp1.items())),
        "tp1_then_stop_like_count": tp1_then_stop,
        "tp1_then_stop_like_rate_of_tp1_reached": tp1_then_stop / len(reached) if reached else None,
        "warning": "TP1 was informational in frozen P00. This diagnostic does not authorize partial exits or stop changes.",
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
        "warning": "Concentration metrics are explanatory only and cannot be used to exclude symbols, months, or trades from closed P00.",
    }


def _geometry_funnel(candles_by_symbol: Mapping[str, list[Candle]], parameters, costs) -> dict[str, dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    for symbol in FROZEN_UNIVERSE:
        segments, gap_count = split_contiguous_segments(candles_by_symbol[symbol])
        raw = 0
        rejected = 0
        ready = 0
        for segment in segments:
            geometries = derive_signal_geometries(segment, parameters, costs, require_regular_spacing=True)
            raw += len(geometries)
            rejected += sum(g.geometry_status == "REJECTED_NET_RR" for g in geometries)
            ready += sum(g.geometry_status == "GEOMETRY_READY" for g in geometries)
        selected_records, diagnostics = evaluate_symbol(symbol, candles_by_symbol[symbol], parameters, costs)
        output[symbol] = {
            "raw_geometry_count": raw,
            "net_rr_rejected_count": rejected,
            "geometry_ready_count": ready,
            "overlap_skipped_count": diagnostics["overlap_skipped_count"],
            "selected_trade_count": len(selected_records),
            "contiguous_segment_count": len(segments),
            "detected_gap_count": gap_count,
            "net_rr_rejection_rate_of_raw": rejected / raw if raw else None,
        }
    return output


def _write_trade_ledger(path: Path, records: list[ResearchTradeRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "symbol",
        "entry_utc",
        "exit_utc",
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
            writer.writerow(
                {
                    "symbol": record.symbol,
                    "entry_utc": datetime.fromtimestamp(signal.entry_open_time / 1000.0, tz=timezone.utc).isoformat(),
                    "exit_utc": datetime.fromtimestamp(outcome.exit_open_time / 1000.0, tz=timezone.utc).isoformat() if outcome.exit_open_time is not None else "",
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


def run_postmortem(raw_dir: str | Path, output_dir: str | Path, ledger_path: str | Path | None = None) -> PostMortemReceipt:
    closeout = _load_json(CLOSEOUT_PATH)
    if closeout.get("status") != "CLOSED_NO_EDGE" or closeout.get("classification") != "NO_EDGE":
        raise RuntimeError("P00 closeout is not frozen CLOSED_NO_EDGE")
    governance = closeout.get("governance_closeout", {})
    if governance.get("descriptive_postmortem_on_already_open_discovery_data_allowed") is not True:
        raise RuntimeError("descriptive post-mortem is not authorized by closeout")
    if governance.get("reproducibility_rerun_with_identical_frozen_inputs_allowed") is not True:
        raise RuntimeError("identical-input reproducibility rerun is not authorized")

    # Reproduce the exact closed P00 run first. A mismatch blocks all diagnostics.
    reproduction = run_p00_discovery(raw_dir, output_dir)
    decision = reproduction.decision or {}
    if reproduction.status != "P00_DISCOVERY_COMPLETE":
        raise RuntimeError(f"P00 reproducibility preflight failed: {reproduction.status}")
    if reproduction.fingerprint != closeout["run_fingerprint"]:
        raise RuntimeError("closed P00 run fingerprint did not reproduce")
    if decision.get("fingerprint") != closeout["decision_fingerprint"]:
        raise RuntimeError("closed P00 decision fingerprint did not reproduce")
    if decision.get("classification") != "NO_EDGE" or decision.get("next_stage_unlocked") is not False:
        raise RuntimeError("closed P00 decision changed")
    if reproduction.validation_2025_access_performed or reproduction.holdout_2026_access_performed:
        raise RuntimeError("future-stage access detected")
    if reproduction.network_access_performed or reproduction.exchange_mutation_performed or reproduction.submitted_to_exchange:
        raise RuntimeError("forbidden network/exchange activity detected")

    freeze, amendment, start_ms, end_ms = _freeze_bindings()
    parameters = _parameters_from_freeze(freeze)
    base_costs = _cost_from_freeze(freeze, "BASE_SENSITIVITY")
    output_root = Path(output_dir)
    candles_by_symbol: dict[str, list[Candle]] = {}
    for symbol in FROZEN_UNIVERSE:
        prefix = _prefix(symbol)
        series: list[Candle] = []
        for month in _month_sequence(START_MONTH, END_MONTH):
            canonical = output_root / "canonical" / f"{prefix}-Min15-{month}-01.canonical.csv"
            series.extend(_load_canonical_window(canonical, start_ms=start_ms, end_ms=end_ms))
        candles_by_symbol[symbol] = series

    records, global_metrics = evaluate_universe(candles_by_symbol, parameters, base_costs)
    if len(records) != closeout["base_metrics"]["resolved_trade_count"]:
        raise RuntimeError("post-mortem record count diverges from closed P00")
    values = [float(r.outcome.net_r) for r in records if r.outcome.net_r is not None]
    if not values or abs(mean(values) - closeout["base_metrics"]["net_expectancy_r"]) > 1e-12:
        raise RuntimeError("post-mortem expectancy diverges from closed P00")

    for record in records:
        if record.outcome.net_r is not None and not isfinite(float(record.outcome.net_r)):
            raise RuntimeError("non-finite post-mortem net R")

    by_symbol = _group_records(records, lambda r: r.symbol)
    by_exit = _group_records(records, lambda r: r.outcome.exit_reason)
    by_year = _group_records(records, lambda r: datetime.fromtimestamp(r.signal.entry_open_time / 1000.0, tz=timezone.utc).strftime("%Y"))
    by_month = _group_records(records, lambda r: datetime.fromtimestamp(r.signal.entry_open_time / 1000.0, tz=timezone.utc).strftime("%Y-%m"))
    by_hour = _group_records(records, lambda r: f"{datetime.fromtimestamp(r.signal.entry_open_time / 1000.0, tz=timezone.utc).hour:02d}")

    receipt_payload = {
        "document_type": "PHASE_B_P00_DISCOVERY_POSTMORTEM",
        "version": POSTMORTEM_VERSION,
        "status": "DESCRIPTIVE_DIAGNOSTIC_COMPLETE",
        "profile_id": "P00_PRIMARY",
        "setup_id": "PBR01_BREAKOUT_RETEST_LONG",
        "stage": "DISCOVERY_POSTMORTEM",
        "closed_classification": "NO_EDGE",
        "reproduction_run_fingerprint": reproduction.fingerprint,
        "reproduction_decision_fingerprint": decision["fingerprint"],
        "effective_start_utc_inclusive": amendment["effective_discovery_window"]["start_utc_inclusive"],
        "effective_end_utc_exclusive": amendment["effective_discovery_window"]["end_utc_exclusive"],
        "resolved_trade_count": len(values),
        "global_metrics": asdict(global_metrics),
        "geometry_funnel_by_symbol": _geometry_funnel(candles_by_symbol, parameters, base_costs),
        "by_symbol": by_symbol,
        "by_exit_reason": by_exit,
        "tp1_path": _tp1_path(records),
        "net_r_distribution": _net_r_distribution(records),
        "by_year": by_year,
        "by_month_utc": by_month,
        "by_entry_hour_utc": by_hour,
        "volatility_quartiles_descriptive": _volatility_quartiles(records),
        "concentration": _concentration(records),
        "governance": {
            "diagnostic_only": True,
            "p00_closed_no_edge": True,
            "may_rescue_p00": False,
            "may_define_posthoc_filter_for_p00": False,
            "may_retune_p00": False,
            "may_unlock_2025": False,
            "may_open_2026": False,
            "sensitivity_profiles_evaluated": False,
            "new_hypothesis_required_for_future_trading_candidate": True,
            "note": "Any apparent subgroup strength is post-hoc descriptive evidence only. It cannot promote, filter, or rescue P00.",
        },
        "network_access_performed": False,
        "exchange_mutation_performed": False,
        "validation_2025_access_performed": False,
        "holdout_2026_access_performed": False,
        "submitted_to_exchange": False,
    }
    fingerprint = _canonical_hash(receipt_payload)
    receipt = PostMortemReceipt(**receipt_payload, fingerprint=fingerprint)
    if ledger_path is not None:
        _write_trade_ledger(Path(ledger_path), records)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline descriptive post-mortem for closed P00 Discovery NO_EDGE.")
    parser.add_argument("raw_dir")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--ledger", required=True)
    args = parser.parse_args()
    try:
        receipt = run_postmortem(args.raw_dir, args.output_dir, args.ledger)
    except Exception as exc:
        print(json.dumps({"status": "BLOCKED_POSTMORTEM", "reason": f"{type(exc).__name__}:{exc}"}, indent=2, sort_keys=True))
        return 2
    payload = asdict(receipt)
    Path(args.receipt).parent.mkdir(parents=True, exist_ok=True)
    Path(args.receipt).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
