from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DISCOVERY_MIN_MONTH = "2023-01"
DISCOVERY_MAX_MONTH = "2024-12"


@dataclass(frozen=True)
class IntakeMonth:
    month: str
    file_name: str
    status: str
    source_sha256: str | None
    destination_sha256: str | None


@dataclass(frozen=True)
class IntakeReceipt:
    status: str
    reasons: tuple[str, ...]
    symbol: str
    start_month: str
    end_month: str
    expected_month_count: int
    copied_count: int
    already_present_count: int
    missing_count: int
    conflict_count: int
    months: tuple[IntakeMonth, ...]
    p00_evaluation_performed: bool
    network_access_performed: bool
    exchange_mutation_performed: bool
    fingerprint: str


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _fingerprint(payload: dict[str, Any]) -> str:
    clone = dict(payload)
    clone.pop("fingerprint", None)
    return hashlib.sha256(_canonical_json(clone)).hexdigest()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _month_dt(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m").replace(tzinfo=timezone.utc)


def _month_sequence(start_month: str, end_month: str) -> list[str]:
    start = _month_dt(start_month)
    end = _month_dt(end_month)
    if start > end:
        raise ValueError("start month after end month")
    result: list[str] = []
    cursor = start
    while cursor <= end:
        result.append(cursor.strftime("%Y-%m"))
        year = cursor.year + (1 if cursor.month == 12 else 0)
        month = 1 if cursor.month == 12 else cursor.month + 1
        cursor = cursor.replace(year=year, month=month, day=1)
    return result


def _symbol_prefix(symbol: str) -> str:
    if not symbol.endswith("USDT") or len(symbol) <= 4:
        raise ValueError("only frozen USDT symbols are accepted")
    return f"{symbol[:-4]}_USDT"


def _build_receipt(*, status: str, reasons: list[str], symbol: str, start_month: str, end_month: str, months: list[IntakeMonth]) -> IntakeReceipt:
    payload = {
        "status": status,
        "reasons": tuple(sorted(set(reasons))),
        "symbol": symbol,
        "start_month": start_month,
        "end_month": end_month,
        "expected_month_count": len(months),
        "copied_count": sum(1 for item in months if item.status == "COPIED"),
        "already_present_count": sum(1 for item in months if item.status == "ALREADY_PRESENT"),
        "missing_count": sum(1 for item in months if item.status == "MISSING"),
        "conflict_count": sum(1 for item in months if item.status == "BLOCKED_CONFLICT"),
        "months": tuple(months),
        "p00_evaluation_performed": False,
        "network_access_performed": False,
        "exchange_mutation_performed": False,
        "fingerprint": "",
    }
    serializable = {**payload, "months": [asdict(item) for item in months]}
    payload["fingerprint"] = _fingerprint(serializable)
    return IntakeReceipt(**payload)


def intake_downloads(source_dir: str | Path, destination_dir: str | Path, *, symbol: str, start_month: str, end_month: str) -> IntakeReceipt:
    """Copy only exact expected official-MEXC monthly filenames into the offline Discovery raw directory.

    This function performs no network access, no parsing of market values, no P00 evaluation,
    and never overwrites a conflicting destination file.
    """

    source_root = Path(source_dir)
    destination_root = Path(destination_dir)
    reasons: list[str] = []

    try:
        months = _month_sequence(start_month, end_month)
        prefix = _symbol_prefix(symbol)
        if _month_dt(start_month) < _month_dt(DISCOVERY_MIN_MONTH) or _month_dt(end_month) > _month_dt(DISCOVERY_MAX_MONTH):
            reasons.append("INTAKE_RANGE_OUTSIDE_PRE_2025_DISCOVERY_BOUNDARY")
    except (TypeError, ValueError):
        return _build_receipt(status="BLOCKED_INTAKE", reasons=["INVALID_INTAKE_DECLARATION"], symbol=symbol, start_month=start_month, end_month=end_month, months=[])

    if reasons:
        return _build_receipt(status="BLOCKED_INTAKE", reasons=reasons, symbol=symbol, start_month=start_month, end_month=end_month, months=[])

    destination_root.mkdir(parents=True, exist_ok=True)
    receipts: list[IntakeMonth] = []

    for month in months:
        file_name = f"{prefix}-Min15-{month}-01.csv"
        source_path = source_root / file_name
        destination_path = destination_root / file_name

        if not source_path.is_file():
            receipts.append(IntakeMonth(month, file_name, "MISSING", None, _sha256(destination_path) if destination_path.is_file() else None))
            continue

        source_sha = _sha256(source_path)
        if destination_path.is_file():
            destination_sha = _sha256(destination_path)
            if destination_sha == source_sha:
                receipts.append(IntakeMonth(month, file_name, "ALREADY_PRESENT", source_sha, destination_sha))
            else:
                receipts.append(IntakeMonth(month, file_name, "BLOCKED_CONFLICT", source_sha, destination_sha))
            continue

        temporary_path = destination_path.with_suffix(destination_path.suffix + ".tmp")
        if temporary_path.exists():
            temporary_path.unlink()
        shutil.copyfile(source_path, temporary_path)
        copied_sha = _sha256(temporary_path)
        if copied_sha != source_sha:
            temporary_path.unlink(missing_ok=True)
            receipts.append(IntakeMonth(month, file_name, "BLOCKED_CONFLICT", source_sha, copied_sha))
            continue
        temporary_path.replace(destination_path)
        receipts.append(IntakeMonth(month, file_name, "COPIED", source_sha, copied_sha))

    conflicts = [item for item in receipts if item.status == "BLOCKED_CONFLICT"]
    missing = [item for item in receipts if item.status == "MISSING"]
    if conflicts:
        status = "BLOCKED_INTAKE"
        reasons.append("DESTINATION_HASH_CONFLICT")
    elif missing:
        status = "INCOMPLETE_INTAKE"
    else:
        status = "PASS_INTAKE_COMPLETE"

    return _build_receipt(status=status, reasons=reasons, symbol=symbol, start_month=start_month, end_month=end_month, months=receipts)


def write_receipt(path: str | Path, receipt: IntakeReceipt) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(asdict(receipt), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _main() -> int:
    parser = argparse.ArgumentParser(description="Offline intake of already-downloaded official MEXC monthly CSVs")
    parser.add_argument("source_dir")
    parser.add_argument("--destination-dir", required=True)
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--start-month", required=True)
    parser.add_argument("--end-month", required=True)
    parser.add_argument("--receipt")
    args = parser.parse_args()

    result = intake_downloads(args.source_dir, args.destination_dir, symbol=args.symbol, start_month=args.start_month, end_month=args.end_month)
    if args.receipt:
        write_receipt(args.receipt, result)
    print(json.dumps(asdict(result), indent=2, sort_keys=True))
    return 2 if result.status == "BLOCKED_INTAKE" else 0


if __name__ == "__main__":
    raise SystemExit(_main())
