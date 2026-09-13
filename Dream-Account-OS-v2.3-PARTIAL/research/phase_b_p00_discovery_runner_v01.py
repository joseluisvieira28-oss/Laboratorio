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
from research.phase_b_mexc_discovery_corpus_v01 import (
    PASS_CORPUS_STATUSES,
    build_discovery_corpus,
)
from research.phase_b_research_evaluator_v01 import (
    day_block_bootstrap_expectancy,
    evaluate_universe,
    reprice_fixed_cohort,
)
from research.phase_b_signal_formation_v01 import CostAssumptions, ResearchParameters, validate_candles
from research.phase_b_stage_classifier_v01 import ResearchStage, classify_stage


ROOT = Path(__file__).resolve().parents[1]
FREEZE_PATH = ROOT / "research" / "PHASE_B_PRE_DATA_RESEARCH_FREEZE_V0.1.json"
AMENDMENT_PATH = ROOT / "research" / "PHASE_B_DISCOVERY_WINDOW_AMENDMENT_V0.1.json"
FROZEN_UNIVERSE = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT")
START_MONTH = "2023-02"
END_MONTH = "2024-12"
CANONICAL_HEADER = ("open_time_ms", "open", "high", "low", "close", "volume", "close_time_ms")


@dataclass(frozen=True)
class P00DiscoveryReceipt:
    status: str
    reasons: tuple[str, ...]
    profile_id: str
    setup_id: str
    universe: tuple[str, ...]
    timeframe: str
    source_start_month: str
    source_end_month: str
    effective_start_utc_inclusive: str
    effective_end_utc_exclusive: str
    corpus_status_by_symbol: dict[str, str]
    corpus_fingerprint_by_symbol: dict[str, str]
    source_row_count_by_symbol: dict[str, int]
    effective_candle_count_by_symbol: dict[str, int]
    total_source_rows: int
    total_effective_candles: int
    total_detected_gap_count: int
    total_missing_candle_count: int
    base_metrics: dict[str, Any] | None
    fixed_cohort_stress_metrics: dict[str, Any] | None
    bootstrap: dict[str, Any] | None
    decision: dict[str, Any] | None
    validation_2025_unlock_eligible: bool
    validation_2025_access_performed: bool
    holdout_2026_access_performed: bool
    network_access_performed: bool
    exchange_mutation_performed: bool
    submitted_to_exchange: bool
    p00_evaluation_performed: bool
    fingerprint: str


def _canonical_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return sha256(encoded).hexdigest()


def _with_fingerprint(receipt: P00DiscoveryReceipt) -> P00DiscoveryReceipt:
    payload = asdict(receipt)
    payload.pop("fingerprint", None)
    return replace(receipt, fingerprint=_canonical_hash(payload))


def _blocked(reason: str, *, start_utc: str = "", end_utc: str = "") -> P00DiscoveryReceipt:
    receipt = P00DiscoveryReceipt(
        status="BLOCKED_PRE_P00",
        reasons=(reason,),
        profile_id="P00_PRIMARY",
        setup_id="PBR01_BREAKOUT_RETEST_LONG",
        universe=FROZEN_UNIVERSE,
        timeframe="15m",
        source_start_month=START_MONTH,
        source_end_month=END_MONTH,
        effective_start_utc_inclusive=start_utc,
        effective_end_utc_exclusive=end_utc,
        corpus_status_by_symbol={},
        corpus_fingerprint_by_symbol={},
        source_row_count_by_symbol={},
        effective_candle_count_by_symbol={},
        total_source_rows=0,
        total_effective_candles=0,
        total_detected_gap_count=0,
        total_missing_candle_count=0,
        base_metrics=None,
        fixed_cohort_stress_metrics=None,
        bootstrap=None,
        decision=None,
        validation_2025_unlock_eligible=False,
        validation_2025_access_performed=False,
        holdout_2026_access_performed=False,
        network_access_performed=False,
        exchange_mutation_performed=False,
        submitted_to_exchange=False,
        p00_evaluation_performed=False,
        fingerprint="",
    )
    return _with_fingerprint(receipt)


