from __future__ import annotations

import argparse
import csv
import hashlib
import json
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from math import isfinite
from pathlib import Path, PurePosixPath
from typing import Any, Iterable
from zipfile import BadZipFile, ZipFile

from dream_account.models import Candle


CONTRACT_PATH = Path(__file__).with_name("PHASE_B_OFFLINE_DATA_INGEST_FREEZE_V0.1.json")
SIDECAR_SCHEMA = "PHASE_B_DATASET_SIDECAR_V0.1"
CANONICAL_SCHEMA = "CANONICAL_KLINE_CSV_V0.1"
IDENTITY_ADAPTER = "IDENTITY_CANONICAL_KLINE_CSV_V0.1"
EXPECTED_HEADER = (
    "open_time_ms",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "close_time_ms",
)
TIMEFRAME_MS = 15 * 60 * 1000


@dataclass(frozen=True)
class SourceProbe:
    status: str
    file_name: str
    byte_size: int | None
    sha256: str | None
    suffix: str
    zip_entry_count: int | None
    zip_entries: tuple[str, ...]
    unsafe_zip_entries: tuple[str, ...]
    reason: str | None
    fingerprint: str


@dataclass(frozen=True)
class DataAuditManifest:
    contract_version: str
    status: str
    reasons: tuple[str, ...]
    stage: str | None
    symbol: str | None
    timeframe: str | None
    metadata_fingerprint: str | None
    raw_source_filename: str | None
    raw_source_sha256_declared: str | None
    raw_source_sha256_actual: str | None
    canonical_file_name: str | None
    canonical_file_sha256: str | None
    canonical_byte_size: int | None
    row_count: int
    first_open_time_utc: str | None
    last_open_time_utc: str | None
    duplicate_open_time_count: int
    out_of_order_count: int
    malformed_row_count: int
    non_finite_numeric_count: int
    ohlc_violation_count: int
    negative_volume_count: int
    open_time_alignment_violation_count: int
    close_time_violation_count: int
    declared_range_violation_count: int
    stage_boundary_violation_count: int
    detected_gap_count: int
    missing_candle_count: int
    contiguous_segment_count: int
    gap_examples_utc: tuple[tuple[str, str, int], ...]
    returned_candle_count: int
    p00_evaluation_performed: bool
    network_access_performed: bool
    exchange_mutation_performed: bool
    audit_fingerprint: str


