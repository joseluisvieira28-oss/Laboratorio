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
from research.phase_b_research_evaluator_v01 import day_block_bootstrap_expectancy
from research.phase_b_signal_formation_v01 import CostAssumptions
from research.tfg_pbr01_1d_v01 import (
    LAB_ID,
    ONE_DAY_MS,
    ResearchParameters1D,
    aggregate_15m_to_1d,
    classify_discovery_1d,
    evaluate_universe_1d,
    records_as_dict_1d,
    reprice_fixed_cohort_1d,
)

ROOT = Path(__file__).resolve().parents[1]
FREEZE_PATH = ROOT / "research" / "timeframe_gap" / "TFG_PBR01_1D_001_FREEZE.json"
ACTIVATION_PATH = ROOT / "research" / "timeframe_gap" / "TFG_PBR01_1D_001_ACTIVATION_V0.1.json"
FROZEN_UNIVERSE = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT")
START_MONTH = "2023-02"
END_MONTH = "2024-12"
DISCOVERY_START = "2023-02-01T00:00:00.000Z"
DISCOVERY_END = "2024-12-31T16:00:00.000Z"
CANONICAL_HEADER = ("open_time_ms", "open", "high", "low", "close", "volume", "close_time_ms")
EXPECTED_SOURCE_ROWS_PER_SYMBOL = 67_183
EXPECTED_EFFECTIVE_15M_PER_SYMBOL = 67_151
EXPECTED_BASE_SCENARIO = "BASE_SENSITIVITY"
EXPECTED_STRESS_SCENARIO = "STRESS"
EXPECTED_STRESS_COHORT = "BASE_SENSITIVITY_SELECTED_TFG_PBR01_1D_TRADES"
EXPECTED_BOOTSTRAP_METHOD = "UTC_CALENDAR_DAY_BLOCK_BOOTSTRAP"
EXPECTED_BOOTSTRAP_REPETITIONS = 5000
EXPECTED_BOOTSTRAP_SEED = 230911
EXPECTED_BOOTSTRAP_CONFIDENCE = 0.95
EXPECTED_PARENT_CORPUS_FP = {
    "BTCUSDT": "fba38a205b911fad0494b86174ef06a2d04a5908b0617a27efb74f067f8cf1d9",
    "ETHUSDT": "5a6433eb8703a9bcd0714fc6485ccc965cf754941ee6c69981158a7f11f36b7f",
    "SOLUSDT": "db013d47799b99a7c827740cf03c8e7e27b08c317097836143c855f1a51dde9b",
    "BNBUSDT": "ec43c0ab51dbf80fcde273c7d817b7cf9995e1614dfa5c05de4f664b9880437a",
    "XRPUSDT": "9b15ebea40555f5d6def5aab65cc5485db8120e0a6fa74f53ac4bb981a004427",
    "DOGEUSDT": "786a0129a2a7c9b58e2a465383d4849cedc3192e2c24bf8e4474ee709a3323fe",
}


@dataclass(frozen=True)
class TFG1DReceipt:
    status: str
    reasons: tuple[str, ...]
    lab_id: str
    universe: tuple[str, ...]
    source_timeframe: str
    derived_timeframe: str
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


def _hash(payload: dict[str, Any]) -> str:
    return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()


def _finalize(receipt: TFG1DReceipt) -> TFG1DReceipt:
    payload = asdict(receipt)
    payload.pop("fingerprint", None)
    return replace(receipt, fingerprint=_hash(payload))


def _blocked(reason: str) -> TFG1DReceipt:
    return _finalize(TFG1DReceipt(
        status="BLOCKED_PRE_OUTCOME",
        reasons=(reason,),
        lab_id=LAB_ID,
        universe=FROZEN_UNIVERSE,
        source_timeframe="15m",
        derived_timeframe="1d",
        discovery_start_utc=DISCOVERY_START,
        discovery_end_utc=DISCOVERY_END,
        source_binding_status=None,
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
    ))


