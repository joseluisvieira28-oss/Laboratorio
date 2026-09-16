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
FROZEN_UNIVERSE = parent.FROZEN_UNIVERSE
DAY_MS = common.DAY_MS
OOS_START_MS = int(datetime(2025, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
OOS_END_MS = int(datetime(2026, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
WARMUP_START_MS = int(datetime(2024, 12, 1, tzinfo=timezone.utc).timestamp() * 1000)
OVERLAP_END_MS = OOS_START_MS
MAX_HOLD = parent.MAX_HOLD
MIN_RESOLVED = 30
MAX_SYMBOL_POSITIVE_SHARE = 0.70
BASE_COST_PCT = parent.BASE_COST_PCT

ROOT = Path(__file__).resolve().parents[1]
FREEZE_PATH = ROOT / "research" / "timeframe_gap" / "TFG_DONCHIAN_1D_001_2025_OOS_FREEZE_V0.1.json"
AMENDMENT_PATH = ROOT / "research" / "timeframe_gap" / "TFG_DONCHIAN_1D_001_2025_OOS_FREEZE_AMENDMENT01_V0.1.json"


def canonical_hash(payload: Any) -> str:
    return common.canonical_hash(payload)


def verify_frozen_authority() -> tuple[dict[str, Any], dict[str, Any]]:
    freeze = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    amendment = json.loads(AMENDMENT_PATH.read_text(encoding="utf-8"))
    assert freeze["experiment_id"] == EXPERIMENT_ID
    assert freeze["status"] == "FROZEN_BEFORE_2025_OUTCOME_ACCESS"
    assert freeze["fingerprint"] == "006707c233257c4066cce9a84a51d255b3f4ef800f7b7cf9929a7acb2f085c56"
    clone = dict(freeze); fp = clone.pop("fingerprint")
    assert canonical_hash(clone) == fp
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
    assert amendment["status"] == "FROZEN_BEFORE_2025_OUTCOME_ACCESS"
    assert amendment["base_freeze_fingerprint"] == freeze["fingerprint"]
    assert amendment["fingerprint"] == "5429502880fb20bfa47be5509c4f13642e4ee690612bfee371fe2ab8f95f053c"
    clone = dict(amendment); fp = clone.pop("fingerprint")
    assert canonical_hash(clone) == fp
    assert amendment["market_outcomes_accessed_before_amendment"] is False
    assert amendment["scientific_rules_changed"] is False
    return freeze, amendment


def _iso(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def _profit_factor(values: list[float]) -> float | None:
    gains = sum(v for v in values if v > 0)
    losses = -sum(v for v in values if v < 0)
    if losses == 0:
        return None if gains == 0 else 999999999.0
    return gains / losses


def fetch_mexc_daily(symbol: str, start_ms: int, end_ms_exclusive: int) -> list[common.Candle]:
    params = urllib.parse.urlencode({
        "symbol": symbol,
        "interval": "1d",
        "startTime": start_ms,
        "endTime": end_ms_exclusive - 1,
        "limit": 1000,
    })
    url = "https://api.mexc.com/api/v3/klines?" + params
    payload: Any = None
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "CryptoLabResearch/1.0 read-only"})
            with urllib.request.urlopen(req, timeout=30) as response:
                payload = json.load(response)
            break
        except Exception as exc:
            if attempt == 3:
                raise RuntimeError(f"MEXC_READ_ONLY_FETCH_FAILED:{symbol}:{exc}") from exc
            time.sleep(2 ** attempt)
    if not isinstance(payload, list):
        raise RuntimeError(f"MEXC_RESPONSE_NOT_LIST:{symbol}:{type(payload).__name__}")
    rows: list[common.Candle] = []
    for item in payload:
        if not isinstance(item, list) or len(item) < 7:
            raise RuntimeError(f"MEXC_MALFORMED_KLINE:{symbol}")
        t = int(item[0])
        if not (start_ms <= t < end_ms_exclusive):
            continue
        if t % DAY_MS != 0:
            raise RuntimeError(f"MEXC_DAILY_NOT_UTC_ALIGNED:{symbol}:{t}")
        o, h, l, c, v = map(float, (item[1], item[2], item[3], item[4], item[5]))
        if not all(math.isfinite(x) for x in (o, h, l, c, v)):
            raise RuntimeError(f"MEXC_NONFINITE:{symbol}:{t}")
        if min(o, h, l, c) <= 0 or v < 0 or h < max(o, c, l) or l > min(o, c, h):
            raise RuntimeError(f"MEXC_INVALID_OHLC:{symbol}:{t}")
        rows.append(common.Candle(t, o, h, l, c, v, t + DAY_MS - 1))
    rows.sort(key=lambda x: x.open_time)
    if len({r.open_time for r in rows}) != len(rows):
        raise RuntimeError(f"MEXC_DUPLICATE_DAY:{symbol}")
    return rows


def parent_december_reference(parent_canonical_dir: Path, symbol: str) -> list[common.Candle]:
    prefix = f"{symbol[:-4]}_USDT"
    candidates = sorted(parent_canonical_dir.glob(f"{prefix}-Min15-2024-12-01*.canonical.csv"))
    if len(candidates) != 1:
        raise RuntimeError(f"PARENT_DEC_CANONICAL_FILE_COUNT:{symbol}:{len(candidates)}")
    rows = common.load_canonical(candidates[0], WARMUP_START_MS, OVERLAP_END_MS)
    daily, _ = common.aggregate_15m_to_1d(rows)
    return daily


def equivalent(a: float, b: float) -> bool:
    return math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-12)


def verify_overlap(parent_canonical_dir: Path) -> tuple[dict[str, Any], dict[str, list[common.Candle]]]:
    diagnostics: dict[str, Any] = {}
    api_overlap: dict[str, list[common.Candle]] = {}
    for symbol in FROZEN_UNIVERSE:
        ref = parent_december_reference(parent_canonical_dir, symbol)
        if len(ref) < 25:
            raise RuntimeError(f"PARENT_OVERLAP_TOO_SHORT:{symbol}:{len(ref)}")
        api = fetch_mexc_daily(symbol, WARMUP_START_MS, OVERLAP_END_MS)
        api_map = {c.open_time: c for c in api}
        mismatches: list[str] = []
        matched = 0
        for r in ref:
            a = api_map.get(r.open_time)
            if a is None:
                mismatches.append(f"{_iso(r.open_time)}:missing_api_day")
                continue
            bad = [f for f in ("open", "high", "low", "close") if not equivalent(float(getattr(r, f)), float(getattr(a, f)))]
            if bad:
                mismatches.append(f"{_iso(r.open_time)}:" + ",".join(bad))
            else:
                matched += 1
        if mismatches:
            raise RuntimeError(f"SOURCE_EQUIVALENCE_FAIL:{symbol}:{'|'.join(mismatches[:8])}")
        diagnostics[symbol] = {
            "parent_complete_daily_bars_compared": len(ref),
            "api_overlap_daily_bars_seen": len(api),
            "matched_ohlc_days": matched,
            "mismatch_count": 0,
            "status": "PASS_EXACT_NUMERIC_OHLC",
        }
        api_overlap[symbol] = api
    return diagnostics, api_overlap


def validate_contiguous_daily(symbol: str, rows: list[common.Candle], start_ms: int, end_ms: int) -> None:
    expected = list(range(start_ms, end_ms, DAY_MS))
    observed = [c.open_time for c in rows]
    if observed != expected:
        missing = sorted(set(expected) - set(observed))
        extra = sorted(set(observed) - set(expected))
        raise RuntimeError(f"DAILY_CONTINUITY_FAIL:{symbol}:count={len(observed)}:expected={len(expected)}:missing={[_iso(x) for x in missing[:5]]}:extra={[_iso(x) for x in extra[:5]]}")


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
        diag[symbol] = {
            "all_2025_ready_signals": len(oos_signals),
            "full_path_eligible_signals": len(eligible),
            "right_censored_signals": len(oos_signals) - len(eligible),
            "selected_trades": selected,
            "overlap_skipped": overlap_skipped,
            "unresolved_execution_paths": unresolved,
        }
    records.sort(key=lambda r: (r.signal.entry_open_time, r.symbol, r.signal.fingerprint))
    return records, diag


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
    max_positive_share = max(positive_by_symbol.values()) / total_positive if total_positive > 0 else None
    per_symbol = {s: {"n": len(vals), "mean_net_r": mean(vals), "profit_factor": _profit_factor(vals), "total_net_r": sum(vals)} for s, vals in sorted(by_symbol.items())}
    per_quarter = {q: {"n": len(vals), "mean_net_r": mean(vals), "profit_factor": _profit_factor(vals), "total_net_r": sum(vals)} for q, vals in sorted(by_quarter.items())}
    leave_one_out: dict[str, Any] = {}
    for s in FROZEN_UNIVERSE:
        vals = [float(r.outcome.net_r) for r in resolved if r.symbol != s and r.outcome.net_r is not None]
        leave_one_out[s] = {"n": len(vals), "mean_net_r": mean(vals) if vals else None, "profit_factor": _profit_factor(vals)}
    return {
        "selected_trade_count": len(records),
        "resolved_trade_count": len(resolved),
        "unresolved_execution_path_count": len(records) - len(resolved),
        "net_expectancy_r": mean(values) if values else None,
        "median_net_r": median(values) if values else None,
        "profit_factor_r": _profit_factor(values),
        "win_rate": sum(v > 0 for v in values) / len(values) if values else None,
        "loss_rate": sum(v < 0 for v in values) / len(values) if values else None,
        "total_net_r": sum(values),
        "target_reach_rate": sum(r.outcome.exit_reason == "TARGET" for r in resolved) / len(resolved) if resolved else None,
        "max_single_symbol_positive_net_r_share": max_positive_share,
        "per_symbol": per_symbol,
        "per_quarter": per_quarter,
        "leave_one_asset_out": leave_one_out,
    }


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


def ledger_payload(records: list[parent.TradeRecord]) -> dict[str, Any]:
    rows = [{"symbol": r.symbol, "signal": asdict(r.signal), "outcome": asdict(r.outcome), "entry_time_utc": _iso(r.signal.entry_open_time)} for r in records]
    body: dict[str, Any] = {"experiment_id": EXPERIMENT_ID, "stage": "2025_OOS_CONFIRMATION", "records": rows, "2026_accessed": False, "live_trading": False, "exchange_mutation": False}
    body["fingerprint"] = canonical_hash(body)
    return body


def blocked_receipt(reason: str, source_equivalence: dict[str, Any] | None = None) -> dict[str, Any]:
    body: dict[str, Any] = {"experiment_id": EXPERIMENT_ID, "status": "BLOCKED_NON_SCIENTIFIC", "reason": reason, "source_equivalence": source_equivalence or {}, "2025_outcome_evaluation_performed": False, "2026_accessed": False, "live_trading": False, "exchange_mutation": False, "orders": False}
    body["fingerprint"] = canonical_hash(body)
    return body


def run(parent_canonical_dir: Path, output_dir: Path) -> int:
    freeze, amendment = verify_frozen_authority()
    output_dir.mkdir(parents=True, exist_ok=True)
    receipt_path = output_dir / "TFG_DONCHIAN_1D_2025_OOS_RECEIPT_V0.1.json"
    ledger_path = output_dir / "TFG_DONCHIAN_1D_2025_OOS_LEDGER_V0.1.json"
    try:
        equivalence, overlap = verify_overlap(parent_canonical_dir)
    except Exception as exc:
        receipt = blocked_receipt(f"SOURCE_EQUIVALENCE_GATE:{type(exc).__name__}:{exc}")
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(receipt, indent=2, sort_keys=True))
        return 2
    try:
        candles_by_symbol: dict[str, list[common.Candle]] = {}
        source_counts: dict[str, int] = {}
        for symbol in FROZEN_UNIVERSE:
            oos = fetch_mexc_daily(symbol, OOS_START_MS, OOS_END_MS)
            validate_contiguous_daily(symbol, oos, OOS_START_MS, OOS_END_MS)
            warmup = overlap[symbol]
            validate_contiguous_daily(symbol + "_WARMUP", warmup, WARMUP_START_MS, OVERLAP_END_MS)
            combined = warmup + oos
            common.validate_1d(combined, regular=True)
            candles_by_symbol[symbol] = combined
            source_counts[symbol] = len(oos)
        records, signal_diag = build_oos_records(candles_by_symbol)
        base = metrics(records)
        stress = asdict(parent.reprice_stress(records))
        bootstrap = asdict(parent.bootstrap_expectancy(records))
        decision = classify(base, stress)
        total_unresolved = sum(v["unresolved_execution_paths"] for v in signal_diag.values())
        if total_unresolved != base["unresolved_execution_path_count"]:
            raise RuntimeError("UNRESOLVED_PATH_ACCOUNTING_MISMATCH")
        receipt: dict[str, Any] = {
            "experiment_id": EXPERIMENT_ID,
            "parent_experiment_id": "TFG-DONCHIAN-1D-001",
            "status": decision["classification"],
            "freeze_fingerprint": freeze["fingerprint"],
            "amendment_fingerprint": amendment["fingerprint"],
            "source_delivery": "OFFICIAL_MEXC_SPOT_PUBLIC_READ_ONLY_API_AFTER_PRE2025_EQUIVALENCE_GATE",
            "source_endpoint": "GET /api/v3/klines",
            "source_interval": "1d",
            "source_equivalence": equivalence,
            "source_2025_daily_count_by_symbol": source_counts,
            "signal_diagnostics": signal_diag,
            "base_metrics": base,
            "stress_metrics": stress,
            "bootstrap": bootstrap,
            "decision": decision,
            "2025_data_accessed": True,
            "2025_outcome_evaluation_performed": True,
            "2026_accessed": False,
            "live_trading": False,
            "exchange_mutation": False,
            "orders": False,
            "authenticated_exchange_api_used": False,
            "post_outcome_tuning": False,
            "merge_to_main": False,
        }
        receipt["fingerprint"] = canonical_hash(receipt)
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        ledger_path.write_text(json.dumps(ledger_payload(records), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(receipt, indent=2, sort_keys=True))
        return 0
    except Exception as exc:
        receipt = blocked_receipt(f"TECHNICAL_OR_DATA_GATE:{type(exc).__name__}:{exc}", equivalence)
        receipt["2025_data_accessed"] = True
        no_fp = {k: v for k, v in receipt.items() if k != "fingerprint"}
        receipt["fingerprint"] = canonical_hash(no_fp)
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(receipt, indent=2, sort_keys=True))
        return 2


def self_test() -> int:
    verify_frozen_authority()
    nov21 = int(datetime(2025, 11, 21, tzinfo=timezone.utc).timestamp() * 1000)
    nov22 = int(datetime(2025, 11, 22, tzinfo=timezone.utc).timestamp() * 1000)
    assert nov21 + MAX_HOLD * DAY_MS < OOS_END_MS
    assert not (nov22 + MAX_HOLD * DAY_MS < OOS_END_MS)
    assert parent.TARGET_R == 3.0 and parent.MAX_HOLD == 40
    print("TFG_DONCHIAN_1D_OOS_2025_SELF_TEST=PASS")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent-canonical-dir")
    parser.add_argument("--output-dir")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if not args.parent_canonical_dir or not args.output_dir:
        parser.error("--parent-canonical-dir and --output-dir are required")
    return run(Path(args.parent_canonical_dir), Path(args.output_dir))


if __name__ == "__main__":
    raise SystemExit(main())
