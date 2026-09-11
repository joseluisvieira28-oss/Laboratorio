from __future__ import annotations

"""Fail-closed H01 Discovery orchestrator.

The runner is intentionally inert without a separately valid H01 2025 Discovery data
access authorization. It has no downloader, network client, validation-data path,
2026 holdout path, live route, or exchange mutation capability.

All signal/management/decision semantics are frozen before data access:
- P00 signal geometry is inherited unchanged through ResearchParameters;
- H01 outcome management is supplied by the H01 evaluator;
- BASE cohort selection is fixed before STRESS repricing;
- the frozen UTC-day bootstrap and H01 classifier decide the stage.
"""

import json
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any

from research.phase_b_h01_mexc_adapter_audit_v01 import PASS_STATUSES, audit_h01_month
from research.phase_b_h01_mexc_discovery_access_v01 import (
    DISCOVERY_END_MONTH,
    DISCOVERY_START_MONTH,
    EXPECTED_MONTHS,
    FAMILY_ID,
    FROZEN_UNIVERSE,
    HYPOTHESIS_ID,
    validate_h01_discovery_access_request,
)
from research.phase_b_h01_research_evaluator_v01 import (
    day_block_bootstrap_expectancy,
    evaluate_h01_universe,
    reprice_h01_fixed_cohort,
)
from research.phase_b_h01_stage_classifier_v01 import (
    H01ResearchStage,
    classify_h01_stage,
)
from research.phase_b_mexc_bulk_csv_adapter_v01 import (
    adapt_mexc_bulk_csv,
    write_receipt as write_adapter_receipt,
)
from research.phase_b_signal_formation_v01 import (
    TIMEFRAME_MS,
    CostAssumptions,
    ResearchParameters,
    validate_candles,
)


ROOT = Path(__file__).resolve().parents[1]
H01_FREEZE_PATH = ROOT / "research" / "PHASE_B_H01_PROTECT_AFTER_TP1_PROSPECTIVE_FREEZE_V0.1.json"
P00_FREEZE_PATH = ROOT / "research" / "PHASE_B_PRE_DATA_RESEARCH_FREEZE_V0.1.json"
H01_FREEZE_FINGERPRINT = "5229b820df2fc40036fe064e2b25361f3905b63345732f960eb7d9e457033d0b"
EFFECTIVE_START_UTC = "2025-01-01T00:00:00.000Z"
EFFECTIVE_END_UTC = "2025-08-31T16:00:00.000Z"
LIVE_AUTHORIZED = False
EXCHANGE_MUTATION_AUTHORIZED = False
HOLDOUT_2026_AUTHORIZED = False


@dataclass(frozen=True)
class H01DiscoveryReceipt:
    status: str
    reasons: tuple[str, ...]
    hypothesis_id: str
    family_id: str
    h01_freeze_fingerprint: str
    authorization_fingerprint: str | None
    universe: tuple[str, ...]
    timeframe: str
    source_start_month: str
    source_end_month: str
    effective_start_utc_inclusive: str
    effective_end_utc_exclusive: str
    audit_status_by_partition: dict[str, str]
    audit_fingerprint_by_partition: dict[str, str]
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
    validation_unlock_eligible: bool
    validation_2025_access_performed: bool
    holdout_2026_access_performed: bool
    source_market_bytes_read: bool
    network_access_performed: bool
    exchange_mutation_performed: bool
    submitted_to_exchange: bool
    h01_evaluation_performed: bool
    fingerprint: str


def _canonical_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _with_fingerprint(receipt: H01DiscoveryReceipt) -> H01DiscoveryReceipt:
    payload = asdict(receipt)
    payload.pop("fingerprint", None)
    return replace(receipt, fingerprint=_canonical_hash(payload))


