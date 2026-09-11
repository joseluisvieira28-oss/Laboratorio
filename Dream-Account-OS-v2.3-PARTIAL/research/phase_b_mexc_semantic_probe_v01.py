from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any

from research.phase_b_mexc_offline_ingest_v01 import file_sha256


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
MAX_ROWS_INSPECTED = 32
_NUMERIC_MARKET_COLUMNS = ("open", "high", "low", "close", "volume", "amount")


@dataclass(frozen=True)
class RawSemanticProbe:
    status: str
    file_name: str
    byte_size: int | None
    sha256: str | None
    header_match: bool
    rows_inspected: int
    field_count_consistent: bool
    numeric_market_columns_parseable: bool
    timestamp_representation: str | None
    timestamp_digit_widths: tuple[int, ...]
    timestamp_unit_candidate: str | None
    open_time_spacing_candidate_ms: int | None
    open_time_spacing_is_exact_15m: bool | None
    close_time_relation_candidate: str | None
    close_time_relation_consistent: bool | None
    amount_semantics_authorized: bool
    market_values_returned: bool
    p00_evaluation_performed: bool
    network_access_performed: bool
    blocked_reasons: tuple[str, ...]
    fingerprint: str


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _fingerprint(instance: RawSemanticProbe) -> str:
    payload = asdict(instance)
    payload.pop("fingerprint", None)
    return hashlib.sha256(_canonical_json(payload)).hexdigest()


def _timestamp_candidate(values: list[str]) -> tuple[str | None, tuple[int, ...], str | None]:
    if not values:
        return None, (), None
    stripped = [value.strip() for value in values]
    if all(re.fullmatch(r"\d+", value) for value in stripped):
        widths = tuple(sorted({len(value) for value in stripped}))
        if widths == (13,):
            return "INTEGER_DECIMAL_STRING", widths, "MILLISECONDS"
        if widths == (10,):
            return "INTEGER_DECIMAL_STRING", widths, "SECONDS"
        return "INTEGER_DECIMAL_STRING", widths, "UNKNOWN_INTEGER_WIDTH"
    return "NON_INTEGER_TEXT", tuple(sorted({len(value) for value in stripped})), None


def _to_milliseconds(value: str, unit: str | None) -> int | None:
    if unit not in {"MILLISECONDS", "SECONDS"}:
        return None
    try:
        integer = int(value)
    except ValueError:
        return None
    return integer if unit == "MILLISECONDS" else integer * 1000


def _uniform_delta(values: list[int]) -> tuple[int | None, bool | None]:
    if len(values) < 2:
        return None, None
    deltas = [right - left for left, right in zip(values, values[1:])]
    if not deltas:
        return None, None
    unique = set(deltas)
    if len(unique) != 1:
        return None, False
    return deltas[0], True


