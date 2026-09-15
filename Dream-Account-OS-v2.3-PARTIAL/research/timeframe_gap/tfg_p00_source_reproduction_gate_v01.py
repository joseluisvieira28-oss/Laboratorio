from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from research.phase_b_mexc_discovery_corpus_v01 import (
    PASS_CORPUS_STATUSES,
    build_discovery_corpus,
    write_manifest,
)

START_MONTH = "2023-02"
END_MONTH = "2024-12"
SYMBOLS = (
    "BTCUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "BNBUSDT",
    "XRPUSDT",
    "DOGEUSDT",
)

# Historical P00 corpus fingerprints recovered from the original offline
# Phase B corpus audit receipts. Each fingerprint commits to the full corpus
# manifest, including every monthly source SHA-256, canonical SHA-256,
# adapter/audit fingerprint, row count, gap accounting and boundary checks.
EXPECTED_CORPUS_FINGERPRINTS = {
    "BTCUSDT": "fba38a205b911fad0494b86174ef06a2d04a5908b0617a27efb74f067f8cf1d9",
    "ETHUSDT": "5a6433eb8703a9bcd0714fc6485ccc965cf754941ee6c69981158a7f11f36b7f",
    "SOLUSDT": "db013d47799b99a7c827740cf03c8e7e27b08c317097836143c855f1a51dde9b",
    "BNBUSDT": "ec43c0ab51dbf80fcde273c7d817b7cf9995e1614dfa5c05de4f664b9880437a",
    "XRPUSDT": "9b15ebea40555f5d6def5aab65cc5485db8120e0a6fa74f53ac4bb981a004427",
    "DOGEUSDT": "786a0129a2a7c9b58e2a465383d4849cedc3192e2c24bf8e4474ee709a3323fe",
}

PASS_STATUS = "PASS_EXACT_P00_CORPUS_REPRODUCTION"
BLOCK_STATUS = "BLOCKED_CORPUS_REPRODUCTION"

# Hard research posture. This module is source-integrity only.
P00_EVALUATION_PERFORMED = False
MARKET_OUTCOME_EVALUATION_PERFORMED = False
NETWORK_ACCESS_PERFORMED = False
EXCHANGE_MUTATION_PERFORMED = False
ACCESS_2025_PERFORMED = False
ACCESS_2026_PERFORMED = False


@dataclass(frozen=True)
class SymbolReproductionReceipt:
    symbol: str
    corpus_status: str
    observed_fingerprint: str
    expected_fingerprint: str
    fingerprint_match: bool
    passed_month_count: int
    expected_month_count: int
    total_row_count: int
    months_with_gaps_count: int
    total_detected_gap_count: int
    total_missing_candle_count: int


@dataclass(frozen=True)
class ReproductionReceipt:
    status: str
    reasons: tuple[str, ...]
    start_month: str
    end_month: str
    expected_symbol_count: int
    matched_symbol_count: int
    symbols: tuple[SymbolReproductionReceipt, ...]
    p00_evaluation_performed: bool
    market_outcome_evaluation_performed: bool
    network_access_performed: bool
    exchange_mutation_performed: bool
    access_2025_performed: bool
    access_2026_performed: bool
    fingerprint: str


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _receipt_fingerprint(payload: dict[str, Any]) -> str:
    clone = dict(payload)
    clone.pop("fingerprint", None)
    return hashlib.sha256(_canonical_json(clone)).hexdigest()


def _build_receipt(
    *,
    status: str,
    reasons: list[str],
    symbols: list[SymbolReproductionReceipt],
) -> ReproductionReceipt:
    payload: dict[str, Any] = {
        "status": status,
        "reasons": tuple(sorted(set(reasons))),
        "start_month": START_MONTH,
        "end_month": END_MONTH,
        "expected_symbol_count": len(SYMBOLS),
        "matched_symbol_count": sum(1 for item in symbols if item.fingerprint_match),
        "symbols": tuple(symbols),
        "p00_evaluation_performed": P00_EVALUATION_PERFORMED,
        "market_outcome_evaluation_performed": MARKET_OUTCOME_EVALUATION_PERFORMED,
        "network_access_performed": NETWORK_ACCESS_PERFORMED,
        "exchange_mutation_performed": EXCHANGE_MUTATION_PERFORMED,
        "access_2025_performed": ACCESS_2025_PERFORMED,
        "access_2026_performed": ACCESS_2026_PERFORMED,
        "fingerprint": "",
    }
    serializable = {
        **payload,
        "symbols": [asdict(item) for item in symbols],
    }
    payload["fingerprint"] = _receipt_fingerprint(serializable)
    return ReproductionReceipt(**payload)


