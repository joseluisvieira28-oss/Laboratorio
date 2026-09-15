from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import asdict, dataclass, replace
from math import isfinite
from pathlib import Path
from statistics import mean, median
from typing import Any, Iterable

from research import tfg_ema_pullback_1d_discovery_runner_v01 as common

LAB_ID = "TFG-DONCHIAN-1D-001"
SETUP_ID = "DONCHIAN20_DAILY_CLOSE_BREAKOUT_LONG"
FROZEN_UNIVERSE = common.FROZEN_UNIVERSE
DISCOVERY_START = common.DISCOVERY_START
DISCOVERY_END = common.DISCOVERY_END
START_MONTH = common.START_MONTH
END_MONTH = common.END_MONTH
EXPECTED_EFFECTIVE_15M_PER_SYMBOL = common.EXPECTED_EFFECTIVE_15M_PER_SYMBOL
EXPECTED_1D_PER_SYMBOL = common.EXPECTED_1D_PER_SYMBOL
DAY_MS = common.DAY_MS
LOOKBACK = 20
ATR_LENGTH = 14
STOP_ATR_FRACTION = 0.25
TARGET_R = 3.0
MAX_HOLD = 40
MIN_RESOLVED = 100
BASE_COST_PCT = 0.20
STRESS_COST_PCT = 0.30

ROOT = Path(__file__).resolve().parents[1]
FREEZE_PATH = ROOT / "research" / "timeframe_gap" / "TFG_DONCHIAN_1D_001_FREEZE.json"

Candle = common.Candle
Outcome = common.Outcome
EvaluationMetrics = common.EvaluationMetrics
StressMetrics = common.StressMetrics
BootstrapInterval = common.BootstrapInterval
DiscoveryDecision = common.DiscoveryDecision
DiscoveryReceipt = common.DiscoveryReceipt


@dataclass(frozen=True)
class Signal:
    symbol: str
    signal_open_time: int
    entry_open_time: int
    prior_20_day_high: float
    atr14: float
    signal_low: float
    signal_close: float
    entry: float
    stop: float
    target: float
    initial_risk_fraction: float
    fingerprint: str


@dataclass(frozen=True)
class TradeRecord:
    symbol: str
    signal: Signal
    outcome: Outcome


def canonical_hash(payload: Any) -> str:
    return common.canonical_hash(payload)


def finalize_receipt(receipt: DiscoveryReceipt) -> DiscoveryReceipt:
    payload = asdict(receipt)
    payload.pop("fingerprint", None)
    return replace(receipt, fingerprint=canonical_hash(payload))


def blocked(reason: str, *, source_binding_status: str | None = None) -> DiscoveryReceipt:
    return finalize_receipt(
        DiscoveryReceipt(
            status="BLOCKED_PRE_OUTCOME",
            reasons=(reason,),
            lab_id=LAB_ID,
            source_timeframe="15m",
            derived_timeframe="1d",
            universe=FROZEN_UNIVERSE,
            discovery_start_utc=DISCOVERY_START,
            discovery_end_utc=DISCOVERY_END,
            source_binding_status=source_binding_status,
            parent_corpus_fingerprint_by_symbol={},
            source_15m_count_by_symbol={},
            derived_1d_count_by_symbol={},
            total_incomplete_1d_buckets=0,
            base_metrics=None,
            fixed_cohort_stress_metrics=None,
            bootstrap=None,
            decision=None,
            validation_2025_access_performed=False,
            holdout_2026_access_performed=False,
            network_access_performed=False,
            exchange_mutation_performed=False,
            submitted_to_exchange=False,
            outcome_evaluation_performed=False,
            fingerprint="",
        )
    )


