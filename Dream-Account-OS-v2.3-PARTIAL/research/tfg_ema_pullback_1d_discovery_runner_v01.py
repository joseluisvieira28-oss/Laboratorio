from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from math import isfinite
from pathlib import Path
from random import Random
from statistics import mean, median
from typing import Any, Iterable

LAB_ID = "TFG-EMA-PULLBACK-1D-001"
SETUP_ID = "EMA20_EMA50_DAILY_PULLBACK_RECLAIM_LONG"
DAY_MS = 86_400_000
FIFTEEN_MIN_MS = 900_000
CANDLES_PER_DAY = 96
FROZEN_UNIVERSE = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT")
START_MONTH = "2023-02"
END_MONTH = "2024-12"
DISCOVERY_START = "2023-02-01T00:00:00.000Z"
DISCOVERY_END = "2024-12-31T16:00:00.000Z"
EXPECTED_EFFECTIVE_15M_PER_SYMBOL = 67_151
EXPECTED_1D_PER_SYMBOL = 697
EMA_FAST = 20
EMA_SLOW = 50
ATR_LENGTH = 14
STOP_ATR_FRACTION = 0.25
TARGET_R = 2.0
MAX_HOLD = 20
MIN_RESOLVED = 100
BASE_COST_PCT = 0.20
STRESS_COST_PCT = 0.30
BOOTSTRAP_REPS = 5000
BOOTSTRAP_SEED = 230911
BOOTSTRAP_CONFIDENCE = 0.95
CANONICAL_HEADER = ("open_time_ms", "open", "high", "low", "close", "volume", "close_time_ms")

ROOT = Path(__file__).resolve().parents[1]
FREEZE_PATH = ROOT / "research" / "timeframe_gap" / "TFG_EMA_PULLBACK_1D_001_FREEZE.json"


@dataclass(frozen=True)
class Candle:
    open_time: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    close_time: int


@dataclass(frozen=True)
class Signal:
    symbol: str
    signal_open_time: int
    entry_open_time: int
    ema20: float
    ema50: float
    atr14: float
    signal_low: float
    signal_close: float
    entry: float
    stop: float
    target: float
    initial_risk_fraction: float
    fingerprint: str


@dataclass(frozen=True)
class Outcome:
    exit_reason: str
    exit_open_time: int | None
    exit_price: float | None
    bars_held: int | None
    gross_return_pct: float | None
    net_r: float | None
    same_bar_stop_target_ambiguity: bool


@dataclass(frozen=True)
class TradeRecord:
    symbol: str
    signal: Signal
    outcome: Outcome


@dataclass(frozen=True)
class EvaluationMetrics:
    cost_scenario: str
    raw_trigger_count: int
    pre_entry_cancelled_count: int
    selected_trade_count: int
    overlap_skipped_count: int
    unresolved_trade_count: int
    resolved_trade_count: int
    net_expectancy_r: float | None
    median_net_r: float | None
    win_rate: float | None
    loss_rate: float | None
    profit_factor_r: float | None
    target_reach_rate: float | None
    same_bar_ambiguity_rate: float | None
    time_exit_rate: float | None
    stop_gap_rate: float | None
    signal_frequency_per_30d: float | None
    symbol_distribution: dict[str, int]
    contiguous_segment_count: int
    detected_gap_count: int


@dataclass(frozen=True)
class StressMetrics:
    cost_scenario: str
    cohort_source: str
    selected_trade_count: int
    resolved_trade_count: int
    unresolved_trade_count: int
    net_expectancy_r: float | None
    median_net_r: float | None
    profit_factor_r: float | None


@dataclass(frozen=True)
class BootstrapInterval:
    method: str
    repetitions: int
    seed: int
    confidence: float
    sample_days: int
    lower: float | None
    point_estimate: float | None
    upper: float | None
    undefined_reason: str | None


