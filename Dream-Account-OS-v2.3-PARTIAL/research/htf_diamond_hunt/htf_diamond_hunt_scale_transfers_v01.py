from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from math import isfinite
from pathlib import Path
from random import Random
from statistics import mean, median
from typing import Any, Iterable

CAMPAIGN_ID = "HTF-DIAMOND-HUNT-001"
SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT")
FIFTEEN_MIN_MS = 900_000
DAY_MS = 86_400_000
BASE_COST_PCT = 0.20
STRESS_COST_PCT = 0.30
MIN_RESOLVED = 100
BOOTSTRAP_REPS = 5000
BOOTSTRAP_SEED = 230911
BOOTSTRAP_CONFIDENCE = 0.95
ROOT = Path(__file__).resolve().parents[2]
FREEZE_PATH = ROOT / "research" / "htf_diamond_hunt" / "HTF_DIAMOND_HUNT_001_CAMPAIGN_FREEZE_V0.1.json"
BINDING_PATH = ROOT / "research" / "htf_diamond_hunt" / "HTF_DIAMOND_HUNT_001_SOURCE_BINDING_V0.1.json"
OUT_DIR = ROOT / "research" / "local_data" / "htf_diamond_hunt_scale_transfers_v01"


@dataclass(frozen=True)
class Bar:
    open_time: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    close_time: int


@dataclass(frozen=True)
class Signal:
    cell_id: str
    symbol: str
    signal_open_time: int
    entry_open_time: int
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