def probe_raw_semantics(path: str | Path) -> RawSemanticProbe:
    """Inspect bounded row semantics without returning historical market values.

    This probe exists only to verify raw timestamp representation, interval spacing,
    row shape, and numeric parseability after the structure-only probe has identified
    an exact official MEXC CSV header. It never returns OHLCV/amount values, never
    invokes P00, and never performs network access.
    """

    source = Path(path)
    reasons: list[str] = []
    if not source.is_file():
        provisional = RawSemanticProbe(
            status="BLOCKED_SEMANTIC_PROBE",
            file_name=source.name,
            byte_size=None,
            sha256=None,
            header_match=False,
            rows_inspected=0,
            field_count_consistent=False,
            numeric_market_columns_parseable=False,
            timestamp_representation=None,
            timestamp_digit_widths=(),
            timestamp_unit_candidate=None,
            open_time_spacing_candidate_ms=None,
            open_time_spacing_is_exact_15m=None,
            close_time_relation_candidate=None,
            close_time_relation_consistent=None,
            amount_semantics_authorized=False,
            market_values_returned=False,
            p00_evaluation_performed=False,
            network_access_performed=False,
            blocked_reasons=("SOURCE_FILE_NOT_FOUND",),
            fingerprint="",
        )
        return replace(provisional, fingerprint=_fingerprint(provisional))

    if source.suffix.lower() != ".csv":
        reasons.append("SEMANTIC_PROBE_REQUIRES_CSV")

    sha256, byte_size = file_sha256(source)
    header_match = False
    rows: list[dict[str, str]] = []
    field_count_consistent = False
    numeric_parseable = False
    timestamp_representation: str | None = None
    timestamp_digit_widths: tuple[int, ...] = ()
    timestamp_unit_candidate: str | None = None
    spacing_candidate_ms: int | None = None
    spacing_is_15m: bool | None = None
    close_relation_candidate: str | None = None
    close_relation_consistent: bool | None = None

    if not reasons:
        try:
            with source.open("r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.reader(handle)
                header = tuple(next(reader, []))
                header_match = header == RAW_HEADER
                if not header_match:
                    reasons.append("RAW_HEADER_MISMATCH")
                else:
                    for raw_row in reader:
                        if not raw_row:
                            continue
                        if len(rows) >= MAX_ROWS_INSPECTED:
                            break
                        if len(raw_row) != len(RAW_HEADER):
                            reasons.append("RAW_FIELD_COUNT_MISMATCH")
                            break
                        rows.append(dict(zip(RAW_HEADER, raw_row)))
        except (OSError, UnicodeError, csv.Error):
            reasons.append("CSV_READ_FAILURE")

    if header_match and not rows and not reasons:
        reasons.append("NO_DATA_ROWS")

    if rows and not reasons:
        field_count_consistent = True
        try:
            numeric_parseable = all(
                math.isfinite(float(row[column]))
                for row in rows
                for column in _NUMERIC_MARKET_COLUMNS
            )
        except (TypeError, ValueError):
            numeric_parseable = False
        if not numeric_parseable:
            reasons.append("MARKET_NUMERIC_PARSE_FAILURE")

        timestamp_values = [row["open_time"] for row in rows] + [row["close_time"] for row in rows]
        timestamp_representation, timestamp_digit_widths, timestamp_unit_candidate = _timestamp_candidate(timestamp_values)
        if timestamp_unit_candidate not in {"MILLISECONDS", "SECONDS"}:
            reasons.append("TIMESTAMP_UNIT_UNRESOLVED")
        else:
            open_times_ms = [_to_milliseconds(row["open_time"], timestamp_unit_candidate) for row in rows]
            close_times_ms = [_to_milliseconds(row["close_time"], timestamp_unit_candidate) for row in rows]
            if any(value is None for value in open_times_ms + close_times_ms):
                reasons.append("TIMESTAMP_PARSE_FAILURE")
            else:
                open_values = [int(value) for value in open_times_ms if value is not None]
                close_values = [int(value) for value in close_times_ms if value is not None]
                spacing_candidate_ms, spacing_consistent = _uniform_delta(open_values)
                spacing_is_15m = bool(spacing_consistent and spacing_candidate_ms == 900_000)
                if not spacing_is_15m:
                    reasons.append("OPEN_TIME_SPACING_NOT_EXACT_15M")

                offsets = [close - open_ for open_, close in zip(open_values, close_values)]
                unique_offsets = set(offsets)
                close_relation_consistent = len(unique_offsets) == 1
                if close_relation_consistent:
                    offset = offsets[0]
                    if offset == 899_999:
                        close_relation_candidate = "OPEN_PLUS_899999_MS"
                    elif offset == 900_000:
                        close_relation_candidate = "OPEN_PLUS_900000_MS"
                    else:
                        close_relation_candidate = "CONSISTENT_OTHER_OFFSET"
                else:
                    close_relation_candidate = "INCONSISTENT_OFFSET"
                if close_relation_candidate not in {"OPEN_PLUS_899999_MS", "OPEN_PLUS_900000_MS"}:
                    reasons.append("CLOSE_TIME_SEMANTICS_UNRESOLVED")

    status = "BLOCKED_SEMANTIC_PROBE" if reasons else "PASS_REDACTED_SEMANTICS"
    provisional = RawSemanticProbe(
        status=status,
        file_name=source.name,
        byte_size=byte_size,
        sha256=sha256,
        header_match=header_match,
        rows_inspected=len(rows),
        field_count_consistent=field_count_consistent,
        numeric_market_columns_parseable=numeric_parseable,
        timestamp_representation=timestamp_representation,
        timestamp_digit_widths=timestamp_digit_widths,
        timestamp_unit_candidate=timestamp_unit_candidate,
        open_time_spacing_candidate_ms=spacing_candidate_ms,
        open_time_spacing_is_exact_15m=spacing_is_15m,
        close_time_relation_candidate=close_relation_candidate,
        close_time_relation_consistent=close_relation_consistent,
        amount_semantics_authorized=False,
        market_values_returned=False,
        p00_evaluation_performed=False,
        network_access_performed=False,
        blocked_reasons=tuple(sorted(set(reasons))),
        fingerprint="",
    )
    return replace(provisional, fingerprint=_fingerprint(provisional))


def _main() -> int:
    parser = argparse.ArgumentParser(description="Phase B redacted MEXC CSV semantic probe")
    parser.add_argument("source")
    args = parser.parse_args()
    result = probe_raw_semantics(args.source)
    print(json.dumps(asdict(result), indent=2, sort_keys=True))
    return 0 if result.status == "PASS_REDACTED_SEMANTICS" else 2


if __name__ == "__main__":
    raise SystemExit(_main())