def reproduce_exact_p00_corpus(
    raw_dir: str | Path,
    work_dir: str | Path,
) -> ReproductionReceipt:
    """Rebuild the original P00 source corpus audit and require 6/6 identity.

    This function is deliberately outcome-blind. It only calls the original
    offline Phase B corpus builder, then compares each resulting full-manifest
    fingerprint with the historical P00 fingerprint for that symbol.

    It performs no network access, no exchange action, no signal/trade/return
    calculation, and cannot open 2025 or 2026 because the range is hard-coded
    to the already-open 2023-02 through 2024-12 P00 source interval.
    """

    raw_root = Path(raw_dir)
    work_root = Path(work_dir)
    reasons: list[str] = []
    symbol_receipts: list[SymbolReproductionReceipt] = []

    if not raw_root.is_dir():
        return _build_receipt(
            status=BLOCK_STATUS,
            reasons=["RAW_DIRECTORY_NOT_FOUND"],
            symbols=[],
        )

    for symbol in SYMBOLS:
        output_dir = work_root / f"{symbol}_{START_MONTH}_{END_MONTH}"
        manifest = build_discovery_corpus(
            raw_root,
            output_dir,
            symbol=symbol,
            start_month=START_MONTH,
            end_month=END_MONTH,
        )

        manifest_receipt = output_dir / "reproduction_corpus_manifest.json"
        write_manifest(manifest_receipt, manifest)

        expected = EXPECTED_CORPUS_FINGERPRINTS[symbol]
        corpus_pass = manifest.status in PASS_CORPUS_STATUSES
        fingerprint_match = corpus_pass and manifest.fingerprint == expected

        symbol_receipts.append(
            SymbolReproductionReceipt(
                symbol=symbol,
                corpus_status=manifest.status,
                observed_fingerprint=manifest.fingerprint,
                expected_fingerprint=expected,
                fingerprint_match=fingerprint_match,
                passed_month_count=manifest.passed_month_count,
                expected_month_count=manifest.expected_month_count,
                total_row_count=manifest.total_row_count,
                months_with_gaps_count=manifest.months_with_gaps_count,
                total_detected_gap_count=manifest.total_detected_gap_count,
                total_missing_candle_count=manifest.total_missing_candle_count,
            )
        )

        if not corpus_pass:
            reasons.append(f"{symbol}:CORPUS_AUDIT_NOT_PASS:{manifest.status}")
        elif manifest.fingerprint != expected:
            reasons.append(f"{symbol}:HISTORICAL_CORPUS_FINGERPRINT_MISMATCH")

    all_matched = len(symbol_receipts) == len(SYMBOLS) and all(
        item.fingerprint_match for item in symbol_receipts
    )
    status = PASS_STATUS if all_matched else BLOCK_STATUS
    if not all_matched and not reasons:
        reasons.append("NOT_ALL_FROZEN_SYMBOLS_REPRODUCED")

    return _build_receipt(status=status, reasons=reasons, symbols=symbol_receipts)


def write_receipt(path: str | Path, receipt: ReproductionReceipt) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(asdict(receipt), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _main() -> int:
    parser = argparse.ArgumentParser(
        description="Outcome-blind exact reproduction gate for the historical P00 MEXC source corpus"
    )
    parser.add_argument("raw_dir", help="Directory containing the official monthly MEXC Spot 15m CSVs")
    parser.add_argument(
        "--work-dir",
        required=True,
        help="Directory used for canonicalized corpus/audit artifacts",
    )
    parser.add_argument("--receipt", help="Optional sanitized reproduction receipt path")
    args = parser.parse_args()

    result = reproduce_exact_p00_corpus(args.raw_dir, args.work_dir)
    if args.receipt:
        write_receipt(args.receipt, result)
    print(json.dumps(asdict(result), indent=2, sort_keys=True))
    return 0 if result.status == PASS_STATUS else 2


if __name__ == "__main__":
    raise SystemExit(_main())