def _parse_utc_ms(value: str) -> int:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("UTC boundary must be timezone-aware")
    parsed = parsed.astimezone(timezone.utc)
    return int(parsed.timestamp() * 1000)


def _month_sequence(start: str, end: str) -> list[str]:
    cursor = datetime.strptime(start, "%Y-%m")
    finish = datetime.strptime(end, "%Y-%m")
    result: list[str] = []
    while cursor <= finish:
        result.append(cursor.strftime("%Y-%m"))
        year = cursor.year + (1 if cursor.month == 12 else 0)
        month = 1 if cursor.month == 12 else cursor.month + 1
        cursor = cursor.replace(year=year, month=month, day=1)
    return result


def _prefix(symbol: str) -> str:
    if symbol not in FROZEN_UNIVERSE:
        raise ValueError("symbol outside frozen universe")
    return f"{symbol[:-4]}_USDT"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _freeze_bindings() -> tuple[dict[str, Any], dict[str, Any], int, int]:
    freeze = _load_json(FREEZE_PATH)
    amendment = _load_json(AMENDMENT_PATH)
    if amendment.get("status") != "FROZEN_BEFORE_FIRST_P00_OUTCOME_EVALUATION":
        raise ValueError("Discovery amendment is not frozen")
    authority = amendment["authority_boundary"]
    if authority.get("p00_discovery_evaluation_authorized_after_preflight") is not True:
        raise ValueError("P00 Discovery evaluation is not authorized after preflight")
    if authority.get("validation_2025_access_authorized") is not False:
        raise ValueError("2025 must remain locked before Discovery result")
    if authority.get("holdout_2026_access_authorized") is not False:
        raise ValueError("2026 must remain locked")
    if tuple(amendment["frozen_universe"]) != FROZEN_UNIVERSE:
        raise ValueError("amended universe differs from pre-registered universe")
    source = amendment["source_contract"]
    if source["source_partition_start_month"] != START_MONTH or source["source_partition_end_month"] != END_MONTH:
        raise ValueError("source partition range mismatch")
    if source["expected_partition_count_per_symbol"] != 23:
        raise ValueError("expected partition count mismatch")
    if source["source_partition_timezone"] != "UTC+08:00":
        raise ValueError("source partition timezone mismatch")
    if source["cross_exchange_backfill_allowed"] is not False or source["interpolation_allowed"] is not False:
        raise ValueError("forbidden data rescue enabled")
    window = amendment["effective_discovery_window"]
    start_utc = window["start_utc_inclusive"]
    end_utc = window["end_utc_exclusive"]
    start_ms = _parse_utc_ms(start_utc)
    end_ms = _parse_utc_ms(end_utc)
    if start_ms >= end_ms:
        raise ValueError("invalid effective Discovery window")
    if end_utc != "2024-12-31T16:00:00.000Z":
        raise ValueError("2025 partition boundary reconciliation changed")
    primary = freeze["primary_hypothesis"]
    if primary["profile_id"] != "P00_PRIMARY":
        raise ValueError("primary profile mismatch")
    if tuple(freeze["data_contract"]["symbols"]) != FROZEN_UNIVERSE:
        raise ValueError("pre-data frozen universe mismatch")
    if freeze["data_contract"]["validation"]["status"] != "LOCKED_UNTIL_DISCOVERY_SURVIVES":
        raise ValueError("2025 validation lock changed")
    if not freeze["data_contract"]["final_holdout"]["status"].startswith("LOCKED_"):
        raise ValueError("2026 holdout lock changed")
    return freeze, amendment, start_ms, end_ms


def _parameters_from_freeze(freeze: dict[str, Any]) -> ResearchParameters:
    p = freeze["primary_hypothesis"]["parameters"]
    parameters = ResearchParameters(
        timeframe="15m",
        lookback_bars=p["lookback_bars"],
        atr_length=p["atr_length"],
        zone_atr_fraction=p["zone_atr_fraction"],
        retest_window_bars=p["retest_window_bars"],
        stop_atr_fraction=p["stop_atr_fraction"],
        tp1_r_multiple=p["tp1_r_multiple"],
        tp2_r_multiple=p["tp2_r_multiple"],
        min_net_rr=p["min_net_rr"],
        max_holding_bars=p["max_holding_bars"],
        require_bullish_breakout_body=p["require_bullish_breakout_body"],
    )
    parameters.validate()
    return parameters


