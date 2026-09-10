from __future__ import annotations

import argparse
import csv
import hashlib
import json
from dataclasses import asdict, dataclass, replace
from pathlib import Path, PurePosixPath
from typing import Any
from zipfile import BadZipFile, ZipFile, ZipInfo

from research.phase_b_mexc_offline_ingest_v01 import EXPECTED_HEADER, file_sha256


MAX_HEADER_LINE_BYTES = 65_536
MAX_ZIP_ENTRIES_REPORTED = 100
MAX_ZIP_TEXT_ENTRIES_PROBED = 10
MAX_ZIP_ENTRY_UNCOMPRESSED_BYTES = 10_485_760


@dataclass(frozen=True)
class EntrySchemaProbe:
    entry_name: str
    uncompressed_size: int
    suffix: str
    header_fields: tuple[str, ...]
    first_data_field_count: int | None
    canonical_header_match: bool | None
    json_top_level_shape: str | None
    reason: str | None


@dataclass(frozen=True)
class RawSchemaProbe:
    status: str
    file_name: str
    suffix: str
    byte_size: int | None
    sha256: str | None
    header_fields: tuple[str, ...]
    first_data_field_count: int | None
    canonical_header_match: bool | None
    json_top_level_shape: str | None
    zip_entry_count: int | None
    zip_entries_reported: tuple[str, ...]
    zip_entries_truncated: bool
    zip_text_entries_probed: tuple[EntrySchemaProbe, ...]
    blocked_reasons: tuple[str, ...]
    market_values_returned: bool
    p00_evaluation_performed: bool
    network_access_performed: bool
    fingerprint: str


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _fingerprint(instance: RawSchemaProbe) -> str:
    payload = asdict(instance)
    payload.pop("fingerprint", None)
    return hashlib.sha256(_canonical_json(payload)).hexdigest()


def _unsafe_zip_name(name: str) -> bool:
    normalized = name.replace("\\", "/")
    path = PurePosixPath(normalized)
    return path.is_absolute() or normalized.startswith("/") or ".." in path.parts


def _parse_csv_structure(first_line: bytes, second_line: bytes) -> tuple[tuple[str, ...], int | None, bool]:
    header_text = first_line.decode("utf-8-sig").rstrip("\r\n")
    header = tuple(next(csv.reader([header_text]))) if header_text else ()
    field_count = None
    if second_line:
        second_text = second_line.decode("utf-8-sig").rstrip("\r\n")
        if second_text:
            field_count = len(next(csv.reader([second_text])))
    return header, field_count, header == EXPECTED_HEADER


def _json_shape(prefix: bytes) -> str:
    stripped = prefix.lstrip()
    if not stripped:
        return "EMPTY"
    if stripped.startswith(b"["):
        return "ARRAY"
    if stripped.startswith(b"{"):
        return "OBJECT"
    return "OTHER"


def _read_two_lines(handle) -> tuple[bytes, bytes, str | None]:
    first = handle.readline(MAX_HEADER_LINE_BYTES + 1)
    if len(first) > MAX_HEADER_LINE_BYTES:
        return b"", b"", "HEADER_LINE_TOO_LARGE"
    second = handle.readline(MAX_HEADER_LINE_BYTES + 1)
    if len(second) > MAX_HEADER_LINE_BYTES:
        return b"", b"", "FIRST_DATA_LINE_TOO_LARGE"
    return first, second, None


def _probe_zip_entry(archive: ZipFile, info: ZipInfo) -> EntrySchemaProbe:
    suffix = Path(info.filename).suffix.lower()
    if info.flag_bits & 0x1:
        return EntrySchemaProbe(info.filename, info.file_size, suffix, (), None, None, None, "ENCRYPTED_ZIP_ENTRY")
    if info.file_size > MAX_ZIP_ENTRY_UNCOMPRESSED_BYTES:
        return EntrySchemaProbe(info.filename, info.file_size, suffix, (), None, None, None, "ZIP_ENTRY_TOO_LARGE_FOR_HEADER_PROBE")

    try:
        with archive.open(info, "r") as handle:
            if suffix == ".csv":
                first, second, reason = _read_two_lines(handle)
                if reason:
                    return EntrySchemaProbe(info.filename, info.file_size, suffix, (), None, None, None, reason)
                try:
                    header, field_count, match = _parse_csv_structure(first, second)
                except (UnicodeError, csv.Error, StopIteration):
                    return EntrySchemaProbe(info.filename, info.file_size, suffix, (), None, None, None, "CSV_HEADER_PARSE_FAILURE")
                return EntrySchemaProbe(info.filename, info.file_size, suffix, header, field_count, match, None, None)

            prefix = handle.read(MAX_HEADER_LINE_BYTES)
            return EntrySchemaProbe(info.filename, info.file_size, suffix, (), None, None, _json_shape(prefix), None)
    except (OSError, RuntimeError, BadZipFile):
        return EntrySchemaProbe(info.filename, info.file_size, suffix, (), None, None, None, "ZIP_ENTRY_READ_FAILURE")


