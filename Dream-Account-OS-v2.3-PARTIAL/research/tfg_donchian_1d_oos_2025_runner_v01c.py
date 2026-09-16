from __future__ import annotations

import argparse
import json
import math
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median
from typing import Any

from research import tfg_donchian_1d_discovery_runner_v01 as parent
from research import tfg_ema_pullback_1d_discovery_runner_v01 as common

EXPERIMENT_ID = "TFG-DONCHIAN-1D-001-OOS2025-V0.1"
CORRECTION_ID = "TFG-DONCHIAN-1D-001-OOS2025-V0.1C-SOURCE-DELIVERY"
FROZEN_UNIVERSE = parent.FROZEN_UNIVERSE
DAY_MS = common.DAY_MS
HOUR_MS = 60 * 60 * 1000
OOS_START_MS = int(datetime(2025, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
OOS_END_MS = int(datetime(2026, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
WARMUP_START_MS = int(datetime(2024, 12, 1, tzinfo=timezone.utc).timestamp() * 1000)
MAX_HOLD = parent.MAX_HOLD
MIN_RESOLVED = 30
MAX_SYMBOL_POSITIVE_SHARE = 0.70
BASE_COST_PCT = parent.BASE_COST_PCT
ROOT = Path(__file__).resolve().parents[1]
FREEZE_PATH = ROOT / "research" / "timeframe_gap" / "TFG_DONCHIAN_1D_001_2025_OOS_FREEZE_V0.1.json"
AMENDMENT_PATH = ROOT / "research" / "timeframe_gap" / "TFG_DONCHIAN_1D_001_2025_OOS_FREEZE_AMENDMENT01_V0.1.json"
CORRECTION_PATH = ROOT / "research" / "timeframe_gap" / "TFG_DONCHIAN_1D_001_2025_OOS_SOURCE_DELIVERY_CORRECTION_V0.1C.json"


def canonical_hash(payload: Any) -> str:
    return common.canonical_hash(payload)


def _verify_fingerprint(payload: dict[str, Any], expected: str) -> None:
    clone = dict(payload)
    stored = clone.pop("fingerprint")
    assert stored == expected
    assert canonical_hash(clone) == expected


def verify_frozen_authority() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    freeze = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    amendment = json.loads(AMENDMENT_PATH.read_text(encoding="utf-8"))
    correction = json.loads(CORRECTION_PATH.read_text(encoding="utf-8"))
    assert freeze["experiment_id"] == EXPERIMENT_ID
    _verify_fingerprint(freeze, "006707c233257c4066cce9a84a51d255b3f4ef800f7b7cf9929a7acb2f085c56")
    assert freeze["lineage"]["parent_closeout_commit"] == "62422965b23e91671f6720b818bb26686b9d5bd2"
    assert freeze["frozen_rule"]["donchian_lookback_complete_days"] == parent.LOOKBACK
    assert freeze["frozen_rule"]["atr_length"] == parent.ATR_LENGTH
    assert freeze["frozen_rule"]["target_r"] == parent.TARGET_R == 3.0
    assert freeze["frozen_rule"]["max_holding_bars"] == parent.MAX_HOLD == 40
    assert freeze["costs"]["BASE_round_trip_pct"] == parent.BASE_COST_PCT == 0.20
    assert freeze["costs"]["STRESS_round_trip_pct"] == parent.STRESS_COST_PCT == 0.30
    assert freeze["decision_rule"]["minimum_resolved_oos_trades"] == MIN_RESOLVED
    assert freeze["decision_rule"]["max_single_symbol_positive_net_r_share_lte"] == MAX_SYMBOL_POSITIVE_SHARE
    assert freeze["governance"]["2025_oos_access_authorized_by_user"] is True
    assert freeze["governance"]["2026_historical_outcome_access"] is False
    assert freeze["governance"]["live_trading"] is False
    assert freeze["governance"]["exchange_mutation"] is False

    assert amendment["experiment_id"] == EXPERIMENT_ID
    _verify_fingerprint(amendment, "5429502880fb20bfa47be5509c4f13642e4ee690612bfee371fe2ab8f95f053c")
    assert amendment["market_outcomes_accessed_before_amendment"] is False
    assert amendment["scientific_rules_changed"] is False

    assert correction["experiment_id"] == EXPERIMENT_ID
    assert correction["correction_id"] == CORRECTION_ID
    _verify_fingerprint(correction, "b6bbaf86ee19a5234f84a906230f70233a2b3ba12c8a0093e198429957ab7571")
    assert correction["governance"]["2025_outcomes_accessed_before_correction"] is False
    assert correction["correction"]["to_delivery"] == "OFFICIAL_MEXC_SPOT_PUBLIC_READ_ONLY_API_1H"
    for key in ("scientific_signal_changed", "assets_changed", "costs_changed", "entry_exit_changed", "decision_gates_changed", "oos_window_changed"):
        assert correction["correction"][key] is False
    assert all(not a["outcomes_evaluated"] for a in correction["prior_source_attempts"])
    return freeze, amendment, correction


def _iso(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def _request_json(url: str) -> Any:
    last: Exception | None = None
    for attempt in range(5):
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "CryptoLabResearch/1.0 read-only"})
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.load(response)
        except Exception as exc:
            last = exc
            if attempt == 4:
                break
            time.sleep(min(8, 2 ** attempt))
    raise RuntimeError(f"MEXC_READ_ONLY_FETCH_FAILED:{last}")


def fetch_mexc_1h(symbol: str, start_ms: int, end_ms_exclusive: int) -> list[common.Candle]:
    rows: list[common.Candle] = []
    cursor = start_ms
    window = 1000 * HOUR_MS
    while cursor < end_ms_exclusive:
        chunk_end = min(end_ms_exclusive, cursor + window)
        params = urllib.parse.urlencode({"symbol": symbol, "interval": "1h", "startTime": cursor, "endTime": chunk_end - 1, "limit": 1000})
        payload = _request_json("https://api.mexc.com/api/v3/klines?" + params)
        if not isinstance(payload, list):
            raise RuntimeError(f"MEXC_RESPONSE_NOT_LIST:{symbol}:{type(payload).__name__}")
        chunk: list[common.Candle] = []
        for item in payload:
            if not isinstance(item, list) or len(item) < 6:
                raise RuntimeError(f"MEXC_MALFORMED_KLINE:{symbol}")
            t = int(item[0])
            if not (cursor <= t < chunk_end):
                continue
            if t % HOUR_MS != 0:
                raise RuntimeError(f"MEXC_1H_NOT_UTC_ALIGNED:{symbol}:{t}")
            o, h, l, c, v = map(float, (item[1], item[2], item[3], item[4], item[5]))
            if not all(math.isfinite(x) for x in (o, h, l, c, v)):
                raise RuntimeError(f"MEXC_NONFINITE:{symbol}:{t}")
            if min(o, h, l, c) <= 0 or v < 0 or h < max(o, c, l) or l > min(o, c, h):
                raise RuntimeError(f"MEXC_INVALID_OHLC:{symbol}:{t}")
            chunk.append(common.Candle(t, o, h, l, c, v, t + HOUR_MS - 1))
        chunk.sort(key=lambda x: x.open_time)
        expected = list(range(cursor, chunk_end, HOUR_MS))
        observed = [c.open_time for c in chunk]
        if observed != expected:
            missing = sorted(set(expected) - set(observed))
            extra = sorted(set(observed) - set(expected))
            raise RuntimeError(f"MEXC_1H_CHUNK_CONTINUITY_FAIL:{symbol}:{_iso(cursor)}:{_iso(chunk_end)}:count={len(chunk)}:expected={len(expected)}:missing={[_iso(x) for x in missing[:5]]}:extra={[_iso(x) for x in extra[:5]]}")
        rows.extend(chunk)
        cursor = chunk_end
        time.sleep(0.02)
    if len({r.open_time for r in rows}) != len(rows):
        raise RuntimeError(f"MEXC_DUPLICATE_1H:{symbol}")
    return rows


def load_parent_dec_15m(parent_canonical_dir: Path, symbol: str) -> list[common.Candle]:
    prefix = f"{symbol[:-4]}_USDT"
    candidates = sorted(parent_canonical_dir.glob(f"{prefix}-Min15-2024-12-01*.canonical.csv"))
    if len(candidates) != 1:
        raise RuntimeError(f"PARENT_DEC_CANONICAL_FILE_COUNT:{symbol}:{len(candidates)}")
    rows = common.load_canonical(candidates[0], WARMUP_START_MS, OOS_START_MS)
    if len(rows) < 2900:
        raise RuntimeError(f"PARENT_DEC_REFERENCE_TOO_SHORT:{symbol}:{len(rows)}")
    return rows


def aggregate_15m_to_1h(rows: list[common.Candle]) -> list[common.Candle]:
    groups: dict[int, list[common.Candle]] = defaultdict(list)
    for c in rows:
        h = (c.open_time // HOUR_MS) * HOUR_MS
        groups[h].append(c)
    out: list[common.Candle] = []
    for h in sorted(groups):
        g = sorted(groups[h], key=lambda x: x.open_time)
        expected = [h + i * 15 * 60 * 1000 for i in range(4)]
        if [x.open_time for x in g] != expected:
            continue
        out.append(common.Candle(h, g[0].open, max(x.high for x in g), min(x.low for x in g), g[-1].close, sum(x.volume for x in g), h + HOUR_MS - 1))
    return out


def aggregate_1h_to_1d(rows: list[common.Candle]) -> tuple[list[common.Candle], int]:
    groups: dict[int, list[common.Candle]] = defaultdict(list)
    for c in rows:
        d = (c.open_time // DAY_MS) * DAY_MS
        groups[d].append(c)
    out: list[common.Candle] = []
    dropped = 0
    for d in sorted(groups):
        g = sorted(groups[d], key=lambda x: x.open_time)
        expected = [d + i * HOUR_MS for i in range(24)]
        if [x.open_time for x in g] != expected:
            dropped += 1
            continue
        out.append(common.Candle(d, g[0].open, max(x.high for x in g), min(x.low for x in g), g[-1].close, sum(x.volume for x in g), d + DAY_MS - 1))
    return out, dropped


def equivalent(a: float, b: float) -> bool:
    return math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-12)


def verify_exact_1h_overlap(parent_canonical_dir: Path) -> dict[str, Any]:
    diagnostics: dict[str, Any] = {}
    for symbol in FROZEN_UNIVERSE:
        ref_15m = load_parent_dec_15m(parent_canonical_dir, symbol)
        ref = aggregate_15m_to_1h(ref_15m)
        if len(ref) < 700:
            raise RuntimeError(f"PARENT_DERIVED_1H_REFERENCE_TOO_SHORT:{symbol}:{len(ref)}")
        api = fetch_mexc_1h(symbol, WARMUP_START_MS, OOS_START_MS)
        api_map = {c.open_time: c for c in api}
        mismatches: list[str] = []
        matched = 0
        for r in ref:
            a = api_map.get(r.open_time)
            if a is None:
                mismatches.append(f"{_iso(r.open_time)}:missing_api_bar")
                continue
            bad = [f for f in ("open", "high", "low", "close") if not equivalent(float(getattr(r, f)), float(getattr(a, f)))]
            if bad:
                mismatches.append(f"{_iso(r.open_time)}:" + ",".join(bad))
            else:
                matched += 1
        if mismatches:
            raise RuntimeError(f"SOURCE_1H_EQUIVALENCE_FAIL:{symbol}:{'|'.join(mismatches[:12])}")
        diagnostics[symbol] = {"parent_derived_1h_bars_compared": len(ref), "api_december_1h_bars_seen": len(api), "matched_ohlc_bars": matched, "mismatch_count": 0, "status": "PASS_EXACT_NUMERIC_1H_OHLC"}
    return diagnostics


def validate_contiguous(rows: list[common.Candle], start_ms: int, end_ms: int, step_ms: int, label: str) -> None:
    expected = list(range(start_ms, end_ms, step_ms))
    observed = [c.open_time for c in rows]
    if observed != expected:
        missing = sorted(set(expected) - set(observed))
        extra = sorted(set(observed) - set(expected))
        raise RuntimeError(f"CONTINUITY_FAIL:{label}:count={len(observed)}:expected={len(expected)}:missing={[_iso(x) for x in missing[:5]]}:extra={[_iso(x) for x in extra[:5]]}")


def build_oos_records(candles_by_symbol: dict[str, list[common.Candle]]) -> tuple[list[parent.TradeRecord], dict[str, Any]]:
    records: list[parent.TradeRecord] = []
    diag: dict[str, Any] = {}
    for symbol in FROZEN_UNIVERSE:
        series = candles_by_symbol[symbol]
        signals, _, _ = parent.derive_signals(symbol, series)
        oos_signals = [s for s in signals if OOS_START_MS <= s.entry_open_time < OOS_END_MS]
        eligible = [s for s in oos_signals if s.entry_open_time + MAX_HOLD * DAY_MS < OOS_END_MS]
        active_until: int | None = None
        overlap_skipped = 0
        unresolved = 0
        selected = 0
        for sig in eligible:
            if active_until is not None and sig.entry_open_time <= active_until:
                overlap_skipped += 1
                continue
            outcome = parent.simulate(sig, series, BASE_COST_PCT)
            selected += 1
            if outcome.net_r is None:
                unresolved += 1
            records.append(parent.TradeRecord(symbol, sig, outcome))
            active_until = outcome.exit_open_time if outcome.exit_open_time is not None else sig.entry_open_time + MAX_HOLD * DAY_MS
        diag[symbol] = {"all_2025_ready_signals": len(oos_signals), "full_path_eligible_signals": len(eligible), "right_censored_signals": len(oos_signals) - len(eligible), "selected_trades": selected, "overlap_skipped": overlap_skipped, "unresolved_execution_paths": unresolved}
    records.sort(key=lambda r: (r.signal.entry_open_time, r.symbol, r.signal.fingerprint))
    return records, diag


def _profit_factor(values: list[float]) -> float | None:
    gains = sum(v for v in values if v > 0)
    losses = -sum(v for v in values if v < 0)
    if losses == 0:
        return None if gains == 0 else 999999999.0
    return gains / losses


def metrics(records: list[parent.TradeRecord]) -> dict[str, Any]:
    resolved = [r for r in records if r.outcome.net_r is not None]
    values = [float(r.outcome.net_r) for r in resolved]
    by_symbol: dict[str, list[float]] = defaultdict(list)
    by_quarter: dict[str, list[float]] = defaultdict(list)
    for r in resolved:
        v = float(r.outcome.net_r)
        by_symbol[r.symbol].append(v)
        dt = datetime.fromtimestamp(r.signal.entry_open_time / 1000, tz=timezone.utc)
        by_quarter[f"2025-Q{((dt.month - 1)//3)+1}"].append(v)
    positive_by_symbol = {s: sum(v for v in vals if v > 0) for s, vals in by_symbol.items()}
    total_positive = sum(positive_by_symbol.values())
    share = max(positive_by_symbol.values()) / total_positive if total_positive > 0 else None
    per_symbol = {s: {"n": len(vals), "mean_net_r": mean(vals), "profit_factor": _profit_factor(vals), "total_net_r": sum(vals)} for s, vals in sorted(by_symbol.items())}
    per_quarter = {q: {"n": len(vals), "mean_net_r": mean(vals), "profit_factor": _profit_factor(vals), "total_net_r": sum(vals)} for q, vals in sorted(by_quarter.items())}
    loo = {}
    for s in FROZEN_UNIVERSE:
        vals = [float(r.outcome.net_r) for r in resolved if r.symbol != s and r.outcome.net_r is not None]
        loo[s] = {"n": len(vals), "mean_net_r": mean(vals) if vals else None, "profit_factor": _profit_factor(vals)}
    return {"selected_trade_count": len(records), "resolved_trade_count": len(resolved), "unresolved_execution_path_count": len(records)-len(resolved), "net_expectancy_r": mean(values) if values else None, "median_net_r": median(values) if values else None, "profit_factor_r": _profit_factor(values), "win_rate": sum(v > 0 for v in values)/len(values) if values else None, "loss_rate": sum(v < 0 for v in values)/len(values) if values else None, "total_net_r": sum(values), "target_reach_rate": sum(r.outcome.exit_reason == "TARGET" for r in resolved)/len(resolved) if resolved else None, "max_single_symbol_positive_net_r_share": share, "per_symbol": per_symbol, "per_quarter": per_quarter, "leave_one_asset_out": loo}


def classify(base: dict[str, Any], stress: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    n = int(base["resolved_trade_count"])
    if n < MIN_RESOLVED:
        classification = "INSUFFICIENT_OOS_SAMPLE"
        failures.append("resolved_trade_count_below_30")
    else:
        if base["net_expectancy_r"] is None or not base["net_expectancy_r"] > 0: failures.append("base_net_expectancy_not_positive")
        if base["profit_factor_r"] is None or not base["profit_factor_r"] > 1: failures.append("base_profit_factor_not_above_1")
        if stress["net_expectancy_r"] is None or not stress["net_expectancy_r"] > 0: failures.append("stress_net_expectancy_not_positive")
        if stress["profit_factor_r"] is None or not stress["profit_factor_r"] > 1: failures.append("stress_profit_factor_not_above_1")
        share = base["max_single_symbol_positive_net_r_share"]
        if share is None or share > MAX_SYMBOL_POSITIVE_SHARE: failures.append("single_symbol_positive_r_concentration_above_70pct")
        if int(base["unresolved_execution_path_count"]) != 0: failures.append("unresolved_execution_paths_nonzero")
        classification = "OOS_CONFIRMATION_SURVIVES_SHADOW_ELIGIBLE" if not failures else "OOS_CONFIRMATION_FAIL"
    return {"classification": classification, "failed_conditions": failures, "minimum_resolved_oos_trades": MIN_RESOLVED, "shadow_eligible": classification == "OOS_CONFIRMATION_SURVIVES_SHADOW_ELIGIBLE", "live_trading_authorized": False}


def blocked(reason: str, equivalence: dict[str, Any] | None = None, data_2025_accessed: bool = False) -> dict[str, Any]:
    body: dict[str, Any] = {"experiment_id": EXPERIMENT_ID, "source_correction": CORRECTION_ID, "status": "BLOCKED_NON_SCIENTIFIC", "reason": reason, "source_equivalence": equivalence or {}, "2025_data_accessed": data_2025_accessed, "2025_outcome_evaluation_performed": False, "2026_accessed": False, "live_trading": False, "exchange_mutation": False, "orders": False}
    body["fingerprint"] = canonical_hash(body)
    return body


def run(parent_canonical_dir: Path, output_dir: Path) -> int:
    freeze, amendment, correction = verify_frozen_authority()
    output_dir.mkdir(parents=True, exist_ok=True)
    receipt_path = output_dir / "TFG_DONCHIAN_1D_2025_OOS_RECEIPT_V0.1C.json"
    ledger_path = output_dir / "TFG_DONCHIAN_1D_2025_OOS_LEDGER_V0.1C.json"
    try:
        equivalence = verify_exact_1h_overlap(parent_canonical_dir)
    except Exception as exc:
        receipt = blocked(f"SOURCE_1H_EQUIVALENCE_GATE:{type(exc).__name__}:{exc}")
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True)+"\n", encoding="utf-8")
        print(json.dumps(receipt, indent=2, sort_keys=True))
        return 2
    try:
        candles_by_symbol: dict[str, list[common.Candle]] = {}
        source_counts: dict[str, int] = {}
        for symbol in FROZEN_UNIVERSE:
            warmup = fetch_mexc_1h(symbol, WARMUP_START_MS, OOS_START_MS)
            oos = fetch_mexc_1h(symbol, OOS_START_MS, OOS_END_MS)
            validate_contiguous(warmup, WARMUP_START_MS, OOS_START_MS, HOUR_MS, symbol+"_WARMUP_1H")
            validate_contiguous(oos, OOS_START_MS, OOS_END_MS, HOUR_MS, symbol+"_2025_1H")
            daily, dropped = aggregate_1h_to_1d(warmup + oos)
            if dropped != 0: raise RuntimeError(f"INCOMPLETE_1D_BUCKETS:{symbol}:{dropped}")
            common.validate_1d(daily, regular=True)
            validate_contiguous(daily, WARMUP_START_MS, OOS_END_MS, DAY_MS, symbol+"_DAILY")
            candles_by_symbol[symbol] = daily
            source_counts[symbol] = len(oos)
        records, signal_diag = build_oos_records(candles_by_symbol)
        base = metrics(records)
        stress = asdict(parent.reprice_stress(records))
        bootstrap = asdict(parent.bootstrap_expectancy(records))
        decision = classify(base, stress)
        ledger_rows = [{"symbol": r.symbol, "signal": asdict(r.signal), "outcome": asdict(r.outcome), "entry_time_utc": _iso(r.signal.entry_open_time)} for r in records]
        ledger: dict[str, Any] = {"experiment_id": EXPERIMENT_ID, "source_correction": CORRECTION_ID, "stage": "2025_OOS_CONFIRMATION", "records": ledger_rows, "2026_accessed": False, "live_trading": False, "exchange_mutation": False}
        ledger["fingerprint"] = canonical_hash(ledger)
        receipt: dict[str, Any] = {"experiment_id": EXPERIMENT_ID, "parent_experiment_id": "TFG-DONCHIAN-1D-001", "status": decision["classification"], "freeze_fingerprint": freeze["fingerprint"], "amendment_fingerprint": amendment["fingerprint"], "source_correction_fingerprint": correction["fingerprint"], "source_delivery": "OFFICIAL_MEXC_SPOT_PUBLIC_READ_ONLY_1H_API_AFTER_PRE2025_EXACT_1H_EQUIVALENCE_GATE", "source_endpoint": "GET /api/v3/klines", "source_interval": "1h", "source_equivalence": equivalence, "source_2025_1h_count_by_symbol": source_counts, "signal_diagnostics": signal_diag, "base_metrics": base, "stress_metrics": stress, "bootstrap": bootstrap, "decision": decision, "2025_data_accessed": True, "2025_outcome_evaluation_performed": True, "2026_accessed": False, "live_trading": False, "exchange_mutation": False, "orders": False, "authenticated_exchange_api_used": False, "post_outcome_tuning": False, "merge_to_main": False}
        receipt["fingerprint"] = canonical_hash(receipt)
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True)+"\n", encoding="utf-8")
        ledger_path.write_text(json.dumps(ledger, indent=2, sort_keys=True)+"\n", encoding="utf-8")
        print(json.dumps(receipt, indent=2, sort_keys=True))
        return 0
    except Exception as exc:
        receipt = blocked(f"TECHNICAL_OR_DATA_GATE:{type(exc).__name__}:{exc}", equivalence, True)
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True)+"\n", encoding="utf-8")
        print(json.dumps(receipt, indent=2, sort_keys=True))
        return 2


def self_test() -> int:
    verify_frozen_authority()
    assert HOUR_MS * 24 == DAY_MS
    assert parent.TARGET_R == 3.0 and parent.MAX_HOLD == 40
    nov21 = int(datetime(2025, 11, 21, tzinfo=timezone.utc).timestamp()*1000)
    nov22 = int(datetime(2025, 11, 22, tzinfo=timezone.utc).timestamp()*1000)
    assert nov21 + MAX_HOLD*DAY_MS < OOS_END_MS
    assert not (nov22 + MAX_HOLD*DAY_MS < OOS_END_MS)
    print("TFG_DONCHIAN_1D_OOS_2025_V01C_SELF_TEST=PASS")
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--parent-canonical-dir")
    p.add_argument("--output-dir")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()
    if args.self_test: return self_test()
    if not args.parent_canonical_dir or not args.output_dir: p.error("--parent-canonical-dir and --output-dir are required")
    return run(Path(args.parent_canonical_dir), Path(args.output_dir))


if __name__ == "__main__":
    raise SystemExit(main())