def load_freeze() -> dict[str, Any]:
    d = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    assert d["experiment_id"] == LAB_ID
    assert d["status"] == "FROZEN_BEFORE_ANY_EXPERIMENT_OUTCOME_EVALUATION"
    assert d["lineage"]["this_experiment_is_historical_replication"] is False
    assert d["indicator_definition"]["donchian_lookback_complete_days"] == LOOKBACK
    assert d["indicator_definition"]["atr_length"] == ATR_LENGTH
    assert d["signal_rules"]["breakout"] == "signal_close > prior_20_day_high"
    assert d["signal_rules"]["stop"] == "signal_low - 0.25 * ATR14_signal"
    assert d["signal_rules"]["target"] == "entry + 3.0 * (entry - stop)"
    assert d["execution_semantics"]["max_holding_bars"] == MAX_HOLD
    assert d["costs"]["BASE_round_trip_pct"] == BASE_COST_PCT
    assert d["costs"]["STRESS_round_trip_pct"] == STRESS_COST_PCT
    assert d["discovery"]["minimum_resolved_trades"] == MIN_RESOLVED
    assert d["discovery"]["start_utc_inclusive"] == DISCOVERY_START
    assert d["discovery"]["end_utc_exclusive"] == DISCOVERY_END
    assert d["governance"]["2025_access"] is False
    assert d["governance"]["2026_access"] is False
    assert d["governance"]["live_trading"] is False
    assert d["governance"]["exchange_mutation"] is False
    return d


def load_binding(path: Path, manifest_dir: Path) -> tuple[dict[str, Any], dict[str, str]]:
    d = json.loads(path.read_text(encoding="utf-8"))
    if d["experiment_id"] != LAB_ID:
        raise ValueError("binding experiment mismatch")
    if d["status"] != "FROZEN_EXACT_SOURCE_BEFORE_ANY_DONCHIAN_1D_OUTCOME_EVALUATION":
        raise ValueError("binding status mismatch")
    if d["artifact_id"] != 10419067320:
        raise ValueError("artifact id mismatch")
    if d["artifact_digest"] != "sha256:7b2562af14983d0344c9a28e81e9c1866f2e5e9dfafe94203da9a4ca1ffa36cb":
        raise ValueError("artifact digest mismatch")
    expected = dict(d["parent_corpus_fingerprint_by_symbol"])
    observed: dict[str, str] = {}
    for symbol in FROZEN_UNIVERSE:
        m = json.loads((manifest_dir / f"{symbol}_MANIFEST.json").read_text(encoding="utf-8"))
        if m["fingerprint"] != expected[symbol]:
            raise ValueError(f"manifest fingerprint mismatch:{symbol}")
        if m["status"] != "PASS_CORPUS_AUDIT_ONLY_WITH_GAPS":
            raise ValueError(f"manifest status mismatch:{symbol}:{m['status']}")
        if m["total_row_count"] != 67_183:
            raise ValueError(f"manifest row count mismatch:{symbol}")
        observed[symbol] = m["fingerprint"]
    return d, observed


def derive_signals(symbol: str, segment: list[Candle]) -> tuple[list[Signal], int, int]:
    series = common.validate_1d(segment, regular=True)
    atr14 = common.atr_series(series, ATR_LENGTH)
    ready: list[Signal] = []
    raw = cancelled = 0
    start = max(LOOKBACK, ATR_LENGTH)
    for i in range(start, len(series) - 1):
        if atr14[i] is None:
            continue
        signal = series[i]
        prior_high = max(c.high for c in series[i - LOOKBACK : i])
        if not signal.close > prior_high:
            continue
        raw += 1
        atr = float(atr14[i])
        stop = signal.low - STOP_ATR_FRACTION * atr
        entry_candle = series[i + 1]
        entry = entry_candle.open
        if stop <= 0 or entry <= stop:
            cancelled += 1
            continue
        risk = (entry - stop) / entry
        if risk <= 0 or not isfinite(risk):
            cancelled += 1
            continue
        target = entry + TARGET_R * (entry - stop)
        payload = {
            "setup_id": SETUP_ID,
            "symbol": symbol,
            "signal_open_time": signal.open_time,
            "entry_open_time": entry_candle.open_time,
            "prior_20_day_high": prior_high,
            "atr14": atr,
            "signal_low": signal.low,
            "signal_close": signal.close,
            "entry": entry,
            "stop": stop,
            "target": target,
            "initial_risk_fraction": risk,
        }
        ready.append(
            Signal(
                symbol=symbol,
                signal_open_time=signal.open_time,
                entry_open_time=entry_candle.open_time,
                prior_20_day_high=prior_high,
                atr14=atr,
                signal_low=signal.low,
                signal_close=signal.close,
                entry=entry,
                stop=stop,
                target=target,
                initial_risk_fraction=risk,
                fingerprint=canonical_hash(payload),
            )
        )
    return ready, raw, cancelled