@dataclass(frozen=True)
class DiscoveryDecision:
    lab_id: str
    stage: str
    classification: str
    resolved_trade_count: int
    minimum_required_trades: int
    base_net_expectancy_r: float | None
    base_profit_factor_r: float | None
    base_bootstrap_lower_95: float | None
    fixed_cohort_stress_net_expectancy_r: float | None
    failed_conditions: tuple[str, ...]
    validation_unlock_eligible: bool
    live_authorized: bool
    fingerprint: str


@dataclass(frozen=True)
class DiscoveryReceipt:
    status: str
    reasons: tuple[str, ...]
    lab_id: str
    source_timeframe: str
    derived_timeframe: str
    universe: tuple[str, ...]
    discovery_start_utc: str
    discovery_end_utc: str
    source_binding_status: str | None
    parent_corpus_fingerprint_by_symbol: dict[str, str]
    source_15m_count_by_symbol: dict[str, int]
    derived_1d_count_by_symbol: dict[str, int]
    total_incomplete_1d_buckets: int
    base_metrics: dict[str, Any] | None
    fixed_cohort_stress_metrics: dict[str, Any] | None
    bootstrap: dict[str, Any] | None
    decision: dict[str, Any] | None
    validation_2025_access_performed: bool
    holdout_2026_access_performed: bool
    network_access_performed: bool
    exchange_mutation_performed: bool
    submitted_to_exchange: bool
    outcome_evaluation_performed: bool
    fingerprint: str


def canonical_hash(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()


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


def parse_ms(value: str) -> int:
    return int(datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc).timestamp() * 1000)


def month_sequence(start: str, end: str) -> list[str]:
    cur = datetime.strptime(start, "%Y-%m")
    finish = datetime.strptime(end, "%Y-%m")
    out: list[str] = []
    while cur <= finish:
        out.append(cur.strftime("%Y-%m"))
        cur = cur.replace(
            year=cur.year + (1 if cur.month == 12 else 0),
            month=1 if cur.month == 12 else cur.month + 1,
            day=1,
        )
    return out


def prefix(symbol: str) -> str:
    if symbol not in FROZEN_UNIVERSE:
        raise ValueError("symbol outside frozen universe")
    return f"{symbol[:-4]}_USDT"


def load_freeze() -> dict[str, Any]:
    d = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    assert d["experiment_id"] == LAB_ID
    assert d["status"] == "FROZEN_BEFORE_ANY_EXPERIMENT_OUTCOME_EVALUATION"
    assert d["lineage"]["this_experiment_is_historical_replication"] is False
    assert d["indicator_definition"]["ema_fast_length"] == EMA_FAST
    assert d["indicator_definition"]["ema_slow_length"] == EMA_SLOW
    assert d["indicator_definition"]["atr_length"] == ATR_LENGTH
    assert d["signal_rules"]["stop"] == "signal_low - 0.25 * ATR14_signal"
    assert d["signal_rules"]["target"] == "entry + 2.0 * (entry - stop)"
    assert d["execution_semantics"]["max_holding_bars"] == MAX_HOLD
    assert d["costs"]["BASE_round_trip_pct"] == BASE_COST_PCT
    assert d["costs"]["STRESS_round_trip_pct"] == STRESS_COST_PCT
    assert d["discovery"]["minimum_resolved_trades"] == MIN_RESOLVED
    assert d["discovery"]["start_utc_inclusive"] == DISCOVERY_START
    assert d["discovery"]["end_utc_exclusive"] == DISCOVERY_END
    assert d["protected_data"]["validation_2025"].startswith("LOCKED_")
    assert d["protected_data"]["holdout_2026"].startswith("LOCKED_")
    assert d["governance"]["2025_access"] is False
    assert d["governance"]["2026_access"] is False
    assert d["governance"]["live_trading"] is False
    assert d["governance"]["exchange_mutation"] is False
    return d