def canonical_hash(x: Any) -> str:
    return hashlib.sha256(json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_authority(source_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    freeze = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    bind = json.loads(BINDING_PATH.read_text(encoding="utf-8"))
    assert freeze["campaign_id"] == CAMPAIGN_ID
    assert freeze["status"] == "FROZEN_PRE_OUTCOME"
    assert freeze["execution_order"] == ["DH-01", "DH-04", "DH-07", "DH-02", "DH-03", "DH-05", "DH-06"]
    assert freeze["statistics"]["minimum_resolved_trades"] == MIN_RESOLVED
    assert freeze["statistics"]["bootstrap_repetitions"] == BOOTSTRAP_REPS
    assert freeze["statistics"]["bootstrap_seed"] == BOOTSTRAP_SEED
    assert freeze["costs"]["base_round_trip_pct"] == BASE_COST_PCT
    assert freeze["costs"]["stress_round_trip_pct"] == STRESS_COST_PCT
    assert bind["status"] == "FROZEN_EXACT_SOURCE_BEFORE_ANY_CAMPAIGN_OUTCOME"
    assert bind["artifact_id"] == 10434938955
    assert bind["artifact_digest"] == "sha256:39fa00e9c3e022b6135f5efdeef0868c1dfb25a80e31331625ace79156212c62"
    assert bind["source_fingerprint"] == "08402ecb8931e42a0766370f55e46adc3de02474ce3a6128f4b2cdd89bb4ac78"
    receipt = json.loads((source_dir / "HTF_DIAMOND_HUNT_001_SOURCE_GATE_V0.1.json").read_text(encoding="utf-8"))
    assert receipt["status"] == "SOURCE_DATA_PASS"
    assert receipt["source_fingerprint"] == bind["source_fingerprint"]
    assert receipt["outcome_evaluation_performed"] is False
    for year in (2023, 2024, 2025, 2026):
        assert receipt[f"access_{year}_performed"] is False
    for symbol in SYMBOLS:
        p = source_dir / "canonical_15m" / f"{symbol}_15m.csv"
        assert p.is_file()
        assert sha256_file(p) == bind["canonical_15m"][symbol]["sha256"]
        assert bind["canonical_15m"][symbol]["complete_count"] == 70013
    return freeze, bind


def cell_map(freeze: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out = {x["cell_id"]: x for x in freeze["cells"]}
    assert set(("DH-02", "DH-03", "DH-05", "DH-06")).issubset(out)
    # Hard assertions make the campaign freeze executable authority.
    assert out["DH-02"]["rule"]["donchian_lookback_complete_bars"] == 80
    assert out["DH-02"]["rule"]["atr_length"] == 56
    assert out["DH-02"]["rule"]["target_r"] == 3.0
    assert out["DH-02"]["rule"]["max_hold_bars"] == 160
    assert out["DH-03"]["rule"]["donchian_lookback_complete_bars"] == 40
    assert out["DH-03"]["rule"]["atr_length"] == 28
    assert out["DH-03"]["rule"]["target_r"] == 3.0
    assert out["DH-03"]["rule"]["max_hold_bars"] == 80
    assert out["DH-05"]["rule"]["fast_ema"] == 80 and out["DH-05"]["rule"]["slow_ema"] == 200
    assert out["DH-05"]["rule"]["atr_length"] == 56 and out["DH-05"]["rule"]["target_r"] == 2.0 and out["DH-05"]["rule"]["max_hold_bars"] == 80
    assert out["DH-06"]["rule"]["fast_ema"] == 40 and out["DH-06"]["rule"]["slow_ema"] == 100
    assert out["DH-06"]["rule"]["atr_length"] == 28 and out["DH-06"]["rule"]["target_r"] == 2.0 and out["DH-06"]["rule"]["max_hold_bars"] == 40
    return out


def load_15m(path: Path) -> list[Bar]:
    out: list[Bar] = []
    with path.open("r", encoding="utf-8", newline="") as h:
        r = csv.DictReader(h)
        assert tuple(r.fieldnames or ()) == ("open_time", "open", "high", "low", "close", "volume", "minute_count")
        prev = None
        for x in r:
            t = int(x["open_time"])
            assert int(x["minute_count"]) == 15
            assert t % FIFTEEN_MIN_MS == 0
            if prev is not None:
                assert t > prev
            prev = t
            o, hi, lo, c, v = map(float, (x["open"], x["high"], x["low"], x["close"], x["volume"]))
            assert min(o, hi, lo, c) > 0 and v >= 0 and hi >= max(o, c, lo) and lo <= min(o, c, hi)
            out.append(Bar(t, o, hi, lo, c, v, t + FIFTEEN_MIN_MS - 1))
    return out


def aggregate(candles: list[Bar], bar_ms: int) -> tuple[list[Bar], int]:
    expected_n = bar_ms // FIFTEEN_MIN_MS
    buckets: dict[int, list[Bar]] = defaultdict(list)
    for c in candles:
        b = c.open_time - (c.open_time % bar_ms)
        buckets[b].append(c)
    out: list[Bar] = []
    incomplete = 0
    for b in sorted(buckets):
        rows = sorted(buckets[b], key=lambda x: x.open_time)
        expected = [b + i * FIFTEEN_MIN_MS for i in range(expected_n)]
        if len(rows) != expected_n or [x.open_time for x in rows] != expected:
            incomplete += 1
            continue
        out.append(Bar(b, rows[0].open, max(x.high for x in rows), min(x.low for x in rows), rows[-1].close, sum(x.volume for x in rows), b + bar_ms - 1))
    return out, incomplete


def split_segments(bars: list[Bar], bar_ms: int) -> tuple[list[list[Bar]], int]:
    if not bars:
        return [], 0
    segs = [[bars[0]]]
    gaps = 0
    for b in bars[1:]:
        if b.open_time - segs[-1][-1].open_time == bar_ms:
            segs[-1].append(b)
        else:
            gaps += 1
            segs.append([b])
    return segs, gaps


def ema_series(values: list[float], length: int) -> list[float | None]:
    out: list[float | None] = [None] * len(values)
    if len(values) < length:
        return out
    value = mean(values[:length])
    out[length - 1] = value
    alpha = 2.0 / (length + 1.0)
    for i in range(length, len(values)):
        value = alpha * values[i] + (1 - alpha) * value
        out[i] = value
    return out


def atr_series(bars: list[Bar], length: int) -> list[float | None]:
    out: list[float | None] = [None] * len(bars)
    if len(bars) <= length:
        return out
    trs: list[float | None] = [None]
    for i in range(1, len(bars)):
        c, p = bars[i], bars[i - 1]
        trs.append(max(c.high - c.low, abs(c.high - p.close), abs(c.low - p.close)))
    seed = [float(x) for x in trs[1:length + 1] if x is not None]
    if len(seed) != length:
        return out
    value = mean(seed)
    out[length] = value
    for i in range(length + 1, len(bars)):
        value = ((value * (length - 1)) + float(trs[i])) / length
        out[i] = value
    return out


def derive_donchian(cell_id: str, symbol: str, segment: list[Bar], rule: dict[str, Any]) -> tuple[list[Signal], int, int]:
    lookback = int(rule["donchian_lookback_complete_bars"])
    atr_len = int(rule["atr_length"])
    target_r = float(rule["target_r"])
    atr = atr_series(segment, atr_len)
    signals: list[Signal] = []
    raw = cancelled = 0
    for i in range(max(lookback, atr_len), len(segment) - 1):
        if atr[i] is None:
            continue
        s = segment[i]
        prior_high = max(x.high for x in segment[i-lookback:i])
        if not s.close > prior_high:
            continue
        raw += 1
        stop = s.low - 0.25 * float(atr[i])
        entry = segment[i+1].open
        if stop <= 0 or entry <= stop:
            cancelled += 1
            continue
        risk = (entry - stop) / entry
        if risk <= 0 or not isfinite(risk):
            cancelled += 1
            continue
        target = entry + target_r * (entry - stop)
        payload = {"cell_id": cell_id, "symbol": symbol, "signal_open_time": s.open_time, "entry_open_time": segment[i+1].open_time, "entry": entry, "stop": stop, "target": target, "risk": risk}
        signals.append(Signal(cell_id, symbol, s.open_time, segment[i+1].open_time, entry, stop, target, risk, canonical_hash(payload)))
    return signals, raw, cancelled


def derive_ema(cell_id: str, symbol: str, segment: list[Bar], rule: dict[str, Any]) -> tuple[list[Signal], int, int]:
    fast, slow, atr_len = int(rule["fast_ema"]), int(rule["slow_ema"]), int(rule["atr_length"])
    target_r = float(rule["target_r"])
    closes = [x.close for x in segment]
    ef, es, atr = ema_series(closes, fast), ema_series(closes, slow), atr_series(segment, atr_len)
    signals: list[Signal] = []
    raw = cancelled = 0
    for i in range(max(slow - 1, atr_len, 1), len(segment) - 1):
        if ef[i] is None or es[i] is None or ef[i-1] is None or atr[i] is None:
            continue
        s, prev = segment[i], segment[i-1]
        f = float(ef[i])
        if not (f > float(es[i]) and prev.close > float(ef[i-1]) and s.low <= f and s.close >= f and s.close > s.open):
            continue
        raw += 1
        stop = s.low - 0.25 * float(atr[i])
        entry = segment[i+1].open
        if stop <= 0 or entry <= stop:
            cancelled += 1
            continue
        risk = (entry - stop) / entry
        if risk <= 0 or not isfinite(risk):
            cancelled += 1
            continue
        target = entry + target_r * (entry - stop)
        payload = {"cell_id": cell_id, "symbol": symbol, "signal_open_time": s.open_time, "entry_open_time": segment[i+1].open_time, "entry": entry, "stop": stop, "target": target, "risk": risk}
        signals.append(Signal(cell_id, symbol, s.open_time, segment[i+1].open_time, entry, stop, target, risk, canonical_hash(payload)))
    return signals, raw, cancelled


def simulate(sig: Signal, segment: list[Bar], max_hold: int, cost_pct: float) -> Outcome:
    idx = next((i for i, x in enumerate(segment) if x.open_time == sig.entry_open_time), None)
    if idx is None:
        raise ValueError("entry bar missing")
    cost = cost_pct / 100.0
    denom = sig.initial_risk_fraction + cost
    def finish(reason: str, b: Bar, px: float, held: int, ambiguity: bool) -> Outcome:
        gross = (px - sig.entry) / sig.entry
        return Outcome(reason, b.open_time, px, held, gross * 100.0, (gross - cost) / denom, ambiguity)
    last = min(len(segment) - 1, idx + max_hold - 1)
    for i in range(idx, last + 1):
        b = segment[i]
        held = i - idx + 1
        if b.open <= sig.stop:
            return finish("STOP_GAP", b, b.open, held, False)
        if b.open >= sig.target:
            return finish("TARGET", b, sig.target, held, False)
        sh, th = b.low <= sig.stop, b.high >= sig.target
        if sh and th:
            return finish("STOP_AMBIGUOUS_SAME_BAR", b, sig.stop, held, True)
        if sh:
            return finish("STOP", b, sig.stop, held, False)
        if th:
            return finish("TARGET", b, sig.target, held, False)
    exit_idx = idx + max_hold
    if exit_idx >= len(segment):
        return Outcome("UNRESOLVED_END_OF_DATA", None, None, None, None, None, False)
    b = segment[exit_idx]
    return finish("TIME_EXIT_NEXT_OPEN", b, b.open, max_hold, False)


def evaluate_cell(cell_id: str, kind: str, bars_by_symbol: dict[str, list[Bar]], bar_ms: int, rule: dict[str, Any]) -> tuple[list[TradeRecord], dict[str, Any]]:
    rows: list[TradeRecord] = []
    totals = Counter()
    max_hold = int(rule["max_hold_bars"])
    for symbol in sorted(bars_by_symbol):
        segs, gaps = split_segments(bars_by_symbol[symbol], bar_ms)
        totals["segments"] += len(segs); totals["gaps"] += gaps
        for seg in segs:
            signals, raw, cancelled = (derive_donchian(cell_id, symbol, seg, rule) if kind == "donchian" else derive_ema(cell_id, symbol, seg, rule))
            totals["raw"] += raw; totals["cancelled"] += cancelled
            active_until: int | None = None
            for sig in signals:
                if active_until is not None and sig.entry_open_time <= active_until:
                    totals["overlap"] += 1
                    continue
                out = simulate(sig, seg, max_hold, BASE_COST_PCT)
                rows.append(TradeRecord(symbol, sig, out))
                active_until = out.exit_open_time if out.exit_open_time is not None else seg[-1].open_time
    rows.sort(key=lambda r: (r.signal.entry_open_time, r.symbol, r.signal.fingerprint))
    resolved = [r for r in rows if r.outcome.net_r is not None]
    vals = [float(r.outcome.net_r) for r in resolved]
    metrics = {
        "raw_trigger_count": totals["raw"], "pre_entry_cancelled_count": totals["cancelled"],
        "selected_trade_count": len(rows), "overlap_skipped_count": totals["overlap"],
        "unresolved_trade_count": len(rows)-len(resolved), "resolved_trade_count": len(resolved),
        "net_expectancy_r": mean(vals) if vals else None, "median_net_r": median(vals) if vals else None,
        "win_rate": (sum(v > 0 for v in vals)/len(vals)) if vals else None,
        "profit_factor_r": profit_factor(vals), "symbol_distribution": dict(sorted(Counter(r.symbol for r in resolved).items())),
        "contiguous_segment_count": totals["segments"], "detected_gap_count": totals["gaps"]
    }
    return rows, metrics


def profit_factor(vals: list[float]) -> float | None:
    gains = sum(x for x in vals if x > 0); losses = -sum(x for x in vals if x < 0)
    return gains / losses if losses > 0 else None


def stress_metrics(rows: list[TradeRecord]) -> dict[str, Any]:
    vals: list[float] = []
    cost = STRESS_COST_PCT / 100.0
    for r in rows:
        if r.outcome.gross_return_pct is None:
            continue
        gross = r.outcome.gross_return_pct / 100.0
        vals.append((gross - cost) / (r.signal.initial_risk_fraction + cost))
    return {"selected_trade_count": len(rows), "resolved_trade_count": len(vals), "unresolved_trade_count": len(rows)-len(vals), "net_expectancy_r": mean(vals) if vals else None, "median_net_r": median(vals) if vals else None, "profit_factor_r": profit_factor(vals)}


def percentile(vals: list[float], p: float) -> float:
    if p <= 0: return vals[0]
    if p >= 1: return vals[-1]
    pos = (len(vals)-1)*p; lo = int(pos); hi = min(lo+1, len(vals)-1); f = pos-lo
    return vals[lo]*(1-f)+vals[hi]*f


def bootstrap(rows: list[TradeRecord]) -> dict[str, Any]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for r in rows:
        if r.outcome.net_r is None: continue
        d = datetime.fromtimestamp(r.signal.entry_open_time/1000, tz=timezone.utc).date().isoformat()
        grouped[d].append(float(r.outcome.net_r))
    days = sorted(grouped); point = [v for d in days for v in grouped[d]]
    if not point:
        return {"sample_days":0,"lower":None,"point_estimate":None,"upper":None}
    rng = Random(BOOTSTRAP_SEED); draws: list[float] = []
    for _ in range(BOOTSTRAP_REPS):
        sample: list[float] = []
        for _ in range(len(days)):
            sample.extend(grouped[days[rng.randrange(len(days))]])
        draws.append(mean(sample))
    draws.sort(); tail = (1-BOOTSTRAP_CONFIDENCE)/2
    return {"method":"UTC_ENTRY_DAY_BLOCK_BOOTSTRAP","repetitions":BOOTSTRAP_REPS,"seed":BOOTSTRAP_SEED,"sample_days":len(days),"lower":percentile(draws,tail),"point_estimate":mean(point),"upper":percentile(draws,1-tail)}


def classify(base: dict[str, Any], stress: dict[str, Any], boot: dict[str, Any]) -> tuple[str, list[str]]:
    n = int(base["resolved_trade_count"]); fail: list[str] = []
    if n < MIN_RESOLVED:
        return "INSUFFICIENT_SAMPLE", ["resolved_trade_count_below_100"]
    checks = ((base["net_expectancy_r"],0,"base_net_expectancy_not_positive"),(base["profit_factor_r"],1,"base_profit_factor_not_above_1"),(boot["lower"],0,"bootstrap_lower_95_not_positive"),(stress["net_expectancy_r"],0,"stress_expectancy_not_positive"))
    for v,t,r in checks:
        if v is None or not isfinite(float(v)) or float(v) <= t: fail.append(r)
    return ("SURVIVES" if not fail else "NO_EDGE"), fail


def main(argv: list[str]) -> int:
    if len(argv) != 2: raise SystemExit("usage: scale_runner SOURCE_DIR")
    source_dir = Path(argv[1]).resolve(); OUT_DIR.mkdir(parents=True, exist_ok=True)
    freeze, bind = load_authority(source_dir); cells = cell_map(freeze)
    source = {s: load_15m(source_dir/"canonical_15m"/f"{s}_15m.csv") for s in SYMBOLS}
    derived: dict[str, dict[str, list[Bar]]] = {}
    derived_counts: dict[str, dict[str, int]] = {}; incomplete_counts: dict[str, int] = {}
    for tf, ms in (("6H",21_600_000),("12H",43_200_000)):
        derived[tf] = {}; derived_counts[tf] = {}; incomplete_counts[tf] = 0
        for s in SYMBOLS:
            b, inc = aggregate(source[s], ms); derived[tf][s]=b; derived_counts[tf][s]=len(b); incomplete_counts[tf]+=inc
            if len(b) < (2800 if tf=="6H" else 1400): raise ValueError(f"unexpected low coverage:{tf}:{s}:{len(b)}")
    results: dict[str, Any] = {}; ledgers: dict[str, list[TradeRecord]] = {}
    for cid, kind in (("DH-02","donchian"),("DH-03","donchian"),("DH-05","ema"),("DH-06","ema")):
        tf = cells[cid]["signal_timeframe"]; ms = 21_600_000 if tf=="6H" else 43_200_000
        rows, base = evaluate_cell(cid, kind, derived[tf], ms, cells[cid]["rule"])
        stress = stress_metrics(rows); boot = bootstrap(rows); classification, failures = classify(base, stress, boot)
        result = {"cell_id":cid,"classification":classification,"failed_conditions":failures,"base":base,"stress":stress,"bootstrap":boot,"derived_bar_count_by_symbol":derived_counts[tf],"incomplete_bucket_count":incomplete_counts[tf]}
        results[cid]=result; ledgers[cid]=rows
        print(cid, json.dumps(result, sort_keys=True), flush=True)
    receipt = {"campaign_id":CAMPAIGN_ID,"status":"SCALE_TRANSFER_BLOCK_COMPLETE","source_artifact_id":bind["artifact_id"],"source_artifact_digest":bind["artifact_digest"],"source_fingerprint":bind["source_fingerprint"],"execution_order":["DH-02","DH-03","DH-05","DH-06"],"results":results,"multiplicity_note":"Donchian DH-02/DH-03 and EMA DH-05/DH-06 interpreted jointly; no post-outcome winner selection. No inferential p-values computed, so Holm correction is not applicable to this receipt.","access_2023_performed":False,"access_2024_performed":False,"access_2025_performed":False,"access_2026_performed":False,"network_access_performed_by_runner":False,"exchange_mutation_performed":False,"live_trading":False,"post_outcome_tuning":False}
    receipt["fingerprint"] = canonical_hash(receipt)
    (OUT_DIR/"HTF_DIAMOND_HUNT_001_SCALE_TRANSFER_RECEIPT_V0.1.json").write_text(json.dumps(receipt,indent=2,sort_keys=True),encoding="utf-8")
    for cid, rows in ledgers.items():
        (OUT_DIR/f"{cid}_LEDGER.json").write_text(json.dumps([asdict(r) for r in rows],indent=2,sort_keys=True),encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