def simulate(signal: Signal, segment: list[Candle], cost_pct: float) -> Outcome:
    series = common.validate_1d(segment, regular=True)
    entry_idx = next((i for i, c in enumerate(series) if c.open_time == signal.entry_open_time), None)
    if entry_idx is None:
        raise ValueError("entry bar missing")
    if abs(series[entry_idx].open - signal.entry) > max(1e-12, abs(signal.entry) * 1e-12):
        raise ValueError("entry price mismatch")
    cost_fraction = cost_pct / 100.0
    denom = signal.initial_risk_fraction + cost_fraction

    def finish(reason: str, c: Candle, price: float, bars: int, ambiguity: bool) -> Outcome:
        gross = (price - signal.entry) / signal.entry
        net_r = (gross - cost_fraction) / denom
        return Outcome(reason, c.open_time, price, bars, gross * 100.0, net_r, ambiguity)

    last_idx = min(len(series) - 1, entry_idx + MAX_HOLD - 1)
    for i in range(entry_idx, last_idx + 1):
        c = series[i]
        bars = i - entry_idx + 1
        if c.open <= signal.stop:
            return finish("STOP_GAP", c, c.open, bars, False)
        if c.open >= signal.target:
            return finish("TARGET", c, signal.target, bars, False)
        stop_hit = c.low <= signal.stop
        target_hit = c.high >= signal.target
        if stop_hit and target_hit:
            return finish("STOP_AMBIGUOUS_SAME_BAR", c, signal.stop, bars, True)
        if stop_hit:
            return finish("STOP", c, signal.stop, bars, False)
        if target_hit:
            return finish("TARGET", c, signal.target, bars, False)

    exit_idx = entry_idx + MAX_HOLD
    if exit_idx >= len(series):
        return Outcome("UNRESOLVED_END_OF_DATA", None, None, None, None, None, False)
    c = series[exit_idx]
    return finish("TIME_EXIT_NEXT_OPEN", c, c.open, MAX_HOLD, False)


def evaluate_symbol(symbol: str, candles: list[Candle]) -> tuple[list[TradeRecord], dict[str, int]]:
    segments, gaps = common.split_segments(candles)
    records: list[TradeRecord] = []
    raw = cancelled = overlap = 0
    for segment in segments:
        signals, r, c = derive_signals(symbol, segment)
        raw += r
        cancelled += c
        active_until: int | None = None
        for sig in signals:
            if active_until is not None and sig.entry_open_time <= active_until:
                overlap += 1
                continue
            outcome = simulate(sig, segment, BASE_COST_PCT)
            records.append(TradeRecord(symbol, sig, outcome))
            active_until = outcome.exit_open_time if outcome.exit_open_time is not None else segment[-1].open_time
    return records, {
        "raw_trigger_count": raw,
        "pre_entry_cancelled_count": cancelled,
        "overlap_skipped_count": overlap,
        "contiguous_segment_count": len(segments),
        "detected_gap_count": gaps,
    }