def _blocked(
    reason: str,
    *,
    authorization_fingerprint: str | None = None,
    audit_status_by_partition: dict[str, str] | None = None,
    audit_fingerprint_by_partition: dict[str, str] | None = None,
    source_row_count_by_symbol: dict[str, int] | None = None,
    effective_candle_count_by_symbol: dict[str, int] | None = None,
    total_detected_gap_count: int = 0,
    total_missing_candle_count: int = 0,
    source_market_bytes_read: bool = False,
) -> H01DiscoveryReceipt:
    rows = source_row_count_by_symbol or {}
    counts = effective_candle_count_by_symbol or {}
    receipt = H01DiscoveryReceipt(
        status="BLOCKED_PRE_H01_DISCOVERY",
        reasons=(reason,),
        hypothesis_id=HYPOTHESIS_ID,
        family_id=FAMILY_ID,
        h01_freeze_fingerprint=H01_FREEZE_FINGERPRINT,
        authorization_fingerprint=authorization_fingerprint,
        universe=FROZEN_UNIVERSE,
        timeframe="15m",
        source_start_month=DISCOVERY_START_MONTH,
        source_end_month=DISCOVERY_END_MONTH,
        effective_start_utc_inclusive=EFFECTIVE_START_UTC,
        effective_end_utc_exclusive=EFFECTIVE_END_UTC,
        audit_status_by_partition=audit_status_by_partition or {},
        audit_fingerprint_by_partition=audit_fingerprint_by_partition or {},
        source_row_count_by_symbol=rows,
        effective_candle_count_by_symbol=counts,
        total_source_rows=sum(rows.values()),
        total_effective_candles=sum(counts.values()),
        total_detected_gap_count=total_detected_gap_count,
        total_missing_candle_count=total_missing_candle_count,
        base_metrics=None,
        fixed_cohort_stress_metrics=None,
        bootstrap=None,
        decision=None,
        validation_unlock_eligible=False,
        validation_2025_access_performed=False,
        holdout_2026_access_performed=False,
        source_market_bytes_read=source_market_bytes_read,
        network_access_performed=False,
        exchange_mutation_performed=False,
        submitted_to_exchange=False,
        h01_evaluation_performed=False,
        fingerprint="",
    )
    return _with_fingerprint(receipt)


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON authority is not an object: {path.name}")
    return value


def _hash_without_fingerprint(payload: dict[str, Any]) -> str:
    clone = dict(payload)
    clone.pop("fingerprint", None)
    return _canonical_hash(clone)


def _parse_utc_ms(value: str) -> int:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("UTC boundary must be timezone-aware")
    return int(parsed.astimezone(timezone.utc).timestamp() * 1000)


