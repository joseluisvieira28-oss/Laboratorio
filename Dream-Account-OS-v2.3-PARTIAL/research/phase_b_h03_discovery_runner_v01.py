from __future__ import annotations

"""Authorized offline H03 Binance Discovery runner.

Network acquisition is deliberately outside this research module. This runner accepts
only a complete local corpus of the exact frozen 4,380 official Binance daily Spot
15m archives plus their CHECKSUM files. It verifies the separately frozen H03 data
access authorization before any market-data bytes are opened, adapts/audits every
archive fail-closed, evaluates the unchanged H03 rule only after the full corpus
passes, and writes one machine-readable Discovery receipt.
"""

from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

from research.phase_b_h03_binance_daily_manifest_v01 import (
    EXPECTED_ARCHIVE_COUNT,
    FREEZE_FINGERPRINT,
    build_h03_manifest_receipt,
    expected_h03_daily_objects,
)
from research.phase_b_h03_binance_offline_adapter_v01 import (
    TIMEFRAME_MS,
    adapt_binance_daily_archive_bytes,
)
from research.phase_b_h03_research_evaluator_v01 import (
    day_block_bootstrap_expectancy,
    evaluate_h03_universe,
    reprice_h03_fixed_cohort,
)
from research.phase_b_h03_stage_classifier_v01 import (
    classify_h03_binance_discovery,
    decision_as_dict,
)
from research.phase_b_signal_formation_v01 import CostAssumptions, ResearchParameters


HYPOTHESIS_ID = "H03_BINANCE_CROSS_VENUE_US_EU_OVERLAP_REPLICATION"
AUTHORIZATION_DOCUMENT_TYPE = "PHASE_B_H03_BINANCE_DATA_ACCESS_AUTHORIZATION"
AUTHORIZATION_STATUS = "AUTHORIZED_H03_BINANCE_DISCOVERY_ACQUISITION_AND_OFFLINE_EVALUATION_ONLY"
EXPECTED_AUTHORIZATION_FINGERPRINT = "3d29d29cf2a10030f4558678814d3782ee6f7b469ae1c33ae7a038fec4e7881d"
EXPECTED_MANIFEST_FINGERPRINT = "d6c61428fb54984d13b22fe98294eb5c59f82d4c086ae3120cebeb7998743856"
DEFAULT_AUTHORIZATION_PATH = Path(__file__).with_name("PHASE_B_H03_BINANCE_DATA_ACCESS_AUTHORIZATION_V0.1.json")
DEFAULT_RAW_ROOT = Path(__file__).with_name("local_data") / "h03_binance_raw"
DEFAULT_OUTPUT_PATH = Path(__file__).with_name("local_data") / "h03_binance_output" / "latest_h03_discovery_receipt.json"

BASE_COSTS = CostAssumptions(
    name="BASE_SENSITIVITY",
    fee_pct_each_side=0.05,
    spread_pct=0.05,
    slippage_pct_each_side=0.025,
)
STRESS_COSTS = CostAssumptions(
    name="STRESS",
    fee_pct_each_side=0.05,
    spread_pct=0.10,
    slippage_pct_each_side=0.05,
)
PARAMETERS = ResearchParameters()

NETWORK_ACCESS_PERFORMED_BY_RUNNER = False
EXCHANGE_MUTATION_PERFORMED = False
LIVE_TRADING_PERFORMED = False
MEXC_VALIDATION_2025_ACCESSED = False
HOLDOUT_2026_ACCESSED = False


