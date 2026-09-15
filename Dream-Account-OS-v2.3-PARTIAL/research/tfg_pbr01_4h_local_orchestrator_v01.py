from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict
from pathlib import Path

from research.phase_b_mexc_discovery_corpus_v01 import PASS_CORPUS_STATUSES, build_discovery_corpus
from research import tfg_pbr01_4h_discovery_runner_v01 as runner

REFERENCE_FILE = "BTC_USDT-Min15-2023-02-01.csv"
REFERENCE_SHA256 = "31eff305411e5e5589e53b22e47554c9b50208d372322b19422270bfe5766e25"
EXPECTED_SOURCE_ROWS_PER_SYMBOL = 67_183
EXPECTED_EFFECTIVE_CANDLES_PER_SYMBOL = 67_151
EXPECTED_TOTAL_DETECTED_GAPS = 36
EXPECTED_TOTAL_MISSING_CANDLES = 102
EXPECTED_MONTHS_PER_SYMBOL = 23


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _blocked(reason: str, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "status": "BLOCKED_PRE_OUTCOME",
        "lab_id": runner.LAB_ID,
        "reason": reason,
        "outcome_evaluation_performed": False,
        "validation_access_performed": False,
        "holdout_2026_access_performed": False,
        "network_access_performed": False,
        "exchange_mutation_performed": False,
    }
    (output_dir / "TFG_PBR01_4H_LOCAL_PREFLIGHT_V0.1.json").write_text(
        json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, sort_keys=True, indent=2))
    return 2


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail-closed local execution for TFG-PBR01-4H-001")
    parser.add_argument("--raw-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    reference_path = raw_dir / REFERENCE_FILE
    if not reference_path.is_file():
        return _blocked(f"REFERENCE_FILE_MISSING:{REFERENCE_FILE}", output_dir)
    if _sha256(reference_path) != REFERENCE_SHA256:
        return _blocked("REFERENCE_SHA256_MISMATCH", output_dir)

    corpus_status_by_symbol: dict[str, str] = {}
    source_rows_by_symbol: dict[str, int] = {}
    effective_candles_by_symbol: dict[str, int] = {}
    total_detected_gaps = 0
    total_missing_candles = 0

    start_ms = runner._parse_ms(runner.DISCOVERY_START)
    end_ms = runner._parse_ms(runner.DISCOVERY_END)

    for symbol in runner.FROZEN_UNIVERSE:
        manifest = build_discovery_corpus(
            raw_dir,
            output_dir,
            symbol=symbol,
            start_month=runner.START_MONTH,
            end_month=runner.END_MONTH,
        )
        corpus_status_by_symbol[symbol] = manifest.status
        source_rows_by_symbol[symbol] = manifest.total_row_count
        total_detected_gaps += manifest.total_detected_gap_count
        total_missing_candles += manifest.total_missing_candle_count

        if manifest.status not in PASS_CORPUS_STATUSES:
            return _blocked(f"CORPUS_STATUS_FAILED:{symbol}:{manifest.status}", output_dir)
        if manifest.passed_month_count != EXPECTED_MONTHS_PER_SYMBOL:
            return _blocked(f"MONTH_COUNT_MISMATCH:{symbol}:{manifest.passed_month_count}", output_dir)
        if manifest.total_row_count != EXPECTED_SOURCE_ROWS_PER_SYMBOL:
            return _blocked(f"SOURCE_ROW_COUNT_MISMATCH:{symbol}:{manifest.total_row_count}", output_dir)

        effective = 0
        for month in runner._months(runner.START_MONTH, runner.END_MONTH):
            canonical_path = output_dir / "canonical" / f"{runner._prefix(symbol)}-Min15-{month}-01.canonical.csv"
            if not canonical_path.is_file():
                return _blocked(f"CANONICAL_MISSING:{canonical_path.name}", output_dir)
            effective += len(runner._load_canonical(canonical_path, start_ms, end_ms))
        effective_candles_by_symbol[symbol] = effective
        if effective != EXPECTED_EFFECTIVE_CANDLES_PER_SYMBOL:
            return _blocked(f"EFFECTIVE_CANDLE_COUNT_MISMATCH:{symbol}:{effective}", output_dir)

    if total_detected_gaps != EXPECTED_TOTAL_DETECTED_GAPS:
        return _blocked(f"TOTAL_GAP_COUNT_MISMATCH:{total_detected_gaps}", output_dir)
    if total_missing_candles != EXPECTED_TOTAL_MISSING_CANDLES:
        return _blocked(f"TOTAL_MISSING_CANDLE_COUNT_MISMATCH:{total_missing_candles}", output_dir)

    preflight = {
        "status": "PASS_PRE_OUTCOME_IDENTITY_GATE",
        "lab_id": runner.LAB_ID,
        "reference_file": REFERENCE_FILE,
        "reference_sha256": REFERENCE_SHA256,
        "corpus_status_by_symbol": corpus_status_by_symbol,
        "source_rows_by_symbol": source_rows_by_symbol,
        "effective_candles_by_symbol": effective_candles_by_symbol,
        "total_detected_gap_count": total_detected_gaps,
        "total_missing_candle_count": total_missing_candles,
        "outcome_evaluation_performed": False,
        "validation_access_performed": False,
        "holdout_2026_access_performed": False,
        "network_access_performed": False,
        "exchange_mutation_performed": False,
    }
    (output_dir / "TFG_PBR01_4H_LOCAL_PREFLIGHT_V0.1.json").write_text(
        json.dumps(preflight, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(preflight, sort_keys=True, indent=2))

    receipt = runner.run(raw_dir, output_dir)
    print(json.dumps(asdict(receipt), sort_keys=True, indent=2))
    return 0 if receipt.status == "TFG_PBR01_4H_DISCOVERY_COMPLETE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
