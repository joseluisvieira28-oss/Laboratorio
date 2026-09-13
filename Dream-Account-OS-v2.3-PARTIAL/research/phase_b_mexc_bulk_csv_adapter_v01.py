from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass, replace
from math import isfinite
from pathlib import Path
from typing import Any

from research.phase_b_mexc_offline_ingest_v01 import EXPECTED_HEADER, TIMEFRAME_MS, file_sha256


ADAPTER_ID = "MEXC_BULK_MIN15_CSV_V0.1"
FREEZE_PATH = Path(__file__).with_name("PHASE_B_MEXC_RAW_ADAPTER_FREEZE_V0.1.json")
RAW_HEADER = (
    "open_time",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "amount",
    "close_time",
)
REFERENCE_SAMPLE_SHA256 = "31eff305411e5e5589e53b22e47554c9b50208d372322b19422270bfe5766e25"
REFERENCE_STRUCTURE_PROBE_FINGERPRINT = "37f97d142b649bc681d5b0b12c59c6ee211b71631a6437ffe92600e055bdab7a"
REFERENCE_SEMANTIC_PROBE_FINGERPRINT = "bc17cdf25e2e533e6bec9f4f167d7694cccb496ae98c73e9552912652f92da37"
RAW_CLOSE_DELTA_MS = TIMEFRAME_MS
CANONICAL_CLOSE_DELTA_MS = TIMEFRAME_MS - 1


@dataclass(frozen=True)
class AdapterReceipt:
    status: str
    adapter_id: str
    source_file_name: str
    source_sha256: str | None
    source_byte_size: int | None
    reference_sample_sha256_match: bool | None
    raw_header_match: bool | None
    raw_row_count: int
    canonical_file_name: str | None
    canonical_sha256: str | None
    canonical_byte_size: int | None
    canonical_header: tuple[str, ...]
    mapping_fingerprint: str
    amount_field_ignored: bool
    amount_semantics_authorized: bool
    timestamp_unit: str
    raw_close_time_rule: str
    canonical_close_time_rule: str
    market_values_returned_in_receipt: bool
    p00_evaluation_performed: bool
    network_access_performed: bool
    exchange_mutation_performed: bool
    blocked_reasons: tuple[str, ...]
    fingerprint: str


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def mapping_fingerprint() -> str:
    mapping = {
        "adapter_id": ADAPTER_ID,
        "raw_header": RAW_HEADER,
        "canonical_header": EXPECTED_HEADER,
        "open_time_ms": "raw.open_time",
        "open": "raw.open",
        "high": "raw.high",
        "low": "raw.low",
        "close": "raw.close",
        "volume": "raw.volume",
        "close_time_ms": "raw.close_time - 1",
        "amount": "IGNORED_AFTER_NUMERIC_PARSE_VALIDATION",
        "timestamp_unit": "UNIX_MILLISECONDS",
        "raw_close_delta_ms": RAW_CLOSE_DELTA_MS,
        "canonical_close_delta_ms": CANONICAL_CLOSE_DELTA_MS,
    }
    return _sha256(_canonical_json(mapping))


def _receipt_fingerprint(receipt: AdapterReceipt) -> str:
    payload = asdict(receipt)
    payload.pop("fingerprint", None)
    return _sha256(_canonical_json(payload))


def _receipt(
    *,
    status: str,
    source: Path,
    source_sha256: str | None,
    source_byte_size: int | None,
    reference_match: bool | None,
    raw_header_match: bool | None,
    row_count: int,
    canonical: Path | None,
    canonical_sha256: str | None,
    canonical_byte_size: int | None,
    reasons: list[str],
) -> AdapterReceipt:
    provisional = AdapterReceipt(
        status=status,
        adapter_id=ADAPTER_ID,
        source_file_name=source.name,
        source_sha256=source_sha256,
        source_byte_size=source_byte_size,
        reference_sample_sha256_match=reference_match,
        raw_header_match=raw_header_match,
        raw_row_count=row_count,
        canonical_file_name=canonical.name if canonical is not None else None,
        canonical_sha256=canonical_sha256,
        canonical_byte_size=canonical_byte_size,
        canonical_header=EXPECTED_HEADER,
        mapping_fingerprint=mapping_fingerprint(),
        amount_field_ignored=True,
        amount_semantics_authorized=False,
        timestamp_unit="UNIX_MILLISECONDS",
        raw_close_time_rule="close_time = open_time + 900000",
        canonical_close_time_rule="close_time_ms = open_time_ms + 899999",
        market_values_returned_in_receipt=False,
        p00_evaluation_performed=False,
        network_access_performed=False,
        exchange_mutation_performed=False,
        blocked_reasons=tuple(sorted(set(reasons))),
        fingerprint="",
    )
    return replace(provisional, fingerprint=_receipt_fingerprint(provisional))


def _is_13_digit_unsigned_integer(value: str) -> bool:
    return len(value) == 13 and value.isdigit()


def _all_finite_numeric(values: list[str]) -> bool:
    try:
        return all(isfinite(float(value)) for value in values)
    except (TypeError, ValueError, OverflowError):
        return False


