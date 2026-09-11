from __future__ import annotations

"""H01-only offline MEXC adapter/provenance/integrity auditor.

The closed P00 auditor and its 2024 authority contract remain untouched. This module
reuses the already-frozen temporal-neutral raw->canonical adapter and the exact neutral
integrity semantics from the P00 auditor, but it is gated by the separate H01 data-
access authorization before any market-data bytes are opened.
"""

import calendar
import csv
import hashlib
import json
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timedelta, timezone
from math import isfinite
from pathlib import Path
from typing import Any

from dream_account.models import Candle
from research.phase_b_h01_mexc_discovery_access_v01 import (
    DISCOVERY_END_MONTH,
    DISCOVERY_START_MONTH,
    EXPECTED_MONTHS,
    FROZEN_UNIVERSE,
    HYPOTHESIS_ID,
    validate_h01_discovery_access_request,
)
from research.phase_b_mexc_bulk_csv_adapter_v01 import (
    ADAPTER_ID,
    mapping_fingerprint,
)
from research.phase_b_mexc_offline_ingest_v01 import (
    EXPECTED_HEADER,
    TIMEFRAME_MS,
    _classify_spacing,
    _iso_z_from_ms,
    file_sha256,
)


SOURCE_PARTITION_OFFSET_HOURS = 8
SOURCE_PARTITION_TIMEZONE = "UTC+08:00"
PASS_STATUSES = {"PASS_H01_MONTH", "PASS_H01_MONTH_WITH_GAPS"}


@dataclass(frozen=True)
class H01MonthAuditManifest:
    status: str
    reasons: tuple[str, ...]
    hypothesis_id: str
    symbol: str
    month: str
    source_partition_timezone: str
    provider_start_utc_inclusive: str | None
    provider_end_utc_exclusive: str | None
    expected_source_file_name: str | None
    expected_canonical_file_name: str | None
    authorization_verified: bool
    adapter_id: str | None
    adapter_receipt_fingerprint: str | None
    mapping_fingerprint: str | None
    raw_source_sha256: str | None
    canonical_sha256: str | None
    row_count: int
    expected_row_count: int
    first_open_time_utc: str | None
    last_open_time_utc: str | None
    first_open_time_match: bool
    last_open_time_match: bool
    malformed_row_count: int
    non_finite_numeric_count: int
    duplicate_open_time_count: int
    out_of_order_count: int
    ohlc_violation_count: int
    negative_volume_count: int
    open_time_alignment_violation_count: int
    close_time_violation_count: int
    provider_boundary_violation_count: int
    irregular_interval_count: int
    detected_gap_count: int
    missing_candle_count: int
    contiguous_segment_count: int
    returned_candle_count: int
    source_market_bytes_read: bool
    validation_2025_market_bytes_read: bool
    holdout_2026_market_bytes_read: bool
    network_access_performed: bool
    exchange_mutation_performed: bool
    submitted_to_exchange: bool
    fingerprint: str


@dataclass(frozen=True)
class H01MonthAuditPackage:
    manifest: H01MonthAuditManifest
    candles: tuple[Candle, ...]


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _hash_payload(payload: dict[str, Any]) -> str:
    clone = dict(payload)
    clone.pop("fingerprint", None)
    return hashlib.sha256(_canonical_json(clone)).hexdigest()


def _receipt_fingerprint(receipt: dict[str, Any]) -> str:
    return _hash_payload(receipt)


def _symbol_prefix(symbol: str) -> str:
    if symbol not in FROZEN_UNIVERSE:
        raise ValueError("symbol outside frozen H01 universe")
    return f"{symbol[:-4]}_USDT"


def _month_start(month: str) -> datetime:
    return datetime.strptime(month, "%Y-%m").replace(tzinfo=timezone.utc)


def _next_month_start(month: str) -> datetime:
    current = _month_start(month)
    year = current.year + (1 if current.month == 12 else 0)
    next_month = 1 if current.month == 12 else current.month + 1
    return current.replace(year=year, month=next_month, day=1)


