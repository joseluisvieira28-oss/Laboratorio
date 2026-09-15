from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any

from dream_account.models import Candle
from research.phase_b_mexc_discovery_corpus_v01 import PASS_CORPUS_STATUSES, build_discovery_corpus
from research.phase_b_research_evaluator_v01 import day_block_bootstrap_expectancy
from research.phase_b_signal_formation_v01 import CostAssumptions
from research.tfg_pbr01_4h_v01 import FOUR_H_MS, LAB_ID, ResearchParameters4H, aggregate_15m_to_4h, classify_discovery_4h, evaluate_universe_4h, records_as_dict_4h, reprice_fixed_cohort_4h

ROOT = Path(__file__).resolve().parents[1]
FREEZE_PATH = ROOT / "research" / "TFG_PBR01_4H_PROSPECTIVE_FREEZE_V0.1.json"
FROZEN_UNIVERSE = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT")
START_MONTH = "2023-02"
END_MONTH = "2024-12"
DISCOVERY_START = "2023-02-01T00:00:00.000Z"
DISCOVERY_END = "2024-12-31T16:00:00.000Z"
CANONICAL_HEADER = ("open_time_ms", "open", "high", "low", "close", "volume", "close_time_ms")
EXPECTED_BASE_SCENARIO = "BASE_SENSITIVITY"
EXPECTED_STRESS_SCENARIO = "STRESS"
EXPECTED_STRESS_COHORT = "BASE_SENSITIVITY_SELECTED_TFG_PBR01_4H_TRADES"
EXPECTED_BOOTSTRAP_METHOD = "UTC_CALENDAR_DAY_BLOCK_BOOTSTRAP"
EXPECTED_BOOTSTRAP_REPETITIONS = 5000
EXPECTED_BOOTSTRAP_SEED = 230911
EXPECTED_BOOTSTRAP_CONFIDENCE = 0.95


@dataclass(frozen=True)
class TFG4HReceipt:
    status: str
    reasons: tuple[str, ...]
    lab_id: str
    universe: tuple[str, ...]
    source_timeframe: str
    derived_timeframe: str
    discovery_start_utc: str
    discovery_end_utc: str
    corpus_status_by_symbol: dict[str, str]
    source_15m_count_by_symbol: dict[str, int]
    derived_4h_count_by_symbol: dict[str, int]
    total_incomplete_4h_buckets: int
    base_metrics: dict[str, Any] | None
    fixed_cohort_stress_metrics: dict[str, Any] | None
    bootstrap: dict[str, Any] | None
    decision: dict[str, Any] | None
    validation_access_performed: bool
    holdout_2026_access_performed: bool
    network_access_performed: bool
    exchange_mutation_performed: bool
    submitted_to_exchange: bool
    outcome_evaluation_performed: bool
    fingerprint: str


def _hash(payload: dict[str, Any]) -> str:
    return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()


def _finalize(receipt: TFG4HReceipt) -> TFG4HReceipt:
    payload = asdict(receipt)
    payload.pop("fingerprint", None)
    return replace(receipt, fingerprint=_hash(payload))


def _blocked(reason: str) -> TFG4HReceipt:
    return _finalize(TFG4HReceipt(status="BLOCKED_PRE_OUTCOME", reasons=(reason,), lab_id=LAB_ID, universe=FROZEN_UNIVERSE, source_timeframe="15m", derived_timeframe="4h", discovery_start_utc=DISCOVERY_START, discovery_end_utc=DISCOVERY_END, corpus_status_by_symbol={}, source_15m_count_by_symbol={}, derived_4h_count_by_symbol={}, total_incomplete_4h_buckets=0, base_metrics=None, fixed_cohort_stress_metrics=None, bootstrap=None, decision=None, validation_access_performed=False, holdout_2026_access_performed=False, network_access_performed=False, exchange_mutation_performed=False, submitted_to_exchange=False, outcome_evaluation_performed=False, fingerprint=""))


