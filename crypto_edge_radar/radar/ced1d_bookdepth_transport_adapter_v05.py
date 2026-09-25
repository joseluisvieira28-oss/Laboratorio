from __future__ import annotations

import csv
from datetime import date, datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile

from . import ced1d_render_shadow_collector_v03 as collector

AUTHORITY_ID = "CED1D-0031-BOOKDEPTH-TIMESTAMP-TRANSPORT-V0.5"
TRANSPORT_RECEIPT = "CED1D_0031_BOOKDEPTH_TRANSPORT_RECEIPT_V0.5.json"
TEXT_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"

_ORIGINAL_PARSE_BOOKDEPTH_ZIP = collector.parse_bookdepth_zip
_EVENTS: list[dict] = []


class CED1DBookDepthTransportError(RuntimeError):
    pass


def _is_numeric_timestamp(value: str) -> bool:
    try:
        float(str(value).strip())
        return True
    except (TypeError, ValueError):
        return False


def _text_timestamp_to_ms(value: str, expected_day: date) -> int:
    raw = str(value).strip()
    try:
        dt = datetime.strptime(raw, TEXT_TIMESTAMP_FORMAT).replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise CED1DBookDepthTransportError(
            f"BOOKDEPTH_TIMESTAMP_FORMAT_UNSUPPORTED:{raw}"
        ) from exc
    if dt.date() != expected_day:
        raise CED1DBookDepthTransportError(
            f"BOOKDEPTH_TIMESTAMP_DAY_MISMATCH:{expected_day}:{raw}"
        )
    return int(dt.timestamp() * 1000)


def normalize_bookdepth_zip(raw: bytes, expected_day: date) -> tuple[bytes, dict]:
    raw_sha256 = hashlib.sha256(raw).hexdigest()
    textual_rows = 0
    numeric_rows = 0
    data_rows = 0

    with zipfile.ZipFile(io.BytesIO(raw)) as source_zip:
        members = [name for name in source_zip.namelist() if not name.endswith("/")]
        if len(members) != 1:
            raise CED1DBookDepthTransportError(
                f"BOOKDEPTH_ZIP_MEMBER_COUNT:{len(members)}"
            )
        member = members[0]
        reader = csv.reader(
            io.TextIOWrapper(
                source_zip.open(member),
                encoding="utf-8-sig",
                newline="",
            )
        )
        rows = []
        for index, row in enumerate(reader):
            if not row:
                rows.append(row)
                continue
            if index == 0:
                if str(row[0]).strip().lower() != "timestamp":
                    raise CED1DBookDepthTransportError(
                        f"BOOKDEPTH_HEADER_UNEXPECTED:{row}"
                    )
                rows.append(row)
                continue

            data_rows += 1
            first = str(row[0]).strip()
            normalized = list(row)
            if _is_numeric_timestamp(first):
                numeric_rows += 1
            else:
                normalized[0] = str(_text_timestamp_to_ms(first, expected_day))
                textual_rows += 1
            rows.append(normalized)

    if data_rows <= 0:
        raise CED1DBookDepthTransportError("BOOKDEPTH_EMPTY_DATA")

    if textual_rows == 0:
        event = {
            "expected_day": expected_day.isoformat(),
            "member": member,
            "raw_sha256": raw_sha256,
            "data_rows": data_rows,
            "numeric_timestamp_rows": numeric_rows,
            "text_timestamp_rows_normalized": 0,
            "timestamp_mode": "NUMERIC_PASSTHROUGH",
            "raw_source_hash_preserved_by_collector": True,
        }
        return raw, event

    text_buffer = io.StringIO(newline="")
    writer = csv.writer(text_buffer, lineterminator="\n")
    writer.writerows(rows)
    csv_bytes = text_buffer.getvalue().encode("utf-8")

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(
        zip_buffer,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
    ) as target_zip:
        target_zip.writestr(member, csv_bytes)

    normalized = zip_buffer.getvalue()
    event = {
        "expected_day": expected_day.isoformat(),
        "member": member,
        "raw_sha256": raw_sha256,
        "normalized_transport_sha256": hashlib.sha256(normalized).hexdigest(),
        "data_rows": data_rows,
        "numeric_timestamp_rows": numeric_rows,
        "text_timestamp_rows_normalized": textual_rows,
        "timestamp_mode": (
            "UTC_TEXT_NORMALIZED_TO_EPOCH_MS"
            if numeric_rows == 0
            else "MIXED_NUMERIC_AND_UTC_TEXT_NORMALIZED"
        ),
        "raw_source_hash_preserved_by_collector": True,
        "columns_other_than_timestamp_changed": False,
        "row_order_changed": False,
    }
    return normalized, event


def patched_parse_bookdepth_zip(raw: bytes, expected_day: date):
    normalized, event = normalize_bookdepth_zip(raw, expected_day)
    _EVENTS.append(event)
    return _ORIGINAL_PARSE_BOOKDEPTH_ZIP(normalized, expected_day)


def _output_path_from_argv(argv: list[str]) -> Path | None:
    try:
        index = argv.index("--output")
        return Path(argv[index + 1])
    except (ValueError, IndexError):
        return None


def _transport_receipt(status: str, error: str | None) -> dict:
    collector_sha = hashlib.sha256(Path(collector.__file__).read_bytes()).hexdigest()
    return {
        "authority_id": AUTHORITY_ID,
        "status": status,
        "error": error,
        "frozen_collector_sha256": collector_sha,
        "adapter_scope": "BOOKDEPTH_TIMESTAMP_TRANSPORT_ONLY",
        "timestamp_text_format": TEXT_TIMESTAMP_FORMAT,
        "timestamp_text_timezone": "UTC",
        "events": list(_EVENTS),
        "raw_source_hash_preserved_by_collector": True,
        "scientific_rules_changed": False,
        "authenticated_exchange_api_used": False,
        "orders_created": False,
        "exchange_mutation_performed": False,
        "live_capital_enabled": False,
    }


def main() -> None:
    output = _output_path_from_argv(sys.argv)
    collector.parse_bookdepth_zip = patched_parse_bookdepth_zip
    status = "TRANSPORT_ADAPTER_COMPLETE"
    error = None
    try:
        collector.main()
    except BaseException as exc:
        status = "TRANSPORT_ADAPTER_COLLECTOR_FAIL_CLOSED"
        error = f"{type(exc).__name__}:{exc}"
        raise
    finally:
        if output is not None and output.exists():
            receipt = _transport_receipt(status, error)
            (output / TRANSPORT_RECEIPT).write_text(
                json.dumps(receipt, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )


if __name__ == "__main__":
    main()
