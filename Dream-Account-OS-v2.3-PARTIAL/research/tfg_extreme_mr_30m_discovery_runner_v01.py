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

LAB_ID = "TFG-EXTREME-MR-30M-001"
SETUP_ID = "EMA20_MINUS_1P5ATR_LONG_MEAN_REVERSION_30M"
FIFTEEN_MIN_MS = 900_000
THIRTY_MIN_MS = 1_800_000
CHILDREN_PER_30M = 2
UNIVERSE = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT")
START_MONTH = "2023-02"
END_MONTH = "2024-12"
DISCOVERY_START = "2023-02-01T00:00:00.000Z"
DISCOVERY_END = "2024-12-31T16:00:00.000Z"
EXPECTED_EFFECTIVE_15M_PER_SYMBOL = 67_151
EMA_LENGTH = 20
ATR_LENGTH = 14
EXTREME_ATR = 1.5
STOP_ATR = 0.25
MAX_HOLD = 16
MIN_RESOLVED = 300
BASE_COST_PCT = 0.20
STRESS_COST_PCT = 0.30
BOOTSTRAP_REPS = 5000
BOOTSTRAP_SEED = 230911
BOOTSTRAP_CONFIDENCE = 0.95
CANONICAL_HEADER = ("open_time_ms", "open", "high", "low", "close", "volume", "close_time_ms")

ROOT = Path(__file__).resolve().parents[1]
FREEZE_PATH = ROOT / "research" / "timeframe_gap" / "TFG_EXTREME_MR_30M_001_FREEZE.json"


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
    atr14: float
    signal_low: float
    signal_close: float
    entry: float
    stop: float
    target: float
    risk_fraction: float
    fingerprint: str


@dataclass(frozen=True)
class Outcome:
    exit_reason: str
    exit_open_time: int | None
    exit_price: float | None
    bars_held: int | None
    gross_return_pct: float | None
    net_r: float | None
    ambiguity: bool


@dataclass(frozen=True)
class Trade:
    symbol: str
    signal: Signal
    outcome: Outcome


def canonical_hash(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()


def parse_ms(value: str) -> int:
    return int(datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc).timestamp() * 1000)


def month_sequence(start: str, end: str) -> list[str]:
    cur = datetime.strptime(start, "%Y-%m")
    finish = datetime.strptime(end, "%Y-%m")
    out: list[str] = []
    while cur <= finish:
        out.append(cur.strftime("%Y-%m"))
        if cur.month == 12:
            cur = cur.replace(year=cur.year + 1, month=1, day=1)
        else:
            cur = cur.replace(month=cur.month + 1, day=1)
    return out


def prefix(symbol: str) -> str:
    return f"{symbol[:-4]}_USDT"


def load_freeze() -> dict[str, Any]:
    d = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    assert d["experiment_id"] == LAB_ID
    assert d["status"] == "FROZEN_BEFORE_ANY_EXPERIMENT_OUTCOME_EVALUATION"
    assert d["lineage"]["this_experiment_is_historical_replication"] is False
    assert d["market"]["derived_interval"] == "30m"
    assert d["indicator_definition"]["ema_length"] == EMA_LENGTH
    assert d["indicator_definition"]["atr_length"] == ATR_LENGTH
    assert d["indicator_definition"]["extreme_distance_atr"] == EXTREME_ATR
    assert d["signal_rules"]["stop"] == "signal_low - 0.25 * ATR14_signal"
    assert d["signal_rules"]["target"] == "EMA20_signal"
    assert d["signal_rules"]["max_holding_bars"] == MAX_HOLD
    assert d["costs"]["BASE_round_trip_pct"] == BASE_COST_PCT
    assert d["costs"]["STRESS_round_trip_pct"] == STRESS_COST_PCT
    assert d["discovery"]["minimum_resolved_trades"] == MIN_RESOLVED
    assert d["protected_data"]["validation_2025"].startswith("LOCKED_")
    assert d["protected_data"]["holdout_2026"].startswith("LOCKED_")
    return d