def load_binding(path: Path, manifest_dir: Path) -> tuple[dict[str, Any], dict[str, str]]:
    d = json.loads(path.read_text(encoding="utf-8"))
    if d["experiment_id"] != LAB_ID:
        raise ValueError("binding experiment mismatch")
    if d["status"] != "FROZEN_EXACT_SOURCE_BEFORE_ANY_EMA_1D_OUTCOME_EVALUATION":
        raise ValueError("binding status mismatch")
    if d["artifact_id"] != 10419067320:
        raise ValueError("artifact id mismatch")
    if d["artifact_digest"] != "sha256:7b2562af14983d0344c9a28e81e9c1866f2e5e9dfafe94203da9a4ca1ffa36cb":
        raise ValueError("artifact digest mismatch")
    expected = dict(d["parent_corpus_fingerprint_by_symbol"])
    observed: dict[str, str] = {}
    for symbol in FROZEN_UNIVERSE:
        m = json.loads((manifest_dir / f"{symbol}_MANIFEST.json").read_text(encoding="utf-8"))
        fp = m["fingerprint"]
        if fp != expected[symbol]:
            raise ValueError(f"manifest fingerprint mismatch:{symbol}")
        if m["status"] != "PASS_CORPUS_AUDIT_ONLY_WITH_GAPS":
            raise ValueError(f"manifest status mismatch:{symbol}:{m['status']}")
        if m["total_row_count"] != 67_183:
            raise ValueError(f"manifest row count mismatch:{symbol}")
        observed[symbol] = fp
    return d, observed


def load_canonical(path: Path, start_ms: int, end_ms: int) -> list[Candle]:
    out: list[Candle] = []
    with path.open("r", encoding="utf-8", newline="") as h:
        reader = csv.DictReader(h)
        if tuple(reader.fieldnames or ()) != CANONICAL_HEADER:
            raise ValueError(f"canonical header mismatch:{path.name}")
        for row in reader:
            t = int(row["open_time_ms"])
            if not (start_ms <= t < end_ms):
                continue
            c = Candle(
                open_time=t,
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=float(row["volume"]),
                close_time=int(row["close_time_ms"]),
            )
            out.append(c)
    return out


def validate_15m(candles: Iterable[Candle]) -> list[Candle]:
    series = sorted(candles, key=lambda c: c.open_time)
    seen: set[int] = set()
    for c in series:
        if c.open_time in seen:
            raise ValueError("duplicate 15m timestamp")
        seen.add(c.open_time)
        if c.open_time % FIFTEEN_MIN_MS != 0 or c.close_time != c.open_time + FIFTEEN_MIN_MS - 1:
            raise ValueError("15m timestamp/alignment violation")
        vals = (c.open, c.high, c.low, c.close, c.volume)
        if any(not isfinite(v) for v in vals):
            raise ValueError("non-finite candle")
        if min(c.open, c.high, c.low, c.close) <= 0 or c.volume < 0:
            raise ValueError("invalid candle values")
        if c.high < max(c.open, c.close, c.low) or c.low > min(c.open, c.close, c.high):
            raise ValueError("OHLC ordering violation")
    return series


def aggregate_15m_to_1d(candles: Iterable[Candle]) -> tuple[list[Candle], int]:
    series = validate_15m(candles)
    buckets: dict[int, list[Candle]] = defaultdict(list)
    for c in series:
        day = c.open_time - (c.open_time % DAY_MS)
        buckets[day].append(c)
    out: list[Candle] = []
    incomplete = 0
    for day in sorted(buckets):
        items = sorted(buckets[day], key=lambda c: c.open_time)
        expected = [day + i * FIFTEEN_MIN_MS for i in range(CANDLES_PER_DAY)]
        if len(items) != CANDLES_PER_DAY or [c.open_time for c in items] != expected:
            incomplete += 1
            continue
        out.append(
            Candle(
                open_time=day,
                open=items[0].open,
                high=max(c.high for c in items),
                low=min(c.low for c in items),
                close=items[-1].close,
                volume=sum(c.volume for c in items),
                close_time=day + DAY_MS - 1,
            )
        )
    return out, incomplete


