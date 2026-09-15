from __future__ import annotations

"""Fail-closed pre-outcome corpus audit for TFG-PBR01-1H-001.

This runner validates the exact P00 MEXC Discovery corpus identity, rebuilds the
canonical 15m layer, aggregates it to 1H, writes structural receipts, and stops.
It cannot calculate trade outcomes or performance metrics.
"""

import argparse
import hashlib
import json
from pathlib import Path

from research.phase_b_mexc_discovery_corpus_v01 import PASS_CORPUS_STATUSES, build_discovery_corpus
from research import tfg_pbr01_4h_discovery_runner_v01 as source_contract
from research.timeframe_gap.tfg_pbr01_1h_preoutcome_v01 import (
    LAB_ID,
    OUTCOME_COMPUTATION_AUTHORIZED,
    aggregate_15m_to_1h,
    preoutcome_summary,
)

REFERENCE_FILE = "BTC_USDT-Min15-2023-02-01.csv"
REFERENCE_SHA256 = "31eff305411e5e5589e53b22e47554c9b50208d372322b19422270bfe5766e25"
EXPECTED_SOURCE_ROWS_PER_SYMBOL = 67_183
EXPECTED_EFFECTIVE_CANDLES_PER_SYMBOL = 67_151
EXPECTED_TOTAL_DETECTED_GAPS = 36
EXPECTED_TOTAL_MISSING_CANDLES = 102
EXPECTED_MONTHS_PER_SYMBOL = 23
RECEIPT_NAME = "TFG_PBR01_1H_PREOUTCOME_PREFLIGHT_V0.1.json"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write(output_dir: Path, payload: dict) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / RECEIPT_NAME).write_text(
        json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, sort_keys=True, indent=2))


def _blocked(output_dir: Path, reason: str) -> int:
    _write(output_dir, {
        "status": "BLOCKED_PRE_OUTCOME",
        "lab_id": LAB_ID,
        "reason": reason,
        "outcome_evaluation_performed": False,
        "outcome_computation_authorized": False,
        "validation_2025_access_performed": False,
        "holdout_2026_access_performed": False,
        "network_access_performed": False,
        "exchange_mutation_performed": False,
        "submitted_to_exchange": False,
    })
    return 2


def run(raw_dir: Path, output_dir: Path) -> dict:
    if OUTCOME_COMPUTATION_AUTHORIZED:
        raise RuntimeError("preflight contract violation: outcomes unexpectedly authorized")

    reference = raw_dir / REFERENCE_FILE
    if not reference.is_file():
        raise RuntimeError(f"REFERENCE_FILE_MISSING:{REFERENCE_FILE}")
    if _sha256(reference) != REFERENCE_SHA256:
        raise RuntimeError("REFERENCE_SHA256_MISMATCH")

    start_ms = source_contract._parse_ms(source_contract.DISCOVERY_START)
    end_ms = source_contract._parse_ms(source_contract.DISCOVERY_END)

    source_rows_by_symbol: dict[str, int] = {}
    effective_15m_by_symbol: dict[str, int] = {}
    structural_1h_by_symbol: dict[str, dict] = {}
    corpus_status_by_symbol: dict[str, str] = {}
    total_gaps = 0
    total_missing = 0

    for symbol in source_contract.FROZEN_UNIVERSE:
        manifest = build_discovery_corpus(
            raw_dir,
            output_dir,
            symbol=symbol,
            start_month=source_contract.START_MONTH,
            end_month=source_contract.END_MONTH,
        )
        corpus_status_by_symbol[symbol] = manifest.status
        source_rows_by_symbol[symbol] = manifest.total_row_count
        total_gaps += manifest.total_detected_gap_count
        total_missing += manifest.total_missing_candle_count

        if manifest.status not in PASS_CORPUS_STATUSES:
            raise RuntimeError(f"CORPUS_STATUS_FAILED:{symbol}:{manifest.status}")
        if manifest.passed_month_count != EXPECTED_MONTHS_PER_SYMBOL:
            raise RuntimeError(f"MONTH_COUNT_MISMATCH:{symbol}:{manifest.passed_month_count}")
        if manifest.total_row_count != EXPECTED_SOURCE_ROWS_PER_SYMBOL:
            raise RuntimeError(f"SOURCE_ROW_COUNT_MISMATCH:{symbol}:{manifest.total_row_count}")

        source_15m = []
        for month in source_contract._months(source_contract.START_MONTH, source_contract.END_MONTH):
            path = output_dir / "canonical" / f"{source_contract._prefix(symbol)}-Min15-{month}-01.canonical.csv"
            if not path.is_file():
                raise RuntimeError(f"CANONICAL_MISSING:{path.name}")
            source_15m.extend(source_contract._load_canonical(path, start_ms, end_ms))
        effective_15m_by_symbol[symbol] = len(source_15m)
        if len(source_15m) != EXPECTED_EFFECTIVE_CANDLES_PER_SYMBOL:
            raise RuntimeError(f"EFFECTIVE_CANDLE_COUNT_MISMATCH:{symbol}:{len(source_15m)}")

        bars_1h = aggregate_15m_to_1h(source_15m)
        structural_1h_by_symbol[symbol] = preoutcome_summary(bars_1h)

    if total_gaps != EXPECTED_TOTAL_DETECTED_GAPS:
        raise RuntimeError(f"TOTAL_GAP_COUNT_MISMATCH:{total_gaps}")
    if total_missing != EXPECTED_TOTAL_MISSING_CANDLES:
        raise RuntimeError(f"TOTAL_MISSING_CANDLE_COUNT_MISMATCH:{total_missing}")

    return {
        "status": "PASS_PREOUTCOME_READY_NOT_ACTIVATED",
        "lab_id": LAB_ID,
        "reference_file": REFERENCE_FILE,
        "reference_sha256": REFERENCE_SHA256,
        "corpus_status_by_symbol": corpus_status_by_symbol,
        "source_rows_by_symbol": source_rows_by_symbol,
        "effective_15m_candles_by_symbol": effective_15m_by_symbol,
        "structural_1h_by_symbol": structural_1h_by_symbol,
        "total_source_detected_gap_count": total_gaps,
        "total_source_missing_candle_count": total_missing,
        "signal_geometry_evaluation_performed": False,
        "outcome_evaluation_performed": False,
        "outcome_computation_authorized": False,
        "validation_2025_access_performed": False,
        "holdout_2026_access_performed": False,
        "network_access_performed": False,
        "exchange_mutation_performed": False,
        "submitted_to_exchange": False,
        "next_required_authority": "EXPLICIT_ACTIVATION_AFTER_TFG_PBR01_4H_001_CLASSIFICATION",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Pre-outcome audit for TFG-PBR01-1H-001")
    parser.add_argument("--raw-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    raw_dir = Path(args.raw_dir)
    output_dir = Path(args.output_dir)
    try:
        payload = run(raw_dir, output_dir)
    except Exception as exc:
        return _blocked(output_dir, str(exc))
    _write(output_dir, payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