def evaluate_universe(candles_by_symbol: dict[str, list[Candle]]) -> tuple[list[TradeRecord], EvaluationMetrics]:
    records: list[TradeRecord] = []
    totals = Counter()
    all_times: list[int] = []
    for symbol in sorted(candles_by_symbol):
        all_times.extend(c.open_time for c in candles_by_symbol[symbol])
        rows, diag = evaluate_symbol(symbol, candles_by_symbol[symbol])
        records.extend(rows)
        totals.update(diag)
    records.sort(key=lambda r: (r.signal.entry_open_time, r.symbol, r.signal.fingerprint))
    resolved = [r for r in records if r.outcome.net_r is not None]
    values = [float(r.outcome.net_r) for r in resolved]
    selected = len(records)
    count = len(resolved)
    frequency = None
    if all_times and selected:
        span_days = (max(all_times) - min(all_times) + DAY_MS) / DAY_MS
        frequency = selected / span_days * 30.0
    outcomes = [r.outcome for r in resolved]
    metrics = EvaluationMetrics(
        cost_scenario="BASE_0.20PCT_RT",
        raw_trigger_count=totals["raw_trigger_count"],
        pre_entry_cancelled_count=totals["pre_entry_cancelled_count"],
        selected_trade_count=selected,
        overlap_skipped_count=totals["overlap_skipped_count"],
        unresolved_trade_count=selected - count,
        resolved_trade_count=count,
        net_expectancy_r=mean(values) if values else None,
        median_net_r=median(values) if values else None,
        win_rate=common.safe_rate(sum(v > 0 for v in values), count),
        loss_rate=common.safe_rate(sum(v < 0 for v in values), count),
        profit_factor_r=common.profit_factor(values),
        target_reach_rate=common.safe_rate(sum(o.exit_reason == "TARGET" for o in outcomes), count),
        same_bar_ambiguity_rate=common.safe_rate(sum(o.same_bar_stop_target_ambiguity for o in outcomes), count),
        time_exit_rate=common.safe_rate(sum(o.exit_reason == "TIME_EXIT_NEXT_OPEN" for o in outcomes), count),
        stop_gap_rate=common.safe_rate(sum(o.exit_reason == "STOP_GAP" for o in outcomes), count),
        signal_frequency_per_30d=frequency,
        symbol_distribution=dict(sorted(Counter(r.symbol for r in resolved).items())),
        contiguous_segment_count=totals["contiguous_segment_count"],
        detected_gap_count=totals["detected_gap_count"],
    )
    return records, metrics


def reprice_stress(records: Iterable[TradeRecord]) -> StressMetrics:
    rows = list(records)
    values: list[float] = []
    cost_fraction = STRESS_COST_PCT / 100.0
    for r in rows:
        if r.outcome.gross_return_pct is None:
            continue
        gross = r.outcome.gross_return_pct / 100.0
        denom = r.signal.initial_risk_fraction + cost_fraction
        values.append((gross - cost_fraction) / denom)
    return StressMetrics(
        cost_scenario="STRESS_0.30PCT_RT",
        cohort_source="BASE_SELECTED_TFG_DONCHIAN_1D_TRADES",
        selected_trade_count=len(rows),
        resolved_trade_count=len(values),
        unresolved_trade_count=len(rows) - len(values),
        net_expectancy_r=mean(values) if values else None,
        median_net_r=median(values) if values else None,
        profit_factor_r=common.profit_factor(values),
    )


def bootstrap_expectancy(records: Iterable[TradeRecord]) -> BootstrapInterval:
    # The generic bootstrap only requires .signal.entry_open_time and .outcome.net_r.
    return common.bootstrap_expectancy(records)  # type: ignore[arg-type]