def _canonical_hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def _write_receipt(path: Path, body: dict[str, Any]) -> dict[str, Any]:
    payload = dict(body)
    payload["fingerprint"] = _canonical_hash(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def _load_and_validate_authorization(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    supplied = raw.get("fingerprint")
    unsigned = dict(raw)
    unsigned.pop("fingerprint", None)
    recomputed = _canonical_hash(unsigned)
    if supplied != EXPECTED_AUTHORIZATION_FINGERPRINT or recomputed != EXPECTED_AUTHORIZATION_FINGERPRINT:
        raise PermissionError("H03 authorization fingerprint mismatch")
    required = {
        "document_type": AUTHORIZATION_DOCUMENT_TYPE,
        "status": AUTHORIZATION_STATUS,
        "hypothesis_id": HYPOTHESIS_ID,
        "source": "OFFICIAL_BINANCE_PUBLIC_DATA_ONLY",
        "market_type": "SPOT",
        "timeframe": "15m",
        "archive_granularity": "DAILY_ZIP_FILES",
        "start_utc_inclusive": "2021-02-01T00:00:00.000Z",
        "end_utc_exclusive": "2023-02-01T00:00:00.000Z",
        "expected_calendar_days": 730,
        "expected_archive_count": 4380,
        "expected_checksum_count": 4380,
        "checksum_required": True,
        "market_data_access_authorized": True,
        "network_download_authorized": True,
        "offline_evaluation_authorized": True,
        "mexc_validation_2025_09_through_2025_12_authorized": False,
        "holdout_2026_authorized": False,
        "exchange_mutation_authorized": False,
        "live_trading_authorized": False,
        "main_merge_authorized": False,
        "render_deploy_authorized": False,
        "cross_exchange_backfill_for_h02_authorized": False,
    }
    for key, value in required.items():
        if raw.get(key) != value:
            raise PermissionError(f"H03 authorization field mismatch: {key}")
    bindings = raw.get("required_bindings") or {}
    if bindings.get("h03_prospective_freeze_fingerprint") != FREEZE_FINGERPRINT:
        raise PermissionError("H03 freeze binding mismatch")
    if bindings.get("manifest_fingerprint") != EXPECTED_MANIFEST_FINGERPRINT:
        raise PermissionError("H03 manifest binding mismatch")
    if raw.get("symbols") != ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT"]:
        raise PermissionError("H03 symbol universe mismatch")
    return raw


def _utc_iso(ms: int | None) -> str | None:
    if ms is None:
        return None
    return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def run_h03_discovery(
    raw_root: Path = DEFAULT_RAW_ROOT,
    output_path: Path = DEFAULT_OUTPUT_PATH,
    authorization_path: Path = DEFAULT_AUTHORIZATION_PATH,
) -> dict[str, Any]:
    authorization = _load_and_validate_authorization(authorization_path)
    manifest = build_h03_manifest_receipt()
    if manifest.get("fingerprint") != EXPECTED_MANIFEST_FINGERPRINT:
        raise PermissionError("H03 manifest fingerprint drift")

    objects = expected_h03_daily_objects()
    if len(objects) != EXPECTED_ARCHIVE_COUNT:
        raise RuntimeError("H03 manifest cardinality drift")

    missing: list[str] = []
    for item in objects:
        symbol_dir = raw_root / item["symbol"]
        archive = symbol_dir / item["archive_filename"]
        checksum = symbol_dir / (item["archive_filename"] + ".CHECKSUM")
        if not archive.is_file():
            missing.append(str(archive))
        if not checksum.is_file():
            missing.append(str(checksum))
    if missing:
        return _write_receipt(
            output_path,
            {
                "document_type": "PHASE_B_H03_BINANCE_DISCOVERY_RECEIPT",
                "version": "0.1",
                "status": "H03_DISCOVERY_NOT_RUN_INTAKE_INCOMPLETE",
                "hypothesis_id": HYPOTHESIS_ID,
                "authorization_fingerprint": authorization["fingerprint"],
                "manifest_fingerprint": manifest["fingerprint"],
                "expected_archive_count": EXPECTED_ARCHIVE_COUNT,
                "missing_file_count": len(missing),
                "first_missing": missing[0],
                "market_data_bytes_opened": False,
                "outcome_evaluation_performed": False,
                "mexc_validation_2025_accessed": False,
                "holdout_2026_accessed": False,
                "network_access_performed_by_runner": False,
                "exchange_mutation_performed": False,
                "live_trading_performed": False,
            },
        )

    candles_by_symbol: dict[str, list] = {symbol: [] for symbol in authorization["symbols"]}
    integrity = {
        "archives_expected": EXPECTED_ARCHIVE_COUNT,
        "archives_passed": 0,
        "checksum_verified": 0,
        "source_rows": 0,
        "detected_internal_gap_count": 0,
        "missing_candles_including_day_boundaries": 0,
    }
    per_symbol_rows = {symbol: 0 for symbol in authorization["symbols"]}
    archive_sha256: dict[str, str] = {}

    for item in objects:
        symbol = item["symbol"]
        day = item["date_utc"]
        symbol_dir = raw_root / symbol
        archive_path = symbol_dir / item["archive_filename"]
        checksum_path = symbol_dir / (item["archive_filename"] + ".CHECKSUM")
        archive_bytes = archive_path.read_bytes()
        checksum_text = checksum_path.read_text(encoding="utf-8")
        adapted = adapt_binance_daily_archive_bytes(
            symbol=symbol,
            day=day,
            archive_filename=item["archive_filename"],
            archive_bytes=archive_bytes,
            checksum_text=checksum_text,
        )
        if not adapted.status.startswith("PASS_BINANCE_DAILY"):
            return _write_receipt(
                output_path,
                {
                    "document_type": "PHASE_B_H03_BINANCE_DISCOVERY_RECEIPT",
                    "version": "0.1",
                    "status": "H03_DISCOVERY_NOT_RUN_DATA_INTEGRITY_BLOCK",
                    "hypothesis_id": HYPOTHESIS_ID,
                    "authorization_fingerprint": authorization["fingerprint"],
                    "manifest_fingerprint": manifest["fingerprint"],
                    "blocked_symbol": symbol,
                    "blocked_date_utc": day,
                    "blocked_archive": adapted.archive_filename,
                    "blocked_status": adapted.status,
                    "blocked_reasons": list(adapted.reasons),
                    "archives_passed_before_block": integrity["archives_passed"],
                    "market_data_bytes_opened": True,
                    "outcome_evaluation_performed": False,
                    "mexc_validation_2025_accessed": False,
                    "holdout_2026_accessed": False,
                    "network_access_performed_by_runner": False,
                    "exchange_mutation_performed": False,
                    "live_trading_performed": False,
                },
            )

        if not adapted.candles:
            raise RuntimeError("passing daily adapter returned no candles")
        day_start = int(datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp() * 1000)
        day_end = day_start + 86_400_000
        leading_missing = (adapted.candles[0].open_time - day_start) // TIMEFRAME_MS
        trailing_missing = (day_end - TIMEFRAME_MS - adapted.candles[-1].open_time) // TIMEFRAME_MS
        total_missing = int(leading_missing + adapted.missing_candle_count + trailing_missing)
        if leading_missing < 0 or trailing_missing < 0 or adapted.row_count + total_missing != 96:
            return _write_receipt(
                output_path,
                {
                    "document_type": "PHASE_B_H03_BINANCE_DISCOVERY_RECEIPT",
                    "version": "0.1",
                    "status": "H03_DISCOVERY_NOT_RUN_DAY_COVERAGE_BLOCK",
                    "hypothesis_id": HYPOTHESIS_ID,
                    "authorization_fingerprint": authorization["fingerprint"],
                    "manifest_fingerprint": manifest["fingerprint"],
                    "blocked_symbol": symbol,
                    "blocked_date_utc": day,
                    "row_count": adapted.row_count,
                    "computed_missing_candles": total_missing,
                    "market_data_bytes_opened": True,
                    "outcome_evaluation_performed": False,
                    "mexc_validation_2025_accessed": False,
                    "holdout_2026_accessed": False,
                    "network_access_performed_by_runner": False,
                    "exchange_mutation_performed": False,
                    "live_trading_performed": False,
                },
            )

        integrity["archives_passed"] += 1
        integrity["checksum_verified"] += int(adapted.checksum_verified)
        integrity["source_rows"] += adapted.row_count
        integrity["detected_internal_gap_count"] += adapted.detected_gap_count
        integrity["missing_candles_including_day_boundaries"] += total_missing
        per_symbol_rows[symbol] += adapted.row_count
        archive_sha256[f"{symbol}/{adapted.archive_filename}"] = adapted.archive_sha256
        candles_by_symbol[symbol].extend(adapted.candles)

    if integrity["archives_passed"] != EXPECTED_ARCHIVE_COUNT or integrity["checksum_verified"] != EXPECTED_ARCHIVE_COUNT:
        raise RuntimeError("H03 full-corpus integrity count mismatch")

    base_records, base_metrics, diagnostics = evaluate_h03_universe(
        candles_by_symbol,
        PARAMETERS,
        BASE_COSTS,
    )
    bootstrap = day_block_bootstrap_expectancy(
        base_records,
        repetitions=5000,
        seed=230911,
        confidence=0.95,
    )
    stress = reprice_h03_fixed_cohort(base_records, STRESS_COSTS, min_net_rr=2.0)
    decision = classify_h03_binance_discovery(base_metrics, stress, bootstrap)

    all_times = [c.open_time for values in candles_by_symbol.values() for c in values]
    archive_set_fingerprint = _canonical_hash(archive_sha256)
    body = {
        "document_type": "PHASE_B_H03_BINANCE_DISCOVERY_RECEIPT",
        "version": "0.1",
        "status": "H03_DISCOVERY_COMPLETE",
        "hypothesis_id": HYPOTHESIS_ID,
        "source": "OFFICIAL_BINANCE_PUBLIC_DATA_ONLY",
        "market_type": "SPOT",
        "timeframe": "15m",
        "window_start_utc_inclusive": "2021-02-01T00:00:00.000Z",
        "window_end_utc_exclusive": "2023-02-01T00:00:00.000Z",
        "symbols": authorization["symbols"],
        "authorization_fingerprint": authorization["fingerprint"],
        "h03_freeze_fingerprint": FREEZE_FINGERPRINT,
        "manifest_fingerprint": manifest["fingerprint"],
        "archive_set_fingerprint": archive_set_fingerprint,
        "integrity": integrity,
        "per_symbol_source_rows": per_symbol_rows,
        "first_candle_open_time_utc": _utc_iso(min(all_times) if all_times else None),
        "last_candle_open_time_utc": _utc_iso(max(all_times) if all_times else None),
        "base_metrics": asdict(base_metrics),
        "diagnostics": diagnostics,
        "bootstrap": asdict(bootstrap),
        "fixed_cohort_stress": asdict(stress),
        "decision": decision_as_dict(decision),
        "market_data_bytes_opened": True,
        "outcome_evaluation_performed": True,
        "mexc_validation_2025_accessed": False,
        "holdout_2026_accessed": False,
        "network_access_performed_by_runner": NETWORK_ACCESS_PERFORMED_BY_RUNNER,
        "exchange_mutation_performed": EXCHANGE_MUTATION_PERFORMED,
        "live_trading_performed": LIVE_TRADING_PERFORMED,
    }
    return _write_receipt(output_path, body)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    raw_root = Path(args[0]) if len(args) >= 1 else DEFAULT_RAW_ROOT
    output_path = Path(args[1]) if len(args) >= 2 else DEFAULT_OUTPUT_PATH
    authorization_path = Path(args[2]) if len(args) >= 3 else DEFAULT_AUTHORIZATION_PATH
    try:
        receipt = run_h03_discovery(raw_root, output_path, authorization_path)
    except Exception as exc:
        print(f"H03_DISCOVERY_FATAL: {type(exc).__name__}: {exc}")
        return 2
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt.get("status") == "H03_DISCOVERY_COMPLETE" else 3


if __name__ == "__main__":
    raise SystemExit(main())