def load_binding(path: Path, manifest_dir: Path) -> tuple[dict[str, Any], dict[str, str]]:
    d = json.loads(path.read_text(encoding="utf-8"))
    if d["experiment_id"] != LAB_ID:
        raise ValueError("binding experiment mismatch")
    if d["status"] != "FROZEN_EXACT_SOURCE_BEFORE_ANY_EXTREME_MR_30M_OUTCOME_EVALUATION":
        raise ValueError("binding status mismatch")
    if d["artifact_id"] != 10419067320:
        raise ValueError("artifact id mismatch")
    if d["artifact_digest"] != "sha256:7b2562af14983d0344c9a28e81e9c1866f2e5e9dfafe94203da9a4ca1ffa36cb":
        raise ValueError("artifact digest mismatch")
    expected = dict(d["parent_corpus_fingerprint_by_symbol"])
    observed: dict[str, str] = {}
    for symbol in UNIVERSE:
        m = json.loads((manifest_dir / f"{symbol}_MANIFEST.json").read_text(encoding="utf-8"))
        if m["fingerprint"] != expected[symbol]:
            raise ValueError(f"manifest fingerprint mismatch:{symbol}")
        if m["status"] != "PASS_CORPUS_AUDIT_ONLY_WITH_GAPS" or m["total_row_count"] != 67_183:
            raise ValueError(f"manifest identity mismatch:{symbol}")
        observed[symbol] = m["fingerprint"]
    return d, observed


def load_canonical(path: Path, start_ms: int, end_ms: int) -> list[Candle]:
    out: list[Candle] = []
    with path.open("r", encoding="utf-8", newline="") as h:
        reader = csv.DictReader(h)
        if tuple(reader.fieldnames or ()) != CANONICAL_HEADER:
            raise ValueError(f"canonical header mismatch:{path.name}")
        for row in reader:
            t = int(row["open_time_ms"])
            if start_ms <= t < end_ms:
                out.append(Candle(t, float(row["open"]), float(row["high"]), float(row["low"]), float(row["close"]), float(row["volume"]), int(row["close_time_ms"])))
    return out


def validate_15m(candles: Iterable[Candle]) -> list[Candle]:
    series = sorted(candles, key=lambda c: c.open_time)
    seen: set[int] = set()
    for c in series:
        if c.open_time in seen:
            raise ValueError("duplicate 15m timestamp")
        seen.add(c.open_time)
        if c.open_time % FIFTEEN_MIN_MS != 0 or c.close_time != c.open_time + FIFTEEN_MIN_MS - 1:
            raise ValueError("15m alignment violation")
        vals = (c.open, c.high, c.low, c.close, c.volume)
        if any(not isfinite(v) for v in vals) or min(c.open, c.high, c.low, c.close) <= 0 or c.volume < 0:
            raise ValueError("invalid candle")
        if c.high < max(c.open, c.close, c.low) or c.low > min(c.open, c.close, c.high):
            raise ValueError("OHLC ordering violation")
    return series


def aggregate_15m_to_30m(candles: Iterable[Candle]) -> tuple[list[Candle], int]:
    series = validate_15m(candles)
    buckets: dict[int, list[Candle]] = defaultdict(list)
    for c in series:
        bucket = c.open_time - (c.open_time % THIRTY_MIN_MS)
        buckets[bucket].append(c)
    out: list[Candle] = []
    incomplete = 0
    for bucket in sorted(buckets):
        items = sorted(buckets[bucket], key=lambda c: c.open_time)
        expected = [bucket, bucket + FIFTEEN_MIN_MS]
        if len(items) != CHILDREN_PER_30M or [c.open_time for c in items] != expected:
            incomplete += 1
            continue
        out.append(Candle(bucket, items[0].open, max(c.high for c in items), min(c.low for c in items), items[-1].close, sum(c.volume for c in items), bucket + THIRTY_MIN_MS - 1))
    return out, incomplete


def split_segments(candles: list[Candle]) -> tuple[list[list[Candle]], int]:
    if not candles:
        return [], 0
    series = sorted(candles, key=lambda c: c.open_time)
    segments = [[series[0]]]
    gaps = 0
    for c in series[1:]:
        if c.open_time - segments[-1][-1].open_time == THIRTY_MIN_MS:
            segments[-1].append(c)
        else:
            gaps += 1
            segments.append([c])
    return segments, gaps


def ema_series(values: list[float], length: int) -> list[float | None]:
    out: list[float | None] = [None] * len(values)
    if len(values) < length:
        return out
    v = mean(values[:length])
    out[length - 1] = v
    alpha = 2.0 / (length + 1.0)
    for i in range(length, len(values)):
        v = alpha * values[i] + (1.0 - alpha) * v
        out[i] = v
    return out