def _freeze_bindings() -> tuple[dict[str, Any], dict[str, Any], int, int]:
    h01 = _load_json(H01_FREEZE_PATH)
    p00 = _load_json(P00_FREEZE_PATH)

    if h01.get("hypothesis_id") != HYPOTHESIS_ID or h01.get("family_id") != FAMILY_ID:
        raise ValueError("H01 identity mismatch")
    if h01.get("fingerprint") != H01_FREEZE_FINGERPRINT:
        raise ValueError("H01 declared fingerprint mismatch")
    if _hash_without_fingerprint(h01) != H01_FREEZE_FINGERPRINT:
        raise ValueError("H01 content fingerprint mismatch")
    authority = h01["authority_boundary"]
    if authority.get("this_file_authorizes_2025_data_access") is not False:
        raise ValueError("H01 freeze must not self-authorize 2025 access")
    for key in (
        "live_integration_authorized",
        "phase_b_shadow_authorized",
        "micro_live_authorized",
        "real_trading_authorized",
        "exchange_mutation_authorized",
        "main_merge_authorized",
        "render_deploy_authorized",
    ):
        if authority.get(key) is not False:
            raise ValueError(f"forbidden H01 authority enabled: {key}")
    if authority.get("gate_k_phase_a_unchanged") is not True:
        raise ValueError("Gate K Phase A isolation assertion missing")

    data = h01["data_contract"]
    discovery = data["discovery_2025"]
    validation = data["validation_2025"]
    holdout = data["final_holdout_2026"]
    if discovery.get("status") != "LOCKED_PENDING_EXPLICIT_DATA_ACCESS_AUTHORIZATION":
        raise ValueError("H01 Discovery lock changed")
    if discovery.get("source_partition_start_month") != DISCOVERY_START_MONTH:
        raise ValueError("H01 Discovery start partition mismatch")
    if discovery.get("source_partition_end_month") != DISCOVERY_END_MONTH:
        raise ValueError("H01 Discovery end partition mismatch")
    if discovery.get("effective_start_utc_inclusive") != EFFECTIVE_START_UTC:
        raise ValueError("H01 effective start mismatch")
    if discovery.get("effective_end_utc_exclusive") != EFFECTIVE_END_UTC:
        raise ValueError("H01 effective end mismatch")
    if discovery.get("minimum_resolved_trades") != 100:
        raise ValueError("H01 Discovery minimum sample changed")
    if not str(validation.get("status", "")).startswith("PHYSICALLY_LOCKED_"):
        raise ValueError("H01 Validation is not physically locked")
    if not str(holdout.get("status", "")).startswith("LOCKED_"):
        raise ValueError("H01 2026 holdout is not locked")
    if tuple(data.get("universe", ())) != FROZEN_UNIVERSE:
        raise ValueError("H01 universe mismatch")
    if data.get("cross_exchange_backfill_allowed") is not False:
        raise ValueError("cross-exchange backfill unexpectedly enabled")
    if data.get("interpolation_allowed") is not False:
        raise ValueError("interpolation unexpectedly enabled")

    signal = h01["signal_formation"]
    if signal.get("inherit_exactly_from_closed_p00") is not True:
        raise ValueError("H01 no longer inherits P00 signal formation")
    p00_primary = p00["primary_hypothesis"]
    p00_params = p00_primary["parameters"]
    comparisons = {
        "lookback_bars": "lookback_bars",
        "atr_length": "atr_length",
        "zone_atr_fraction": "zone_atr_fraction",
        "retest_window_bars": "retest_window_bars",
        "stop_atr_fraction": "stop_atr_fraction",
        "tp1_r_multiple": "tp1_r_multiple",
        "tp2_r_multiple": "tp2_r_multiple",
        "min_net_rr": "min_net_rr",
        "max_holding_bars": "max_holding_bars",
        "require_bullish_breakout_body": "require_bullish_breakout_body",
    }
    for h01_key, p00_key in comparisons.items():
        if signal.get(h01_key) != p00_params.get(p00_key):
            raise ValueError(f"H01 signal formation diverged from P00: {h01_key}")
    if h01["cost_policy"].get("inherit_p00_cost_scenarios") is not True:
        raise ValueError("H01 cost inheritance changed")

    uncertainty = h01["uncertainty"]
    if uncertainty != {
        "method": "UTC_CALENDAR_DAY_BLOCK_BOOTSTRAP",
        "repetitions": 5000,
        "seed": 230911,
        "confidence": 0.95,
    }:
        raise ValueError("H01 uncertainty policy changed")

    start_ms = _parse_utc_ms(EFFECTIVE_START_UTC)
    end_ms = _parse_utc_ms(EFFECTIVE_END_UTC)
    if start_ms >= end_ms:
        raise ValueError("invalid H01 effective Discovery window")
    return h01, p00, start_ms, end_ms