def _cost_from_freeze(freeze: dict[str, Any], name: str) -> CostAssumptions:
    match = next((item for item in freeze["cost_scenarios"] if item["name"] == name), None)
    if match is None:
        raise ValueError(f"missing frozen cost scenario {name}")
    costs = CostAssumptions(
        name=name,
        fee_pct_each_side=match["fee_pct_each_side"],
        spread_pct=match["spread_pct"],
        slippage_pct_each_side=match["slippage_pct_each_side"],
    )
    costs.validate()
    if abs(costs.round_trip_cost_pct - match["round_trip_cost_pct"]) > 1e-12:
        raise ValueError(f"frozen cost arithmetic mismatch for {name}")
    return costs


def _load_canonical_window(path: Path, *, start_ms: int, end_ms: int) -> list[Candle]:
    candles: list[Candle] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != CANONICAL_HEADER:
            raise ValueError(f"canonical header mismatch: {path.name}")
        for row in reader:
            open_time = int(row["open_time_ms"])
            if open_time < start_ms or open_time >= end_ms:
                continue
            candle = Candle(
                open_time,
                float(row["open"]),
                float(row["high"]),
                float(row["low"]),
                float(row["close"]),
                float(row["volume"]),
                int(row["close_time_ms"]),
                True,
            )
            candles.append(candle)
    return candles