def source_partition_bounds(month: str) -> tuple[datetime, datetime]:
    if month not in EXPECTED_MONTHS:
        raise ValueError("month outside frozen H01 Discovery provider partitions")
    offset = timedelta(hours=SOURCE_PARTITION_OFFSET_HOURS)
    return _month_start(month) - offset, _next_month_start(month) - offset


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _empty_manifest(
    *,
    status: str,
    reasons: list[str],
    symbol: str,
    month: str,
    authorization_verified: bool,
    source_market_bytes_read: bool = False,
    **overrides: Any,
) -> H01MonthAuditManifest:
    try:
        start, end = source_partition_bounds(month)
        expected_raw = f"{_symbol_prefix(symbol)}-Min15-{month}-01.csv"
        expected_canonical = f"{Path(expected_raw).stem}.canonical.csv"
        expected_rows = calendar.monthrange(start.year if start.month != 12 else int(month[:4]), int(month[5:7]))[1] * 96
        # expected rows are based on the vendor label's calendar month, not the UTC
        # date of partition_start, which may be the previous calendar day/month.
        expected_rows = calendar.monthrange(int(month[:4]), int(month[5:7]))[1] * 96
        start_text, end_text = _iso(start), _iso(end)
    except (TypeError, ValueError):
        expected_raw = None
        expected_canonical = None
        expected_rows = 0
        start_text = None
        end_text = None

    fields = dict(
        status=status,
        reasons=tuple(sorted(set(reasons))),
        hypothesis_id=HYPOTHESIS_ID,
        symbol=symbol,
        month=month,
        source_partition_timezone=SOURCE_PARTITION_TIMEZONE,
        provider_start_utc_inclusive=start_text,
        provider_end_utc_exclusive=end_text,
        expected_source_file_name=expected_raw,
        expected_canonical_file_name=expected_canonical,
        authorization_verified=authorization_verified,
        adapter_id=None,
        adapter_receipt_fingerprint=None,
        mapping_fingerprint=None,
        raw_source_sha256=None,
        canonical_sha256=None,
        row_count=0,
        expected_row_count=expected_rows,
        first_open_time_utc=None,
        last_open_time_utc=None,
        first_open_time_match=False,
        last_open_time_match=False,
        malformed_row_count=0,
        non_finite_numeric_count=0,
        duplicate_open_time_count=0,
        out_of_order_count=0,
        ohlc_violation_count=0,
        negative_volume_count=0,
        open_time_alignment_violation_count=0,
        close_time_violation_count=0,
        provider_boundary_violation_count=0,
        irregular_interval_count=0,
        detected_gap_count=0,
        missing_candle_count=0,
        contiguous_segment_count=0,
        returned_candle_count=0,
        source_market_bytes_read=source_market_bytes_read,
        validation_2025_market_bytes_read=False,
        holdout_2026_market_bytes_read=False,
        network_access_performed=False,
        exchange_mutation_performed=False,
        submitted_to_exchange=False,
        fingerprint="",
    )
    fields.update(overrides)
    provisional = H01MonthAuditManifest(**fields)
    return replace(provisional, fingerprint=_hash_payload(asdict(provisional)))