@dataclass(frozen=True)
class OfflineAuditPackage:
    manifest: DataAuditManifest
    candles: tuple[Candle, ...]


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha256(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


def _fingerprinted_dataclass(instance: Any, field_name: str = "fingerprint") -> str:
    payload = asdict(instance)
    payload.pop(field_name, None)
    return _sha256_bytes(_canonical_json(payload))


def _is_unsafe_zip_name(name: str) -> bool:
    normalized = name.replace("\\", "/")
    path = PurePosixPath(normalized)
    return path.is_absolute() or ".." in path.parts or normalized.startswith("/")


def probe_raw_source(path: str | Path) -> SourceProbe:
    source = Path(path)
    suffix = source.suffix.lower()
    if not source.is_file():
        provisional = SourceProbe(
            status="BLOCKED_SOURCE_NOT_FOUND",
            file_name=source.name,
            byte_size=None,
            sha256=None,
            suffix=suffix,
            zip_entry_count=None,
            zip_entries=(),
            unsafe_zip_entries=(),
            reason="SOURCE_FILE_NOT_FOUND",
            fingerprint="",
        )
        return replace(provisional, fingerprint=_fingerprinted_dataclass(provisional))

    sha256, byte_size = file_sha256(source)
    entries: tuple[str, ...] = ()
    unsafe: tuple[str, ...] = ()
    entry_count: int | None = None
    status = "PASS_PROBE_ONLY"
    reason = None

    if suffix == ".zip":
        try:
            with ZipFile(source, "r") as archive:
                names = tuple(info.filename for info in archive.infolist())
        except BadZipFile:
            status = "BLOCKED_BAD_ZIP"
            reason = "BAD_ZIP_ARCHIVE"
        else:
            entry_count = len(names)
            entries = tuple(sorted(names))
            unsafe = tuple(sorted(name for name in names if _is_unsafe_zip_name(name)))
            if unsafe:
                status = "BLOCKED_UNSAFE_ARCHIVE_PATH"
                reason = "ZIP_PATH_TRAVERSAL_ENTRY"

    provisional = SourceProbe(
        status=status,
        file_name=source.name,
        byte_size=byte_size,
        sha256=sha256,
        suffix=suffix,
        zip_entry_count=entry_count,
        zip_entries=entries,
        unsafe_zip_entries=unsafe,
        reason=reason,
        fingerprint="",
    )
    return replace(provisional, fingerprint=_fingerprinted_dataclass(provisional))


def _load_contract() -> dict[str, Any]:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _parse_utc(value: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise ValueError("UTC timestamp string required")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ValueError("timestamp must be UTC")
    return parsed.astimezone(timezone.utc)


def _utc_ms(value: str) -> int:
    return int(_parse_utc(value).timestamp() * 1000)


def _iso_z_from_ms(value: int) -> str:
    dt = datetime.fromtimestamp(value / 1000.0, tz=timezone.utc)
    rendered = dt.isoformat(timespec="milliseconds")
    return rendered.replace("+00:00", "Z")


def _metadata_fingerprint(metadata: dict[str, Any]) -> str:
    return _sha256_bytes(_canonical_json(metadata))


def _valid_sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _preflight_metadata(metadata: dict[str, Any], contract: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    reasons: list[str] = []
    required = contract["sidecar_metadata_required"]["required_fields"]
    for field in required:
        if field not in metadata:
            reasons.append(f"MISSING_METADATA_FIELD:{field}")

    if reasons:
        return reasons, {}

    exact = contract["sidecar_metadata_required"]
    expected_pairs = {
        "schema_version": SIDECAR_SCHEMA,
        "source_exchange": exact["source_exchange"],
        "market_type": exact["market_type"],
        "source_authority": exact["source_authority"],
        "canonical_schema": exact["canonical_schema"],
    }
    for field, expected in expected_pairs.items():
        if metadata.get(field) != expected:
            reasons.append(f"INVALID_METADATA_VALUE:{field}")

    if metadata.get("adapter_id") != IDENTITY_ADAPTER:
        reasons.append("UNKNOWN_OR_UNFROZEN_ADAPTER")
    if metadata.get("stage") != contract["stage_lock"]["currently_unlocked_stage"]:
        reasons.append("STAGE_NOT_UNLOCKED")
    if metadata.get("timeframe") != contract["discovery_universe"]["timeframe"]:
        reasons.append("TIMEFRAME_OUTSIDE_FROZEN_UNIVERSE")
    if metadata.get("symbol") not in contract["discovery_universe"]["symbols"]:
        reasons.append("SYMBOL_OUTSIDE_FROZEN_UNIVERSE")
    if not _valid_sha256(metadata.get("raw_source_sha256")):
        reasons.append("INVALID_RAW_SOURCE_SHA256")

    try:
        declared_start = _utc_ms(metadata["declared_start_utc"])
        declared_end = _utc_ms(metadata["declared_end_utc"])
        discovery_start = _utc_ms(contract["stage_lock"]["discovery_start_utc"])
        discovery_end = _utc_ms(contract["stage_lock"]["discovery_end_utc"])
    except (TypeError, ValueError, OverflowError):
        reasons.append("INVALID_DECLARED_UTC_RANGE")
        return reasons, {}

    if declared_start > declared_end:
        reasons.append("DECLARED_RANGE_REVERSED")
    if declared_start < discovery_start or declared_end > discovery_end:
        reasons.append("DECLARED_RANGE_OUTSIDE_DISCOVERY")

    return reasons, {
        "declared_start_ms": declared_start,
        "declared_end_ms": declared_end,
        "discovery_start_ms": discovery_start,
        "discovery_end_ms": discovery_end,
    }


def _empty_manifest(
    *,
    contract: dict[str, Any],
    status: str,
    reasons: Iterable[str],
    metadata: dict[str, Any] | None = None,
    metadata_fingerprint: str | None = None,
) -> DataAuditManifest:
    metadata = metadata or {}
    provisional = DataAuditManifest(
        contract_version=str(contract.get("version", "0.1")),
        status=status,
        reasons=tuple(sorted(set(reasons))),
        stage=metadata.get("stage"),
        symbol=metadata.get("symbol"),
        timeframe=metadata.get("timeframe"),
        metadata_fingerprint=metadata_fingerprint,
        raw_source_filename=metadata.get("raw_source_filename"),
        raw_source_sha256_declared=metadata.get("raw_source_sha256"),
        raw_source_sha256_actual=None,
        canonical_file_name=None,
        canonical_file_sha256=None,
        canonical_byte_size=None,
        row_count=0,
        first_open_time_utc=None,
        last_open_time_utc=None,
        duplicate_open_time_count=0,
        out_of_order_count=0,
        malformed_row_count=0,
        non_finite_numeric_count=0,
        ohlc_violation_count=0,
        negative_volume_count=0,
        open_time_alignment_violation_count=0,
        close_time_violation_count=0,
        declared_range_violation_count=0,
        stage_boundary_violation_count=0,
        detected_gap_count=0,
        missing_candle_count=0,
        contiguous_segment_count=0,
        gap_examples_utc=(),
        returned_candle_count=0,
        p00_evaluation_performed=False,
        network_access_performed=False,
        exchange_mutation_performed=False,
        audit_fingerprint="",
    )
    return replace(provisional, audit_fingerprint=_fingerprinted_dataclass(provisional, "audit_fingerprint"))


def _load_sidecar(path: str | Path) -> tuple[dict[str, Any], str]:
    metadata_path = Path(path)
    data = json.loads(metadata_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("sidecar metadata must be a JSON object")
    return data, _metadata_fingerprint(data)


def audit_canonical_dataset(
    metadata_path: str | Path,
    canonical_path: str | Path,
    *,
    raw_source_path: str | Path | None = None,
) -> OfflineAuditPackage:
    """Audit one discovery dataset without networking and return candles only on PASS.

    Validation/holdout metadata is rejected before the market-data file is opened.
    V0.1 intentionally supports only the frozen identity canonical CSV adapter.
    Unknown raw MEXC layouts must first be schema-probed and receive a separate
    validated adapter amendment.
    """

    contract = _load_contract()
    try:
        metadata, metadata_fp = _load_sidecar(metadata_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        manifest = _empty_manifest(
            contract=contract,
            status="BLOCKED_METADATA",
            reasons=(f"INVALID_SIDECAR:{type(exc).__name__}",),
        )
        return OfflineAuditPackage(manifest=manifest, candles=())

    preflight_reasons, bounds = _preflight_metadata(metadata, contract)
    if preflight_reasons:
        manifest = _empty_manifest(
            contract=contract,
            status="BLOCKED_METADATA",
            reasons=preflight_reasons,
            metadata=metadata,
            metadata_fingerprint=metadata_fp,
        )
        return OfflineAuditPackage(manifest=manifest, candles=())

    canonical = Path(canonical_path)
    raw_source = Path(raw_source_path) if raw_source_path is not None else canonical
    if not canonical.is_file() or not raw_source.is_file():
        manifest = _empty_manifest(
            contract=contract,
            status="BLOCKED_SOURCE",
            reasons=("CANONICAL_OR_RAW_SOURCE_NOT_FOUND",),
            metadata=metadata,
            metadata_fingerprint=metadata_fp,
        )
        return OfflineAuditPackage(manifest=manifest, candles=())

    raw_sha, _ = file_sha256(raw_source)
    canonical_sha, canonical_size = file_sha256(canonical)
    provenance_reasons: list[str] = []
    if raw_sha != metadata["raw_source_sha256"]:
        provenance_reasons.append("RAW_SOURCE_SHA256_MISMATCH")
    if canonical.resolve() != raw_source.resolve() or canonical_sha != raw_sha:
        provenance_reasons.append("IDENTITY_ADAPTER_REQUIRES_IDENTICAL_RAW_AND_CANONICAL_FILE")
    if metadata["raw_source_filename"] != raw_source.name:
        provenance_reasons.append("RAW_SOURCE_FILENAME_MISMATCH")

    if provenance_reasons:
        base = _empty_manifest(
            contract=contract,
            status="BLOCKED_PROVENANCE",
            reasons=provenance_reasons,
            metadata=metadata,
            metadata_fingerprint=metadata_fp,
        )
        provisional = replace(
            base,
            raw_source_sha256_actual=raw_sha,
            canonical_file_name=canonical.name,
            canonical_file_sha256=canonical_sha,
            canonical_byte_size=canonical_size,
            audit_fingerprint="",
        )
        manifest = replace(provisional, audit_fingerprint=_fingerprinted_dataclass(provisional, "audit_fingerprint"))
        return OfflineAuditPackage(manifest=manifest, candles=())

    rows: list[tuple[int, float, float, float, float, float, int]] = []
    malformed = 0
    non_finite = 0
    ohlc_violations = 0
    negative_volume = 0
    alignment_violations = 0
    close_time_violations = 0
    declared_range_violations = 0
    stage_boundary_violations = 0
    duplicate_count = 0
    out_of_order_count = 0
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
                        open_price <= 0
                        or high <= 0
                        or low <= 0
                        or close <= 0
                        or high < max(open_price, close)
                        or low > min(open_price, close)
                        or high < low
                    ):
                        ohlc_violations += 1
                    if not bounds["declared_start_ms"] <= open_time <= bounds["declared_end_ms"]:
                        declared_range_violations += 1
                    if not bounds["discovery_start_ms"] <= open_time <= bounds["discovery_end_ms"]:
                        stage_boundary_violations += 1

                    rows.append((open_time, open_price, high, low, close, volume, close_time))
    except (OSError, UnicodeError, csv.Error):
        header_reason = "CSV_READ_FAILURE"

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
    if declared_range_violations:
        reasons.append("DECLARED_RANGE_VIOLATIONS")
    if stage_boundary_violations:
        reasons.append("FORBIDDEN_STAGE_TIMESTAMPS")

    gap_count = 0
    missing_candle_count = 0
    contiguous_segments = 0
    gap_examples: list[tuple[str, str, int]] = []
    if rows:
        contiguous_segments = 1
        ordered_times = [row[0] for row in rows]
        for left, right in zip(ordered_times, ordered_times[1:]):
            delta = right - left
            if delta > TIMEFRAME_MS:
                gap_count += 1
                contiguous_segments += 1
                missing = delta // TIMEFRAME_MS - 1 if delta % TIMEFRAME_MS == 0 else 0
                missing_candle_count += max(missing, 0)
                if len(gap_examples) < 20:
                    gap_examples.append((_iso_z_from_ms(left), _iso_z_from_ms(right), max(missing, 0)))

    blocked = bool(reasons)
    status = "BLOCKED_DATA_INTEGRITY" if blocked else ("PASS_WITH_GAPS" if gap_count else "PASS")
    candles: tuple[Candle, ...] = ()
    if not blocked:
        candles = tuple(
            Candle(open_time, open_price, high, low, close, volume, close_time, True)
            for open_time, open_price, high, low, close, volume, close_time in rows
        )

    first_time = _iso_z_from_ms(rows[0][0]) if rows else None
    last_time = _iso_z_from_ms(rows[-1][0]) if rows else None
    provisional = DataAuditManifest(
        contract_version=str(contract["version"]),
        status=status,
        reasons=tuple(sorted(set(reasons))),
        stage=metadata["stage"],
        symbol=metadata["symbol"],
        timeframe=metadata["timeframe"],
        metadata_fingerprint=metadata_fp,
        raw_source_filename=metadata["raw_source_filename"],
        raw_source_sha256_declared=metadata["raw_source_sha256"],
        raw_source_sha256_actual=raw_sha,
        canonical_file_name=canonical.name,
        canonical_file_sha256=canonical_sha,
        canonical_byte_size=canonical_size,
        row_count=len(rows),
        first_open_time_utc=first_time,
        last_open_time_utc=last_time,
        duplicate_open_time_count=duplicate_count,
        out_of_order_count=out_of_order_count,
        malformed_row_count=malformed,
        non_finite_numeric_count=non_finite,
        ohlc_violation_count=ohlc_violations,
        negative_volume_count=negative_volume,
        open_time_alignment_violation_count=alignment_violations,
        close_time_violation_count=close_time_violations,
        declared_range_violation_count=declared_range_violations,
        stage_boundary_violation_count=stage_boundary_violations,
        detected_gap_count=gap_count,
        missing_candle_count=missing_candle_count,
        contiguous_segment_count=contiguous_segments,
        gap_examples_utc=tuple(gap_examples),
        returned_candle_count=len(candles),
        p00_evaluation_performed=False,
        network_access_performed=False,
        exchange_mutation_performed=False,
        audit_fingerprint="",
    )
    manifest = replace(provisional, audit_fingerprint=_fingerprinted_dataclass(provisional, "audit_fingerprint"))
    return OfflineAuditPackage(manifest=manifest, candles=candles)


def write_manifest(path: str | Path, manifest: DataAuditManifest) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(asdict(manifest), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _main() -> int:
    parser = argparse.ArgumentParser(description="Phase B offline MEXC discovery data auditor")
    subparsers = parser.add_subparsers(dest="command", required=True)

    probe = subparsers.add_parser("probe", help="Fingerprint a raw source without interpreting market rows")
    probe.add_argument("source")

    audit = subparsers.add_parser("audit", help="Audit frozen canonical discovery CSV")
    audit.add_argument("--metadata", required=True)
    audit.add_argument("--canonical", required=True)
    audit.add_argument("--raw-source")
    audit.add_argument("--manifest")

    args = parser.parse_args()
    if args.command == "probe":
        result = probe_raw_source(args.source)
        print(json.dumps(asdict(result), indent=2, sort_keys=True))
        return 0 if result.status == "PASS_PROBE_ONLY" else 2

    package = audit_canonical_dataset(args.metadata, args.canonical, raw_source_path=args.raw_source)
    if args.manifest:
        write_manifest(args.manifest, package.manifest)
    print(json.dumps(asdict(package.manifest), indent=2, sort_keys=True))
    return 0 if package.manifest.status in {"PASS", "PASS_WITH_GAPS"} else 2


if __name__ == "__main__":
    raise SystemExit(_main())