def probe_raw_schema(path: str | Path) -> RawSchemaProbe:
    """Inspect only raw-file structure; never return market row values.

    This is intentionally not an adapter and not an ingestion path. It fingerprints
    the file and reveals only container/header shape needed to design a separately
    reviewed adapter. No P00 evaluator or network client is invoked.
    """

    source = Path(path)
    suffix = source.suffix.lower()
    if not source.is_file():
        provisional = RawSchemaProbe(
            "BLOCKED_SCHEMA_PROBE", source.name, suffix, None, None, (), None, None, None,
            None, (), False, (), ("SOURCE_FILE_NOT_FOUND",), False, False, False, ""
        )
        return replace(provisional, fingerprint=_fingerprint(provisional))

    sha256, byte_size = file_sha256(source)
    header_fields: tuple[str, ...] = ()
    first_data_field_count: int | None = None
    canonical_header_match: bool | None = None
    json_top_level_shape: str | None = None
    zip_entry_count: int | None = None
    zip_entries_reported: tuple[str, ...] = ()
    zip_entries_truncated = False
    zip_text_entries_probed: tuple[EntrySchemaProbe, ...] = ()
    reasons: list[str] = []

    if suffix == ".csv":
        try:
            with source.open("rb") as handle:
                first, second, reason = _read_two_lines(handle)
            if reason:
                reasons.append(reason)
            else:
                header_fields, first_data_field_count, canonical_header_match = _parse_csv_structure(first, second)
        except (OSError, UnicodeError, csv.Error, StopIteration):
            reasons.append("CSV_HEADER_PARSE_FAILURE")

    elif suffix == ".json":
        try:
            with source.open("rb") as handle:
                json_top_level_shape = _json_shape(handle.read(MAX_HEADER_LINE_BYTES))
        except OSError:
            reasons.append("JSON_PREFIX_READ_FAILURE")

    elif suffix == ".zip":
        try:
            with ZipFile(source, "r") as archive:
                infos = archive.infolist()
                zip_entry_count = len(infos)
                unsafe = sorted(info.filename for info in infos if _unsafe_zip_name(info.filename))
                if unsafe:
                    reasons.append("ZIP_PATH_TRAVERSAL_ENTRY")
                if any(info.flag_bits & 0x1 for info in infos):
                    reasons.append("ENCRYPTED_ZIP_ENTRY")

                sorted_names = tuple(sorted(info.filename for info in infos))
                zip_entries_reported = sorted_names[:MAX_ZIP_ENTRIES_REPORTED]
                zip_entries_truncated = len(sorted_names) > MAX_ZIP_ENTRIES_REPORTED

                candidates = [
                    info for info in sorted(infos, key=lambda item: item.filename)
                    if not info.is_dir() and Path(info.filename).suffix.lower() in {".csv", ".json"}
                ][:MAX_ZIP_TEXT_ENTRIES_PROBED]
                zip_text_entries_probed = tuple(_probe_zip_entry(archive, info) for info in candidates)
                if any(entry.reason == "ENCRYPTED_ZIP_ENTRY" for entry in zip_text_entries_probed):
                    reasons.append("ENCRYPTED_ZIP_ENTRY")
        except BadZipFile:
            reasons.append("BAD_ZIP_ARCHIVE")
        except OSError:
            reasons.append("ZIP_READ_FAILURE")

    else:
        reasons.append("UNSUPPORTED_SCHEMA_PROBE_SUFFIX")

    status = "BLOCKED_SCHEMA_PROBE" if reasons else "PASS_STRUCTURE_ONLY"
    provisional = RawSchemaProbe(
        status=status,
        file_name=source.name,
        suffix=suffix,
        byte_size=byte_size,
        sha256=sha256,
        header_fields=header_fields,
        first_data_field_count=first_data_field_count,
        canonical_header_match=canonical_header_match,
        json_top_level_shape=json_top_level_shape,
        zip_entry_count=zip_entry_count,
        zip_entries_reported=zip_entries_reported,
        zip_entries_truncated=zip_entries_truncated,
        zip_text_entries_probed=zip_text_entries_probed,
        blocked_reasons=tuple(sorted(set(reasons))),
        market_values_returned=False,
        p00_evaluation_performed=False,
        network_access_performed=False,
        fingerprint="",
    )
    return replace(provisional, fingerprint=_fingerprint(provisional))


def _main() -> int:
    parser = argparse.ArgumentParser(description="Phase B structure-only raw MEXC schema probe")
    parser.add_argument("source")
    args = parser.parse_args()
    result = probe_raw_schema(args.source)
    print(json.dumps(asdict(result), indent=2, sort_keys=True))
    return 0 if result.status == "PASS_STRUCTURE_ONLY" else 2


if __name__ == "__main__":
    raise SystemExit(_main())