def adapt_mexc_bulk_csv(source_path: str | Path, canonical_path: str | Path) -> AdapterReceipt:
    """Normalize the frozen official MEXC 15m bulk CSV layout to canonical CSV.

    The adapter is offline and deterministic. It does not infer unknown schemas,
    interpret the raw ``amount`` field, evaluate P00, or perform network/exchange
    operations. Canonical output is written atomically only after the entire source
    file passes the frozen mapping checks.
    """

    source = Path(source_path)
    canonical = Path(canonical_path)
    if not source.is_file():
        return _receipt(
            status="BLOCKED_ADAPTER",
            source=source,
            source_sha256=None,
            source_byte_size=None,
            reference_match=None,
            raw_header_match=None,
            row_count=0,
            canonical=None,
            canonical_sha256=None,
            canonical_byte_size=None,
            reasons=["SOURCE_FILE_NOT_FOUND"],
        )
    if source.suffix.lower() != ".csv":
        source_sha, source_size = file_sha256(source)
        return _receipt(
            status="BLOCKED_ADAPTER",
            source=source,
            source_sha256=source_sha,
            source_byte_size=source_size,
            reference_match=source_sha == REFERENCE_SAMPLE_SHA256,
            raw_header_match=None,
            row_count=0,
            canonical=None,
            canonical_sha256=None,
            canonical_byte_size=None,
            reasons=["UNSUPPORTED_SOURCE_SUFFIX"],
        )

    source_sha, source_size = file_sha256(source)
    reasons: list[str] = []
    output_rows: list[tuple[str, str, str, str, str, str, str]] = []
    header_match: bool | None = None
    previous_open: int | None = None

    try:
        with source.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle)
            try:
                header = tuple(next(reader))
            except StopIteration:
                header = ()
            header_match = header == RAW_HEADER
            if not header_match:
                reasons.append("RAW_HEADER_MISMATCH")
            else:
                for raw_row in reader:
                    if not raw_row:
                        reasons.append("BLANK_ROW")
                        continue
                    if len(raw_row) != len(RAW_HEADER):
                        reasons.append("RAW_FIELD_COUNT_MISMATCH")
                        continue

                    open_text = raw_row[0].strip()
                    close_text = raw_row[7].strip()
                    if not _is_13_digit_unsigned_integer(open_text) or not _is_13_digit_unsigned_integer(close_text):
                        reasons.append("TIMESTAMP_NOT_13_DIGIT_MILLISECONDS")
                        continue
                    open_time = int(open_text)
                    close_time = int(close_text)

                    if open_time % TIMEFRAME_MS != 0:
                        reasons.append("OPEN_TIME_NOT_15M_ALIGNED")
                    if close_time != open_time + RAW_CLOSE_DELTA_MS:
                        reasons.append("RAW_CLOSE_TIME_RELATION_MISMATCH")

                    if previous_open is not None:
                        delta = open_time - previous_open
                        if delta <= 0:
                            reasons.append("OPEN_TIME_NOT_STRICTLY_INCREASING")
                        elif delta % TIMEFRAME_MS != 0:
                            reasons.append("IRREGULAR_OPEN_TIME_SPACING")
                    previous_open = open_time

                    # Parse OHLC, volume and amount to prove all raw numeric fields are
                    # finite. Preserve the original strings in canonical output so the
                    # adapter does not round/reformat market values.
                    if not _all_finite_numeric([cell.strip() for cell in raw_row[1:7]]):
                        reasons.append("NONFINITE_OR_NONNUMERIC_MARKET_FIELD")
                        continue

                    output_rows.append(
                        (
                            open_text,
                            raw_row[1].strip(),
                            raw_row[2].strip(),
                            raw_row[3].strip(),
                            raw_row[4].strip(),
                            raw_row[5].strip(),
                            str(close_time - 1),
                        )
                    )
    except (OSError, UnicodeError, csv.Error):
        reasons.append("RAW_CSV_READ_FAILURE")

    if not output_rows:
        reasons.append("EMPTY_OR_UNUSABLE_SOURCE")

    if reasons:
        return _receipt(
            status="BLOCKED_ADAPTER",
            source=source,
            source_sha256=source_sha,
            source_byte_size=source_size,
            reference_match=source_sha == REFERENCE_SAMPLE_SHA256,
            raw_header_match=header_match,
            row_count=len(output_rows),
            canonical=None,
            canonical_sha256=None,
            canonical_byte_size=None,
            reasons=reasons,
        )

    canonical.parent.mkdir(parents=True, exist_ok=True)
    temp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            dir=str(canonical.parent),
            prefix=f".{canonical.name}.",
            suffix=".tmp",
            delete=False,
        ) as temp:
            temp_name = temp.name
            writer = csv.writer(temp, lineterminator="\n")
            writer.writerow(EXPECTED_HEADER)
            writer.writerows(output_rows)
        os.replace(temp_name, canonical)
        temp_name = None
    finally:
        if temp_name is not None:
            try:
                Path(temp_name).unlink(missing_ok=True)
            except OSError:
                pass

    canonical_sha, canonical_size = file_sha256(canonical)
    return _receipt(
        status="PASS_ADAPTER_ONLY",
        source=source,
        source_sha256=source_sha,
        source_byte_size=source_size,
        reference_match=source_sha == REFERENCE_SAMPLE_SHA256,
        raw_header_match=True,
        row_count=len(output_rows),
        canonical=canonical,
        canonical_sha256=canonical_sha,
        canonical_byte_size=canonical_size,
        reasons=[],
    )


def write_receipt(path: str | Path, receipt: AdapterReceipt) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(asdict(receipt), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _main() -> int:
    parser = argparse.ArgumentParser(description="Phase B frozen MEXC bulk 15m CSV adapter")
    parser.add_argument("source")
    parser.add_argument("--canonical", required=True)
    parser.add_argument("--receipt")
    args = parser.parse_args()

    result = adapt_mexc_bulk_csv(args.source, args.canonical)
    if args.receipt:
        write_receipt(args.receipt, result)
    print(json.dumps(asdict(result), indent=2, sort_keys=True))
    return 0 if result.status == "PASS_ADAPTER_ONLY" else 2


if __name__ == "__main__":
    raise SystemExit(_main())