def _load_freeze_and_activation() -> None:
    freeze = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    if freeze.get("experiment_id") != LAB_ID or freeze.get("status") != "PREFROZEN_NOT_EXECUTED":
        raise ValueError("freeze identity/status mismatch")
    tf = freeze["timeframe_transformation"]
    if tf.get("target_timeframe") != "1D" or tf.get("source_candles_per_target_bar") != 96 or tf.get("parameter_rescaling_allowed") is not False:
        raise ValueError("timeframe transformation mismatch")
    market = freeze["market"]
    if tuple(market.get("symbols", ())) != FROZEN_UNIVERSE or market.get("provider") != "MEXC" or market.get("market_type") != "SPOT" or market.get("direction") != "LONG_ONLY":
        raise ValueError("market/source contract mismatch")
    if market.get("cross_exchange_backfill_allowed") is not False or market.get("interpolation_allowed") is not False:
        raise ValueError("source firewall mismatch")
    exact = {
        "lookback_bars": 96,
        "atr_length": 14,
        "zone_atr_fraction": 0.25,
        "retest_window_bars": 2,
        "stop_atr_fraction": 0.25,
        "tp1_r_multiple": 1.0,
        "tp2_r_multiple": 3.0,
        "min_net_rr": 2.0,
        "max_holding_bars": 96,
        "require_bullish_breakout_body": True,
    }
    for key, value in exact.items():
        if freeze["parameters"].get(key) != value:
            raise ValueError(f"frozen parameter mismatch:{key}")
    d = freeze["data_stages"]["discovery"]
    if d.get("source_start") != DISCOVERY_START.replace(".000", "") or d.get("source_end_exclusive") != DISCOVERY_END.replace(".000", "") or d.get("minimum_resolved_trades") != 100:
        raise ValueError("Discovery contract mismatch")
    u = freeze["uncertainty"]
    if u.get("bootstrap") != EXPECTED_BOOTSTRAP_METHOD or u.get("bootstrap_repetitions") != EXPECTED_BOOTSTRAP_REPETITIONS or u.get("bootstrap_seed") != EXPECTED_BOOTSTRAP_SEED or u.get("confidence_interval") != EXPECTED_BOOTSTRAP_CONFIDENCE:
        raise ValueError("uncertainty contract mismatch")
    if freeze["governance"].get("2025_access") is not False or freeze["governance"].get("2026_access") is not False:
        raise ValueError("protected-year firewall mismatch")

    activation = json.loads(ACTIVATION_PATH.read_text(encoding="utf-8"))
    if activation.get("experiment_id") != LAB_ID or activation.get("current_state") != "ACTIVE_SOURCE_RECOVERY_OUTCOME_BLIND":
        raise ValueError("activation identity/status mismatch")
    scope = activation["authorization_scope"]
    if scope.get("discovery_after_full_parent_corpus_identity_pass") is not True:
        raise ValueError("Discovery not authorized after source pass")
    if scope.get("validation_2025") is not False or scope.get("holdout_2026") is not False or scope.get("exchange_mutation") is not False:
        raise ValueError("activation firewall mismatch")


def _load_source_binding(path: Path) -> dict[str, Any]:
    binding = json.loads(path.read_text(encoding="utf-8"))
    if binding.get("experiment_id") != LAB_ID:
        raise ValueError("source binding experiment mismatch")
    if binding.get("status") != "FROZEN_EXACT_PARENT_CORPUS_BEFORE_ANY_1D_OUTCOME_EVALUATION":
        raise ValueError("source binding status mismatch")
    if binding.get("parent_corpus_fingerprint_by_symbol") != EXPECTED_PARENT_CORPUS_FP:
        raise ValueError("parent corpus fingerprint map mismatch")
    if binding.get("validation_2025_remains_locked") is not True or binding.get("holdout_2026_remains_locked") is not True:
        raise ValueError("source binding protected-year firewall mismatch")
    if not binding.get("artifact_id") or not binding.get("artifact_digest"):
        raise ValueError("source artifact identity missing")
    return binding