def atr_series(candles: list[Candle], length: int) -> list[float | None]:
    out: list[float | None] = [None] * len(candles)
    if len(candles) <= length:
        return out
    trs: list[float | None] = [None]
    for i in range(1, len(candles)):
        c, p = candles[i], candles[i - 1]
        trs.append(max(c.high - c.low, abs(c.high - p.close), abs(c.low - p.close)))
    seed = [float(x) for x in trs[1:length + 1] if x is not None]
    if len(seed) != length:
        return out
    v = mean(seed)
    out[length] = v
    for i in range(length + 1, len(candles)):
        v = ((v * (length - 1)) + float(trs[i])) / length
        out[i] = v
    return out


def derive_signals(symbol: str, segment: list[Candle]) -> tuple[list[Signal], int, int]:
    closes = [c.close for c in segment]
    ema = ema_series(closes, EMA_LENGTH)
    atr = atr_series(segment, ATR_LENGTH)
    ready: list[Signal] = []
    raw = cancelled = 0
    for i in range(max(EMA_LENGTH - 1, ATR_LENGTH), len(segment) - 1):
        if ema[i] is None or atr[i] is None:
            continue
        c = segment[i]
        e = float(ema[i])
        a = float(atr[i])
        if c.close > e - EXTREME_ATR * a:
            continue
        raw += 1
        entry_bar = segment[i + 1]
        entry = entry_bar.open
        stop = c.low - STOP_ATR * a
        target = e
        if stop <= 0 or entry <= stop or target <= entry:
            cancelled += 1
            continue
        risk = (entry - stop) / entry
        if risk <= 0 or not isfinite(risk):
            cancelled += 1
            continue
        payload = {"setup_id": SETUP_ID, "symbol": symbol, "signal_open_time": c.open_time, "entry_open_time": entry_bar.open_time, "ema20": e, "atr14": a, "signal_low": c.low, "signal_close": c.close, "entry": entry, "stop": stop, "target": target, "risk_fraction": risk}
        ready.append(Signal(symbol, c.open_time, entry_bar.open_time, e, a, c.low, c.close, entry, stop, target, risk, canonical_hash(payload)))
    return ready, raw, cancelled


def simulate(signal: Signal, segment: list[Candle], cost_pct: float) -> Outcome:
    idx = next((i for i, c in enumerate(segment) if c.open_time == signal.entry_open_time), None)
    if idx is None:
        raise ValueError("entry bar missing")
    cost = cost_pct / 100.0
    denom = signal.risk_fraction + cost

    def finish(reason: str, bar: Candle, price: float, bars: int, ambiguity: bool) -> Outcome:
        gross = (price - signal.entry) / signal.entry
        return Outcome(reason, bar.open_time, price, bars, gross * 100.0, (gross - cost) / denom, ambiguity)

    last = min(len(segment) - 1, idx + MAX_HOLD - 1)
    for j in range(idx, last + 1):
        bar = segment[j]
        held = j - idx + 1
        if bar.open <= signal.stop:
            return finish("STOP_GAP", bar, bar.open, held, False)
        if bar.open >= signal.target:
            return finish("TARGET", bar, signal.target, held, False)
        stop_hit = bar.low <= signal.stop
        target_hit = bar.high >= signal.target
        if stop_hit and target_hit:
            return finish("STOP_AMBIGUOUS_SAME_BAR", bar, signal.stop, held, True)
        if stop_hit:
            return finish("STOP", bar, signal.stop, held, False)
        if target_hit:
            return finish("TARGET", bar, signal.target, held, False)
    exit_idx = idx + MAX_HOLD
    if exit_idx >= len(segment):
        return Outcome("UNRESOLVED_END_OF_DATA", None, None, None, None, None, False)
    bar = segment[exit_idx]
    return finish("TIME_EXIT_NEXT_OPEN", bar, bar.open, MAX_HOLD, False)


def profit_factor(values: list[float]) -> float | None:
    gains = sum(v for v in values if v > 0)
    losses = -sum(v for v in values if v < 0)
    return gains / losses if losses > 0 else None