def validate_1d(candles: Iterable[Candle], *, regular: bool) -> list[Candle]:
    series = list(candles)
    prev: int | None = None
    for c in series:
        if c.open_time % DAY_MS != 0 or c.close_time != c.open_time + DAY_MS - 1:
            raise ValueError("1d timestamp/alignment violation")
        if prev is not None:
            if c.open_time <= prev:
                raise ValueError("1d timestamps not increasing")
            if regular and c.open_time - prev != DAY_MS:
                raise ValueError("1d gap")
        prev = c.open_time
    return series


def split_segments(candles: Iterable[Candle]) -> tuple[list[list[Candle]], int]:
    series = validate_1d(candles, regular=False)
    if not series:
        return [], 0
    segments: list[list[Candle]] = [[series[0]]]
    gaps = 0
    for c in series[1:]:
        if c.open_time - segments[-1][-1].open_time == DAY_MS:
            segments[-1].append(c)
        else:
            gaps += 1
            segments.append([c])
    return segments, gaps


def ema_series(closes: list[float], length: int) -> list[float | None]:
    out: list[float | None] = [None] * len(closes)
    if len(closes) < length:
        return out
    seed = mean(closes[:length])
    out[length - 1] = seed
    alpha = 2.0 / (length + 1.0)
    value = seed
    for i in range(length, len(closes)):
        value = alpha * closes[i] + (1.0 - alpha) * value
        out[i] = value
    return out


def atr_series(candles: list[Candle], length: int) -> list[float | None]:
    out: list[float | None] = [None] * len(candles)
    if len(candles) <= length:
        return out
    trs: list[float | None] = [None]
    for i in range(1, len(candles)):
        c, p = candles[i], candles[i - 1]
        trs.append(max(c.high - c.low, abs(c.high - p.close), abs(c.low - p.close)))
    seed_values = [float(x) for x in trs[1 : length + 1] if x is not None]
    if len(seed_values) != length:
        return out
    value = mean(seed_values)
    out[length] = value
    for i in range(length + 1, len(candles)):
        tr = float(trs[i])
        value = ((value * (length - 1)) + tr) / length
        out[i] = value
    return out


def derive_signals(symbol: str, segment: list[Candle]) -> tuple[list[Signal], int, int]:
    series = validate_1d(segment, regular=True)
    closes = [c.close for c in series]
    e20, e50, atr14 = ema_series(closes, EMA_FAST), ema_series(closes, EMA_SLOW), atr_series(series, ATR_LENGTH)
    ready: list[Signal] = []
    raw = cancelled = 0
    start = max(EMA_SLOW - 1, ATR_LENGTH, 1)
    for i in range(start, len(series) - 1):
        if e20[i] is None or e50[i] is None or e20[i - 1] is None or atr14[i] is None:
            continue
        signal = series[i]
        prev = series[i - 1]
        ema20 = float(e20[i])
        ema50 = float(e50[i])
        if not (
            ema20 > ema50
            and prev.close > float(e20[i - 1])
            and signal.low <= ema20
            and signal.close >= ema20
            and signal.close > signal.open
        ):
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
            "ema20": ema20,
            "ema50": ema50,
            "atr14": atr,
            "signal_low": signal.low,
            "signal_close": signal.close,
            "entry": entry,
            "stop": stop,
            "target": target,
            "initial_risk_fraction": risk,
        }
        ready.append(Signal(**{k: v for k, v in payload.items() if k not in {"setup_id"}}, fingerprint=canonical_hash(payload)))
    return ready, raw, cancelled


def simulate(signal: Signal, segment: list[Candle], cost_pct: float) -> Outcome:
    series = validate_1d(segment, regular=True)
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


def safe_rate(n: int, d: int) -> float | None:
    return n / d if d else None


def profit_factor(values: list[float]) -> float | None:
    gains = sum(v for v in values if v > 0)
    losses = -sum(v for v in values if v < 0)
    return gains / losses if losses > 0 else None