def _load_adapter_receipt(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        receipt = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None, ["INVALID_ADAPTER_RECEIPT"]
    if not isinstance(receipt, dict):
        return None, ["INVALID_ADAPTER_RECEIPT"]
    reasons: list[str] = []
    required = (
        "status", "adapter_id", "source_file_name", "source_sha256", "source_byte_size",
        "canonical_file_name", "canonical_sha256", "canonical_byte_size", "mapping_fingerprint",
        "amount_field_ignored", "amount_semantics_authorized", "market_values_returned_in_receipt",
        "p00_evaluation_performed", "network_access_performed", "exchange_mutation_performed",
        "blocked_reasons", "fingerprint",
    )
    for key in required:
        if key not in receipt:
            reasons.append(f"MISSING_ADAPTER_RECEIPT_FIELD:{key}")
    if reasons:
        return receipt, reasons
    if receipt["status"] != "PASS_ADAPTER_ONLY":
        reasons.append("ADAPTER_STATUS_NOT_PASS")
    if receipt["adapter_id"] != ADAPTER_ID:
        reasons.append("ADAPTER_ID_MISMATCH")
    if receipt["mapping_fingerprint"] != mapping_fingerprint():
        reasons.append("ADAPTER_MAPPING_FINGERPRINT_MISMATCH")
    if receipt["fingerprint"] != _receipt_fingerprint(receipt):
        reasons.append("ADAPTER_RECEIPT_FINGERPRINT_MISMATCH")
    if receipt["amount_field_ignored"] is not True or receipt["amount_semantics_authorized"] is not False:
        reasons.append("ADAPTER_AMOUNT_SEMANTICS_VIOLATION")
    if receipt["market_values_returned_in_receipt"] is not False:
        reasons.append("ADAPTER_RECEIPT_EXPOSES_MARKET_VALUES")
    if receipt["p00_evaluation_performed"] is not False:
        reasons.append("ADAPTER_RECEIPT_CLAIMS_P00_EVALUATION")
    if receipt["network_access_performed"] is not False:
        reasons.append("ADAPTER_RECEIPT_CLAIMS_NETWORK_ACCESS")
    if receipt["exchange_mutation_performed"] is not False:
        reasons.append("ADAPTER_RECEIPT_CLAIMS_EXCHANGE_MUTATION")
    if receipt["blocked_reasons"] not in ([], ()):
        reasons.append("ADAPTER_RECEIPT_HAS_BLOCK_REASONS")
    return receipt, reasons


def audit_h01_month(
    raw_source_path: str | Path,
    canonical_path: str | Path,
    adapter_receipt_path: str | Path,
    *,
    symbol: str,
    month: str,
    authorization_path: str | Path,
) -> H01MonthAuditPackage:
    """Audit one authorized H01 Discovery provider month, fail-closed.

    Authorization and month/symbol scope are checked before any raw/canonical market
    bytes are opened. Validation months and 2026 are outside EXPECTED_MONTHS and block.
    """

    if month not in EXPECTED_MONTHS or symbol not in FROZEN_UNIVERSE:
        return H01MonthAuditPackage(
            _empty_manifest(
                status="BLOCKED_H01_MONTH_METADATA",
                reasons=["MONTH_OR_SYMBOL_OUTSIDE_FROZEN_H01_DISCOVERY"],
                symbol=symbol,
                month=month,
                authorization_verified=False,
            ),
            (),
        )

    access = validate_h01_discovery_access_request(
        symbol=symbol,
        start_month=DISCOVERY_START_MONTH,
        end_month=DISCOVERY_END_MONTH,
        authorization_path=authorization_path,
    )
    if access.status != "PASS_H01_DISCOVERY_ACCESS_PREFLIGHT":
        return H01MonthAuditPackage(
            _empty_manifest(
                status="BLOCKED_H01_MONTH_AUTHORIZATION",
                reasons=list(access.reasons) or ["H01_DISCOVERY_ACCESS_PREFLIGHT_NOT_PASS"],
                symbol=symbol,
                month=month,
                authorization_verified=False,
            ),
            (),
        )

    expected_raw = f"{_symbol_prefix(symbol)}-Min15-{month}-01.csv"
    expected_canonical = f"{Path(expected_raw).stem}.canonical.csv"
    raw = Path(raw_source_path)
    canonical = Path(canonical_path)
    receipt_path = Path(adapter_receipt_path)

    receipt, receipt_reasons = _load_adapter_receipt(receipt_path)
    if receipt_reasons or receipt is None:
        return H01MonthAuditPackage(
            _empty_manifest(
                status="BLOCKED_H01_ADAPTER_RECEIPT",
                reasons=receipt_reasons or ["INVALID_ADAPTER_RECEIPT"],
                symbol=symbol,
                month=month,
                authorization_verified=True,
            ),
            (),
        )

    name_reasons: list[str] = []
    if raw.name != expected_raw or receipt.get("source_file_name") != expected_raw:
        name_reasons.append("RAW_SOURCE_FILENAME_MISMATCH")
    if canonical.name != expected_canonical or receipt.get("canonical_file_name") != expected_canonical:
        name_reasons.append("CANONICAL_FILENAME_MISMATCH")
    if name_reasons:
        return H01MonthAuditPackage(
            _empty_manifest(
                status="BLOCKED_H01_PROVENANCE",
                reasons=name_reasons,
                symbol=symbol,
                month=month,
                authorization_verified=True,
                adapter_id=receipt.get("adapter_id"),
                adapter_receipt_fingerprint=receipt.get("fingerprint"),
                mapping_fingerprint=receipt.get("mapping_fingerprint"),
            ),
            (),
        )

    if not raw.is_file() or not canonical.is_file():
        return H01MonthAuditPackage(
            _empty_manifest(
                status="BLOCKED_H01_SOURCE",
                reasons=["RAW_OR_CANONICAL_SOURCE_NOT_FOUND"],
                symbol=symbol,
                month=month,
                authorization_verified=True,
                adapter_id=receipt.get("adapter_id"),
                adapter_receipt_fingerprint=receipt.get("fingerprint"),
                mapping_fingerprint=receipt.get("mapping_fingerprint"),
            ),
            (),
        )

    raw_sha, raw_size = file_sha256(raw)
    canonical_sha, canonical_size = file_sha256(canonical)
    provenance_reasons: list[str] = []
    if raw_sha != receipt.get("source_sha256") or raw_size != receipt.get("source_byte_size"):
        provenance_reasons.append("RAW_SOURCE_PROVENANCE_MISMATCH")
    if canonical_sha != receipt.get("canonical_sha256") or canonical_size != receipt.get("canonical_byte_size"):
        provenance_reasons.append("CANONICAL_PROVENANCE_MISMATCH")
    if provenance_reasons:
        return H01MonthAuditPackage(
            _empty_manifest(
                status="BLOCKED_H01_PROVENANCE",
                reasons=provenance_reasons,
                symbol=symbol,
                month=month,
                authorization_verified=True,
                source_market_bytes_read=True,
                adapter_id=receipt.get("adapter_id"),
                adapter_receipt_fingerprint=receipt.get("fingerprint"),
                mapping_fingerprint=receipt.get("mapping_fingerprint"),
                raw_source_sha256=raw_sha,
                canonical_sha256=canonical_sha,
            ),
            (),
        )

    start, end = source_partition_bounds(month)
    start_ms = int(start.timestamp() * 1000)
    end_ms = int(end.timestamp() * 1000)
    expected_last_ms = end_ms - TIMEFRAME_MS
    expected_rows = calendar.monthrange(int(month[:4]), int(month[5:7]))[1] * 96

    rows: list[tuple[int, float, float, float, float, float, int]] = []
    malformed = non_finite = duplicate_count = out_of_order_count = 0
    ohlc_violations = negative_volume = alignment_violations = close_time_violations = 0
    boundary_violations = 0
    seen: set[int] = set()
    previous_open: int | None = None
    header_reason: str | None = None

    try:
        with canonical.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle)
            try:
                header = tuple(next(reader))
            except StopIteration:
                header = ()
            if header != EXPECTED_HEADER:
                header_reason = "UNKNOWN_OR_NONCANONICAL_CSV_SCHEMA"
            else:
                for raw_row in reader:
                    if not raw_row or all(not cell.strip() for cell in raw_row):
                        continue
                    if len(raw_row) != len(EXPECTED_HEADER):
                        malformed += 1
                        continue
                    try:
                        open_time = int(raw_row[0])
                        open_price = float(raw_row[1])
                        high = float(raw_row[2])
                        low = float(raw_row[3])
                        close = float(raw_row[4])
                        volume = float(raw_row[5])
                        close_time = int(raw_row[6])
                    except (TypeError, ValueError, OverflowError):
                        malformed += 1
                        continue
                    numeric = (open_price, high, low, close, volume)
                    if not all(isfinite(value) for value in numeric):
                        non_finite += 1
                        continue
                    if open_time in seen:
                        duplicate_count += 1
                    seen.add(open_time)
                    if previous_open is not None and open_time <= previous_open:
                        out_of_order_count += 1
                    previous_open = open_time
                    if open_time % TIMEFRAME_MS != 0:
                        alignment_violations += 1
                    if close_time != open_time + TIMEFRAME_MS - 1:
                        close_time_violations += 1
                    if volume < 0:
                        negative_volume += 1
                    if (
                        open_price <= 0 or high <= 0 or low <= 0 or close <= 0
                        or high < max(open_price, close) or low > min(open_price, close) or high < low
                    ):
                        ohlc_violations += 1
                    if not start_ms <= open_time < end_ms:
                        boundary_violations += 1
                    rows.append((open_time, open_price, high, low, close, volume, close_time))
    except (OSError, UnicodeError, csv.Error):
        header_reason = "CSV_READ_FAILURE"

    irregular, gap_count, missing_count, segments, _ = _classify_spacing(rows)
    first = rows[0][0] if rows else None
    last = rows[-1][0] if rows else None
    first_match = first == start_ms
    last_match = last == expected_last_ms

    reasons: list[str] = []
    if header_reason:
        reasons.append(header_reason)
    if not rows:
        reasons.append("EMPTY_DATASET")
    if malformed:
        reasons.append("MALFORMED_ROWS")
    if non_finite:
        reasons.append("NON_FINITE_NUMERIC_VALUES")
    if duplicate_count:
        reasons.append("DUPLICATE_OPEN_TIMES")
    if out_of_order_count:
        reasons.append("OUT_OF_ORDER_ROWS")
    if ohlc_violations:
        reasons.append("OHLC_INTEGRITY_VIOLATIONS")
    if negative_volume:
        reasons.append("NEGATIVE_VOLUME")
    if alignment_violations:
        reasons.append("OPEN_TIME_ALIGNMENT_VIOLATIONS")
    if close_time_violations:
        reasons.append("CLOSE_TIME_VIOLATIONS")
    if boundary_violations:
        reasons.append("PROVIDER_PARTITION_BOUNDARY_VIOLATIONS")
    if irregular:
        reasons.append("IRREGULAR_INTERVAL_SPACING")
    if not first_match:
        reasons.append("MONTH_START_BOUNDARY_MISMATCH")
    if not last_match:
        reasons.append("MONTH_END_BOUNDARY_MISMATCH")

    if gap_count:
        if missing_count <= 0 or expected_rows - len(rows) != missing_count:
            reasons.append("VALID_GAP_ACCOUNTING_MISMATCH")
    elif len(rows) != expected_rows:
        reasons.append("MONTH_ROW_COUNT_MISMATCH")

    blocked = bool(reasons)
    status = "BLOCKED_H01_MONTH_INTEGRITY" if blocked else (
        "PASS_H01_MONTH_WITH_GAPS" if gap_count else "PASS_H01_MONTH"
    )
    candles: tuple[Candle, ...] = ()
    if not blocked:
        candles = tuple(
            Candle(open_time, open_price, high, low, close, volume, close_time, True)
            for open_time, open_price, high, low, close, volume, close_time in rows
        )

    manifest = _empty_manifest(
        status=status,
        reasons=reasons,
        symbol=symbol,
        month=month,
        authorization_verified=True,
        source_market_bytes_read=True,
        adapter_id=receipt.get("adapter_id"),
        adapter_receipt_fingerprint=receipt.get("fingerprint"),
        mapping_fingerprint=receipt.get("mapping_fingerprint"),
        raw_source_sha256=raw_sha,
        canonical_sha256=canonical_sha,
        row_count=len(rows),
        expected_row_count=expected_rows,
        first_open_time_utc=_iso_z_from_ms(first) if first is not None else None,
        last_open_time_utc=_iso_z_from_ms(last) if last is not None else None,
        first_open_time_match=first_match,
        last_open_time_match=last_match,
        malformed_row_count=malformed,
        non_finite_numeric_count=non_finite,
        duplicate_open_time_count=duplicate_count,
        out_of_order_count=out_of_order_count,
        ohlc_violation_count=ohlc_violations,
        negative_volume_count=negative_volume,
        open_time_alignment_violation_count=alignment_violations,
        close_time_violation_count=close_time_violations,
        provider_boundary_violation_count=boundary_violations,
        irregular_interval_count=irregular,
        detected_gap_count=gap_count,
        missing_candle_count=missing_count,
        contiguous_segment_count=segments,
        returned_candle_count=len(candles),
    )
    return H01MonthAuditPackage(manifest, candles)


def write_manifest(path: str | Path, manifest: H01MonthAuditManifest) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(asdict(manifest), indent=2, sort_keys=True) + "\n", encoding="utf-8")