def evaluate_symbol(symbol: str, candles: list[Candle]) -> tuple[list[Trade], dict[str, int]]:
    segments, gaps = split_segments(candles)
    records: list[Trade] = []
    raw = cancelled = overlap = 0
    for seg in segments:
        signals, r, c = derive_signals(symbol, seg)
        raw += r
        cancelled += c
        active_until: int | None = None
        for sig in signals:
            if active_until is not None and sig.entry_open_time <= active_until:
                overlap += 1
                continue
            out = simulate(sig, seg, BASE_COST_PCT)
            records.append(Trade(symbol, sig, out))
            active_until = out.exit_open_time if out.exit_open_time is not None else seg[-1].open_time
    return records, {"raw_trigger_count": raw, "pre_entry_cancelled_count": cancelled, "overlap_skipped_count": overlap, "segment_count": len(segments), "gap_count": gaps}


def evaluate_universe(candles_by_symbol: dict[str, list[Candle]]) -> tuple[list[Trade], dict[str, Any]]:
    records: list[Trade] = []
    totals = Counter()
    all_times: list[int] = []
    for symbol in sorted(candles_by_symbol):
        all_times.extend(c.open_time for c in candles_by_symbol[symbol])
        r, d = evaluate_symbol(symbol, candles_by_symbol[symbol])
        records.extend(r)
        totals.update(d)
    records.sort(key=lambda r: (r.signal.entry_open_time, r.symbol, r.signal.fingerprint))
    resolved = [r for r in records if r.outcome.net_r is not None]
    values = [float(r.outcome.net_r) for r in resolved]
    n = len(values)
    span_days = ((max(all_times) - min(all_times) + THIRTY_MIN_MS) / 86_400_000) if all_times else None
    metrics = {
        "cost_scenario": "BASE_0.20PCT_RT",
        "raw_trigger_count": totals["raw_trigger_count"],
        "pre_entry_cancelled_count": totals["pre_entry_cancelled_count"],
        "selected_trade_count": len(records),
        "overlap_skipped_count": totals["overlap_skipped_count"],
        "unresolved_trade_count": len(records) - n,
        "resolved_trade_count": n,
        "net_expectancy_r": mean(values) if values else None,
        "median_net_r": median(values) if values else None,
        "win_rate": sum(v > 0 for v in values) / n if n else None,
        "loss_rate": sum(v < 0 for v in values) / n if n else None,
        "profit_factor_r": profit_factor(values),
        "target_reach_rate": sum(r.outcome.exit_reason == "TARGET" for r in resolved) / n if n else None,
        "same_bar_ambiguity_rate": sum(r.outcome.ambiguity for r in resolved) / n if n else None,
        "time_exit_rate": sum(r.outcome.exit_reason == "TIME_EXIT_NEXT_OPEN" for r in resolved) / n if n else None,
        "stop_gap_rate": sum(r.outcome.exit_reason == "STOP_GAP" for r in resolved) / n if n else None,
        "signal_frequency_per_30d": len(records) / span_days * 30 if span_days and span_days > 0 else None,
        "symbol_distribution": dict(sorted(Counter(r.symbol for r in resolved).items())),
        "contiguous_segment_count": totals["segment_count"],
        "detected_gap_count": totals["gap_count"],
    }
    return records, metrics


def stress_metrics(records: list[Trade]) -> dict[str, Any]:
    cost = STRESS_COST_PCT / 100.0
    values: list[float] = []
    for r in records:
        if r.outcome.gross_return_pct is None:
            continue
        gross = r.outcome.gross_return_pct / 100.0
        values.append((gross - cost) / (r.signal.risk_fraction + cost))
    return {"cost_scenario": "STRESS_0.30PCT_RT", "cohort_source": "BASE_SELECTED_FIXED_COHORT", "selected_trade_count": len(records), "resolved_trade_count": len(values), "unresolved_trade_count": len(records) - len(values), "net_expectancy_r": mean(values) if values else None, "median_net_r": median(values) if values else None, "profit_factor_r": profit_factor(values)}


def percentile(values: list[float], p: float) -> float:
    if p <= 0:
        return values[0]
    if p >= 1:
        return values[-1]
    pos = (len(values) - 1) * p
    lo = int(pos)
    hi = min(lo + 1, len(values) - 1)
    frac = pos - lo
    return values[lo] * (1 - frac) + values[hi] * frac