def evaluate_symbol(symbol: str, candles: list[Candle]) -> tuple[list[TradeRecord], dict[str, int]]:
    segments, gaps = split_segments(candles)
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
        r, diag = evaluate_symbol(symbol, candles_by_symbol[symbol])
        records.extend(r)
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
        win_rate=safe_rate(sum(v > 0 for v in values), count),
        loss_rate=safe_rate(sum(v < 0 for v in values), count),
        profit_factor_r=profit_factor(values),
        target_reach_rate=safe_rate(sum(o.exit_reason == "TARGET" for o in outcomes), count),
        same_bar_ambiguity_rate=safe_rate(sum(o.same_bar_stop_target_ambiguity for o in outcomes), count),
        time_exit_rate=safe_rate(sum(o.exit_reason == "TIME_EXIT_NEXT_OPEN" for o in outcomes), count),
        stop_gap_rate=safe_rate(sum(o.exit_reason == "STOP_GAP" for o in outcomes), count),
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
        cohort_source="BASE_SELECTED_TFG_EMA_PULLBACK_1D_TRADES",
        selected_trade_count=len(rows),
        resolved_trade_count=len(values),
        unresolved_trade_count=len(rows) - len(values),
        net_expectancy_r=mean(values) if values else None,
        median_net_r=median(values) if values else None,
        profit_factor_r=profit_factor(values),
    )


def percentile(sorted_values: list[float], p: float) -> float:
    if p <= 0:
        return sorted_values[0]
    if p >= 1:
        return sorted_values[-1]
    pos = (len(sorted_values) - 1) * p
    lo = int(pos)
    hi = min(lo + 1, len(sorted_values) - 1)
    frac = pos - lo
    return sorted_values[lo] * (1 - frac) + sorted_values[hi] * frac


