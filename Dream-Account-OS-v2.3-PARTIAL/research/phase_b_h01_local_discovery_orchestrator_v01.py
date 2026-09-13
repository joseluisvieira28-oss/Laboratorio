from __future__ import annotations

"""One-command local orchestrator for authorized H01 Discovery.

This module is intentionally offline-only. It copies/checks only the exact frozen
2025-01..2025-08 MEXC Spot 15m filenames, then delegates integrity/audit/evaluation
to the already-frozen H01 runner. It never constructs 2025-09..12 or 2026 paths and
contains no downloader, HTTP client, exchange client, order route or live authority.
"""

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from research.phase_b_h01_discovery_runner_v01 import run_h01_discovery, write_receipt as write_discovery_receipt
from research.phase_b_h01_mexc_discovery_access_v01 import (
    DEFAULT_AUTHORIZATION_PATH,
    DISCOVERY_END_MONTH,
    DISCOVERY_START_MONTH,
    EXPECTED_MONTHS,
    FROZEN_UNIVERSE,
    intake_h01_discovery_downloads,
    write_receipt as write_intake_receipt,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW_DIR = Path(__file__).with_name("local_data") / "h01_discovery_raw"
DEFAULT_OUTPUT_DIR = Path(__file__).with_name("local_data") / "h01_discovery_output"


def _prefix(symbol: str) -> str:
    if symbol not in FROZEN_UNIVERSE:
        raise ValueError("symbol outside frozen H01 universe")
    return f"{symbol[:-4]}_USDT"


def expected_raw_paths(raw_dir: str | Path) -> tuple[Path, ...]:
    root = Path(raw_dir)
    return tuple(
        root / f"{_prefix(symbol)}-Min15-{month}-01.csv"
        for symbol in FROZEN_UNIVERSE
        for month in EXPECTED_MONTHS
    )


def run_local_h01_discovery(
    source_dir: str | Path,
    *,
    raw_dir: str | Path = DEFAULT_RAW_DIR,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    authorization_path: str | Path = DEFAULT_AUTHORIZATION_PATH,
) -> dict[str, Any]:
    source_root = Path(source_dir)
    raw_root = Path(raw_dir)
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)

    intake_status_by_symbol: dict[str, str] = {}
    intake_fingerprint_by_symbol: dict[str, str] = {}

    for symbol in FROZEN_UNIVERSE:
        receipt = intake_h01_discovery_downloads(
            source_root,
            raw_root,
            symbol=symbol,
            start_month=DISCOVERY_START_MONTH,
            end_month=DISCOVERY_END_MONTH,
            authorization_path=authorization_path,
        )
        intake_status_by_symbol[symbol] = receipt.status
        intake_fingerprint_by_symbol[symbol] = receipt.fingerprint
        write_intake_receipt(output_root / "intake_receipts" / f"{symbol}_h01_intake.json", receipt)
        if receipt.status == "BLOCKED_H01_DISCOVERY_INTAKE":
            summary = {
                "status": "BLOCKED_H01_DISCOVERY_LOCAL_ORCHESTRATOR",
                "reason": f"INTAKE_BLOCKED:{symbol}",
                "intake_status_by_symbol": intake_status_by_symbol,
                "intake_fingerprint_by_symbol": intake_fingerprint_by_symbol,
                "h01_evaluation_performed": False,
                "validation_2025_access_performed": False,
                "holdout_2026_access_performed": False,
                "network_access_performed": False,
                "exchange_mutation_performed": False,
                "submitted_to_exchange": False,
            }
            _write_summary(output_root, summary)
            return summary

    missing = tuple(path.name for path in expected_raw_paths(raw_root) if not path.is_file())
    if missing:
        summary = {
            "status": "H01_DISCOVERY_NOT_RUN_INTAKE_INCOMPLETE",
            "reason": "MISSING_AUTHORIZED_DISCOVERY_FILES",
            "missing_count": len(missing),
            "first_missing_file": missing[0],
            "intake_status_by_symbol": intake_status_by_symbol,
            "intake_fingerprint_by_symbol": intake_fingerprint_by_symbol,
            "h01_evaluation_performed": False,
            "validation_2025_access_performed": False,
            "holdout_2026_access_performed": False,
            "network_access_performed": False,
            "exchange_mutation_performed": False,
            "submitted_to_exchange": False,
        }
        _write_summary(output_root, summary)
        return summary

    discovery = run_h01_discovery(
        raw_root,
        output_root / "run",
        authorization_path=authorization_path,
    )
    write_discovery_receipt(output_root / "latest_h01_discovery_receipt.json", discovery)
    summary = {
        "status": discovery.status,
        "receipt_fingerprint": discovery.fingerprint,
        "decision": discovery.decision,
        "validation_unlock_eligible": discovery.validation_unlock_eligible,
        "intake_status_by_symbol": intake_status_by_symbol,
        "intake_fingerprint_by_symbol": intake_fingerprint_by_symbol,
        "h01_evaluation_performed": discovery.h01_evaluation_performed,
        "validation_2025_access_performed": discovery.validation_2025_access_performed,
        "holdout_2026_access_performed": discovery.holdout_2026_access_performed,
        "network_access_performed": discovery.network_access_performed,
        "exchange_mutation_performed": discovery.exchange_mutation_performed,
        "submitted_to_exchange": discovery.submitted_to_exchange,
    }
    _write_summary(output_root, summary)
    return summary


def _write_summary(output_root: Path, summary: dict[str, Any]) -> None:
    target = output_root / "latest_h01_local_orchestrator_summary.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Authorized offline H01 Discovery orchestrator")
    parser.add_argument("source_dir", help="Directory containing official MEXC Discovery CSV downloads")
    parser.add_argument("--raw-dir", default=str(DEFAULT_RAW_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--authorization", default=str(DEFAULT_AUTHORIZATION_PATH))
    args = parser.parse_args()

    summary = run_local_h01_discovery(
        args.source_dir,
        raw_dir=args.raw_dir,
        output_dir=args.output_dir,
        authorization_path=args.authorization,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["status"] == "H01_DISCOVERY_COMPLETE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