def _load_freeze() -> dict[str, Any]:
    payload = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    if payload.get("status") != "FROZEN_BEFORE_ANY_4H_OUTCOME_EVALUATION" or payload.get("lab_id") != LAB_ID:
        raise ValueError("freeze identity/status mismatch")
    if tuple(payload["source_contract"]["symbols"]) != FROZEN_UNIVERSE or payload["source_contract"]["venue"] != "MEXC_SPOT":
        raise ValueError("source contract mismatch")
    exact = {"timeframe": "4h", "lookback_bars": 96, "atr_length": 14, "zone_atr_fraction": 0.25, "retest_window_bars": 2, "stop_atr_fraction": 0.25, "tp1_r_multiple": 1.0, "tp2_r_multiple": 3.0, "minimum_net_rr": 2.0, "max_holding_bars": 96, "require_bullish_breakout_body": True}
    for key, value in exact.items():
        if payload["primary_parameters"].get(key) != value:
            raise ValueError(f"frozen parameter mismatch:{key}")
    d = payload["discovery"]
    if d["start_utc_inclusive"] != DISCOVERY_START or d["end_utc_exclusive"] != DISCOVERY_END or d["minimum_resolved_trades"] != 100:
        raise ValueError("Discovery contract mismatch")
    costs = payload["costs"]
    if costs["cohort_selection"] != EXPECTED_BASE_SCENARIO or costs["BASE_SENSITIVITY_round_trip_pct"] != 0.20 or costs["STRESS_round_trip_pct"] != 0.30:
        raise ValueError("cost contract mismatch")
    uncertainty = payload["uncertainty"]
    expected_uncertainty = {"method": EXPECTED_BOOTSTRAP_METHOD, "repetitions": EXPECTED_BOOTSTRAP_REPETITIONS, "seed": EXPECTED_BOOTSTRAP_SEED, "confidence": EXPECTED_BOOTSTRAP_CONFIDENCE}
    for key, value in expected_uncertainty.items():
        if uncertainty.get(key) != value:
            raise ValueError(f"uncertainty contract mismatch:{key}")
    if payload["final_holdout"]["access_allowed_now"] is not False or not payload["future_validation"]["status"].startswith("LOCKED_"):
        raise ValueError("future data firewall mismatch")
    return payload


def _parse_ms(value: str) -> int:
    return int(datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc).timestamp() * 1000)


def _months(start: str, end: str) -> list[str]:
    cursor, finish = datetime.strptime(start, "%Y-%m"), datetime.strptime(end, "%Y-%m")
    result: list[str] = []
    while cursor <= finish:
        result.append(cursor.strftime("%Y-%m"))
        cursor = cursor.replace(year=cursor.year + (1 if cursor.month == 12 else 0), month=1 if cursor.month == 12 else cursor.month + 1, day=1)
    return result


def _prefix(symbol: str) -> str:
    if symbol not in FROZEN_UNIVERSE:
        raise ValueError("symbol outside frozen universe")
    return f"{symbol[:-4]}_USDT"


def _load_canonical(path: Path, start_ms: int, end_ms: int) -> list[Candle]:
    result: list[Candle] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != CANONICAL_HEADER:
            raise ValueError(f"canonical header mismatch:{path.name}")
        for row in reader:
            open_time = int(row["open_time_ms"])
            if start_ms <= open_time < end_ms:
                result.append(Candle(open_time, float(row["open"]), float(row["high"]), float(row["low"]), float(row["close"]), float(row["volume"]), int(row["close_time_ms"]), True))
    return result


def _base_costs() -> CostAssumptions:
    return CostAssumptions(name=EXPECTED_BASE_SCENARIO, fee_pct_each_side=0.05, spread_pct=0.05, slippage_pct_each_side=0.025)


def _stress_costs() -> CostAssumptions:
    return CostAssumptions(name=EXPECTED_STRESS_SCENARIO, fee_pct_each_side=0.05, spread_pct=0.10, slippage_pct_each_side=0.05)


def _validate_gate_inputs(base_metrics: Any, stress: Any, bootstrap: Any) -> None:
    if base_metrics.cost_scenario != EXPECTED_BASE_SCENARIO:
        raise ValueError("base scenario identity mismatch")
    if stress.cost_scenario != EXPECTED_STRESS_SCENARIO or stress.cohort_source != EXPECTED_STRESS_COHORT:
        raise ValueError("stress fixed-cohort identity mismatch")
    if stress.selected_trade_count != base_metrics.selected_trade_count or stress.resolved_trade_count != base_metrics.resolved_trade_count:
        raise ValueError("stress cohort count mismatch")
    if bootstrap.method != EXPECTED_BOOTSTRAP_METHOD:
        raise ValueError("bootstrap method mismatch")
    if bootstrap.repetitions != EXPECTED_BOOTSTRAP_REPETITIONS or bootstrap.seed != EXPECTED_BOOTSTRAP_SEED:
        raise ValueError("bootstrap repetitions/seed mismatch")
    if abs(float(bootstrap.confidence) - EXPECTED_BOOTSTRAP_CONFIDENCE) > 1e-12:
        raise ValueError("bootstrap confidence mismatch")