def classify(base: EvaluationMetrics, stress: StressMetrics, bootstrap: BootstrapInterval) -> DiscoveryDecision:
    failures: list[str] = []
    resolved = base.resolved_trade_count
    if resolved < MIN_RESOLVED:
        classification = "INSUFFICIENT_SAMPLE"
        failures.append("resolved_trade_count_below_100")
    else:
        checks = (
            (base.net_expectancy_r, 0.0, "base_net_expectancy_not_positive"),
            (base.profit_factor_r, 1.0, "base_profit_factor_not_above_1"),
            (bootstrap.lower, 0.0, "bootstrap_lower_95_not_positive"),
            (stress.net_expectancy_r, 0.0, "fixed_cohort_stress_expectancy_not_positive"),
        )
        for value, threshold, reason in checks:
            if value is None or not isfinite(float(value)) or float(value) <= threshold:
                failures.append(reason)
        classification = "NO_EDGE" if failures else "SURVIVES"
    payload = {
        "lab_id": LAB_ID,
        "stage": "DISCOVERY",
        "classification": classification,
        "resolved_trade_count": resolved,
        "minimum_required_trades": MIN_RESOLVED,
        "base_net_expectancy_r": base.net_expectancy_r,
        "base_profit_factor_r": base.profit_factor_r,
        "base_bootstrap_lower_95": bootstrap.lower,
        "fixed_cohort_stress_net_expectancy_r": stress.net_expectancy_r,
        "failed_conditions": tuple(failures),
        "validation_unlock_eligible": classification == "SURVIVES",
        "live_authorized": False,
    }
    return DiscoveryDecision(**payload, fingerprint=canonical_hash(payload))