def _parse_ms(value: str) -> int:
    return int(datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc).timestamp() * 1000)


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
                result.append(Candle(
                    open_time,
                    float(row["open"]),
                    float(row["high"]),
                    float(row["low"]),
                    float(row["close"]),
                    float(row["volume"]),
                    int(row["close_time_ms"]),
                    True,
                ))
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
    if bootstrap.method != EXPECTED_BOOTSTRAP_METHOD or bootstrap.repetitions != EXPECTED_BOOTSTRAP_REPETITIONS or bootstrap.seed != EXPECTED_BOOTSTRAP_SEED:
        raise ValueError("bootstrap identity mismatch")
    if abs(float(bootstrap.confidence) - EXPECTED_BOOTSTRAP_CONFIDENCE) > 1e-12:
        raise ValueError("bootstrap confidence mismatch")


def _manifest_fingerprints(manifest_dir: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for symbol in FROZEN_UNIVERSE:
        p = manifest_dir / f"{symbol}_MANIFEST.json"
        if not p.is_file():
            raise ValueError(f"manifest missing:{symbol}")
        d = json.loads(p.read_text(encoding="utf-8"))
        fp = d.get("fingerprint")
        if fp != EXPECTED_PARENT_CORPUS_FP[symbol]:
            raise ValueError(f"manifest fingerprint mismatch:{symbol}")
        if d.get("status") != "PASS_CORPUS_AUDIT_ONLY_WITH_GAPS" or d.get("total_row_count") != EXPECTED_SOURCE_ROWS_PER_SYMBOL:
            raise ValueError(f"manifest status/count mismatch:{symbol}")
        result[symbol] = fp
    return result


def run(canonical_dir: str | Path, manifest_dir: str | Path, binding_path: str | Path, output_dir: str | Path) -> TFG1DReceipt:
    try:
        _load_freeze_and_activation()
        binding = _load_source_binding(Path(binding_path))
        manifest_fps = _manifest_fingerprints(Path(manifest_dir))
    except Exception as exc:
        return _blocked(f"PRE_OUTCOME_BINDING:{type(exc).__name__}:{exc}")

    canonical_root = Path(canonical_dir)
    output_root = Path(output_dir)
    start_ms, end_ms = _parse_ms(DISCOVERY_START), _parse_ms(DISCOVERY_END)
    expected_last_full_day_open = (end_ms // ONE_DAY_MS) * ONE_DAY_MS - ONE_DAY_MS

    source_counts: dict[str, int] = {}
    derived_by_symbol: dict[str, list[Candle]] = {}
    derived_counts: dict[str, int] = {}
    incomplete_total = 0

    for symbol in FROZEN_UNIVERSE:
        series_15m: list[Candle] = []
        prefix = _prefix(symbol)
        for path in sorted(canonical_root.glob(f"{prefix}-Min15-*.canonical.csv")):
            series_15m.extend(_load_canonical(path, start_ms, end_ms))
        series_15m.sort(key=lambda c: c.open_time)
        if len(series_15m) != EXPECTED_EFFECTIVE_15M_PER_SYMBOL:
            return _blocked(f"EFFECTIVE_15M_COUNT_MISMATCH:{symbol}:{len(series_15m)}")
        source_counts[symbol] = len(series_15m)
        possible = len({c.open_time - (c.open_time % ONE_DAY_MS) for c in series_15m})
        derived = aggregate_15m_to_1d(series_15m)
        incomplete_total += max(0, possible - len(derived))
        if not derived:
            return _blocked(f"EMPTY_DERIVED_1D:{symbol}")
        if derived[0].open_time != start_ms:
            return _blocked(f"1D_START_BOUNDARY_FAILURE:{symbol}:{derived[0].open_time}")
        if derived[-1].open_time != expected_last_full_day_open:
            return _blocked(f"1D_END_BOUNDARY_FAILURE:{symbol}:{derived[-1].open_time}:{expected_last_full_day_open}")
        derived_by_symbol[symbol] = derived
        derived_counts[symbol] = len(derived)

    parameters = ResearchParameters1D()
    parameters.validate()
    base_costs, stress_costs = _base_costs(), _stress_costs()

    # FIRST 1D OUTCOME INSPECTION POINT. Everything above is source/freeze/aggregation only.
    base_records, base_metrics = evaluate_universe_1d(derived_by_symbol, parameters, base_costs)
    stress = reprice_fixed_cohort_1d(base_records, stress_costs, min_net_rr=parameters.min_net_rr)
    bootstrap = day_block_bootstrap_expectancy(
        base_records,
        repetitions=EXPECTED_BOOTSTRAP_REPETITIONS,
        seed=EXPECTED_BOOTSTRAP_SEED,
        confidence=EXPECTED_BOOTSTRAP_CONFIDENCE,
    )
    _validate_gate_inputs(base_metrics, stress, bootstrap)
    decision = classify_discovery_1d(base_metrics, stress, bootstrap)

    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "TFG_PBR01_1D_DISCOVERY_LEDGER_V0.1.json").write_text(
        json.dumps(records_as_dict_1d(base_records), sort_keys=True, indent=2), encoding="utf-8"
    )
    receipt = _finalize(TFG1DReceipt(
        status="TFG_PBR01_1D_DISCOVERY_COMPLETE",
        reasons=(),
        lab_id=LAB_ID,
        universe=FROZEN_UNIVERSE,
        source_timeframe="15m",
        derived_timeframe="1d",
        discovery_start_utc=DISCOVERY_START,
        discovery_end_utc=DISCOVERY_END,
        source_binding_status=binding["status"],
        parent_corpus_fingerprint_by_symbol=manifest_fps,
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
    ))
    (output_root / "TFG_PBR01_1D_DISCOVERY_RECEIPT_V0.1.json").write_text(
        json.dumps(asdict(receipt), sort_keys=True, indent=2), encoding="utf-8"
    )
    return receipt


def self_test() -> None:
    start = _parse_ms("2023-02-01T00:00:00.000Z")
    fifteen = 15 * 60 * 1000
    candles: list[Candle] = []
    for i in range(96 * 110):
        ot = start + i * fifteen
        p = 100.0 + i * 0.001
        candles.append(Candle(ot, p, p + 0.2, p - 0.2, p + 0.05, 10.0, ot + fifteen - 1, True))
    daily = aggregate_15m_to_1d(candles)
    assert len(daily) == 110
    assert daily[0].open_time == start
    assert daily[1].open_time - daily[0].open_time == ONE_DAY_MS
    broken = [c for i, c in enumerate(candles) if i != 96 * 50 + 7]
    daily_broken = aggregate_15m_to_1d(broken)
    assert len(daily_broken) == 109
    assert all(c.open_time != start + 50 * ONE_DAY_MS for c in daily_broken)
    print(json.dumps({"self_test": "PASS", "complete_daily_bars": len(daily), "gap_case_daily_bars": len(daily_broken)}, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description="Frozen TFG-PBR01-1D-001 Discovery runner")
    parser.add_argument("--canonical-dir")
    parser.add_argument("--manifest-dir")
    parser.add_argument("--binding")
    parser.add_argument("--output-dir")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if not all((args.canonical_dir, args.manifest_dir, args.binding, args.output_dir)):
        raise SystemExit("--canonical-dir --manifest-dir --binding --output-dir are required")
    receipt = run(args.canonical_dir, args.manifest_dir, args.binding, args.output_dir)
    print(json.dumps(asdict(receipt), sort_keys=True, indent=2))
    return 0 if receipt.status == "TFG_PBR01_1D_DISCOVERY_COMPLETE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