def bootstrap(records: list[Trade]) -> dict[str, Any]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for r in records:
        if r.outcome.net_r is None:
            continue
        day = datetime.fromtimestamp(r.signal.entry_open_time / 1000, tz=timezone.utc).date().isoformat()
        grouped[day].append(float(r.outcome.net_r))
    days = sorted(grouped)
    vals = [v for d in days for v in grouped[d]]
    if not vals:
        return {"method": "UTC_CALENDAR_DAY_BLOCK_BOOTSTRAP", "repetitions": BOOTSTRAP_REPS, "seed": BOOTSTRAP_SEED, "confidence": BOOTSTRAP_CONFIDENCE, "sample_days": 0, "lower": None, "point_estimate": None, "upper": None, "undefined_reason": "NO_RESOLVED_TRADES"}
    rng = Random(BOOTSTRAP_SEED)
    draws: list[float] = []
    for _ in range(BOOTSTRAP_REPS):
        sample: list[float] = []
        for _ in range(len(days)):
            sample.extend(grouped[days[rng.randrange(len(days))]])
        draws.append(mean(sample))
    draws.sort()
    tail = (1 - BOOTSTRAP_CONFIDENCE) / 2
    return {"method": "UTC_CALENDAR_DAY_BLOCK_BOOTSTRAP", "repetitions": BOOTSTRAP_REPS, "seed": BOOTSTRAP_SEED, "confidence": BOOTSTRAP_CONFIDENCE, "sample_days": len(days), "lower": percentile(draws, tail), "point_estimate": mean(vals), "upper": percentile(draws, 1 - tail), "undefined_reason": None}