def bootstrap_expectancy(records: Iterable[TradeRecord]) -> BootstrapInterval:
    grouped: dict[str, list[float]] = defaultdict(list)
    for r in records:
        if r.outcome.net_r is None:
            continue
        day = datetime.fromtimestamp(r.signal.entry_open_time / 1000, tz=timezone.utc).date().isoformat()
        grouped[day].append(float(r.outcome.net_r))
    days = sorted(grouped)
    point_values = [v for day in days for v in grouped[day]]
    if not point_values:
        return BootstrapInterval(
            "UTC_CALENDAR_DAY_BLOCK_BOOTSTRAP",
            BOOTSTRAP_REPS,
            BOOTSTRAP_SEED,
            BOOTSTRAP_CONFIDENCE,
            0,
            None,
            None,
            None,
            "NO_RESOLVED_TRADES",
        )
    rng = Random(BOOTSTRAP_SEED)
    draws: list[float] = []
    for _ in range(BOOTSTRAP_REPS):
        sample: list[float] = []
        for _ in range(len(days)):
            sample.extend(grouped[days[rng.randrange(len(days))]])
        draws.append(mean(sample))
    draws.sort()
    tail = (1 - BOOTSTRAP_CONFIDENCE) / 2
    return BootstrapInterval(
        "UTC_CALENDAR_DAY_BLOCK_BOOTSTRAP",
        BOOTSTRAP_REPS,
        BOOTSTRAP_SEED,
        BOOTSTRAP_CONFIDENCE,
        len(days),
        percentile(draws, tail),
        mean(point_values),
        percentile(draws, 1 - tail),
        None,
    )


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

    start_ms, end_ms = parse_ms(DISCOVERY_START), parse_ms(DISCOVERY_END)
    daily_by_symbol: dict[str, list[Candle]] = {}
    source_counts: dict[str, int] = {}
    derived_counts: dict[str, int] = {}
    incomplete_total = 0
    try:
        for symbol in FROZEN_UNIVERSE:
            source: list[Candle] = []
            for month in month_sequence(START_MONTH, END_MONTH):
                p = canonical_dir / f"{prefix(symbol)}-Min15-{month}-01.canonical.csv"
                if not p.is_file():
                    raise FileNotFoundError(p.name)
                source.extend(load_canonical(p, start_ms, end_ms))
            source_counts[symbol] = len(source)
            if len(source) != EXPECTED_EFFECTIVE_15M_PER_SYMBOL:
                raise ValueError(f"EFFECTIVE_15M_COUNT_MISMATCH:{symbol}:{len(source)}")
            daily, incomplete = aggregate_15m_to_1d(source)
            incomplete_total += incomplete
            derived_counts[symbol] = len(daily)
            if len(daily) != EXPECTED_1D_PER_SYMBOL:
                raise ValueError(f"DERIVED_1D_COUNT_MISMATCH:{symbol}:{len(daily)}")
            if not daily or daily[0].open_time != start_ms:
                raise ValueError(f"DAILY_START_BOUNDARY_MISMATCH:{symbol}")
            daily_by_symbol[symbol] = daily
    except Exception as exc:
        return blocked(f"SOURCE_TRANSFORM:{type(exc).__name__}:{exc}", source_binding_status=binding["status"])

    # FIRST REAL MARKET OUTCOME EVALUATION POINT FOR THIS NEW HYPOTHESIS.
    base_records, base_metrics = evaluate_universe(daily_by_symbol)
    stress = reprice_stress(base_records)
    bootstrap = bootstrap_expectancy(base_records)
    decision = classify(base_metrics, stress, bootstrap)

    output_dir.mkdir(parents=True, exist_ok=True)
    ledger = [{"symbol": r.symbol, "signal": asdict(r.signal), "outcome": asdict(r.outcome)} for r in base_records]
    (output_dir / "TFG_EMA_PULLBACK_1D_DISCOVERY_LEDGER_V0.1.json").write_text(
        json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    receipt = finalize_receipt(
        DiscoveryReceipt(
            status="TFG_EMA_PULLBACK_1D_DISCOVERY_COMPLETE",
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
    (output_dir / "TFG_EMA_PULLBACK_1D_DISCOVERY_RECEIPT_V0.1.json").write_text(
        json.dumps(asdict(receipt), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return receipt


def self_test() -> dict[str, Any]:
    source: list[Candle] = []
    base = parse_ms("2024-01-01T00:00:00.000Z")
    price = 100.0
    for i in range(2 * CANDLES_PER_DAY):
        t = base + i * FIFTEEN_MIN_MS
        source.append(Candle(t, price, price + 1, price - 1, price + 0.1, 1.0, t + FIFTEEN_MIN_MS - 1))
        price += 0.01
    two, inc0 = aggregate_15m_to_1d(source)
    one, inc1 = aggregate_15m_to_1d(source[1:])
    assert len(two) == 2 and inc0 == 0
    assert len(one) == 1 and inc1 == 1

    const = [10.0] * 60
    e = ema_series(const, 20)
    assert e[19] == 10.0 and e[-1] == 10.0

    daily: list[Candle] = []
    p = 100.0
    for i in range(65):
        t = base + i * DAY_MS
        o = p
        c = p * 1.003
        hi = c * 1.005
        lo = o * 0.998
        daily.append(Candle(t, o, hi, lo, c, 10.0, t + DAY_MS - 1))
        p = c
    e20 = ema_series([c.close for c in daily], 20)
    sig_i = 58
    ema_at = float(e20[sig_i])
    old = daily[sig_i]
    daily[sig_i] = Candle(
        old.open_time,
        ema_at * 0.995,
        ema_at * 1.02,
        ema_at * 0.99,
        ema_at * 1.01,
        old.volume,
        old.close_time,
    )
    signals, raw, cancelled = derive_signals("BTCUSDT", daily)
    assert raw >= 1 and cancelled == 0 and signals

    return {
        "self_test": "PASS",
        "complete_day_aggregation": len(two),
        "gap_case_day_aggregation": len(one),
        "synthetic_raw_triggers": raw,
        "synthetic_ready_signals": len(signals),
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
    return 0 if receipt.status == "TFG_EMA_PULLBACK_1D_DISCOVERY_COMPLETE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