def _parameters_from_h01(h01: dict[str, Any]) -> ResearchParameters:
    p = h01["signal_formation"]
    parameters = ResearchParameters(
        timeframe=p["timeframe"],
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


def _cost_from_p00(p00: dict[str, Any], name: str) -> CostAssumptions:
    match = next((item for item in p00["cost_scenarios"] if item["name"] == name), None)
    if match is None:
        raise ValueError(f"missing inherited P00 cost scenario {name}")
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


def _prefix(symbol: str) -> str:
    if symbol not in FROZEN_UNIVERSE:
        raise ValueError("symbol outside frozen H01 universe")
    return f"{symbol[:-4]}_USDT"


def run_h01_discovery(
    raw_dir: str | Path,
    output_dir: str | Path,
    *,
    authorization_path: str | Path,
) -> H01DiscoveryReceipt:
    """Run only authorized H01 Discovery; fail closed before market bytes otherwise."""

    try:
        h01, p00, start_ms, end_ms = _freeze_bindings()
    except Exception as exc:
        return _blocked(f"AUTHORITY_BINDING:{type(exc).__name__}:{exc}")

    authorization_fingerprint: str | None = None
    for symbol in FROZEN_UNIVERSE:
        preflight = validate_h01_discovery_access_request(
            symbol=symbol,
            start_month=DISCOVERY_START_MONTH,
            end_month=DISCOVERY_END_MONTH,
            authorization_path=authorization_path,
        )
        if preflight.status != "PASS_H01_DISCOVERY_ACCESS_PREFLIGHT":
            reason = preflight.reasons[0] if preflight.reasons else "H01_DISCOVERY_ACCESS_PREFLIGHT_NOT_PASS"
            return _blocked(
                f"DATA_ACCESS_AUTHORIZATION:{symbol}:{reason}",
                authorization_fingerprint=preflight.authorization_fingerprint,
            )
        if authorization_fingerprint is None:
            authorization_fingerprint = preflight.authorization_fingerprint
        elif authorization_fingerprint != preflight.authorization_fingerprint:
            return _blocked("DATA_ACCESS_AUTHORIZATION:FINGERPRINT_CHANGED_DURING_PREFLIGHT")

    raw_root = Path(raw_dir)
    output_root = Path(output_dir)
    expected_paths: list[tuple[str, str, Path]] = []
    for symbol in FROZEN_UNIVERSE:
        prefix = _prefix(symbol)
        for month in EXPECTED_MONTHS:
            expected_paths.append((symbol, month, raw_root / f"{prefix}-Min15-{month}-01.csv"))
    missing = [path.name for _, _, path in expected_paths if not path.is_file()]
    if missing:
        return _blocked(
            f"SOURCE_PREFLIGHT:MISSING_EXPECTED_DISCOVERY_FILE:{missing[0]}",
            authorization_fingerprint=authorization_fingerprint,
        )

    canonical_dir = output_root / "canonical"
    receipt_dir = output_root / "adapter_receipts"
    audit_status: dict[str, str] = {}
    audit_fingerprints: dict[str, str] = {}
    source_rows: dict[str, int] = {symbol: 0 for symbol in FROZEN_UNIVERSE}
    total_gaps = 0
    total_missing = 0
    candles_by_symbol: dict[str, list] = {symbol: [] for symbol in FROZEN_UNIVERSE}

    for symbol, month, raw_path in expected_paths:
        canonical_path = canonical_dir / f"{raw_path.stem}.canonical.csv"
        adapter_receipt_path = receipt_dir / f"{raw_path.stem}.adapter.json"
        adapter = adapt_mexc_bulk_csv(raw_path, canonical_path)
        write_adapter_receipt(adapter_receipt_path, adapter)
        if adapter.status != "PASS_ADAPTER_ONLY":
            return _blocked(
                f"ADAPTER_PREFLIGHT:{symbol}:{month}:{adapter.status}",
                authorization_fingerprint=authorization_fingerprint,
                audit_status_by_partition=audit_status,
                audit_fingerprint_by_partition=audit_fingerprints,
                source_row_count_by_symbol=source_rows,
                total_detected_gap_count=total_gaps,
                total_missing_candle_count=total_missing,
                source_market_bytes_read=True,
            )

        package = audit_h01_month(
            raw_path,
            canonical_path,
            adapter_receipt_path,
            symbol=symbol,
            month=month,
            authorization_path=authorization_path,
        )
        manifest = package.manifest
        key = f"{symbol}:{month}"
        audit_status[key] = manifest.status
        audit_fingerprints[key] = manifest.fingerprint
        source_rows[symbol] += manifest.row_count
        total_gaps += manifest.detected_gap_count
        total_missing += manifest.missing_candle_count
        if manifest.status not in PASS_STATUSES:
            reason = manifest.reasons[0] if manifest.reasons else manifest.status
            return _blocked(
                f"MONTH_AUDIT:{key}:{reason}",
                authorization_fingerprint=authorization_fingerprint,
                audit_status_by_partition=audit_status,
                audit_fingerprint_by_partition=audit_fingerprints,
                source_row_count_by_symbol=source_rows,
                total_detected_gap_count=total_gaps,
                total_missing_candle_count=total_missing,
                source_market_bytes_read=True,
            )
        candles_by_symbol[symbol].extend(package.candles)

    effective_counts: dict[str, int] = {}
    effective: dict[str, list] = {}
    for symbol in FROZEN_UNIVERSE:
        trimmed = [
            candle
            for candle in candles_by_symbol[symbol]
            if start_ms <= candle.open_time < end_ms
        ]
        trimmed = validate_candles(trimmed, require_regular_spacing=False)
        if not trimmed:
            return _blocked(
                f"EFFECTIVE_WINDOW:EMPTY:{symbol}",
                authorization_fingerprint=authorization_fingerprint,
                audit_status_by_partition=audit_status,
                audit_fingerprint_by_partition=audit_fingerprints,
                source_row_count_by_symbol=source_rows,
                effective_candle_count_by_symbol=effective_counts,
                total_detected_gap_count=total_gaps,
                total_missing_candle_count=total_missing,
                source_market_bytes_read=True,
            )
        if trimmed[0].open_time != start_ms:
            return _blocked(
                f"EFFECTIVE_WINDOW:START_MISMATCH:{symbol}",
                authorization_fingerprint=authorization_fingerprint,
                audit_status_by_partition=audit_status,
                audit_fingerprint_by_partition=audit_fingerprints,
                source_row_count_by_symbol=source_rows,
                effective_candle_count_by_symbol=effective_counts,
                total_detected_gap_count=total_gaps,
                total_missing_candle_count=total_missing,
                source_market_bytes_read=True,
            )
        if trimmed[-1].open_time != end_ms - TIMEFRAME_MS:
            return _blocked(
                f"EFFECTIVE_WINDOW:END_MISMATCH:{symbol}",
                authorization_fingerprint=authorization_fingerprint,
                audit_status_by_partition=audit_status,
                audit_fingerprint_by_partition=audit_fingerprints,
                source_row_count_by_symbol=source_rows,
                effective_candle_count_by_symbol=effective_counts,
                total_detected_gap_count=total_gaps,
                total_missing_candle_count=total_missing,
                source_market_bytes_read=True,
            )
        effective[symbol] = trimmed
        effective_counts[symbol] = len(trimmed)

    parameters = _parameters_from_h01(h01)
    base_costs = _cost_from_p00(p00, "BASE_SENSITIVITY")
    stress_costs = _cost_from_p00(p00, "STRESS")

    # FIRST H01 CONFIRMATORY OUTCOME INSPECTION POINT. Everything above is authority,
    # provenance, schema and integrity preflight only.
    base_records, base_metrics = evaluate_h01_universe(effective, parameters, base_costs)
    stress = reprice_h01_fixed_cohort(
        base_records,
        stress_costs,
        min_net_rr=parameters.min_net_rr,
    )
    uncertainty = h01["uncertainty"]
    bootstrap = day_block_bootstrap_expectancy(
        base_records,
        repetitions=uncertainty["repetitions"],
        seed=uncertainty["seed"],
        confidence=uncertainty["confidence"],
    )
    decision = classify_h01_stage(
        H01ResearchStage.DISCOVERY,
        base_metrics,
        stress,
        bootstrap,
    )

    receipt = H01DiscoveryReceipt(
        status="H01_DISCOVERY_COMPLETE",
        reasons=(),
        hypothesis_id=HYPOTHESIS_ID,
        family_id=FAMILY_ID,
        h01_freeze_fingerprint=H01_FREEZE_FINGERPRINT,
        authorization_fingerprint=authorization_fingerprint,
        universe=FROZEN_UNIVERSE,
        timeframe="15m",
        source_start_month=DISCOVERY_START_MONTH,
        source_end_month=DISCOVERY_END_MONTH,
        effective_start_utc_inclusive=EFFECTIVE_START_UTC,
        effective_end_utc_exclusive=EFFECTIVE_END_UTC,
        audit_status_by_partition=audit_status,
        audit_fingerprint_by_partition=audit_fingerprints,
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
        validation_unlock_eligible=decision.validation_unlock_eligible,
        validation_2025_access_performed=False,
        holdout_2026_access_performed=False,
        source_market_bytes_read=True,
        network_access_performed=False,
        exchange_mutation_performed=False,
        submitted_to_exchange=False,
        h01_evaluation_performed=True,
        fingerprint="",
    )
    return _with_fingerprint(receipt)


def write_receipt(path: str | Path, receipt: H01DiscoveryReceipt) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(asdict(receipt), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