def classify(base: dict[str, Any], stress: dict[str, Any], boot: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    n = int(base["resolved_trade_count"])
    if n < MIN_RESOLVED:
        classification = "INSUFFICIENT_SAMPLE"
        failures.append("resolved_trade_count_below_300")
    else:
        checks = ((base["net_expectancy_r"], 0.0, "base_net_expectancy_not_positive"), (base["profit_factor_r"], 1.0, "base_profit_factor_not_above_1"), (boot["lower"], 0.0, "bootstrap_lower_95_not_positive"), (stress["net_expectancy_r"], 0.0, "fixed_cohort_stress_expectancy_not_positive"))
        for value, threshold, reason in checks:
            if value is None or not isfinite(float(value)) or float(value) <= threshold:
                failures.append(reason)
        classification = "NO_EDGE" if failures else "SURVIVES"
    payload = {"lab_id": LAB_ID, "stage": "DISCOVERY", "classification": classification, "resolved_trade_count": n, "minimum_required_trades": MIN_RESOLVED, "base_net_expectancy_r": base["net_expectancy_r"], "base_profit_factor_r": base["profit_factor_r"], "base_bootstrap_lower_95": boot["lower"], "fixed_cohort_stress_net_expectancy_r": stress["net_expectancy_r"], "failed_conditions": failures, "validation_unlock_eligible": classification == "SURVIVES", "live_authorized": False}
    payload["fingerprint"] = canonical_hash(payload)
    return payload


def blocked(reason: str) -> dict[str, Any]:
    p = {"status": "BLOCKED_PRE_OUTCOME", "reason": reason, "lab_id": LAB_ID, "outcome_evaluation_performed": False, "validation_2025_access_performed": False, "holdout_2026_access_performed": False, "network_access_performed": False, "exchange_mutation_performed": False, "orders_submitted": False}
    p["fingerprint"] = canonical_hash(p)
    return p


def run(canonical_dir: Path, manifest_dir: Path, binding_path: Path, output_dir: Path) -> dict[str, Any]:
    try:
        load_freeze()
        binding, fps = load_binding(binding_path, manifest_dir)
    except Exception as exc:
        return blocked(f"PRE_OUTCOME_BINDING:{type(exc).__name__}:{exc}")
    start_ms, end_ms = parse_ms(DISCOVERY_START), parse_ms(DISCOVERY_END)
    bars_by_symbol: dict[str, list[Candle]] = {}
    source_counts: dict[str, int] = {}
    derived_counts: dict[str, int] = {}
    incomplete_total = 0
    try:
        for symbol in UNIVERSE:
            source: list[Candle] = []
            for month in month_sequence(START_MONTH, END_MONTH):
                p = canonical_dir / f"{prefix(symbol)}-Min15-{month}-01.canonical.csv"
                if not p.is_file():
                    raise FileNotFoundError(p.name)
                source.extend(load_canonical(p, start_ms, end_ms))
            source_counts[symbol] = len(source)
            if len(source) != EXPECTED_EFFECTIVE_15M_PER_SYMBOL:
                raise ValueError(f"EFFECTIVE_15M_COUNT_MISMATCH:{symbol}:{len(source)}")
            bars, incomplete = aggregate_15m_to_30m(source)
            derived_counts[symbol] = len(bars)
            incomplete_total += incomplete
            bars_by_symbol[symbol] = bars
    except Exception as exc:
        return blocked(f"SOURCE_TRANSFORM:{type(exc).__name__}:{exc}")

    # FIRST REAL MARKET OUTCOME EVALUATION POINT FOR THIS EXPERIMENT.
    records, base = evaluate_universe(bars_by_symbol)
    stress = stress_metrics(records)
    boot = bootstrap(records)
    decision = classify(base, stress, boot)
    receipt = {"status": "TFG_EXTREME_MR_30M_DISCOVERY_COMPLETE", "lab_id": LAB_ID, "source_timeframe": "15m", "derived_timeframe": "30m", "universe": list(UNIVERSE), "discovery_start_utc": DISCOVERY_START, "discovery_end_utc": DISCOVERY_END, "source_binding_status": binding["status"], "parent_corpus_fingerprint_by_symbol": fps, "source_15m_count_by_symbol": source_counts, "derived_30m_count_by_symbol": derived_counts, "total_incomplete_30m_buckets": incomplete_total, "base_metrics": base, "fixed_cohort_stress_metrics": stress, "bootstrap": boot, "decision": decision, "validation_2025_access_performed": False, "holdout_2026_access_performed": False, "network_access_performed": False, "exchange_mutation_performed": False, "orders_submitted": False, "outcome_evaluation_performed": True}
    receipt["fingerprint"] = canonical_hash(receipt)
    output_dir.mkdir(parents=True, exist_ok=True)
    ledger = [{"symbol": r.symbol, "signal": asdict(r.signal), "outcome": asdict(r.outcome)} for r in records]
    (output_dir / "TFG_EXTREME_MR_30M_DISCOVERY_LEDGER_V0.1.json").write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_dir / "TFG_EXTREME_MR_30M_DISCOVERY_RECEIPT_V0.1.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def self_test() -> dict[str, Any]:
    base = parse_ms("2024-01-01T00:00:00.000Z")
    source = [Candle(base + i * FIFTEEN_MIN_MS, 100.0, 101.0, 99.0, 100.0, 1.0, base + (i + 1) * FIFTEEN_MIN_MS - 1) for i in range(4)]
    bars, inc = aggregate_15m_to_30m(source)
    assert len(bars) == 2 and inc == 0
    bars2, inc2 = aggregate_15m_to_30m(source[1:])
    assert len(bars2) == 1 and inc2 == 1
    const = [10.0] * 40
    e = ema_series(const, 20)
    assert e[19] == 10.0 and e[-1] == 10.0
    synthetic: list[Candle] = []
    p = 100.0
    for i in range(45):
        t = base + i * THIRTY_MIN_MS
        synthetic.append(Candle(t, p, p + 0.5, p - 0.5, p, 1.0, t + THIRTY_MIN_MS - 1))
        p += 0.05
    ema = ema_series([c.close for c in synthetic], 20)
    atr = atr_series(synthetic, 14)
    i = 35
    e0, a0 = float(ema[i]), float(atr[i])
    old = synthetic[i]
    close = e0 - 1.6 * a0
    synthetic[i] = Candle(old.open_time, e0, e0 + 0.2 * a0, close - 0.2 * a0, close, 1.0, old.close_time)
    signals, raw, _ = derive_signals("BTCUSDT", synthetic)
    assert raw >= 1 and signals
    return {"self_test": "PASS", "complete_30m_bars": len(bars), "gap_case_30m_bars": len(bars2), "synthetic_raw_triggers": raw, "synthetic_ready_signals": len(signals), "ambiguity_policy": "STOP_WINS"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--canonical-dir")
    ap.add_argument("--manifest-dir")
    ap.add_argument("--binding")
    ap.add_argument("--output-dir")
    args = ap.parse_args()
    if args.self_test:
        print(json.dumps(self_test(), indent=2, sort_keys=True))
        return 0
    if not all((args.canonical_dir, args.manifest_dir, args.binding, args.output_dir)):
        ap.error("discovery mode requires canonical-dir, manifest-dir, binding and output-dir")
    r = run(Path(args.canonical_dir), Path(args.manifest_dir), Path(args.binding), Path(args.output_dir))
    print(json.dumps(r, indent=2, sort_keys=True))
    return 0 if r.get("status") == "TFG_EXTREME_MR_30M_DISCOVERY_COMPLETE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