def run(canonical_dir: Path, manifest_dir: Path, binding_path: Path, output_dir: Path) -> DiscoveryReceipt:
    try:
        load_freeze()
        binding, observed_fps = load_binding(binding_path, manifest_dir)
    except Exception as exc:
        return blocked(f"PRE_OUTCOME_BINDING:{type(exc).__name__}:{exc}")

    start_ms = common.parse_ms(DISCOVERY_START)
    end_ms = common.parse_ms(DISCOVERY_END)
    daily_by_symbol: dict[str, list[Candle]] = {}
    source_counts: dict[str, int] = {}
    derived_counts: dict[str, int] = {}
    incomplete_total = 0
    try:
        for symbol in FROZEN_UNIVERSE:
            source: list[Candle] = []
            for month in common.month_sequence(START_MONTH, END_MONTH):
                p = canonical_dir / f"{common.prefix(symbol)}-Min15-{month}-01.canonical.csv"
                if not p.is_file():
                    raise FileNotFoundError(p.name)
                source.extend(common.load_canonical(p, start_ms, end_ms))
            source_counts[symbol] = len(source)
            if len(source) != EXPECTED_EFFECTIVE_15M_PER_SYMBOL:
                raise ValueError(f"EFFECTIVE_15M_COUNT_MISMATCH:{symbol}:{len(source)}")
            daily, incomplete = common.aggregate_15m_to_1d(source)
            incomplete_total += incomplete
            derived_counts[symbol] = len(daily)
            if len(daily) != EXPECTED_1D_PER_SYMBOL:
                raise ValueError(f"DERIVED_1D_COUNT_MISMATCH:{symbol}:{len(daily)}")
            if not daily or daily[0].open_time != start_ms:
                raise ValueError(f"DAILY_START_BOUNDARY_MISMATCH:{symbol}")
            daily_by_symbol[symbol] = daily
        if incomplete_total != 18:
            raise ValueError(f"INCOMPLETE_BUCKET_TOTAL_MISMATCH:{incomplete_total}")
    except Exception as exc:
        return blocked(f"SOURCE_TRANSFORM:{type(exc).__name__}:{exc}", source_binding_status=binding["status"])

    # FIRST REAL MARKET OUTCOME EVALUATION POINT FOR THIS HYPOTHESIS.
    base_records, base_metrics = evaluate_universe(daily_by_symbol)
    stress = reprice_stress(base_records)
    bootstrap = bootstrap_expectancy(base_records)
    decision = classify(base_metrics, stress, bootstrap)

    output_dir.mkdir(parents=True, exist_ok=True)
    ledger = [{"symbol": r.symbol, "signal": asdict(r.signal), "outcome": asdict(r.outcome)} for r in base_records]
    (output_dir / "TFG_DONCHIAN_1D_DISCOVERY_LEDGER_V0.1.json").write_text(
        json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    receipt = finalize_receipt(
        DiscoveryReceipt(
            status="TFG_DONCHIAN_1D_DISCOVERY_COMPLETE",
            reasons=(),
            lab_id=LAB_ID,
            source_timeframe="15m",
            derived_timeframe="1d",
            universe=FROZEN_UNIVERSE,
            discovery_start_utc=DISCOVERY_START,
            discovery_end_utc=DISCOVERY_END,
            source_binding_status=binding["status"],
            parent_corpus_fingerprint_by_symbol=observed_fps,
            source_15m_count_by_symbol=source_counts,
            derived_1d_count_by_symbol=derived_counts,
            total_incomplete_1d_buckets=incomplete_total,
            base_metrics=asdict(base_metrics),
            fixed_cohort_stress_metrics=asdict(stress),
            bootstrap=asdict(bootstrap),
            decision=asdict(decision),
            validation_2025_access_performed=False,
            holdout_2026_access_performed=False,
            network_access_performed=False,
            exchange_mutation_performed=False,
            submitted_to_exchange=False,
            outcome_evaluation_performed=True,
            fingerprint="",
        )
    )
    (output_dir / "TFG_DONCHIAN_1D_DISCOVERY_RECEIPT_V0.1.json").write_text(
        json.dumps(asdict(receipt), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return receipt


def self_test() -> dict[str, Any]:
    base_ms = common.parse_ms("2024-01-01T00:00:00.000Z")
    daily: list[Candle] = []
    for i in range(70):
        t = base_ms + i * DAY_MS
        p = 100.0 + i * 0.05
        daily.append(Candle(t, p, p + 1.0, p - 1.0, p + 0.1, 10.0, t + DAY_MS - 1))
    sig_i = 30
    prior_high = max(c.high for c in daily[sig_i - LOOKBACK : sig_i])
    old = daily[sig_i]
    daily[sig_i] = Candle(old.open_time, prior_high - 0.2, prior_high + 1.0, prior_high - 0.5, prior_high + 0.5, 10.0, old.close_time)
    signals, raw, cancelled = derive_signals("BTCUSDT", daily)
    assert raw >= 1 and cancelled == 0 and signals
    sig = next(s for s in signals if s.signal_open_time == daily[sig_i].open_time)
    assert sig.signal_close > sig.prior_20_day_high
    assert sig.target > sig.entry > sig.stop

    # Explicit same-bar ambiguity must stop out conservatively.
    eidx = next(i for i, c in enumerate(daily) if c.open_time == sig.entry_open_time)
    c = daily[eidx]
    daily[eidx] = Candle(c.open_time, sig.entry, sig.target * 1.01, sig.stop * 0.99, sig.entry, c.volume, c.close_time)
    outcome = simulate(sig, daily, BASE_COST_PCT)
    assert outcome.exit_reason == "STOP_AMBIGUOUS_SAME_BAR" and outcome.same_bar_stop_target_ambiguity

    return {
        "self_test": "PASS",
        "synthetic_raw_triggers": raw,
        "synthetic_ready_signals": len(signals),
        "ambiguity_policy": outcome.exit_reason,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--canonical-dir")
    parser.add_argument("--manifest-dir")
    parser.add_argument("--binding")
    parser.add_argument("--output-dir")
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(), indent=2, sort_keys=True))
        return 0
    if not all((args.canonical_dir, args.manifest_dir, args.binding, args.output_dir)):
        parser.error("discovery mode requires canonical-dir, manifest-dir, binding and output-dir")
    receipt = run(Path(args.canonical_dir), Path(args.manifest_dir), Path(args.binding), Path(args.output_dir))
    print(json.dumps(asdict(receipt), indent=2, sort_keys=True))
    return 0 if receipt.status == "TFG_DONCHIAN_1D_DISCOVERY_COMPLETE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