def run(raw_dir: str | Path, output_dir: str | Path) -> TFG4HReceipt:
    try:
        _load_freeze()
    except Exception as exc:
        return _blocked(f"FREEZE_BINDING:{type(exc).__name__}:{exc}")
    raw_root, output_root = Path(raw_dir), Path(output_dir)
    start_ms, end_ms = _parse_ms(DISCOVERY_START), _parse_ms(DISCOVERY_END)
    expected_last_4h_open = end_ms - FOUR_H_MS
    corpus_status: dict[str, str] = {}
    source_counts: dict[str, int] = {}
    for symbol in FROZEN_UNIVERSE:
        manifest = build_discovery_corpus(raw_root, output_root, symbol=symbol, start_month=START_MONTH, end_month=END_MONTH)
        corpus_status[symbol], source_counts[symbol] = manifest.status, manifest.total_row_count
        if manifest.status not in PASS_CORPUS_STATUSES or manifest.passed_month_count != 23:
            blocked = _blocked(f"CORPUS_PREFLIGHT_FAILED:{symbol}:{manifest.status}")
            return _finalize(replace(blocked, corpus_status_by_symbol=corpus_status, source_15m_count_by_symbol=source_counts))

    derived_by_symbol: dict[str, list[Candle]] = {}
    derived_counts: dict[str, int] = {}
    incomplete_total = 0
    for symbol in FROZEN_UNIVERSE:
        series_15m: list[Candle] = []
        for month in _months(START_MONTH, END_MONTH):
            path = output_root / "canonical" / f"{_prefix(symbol)}-Min15-{month}-01.canonical.csv"
            if not path.is_file():
                return _blocked(f"CANONICAL_MISSING_AFTER_PREFLIGHT:{path.name}")
            series_15m.extend(_load_canonical(path, start_ms, end_ms))
        if not series_15m:
            return _blocked(f"EMPTY_DISCOVERY_SERIES:{symbol}")
        possible = len({c.open_time - (c.open_time % FOUR_H_MS) for c in series_15m})
        derived = aggregate_15m_to_4h(series_15m)
        incomplete_total += max(0, possible - len(derived))
        if not derived or derived[0].open_time != start_ms or derived[-1].open_time != expected_last_4h_open:
            return _blocked(f"4H_BOUNDARY_OR_COVERAGE_FAILURE:{symbol}")
        derived_by_symbol[symbol], derived_counts[symbol] = derived, len(derived)

    parameters = ResearchParameters4H()
    parameters.validate()
    base_costs, stress_costs = _base_costs(), _stress_costs()
    # FIRST 4H OUTCOME INSPECTION POINT.
    base_records, base_metrics = evaluate_universe_4h(derived_by_symbol, parameters, base_costs)
    stress = reprice_fixed_cohort_4h(base_records, stress_costs, min_net_rr=parameters.min_net_rr)
    bootstrap = day_block_bootstrap_expectancy(base_records, repetitions=EXPECTED_BOOTSTRAP_REPETITIONS, seed=EXPECTED_BOOTSTRAP_SEED, confidence=EXPECTED_BOOTSTRAP_CONFIDENCE)
    _validate_gate_inputs(base_metrics, stress, bootstrap)
    decision = classify_discovery_4h(base_metrics, stress, bootstrap)

    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "TFG_PBR01_4H_DISCOVERY_LEDGER_V0.1.json").write_text(json.dumps(records_as_dict_4h(base_records), sort_keys=True, indent=2), encoding="utf-8")
    receipt = _finalize(TFG4HReceipt(status="TFG_PBR01_4H_DISCOVERY_COMPLETE", reasons=(), lab_id=LAB_ID, universe=FROZEN_UNIVERSE, source_timeframe="15m", derived_timeframe="4h", discovery_start_utc=DISCOVERY_START, discovery_end_utc=DISCOVERY_END, corpus_status_by_symbol=corpus_status, source_15m_count_by_symbol=source_counts, derived_4h_count_by_symbol=derived_counts, total_incomplete_4h_buckets=incomplete_total, base_metrics=asdict(base_metrics), fixed_cohort_stress_metrics=asdict(stress), bootstrap=asdict(bootstrap), decision=asdict(decision), validation_access_performed=False, holdout_2026_access_performed=False, network_access_performed=False, exchange_mutation_performed=False, submitted_to_exchange=False, outcome_evaluation_performed=True, fingerprint=""))
    (output_root / "TFG_PBR01_4H_DISCOVERY_RECEIPT_V0.1.json").write_text(json.dumps(asdict(receipt), sort_keys=True, indent=2), encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    receipt = run(args.raw_dir, args.output_dir)
    print(json.dumps(asdict(receipt), sort_keys=True, indent=2))
    return 0 if receipt.status == "TFG_PBR01_4H_DISCOVERY_COMPLETE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