def run_p00_discovery(raw_dir: str | Path, output_dir: str | Path) -> P00DiscoveryReceipt:
    raw_root = Path(raw_dir)
    output_root = Path(output_dir)
    try:
        freeze, amendment, start_ms, end_ms = _freeze_bindings()
    except Exception as exc:
        return _blocked(f"AUTHORITY_BINDING:{type(exc).__name__}:{exc}")

    start_utc = amendment["effective_discovery_window"]["start_utc_inclusive"]
    end_utc = amendment["effective_discovery_window"]["end_utc_exclusive"]
    manifests = {}
    corpus_status_by_symbol: dict[str, str] = {}
    corpus_fingerprint_by_symbol: dict[str, str] = {}
    source_rows: dict[str, int] = {}
    total_gaps = 0
    total_missing = 0

    # Preflight every frozen symbol through the full offline adapter/provenance corpus audit.
    # No P00 outcome function is called before all six pass.
    for symbol in FROZEN_UNIVERSE:
        manifest = build_discovery_corpus(raw_root, output_root, symbol=symbol, start_month=START_MONTH, end_month=END_MONTH)
        manifests[symbol] = manifest
        corpus_status_by_symbol[symbol] = manifest.status
        corpus_fingerprint_by_symbol[symbol] = manifest.fingerprint
        source_rows[symbol] = manifest.total_row_count
        total_gaps += manifest.total_detected_gap_count
        total_missing += manifest.total_missing_candle_count
        if manifest.status not in PASS_CORPUS_STATUSES or manifest.passed_month_count != 23:
            blocked = _blocked(f"CORPUS_PREFLIGHT_FAILED:{symbol}:{manifest.status}", start_utc=start_utc, end_utc=end_utc)
            return _with_fingerprint(replace(
                blocked,
                corpus_status_by_symbol=corpus_status_by_symbol,
                corpus_fingerprint_by_symbol=corpus_fingerprint_by_symbol,
                source_row_count_by_symbol=source_rows,
                total_source_rows=sum(source_rows.values()),
                total_detected_gap_count=total_gaps,
                total_missing_candle_count=total_missing,
            ))

    candles_by_symbol: dict[str, list[Candle]] = {}
    effective_counts: dict[str, int] = {}
    months = _month_sequence(START_MONTH, END_MONTH)
    for symbol in FROZEN_UNIVERSE:
        series: list[Candle] = []
        prefix = _prefix(symbol)
        for month in months:
            canonical = output_root / "canonical" / f"{prefix}-Min15-{month}-01.canonical.csv"
            if not canonical.is_file():
                return _blocked(f"CANONICAL_MISSING_AFTER_PREFLIGHT:{canonical.name}", start_utc=start_utc, end_utc=end_utc)
            series.extend(_load_canonical_window(canonical, start_ms=start_ms, end_ms=end_ms))
        series = validate_candles(series, require_regular_spacing=False)
        if not series:
            return _blocked(f"EMPTY_EFFECTIVE_SERIES:{symbol}", start_utc=start_utc, end_utc=end_utc)
        if series[0].open_time != start_ms:
            return _blocked(f"EFFECTIVE_START_MISMATCH:{symbol}", start_utc=start_utc, end_utc=end_utc)
        if series[-1].open_time >= end_ms:
            return _blocked(f"EFFECTIVE_END_VIOLATION:{symbol}", start_utc=start_utc, end_utc=end_utc)
        candles_by_symbol[symbol] = series
        effective_counts[symbol] = len(series)

    parameters = _parameters_from_freeze(freeze)
    base_costs = _cost_from_freeze(freeze, "BASE_SENSITIVITY")
    stress_costs = _cost_from_freeze(freeze, "STRESS")

    # FIRST OUTCOME INSPECTION POINT. Everything above is integrity/governance preflight only.
    base_records, base_metrics = evaluate_universe(candles_by_symbol, parameters, base_costs)
    stress = reprice_fixed_cohort(base_records, stress_costs, min_net_rr=parameters.min_net_rr)
    bootstrap = day_block_bootstrap_expectancy(base_records, repetitions=5000, seed=230911, confidence=0.95)
    decision = classify_stage(ResearchStage.DISCOVERY, base_metrics, stress, bootstrap, profile_id="P00_PRIMARY")

    receipt = P00DiscoveryReceipt(
        status="P00_DISCOVERY_COMPLETE",
        reasons=(),
        profile_id="P00_PRIMARY",
        setup_id="PBR01_BREAKOUT_RETEST_LONG",
        universe=FROZEN_UNIVERSE,
        timeframe="15m",
        source_start_month=START_MONTH,
        source_end_month=END_MONTH,
        effective_start_utc_inclusive=start_utc,
        effective_end_utc_exclusive=end_utc,
        corpus_status_by_symbol=corpus_status_by_symbol,
        corpus_fingerprint_by_symbol=corpus_fingerprint_by_symbol,
        source_row_count_by_symbol=source_rows,
        effective_candle_count_by_symbol=effective_counts,
        total_source_rows=sum(source_rows.values()),
        total_effective_candles=sum(effective_counts.values()),
        total_detected_gap_count=total_gaps,
        total_missing_candle_count=total_missing,
        base_metrics=asdict(base_metrics),
        fixed_cohort_stress_metrics=asdict(stress),
        bootstrap=asdict(bootstrap),
        decision=asdict(decision),
        validation_2025_unlock_eligible=decision.next_stage_unlocked,
        validation_2025_access_performed=False,
        holdout_2026_access_performed=False,
        network_access_performed=False,
        exchange_mutation_performed=False,
        submitted_to_exchange=False,
        p00_evaluation_performed=True,
        fingerprint="",
    )
    return _with_fingerprint(receipt)


def write_receipt(path: str | Path, receipt: P00DiscoveryReceipt) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(asdict(receipt), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _main() -> int:
    parser = argparse.ArgumentParser(description="Phase B frozen offline P00 Discovery runner")
    parser.add_argument("raw_dir")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--receipt")
    args = parser.parse_args()
    result = run_p00_discovery(args.raw_dir, args.output_dir)
    if args.receipt:
        write_receipt(args.receipt, result)
    print(json.dumps(asdict(result), indent=2, sort_keys=True))
    return 0 if result.status == "P00_DISCOVERY_COMPLETE" else 2


if __name__ == "__main__":
    raise SystemExit(_main())
