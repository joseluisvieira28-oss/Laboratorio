from __future__ import annotations

import argparse
import calendar
import csv
import hashlib
import json
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from research.phase_b_mexc_adapter_audit_binding_v01 import audit_adapter_bound_dataset
from research.phase_b_mexc_bulk_csv_adapter_v01 import adapt_mexc_bulk_csv, write_receipt


DISCOVERY_MIN_MONTH = "2022-01"
DISCOVERY_MAX_MONTH = "2024-12"
PASS_ADAPTER = "PASS_ADAPTER_ONLY"
PASS_AUDIT = {"PASS_ADAPTER_BOUND_AUDIT"}
TIMEFRAME_MS = 900_000


@dataclass(frozen=True)
class CorpusMonthReceipt:
    month: str
    source_file_name: str
    source_sha256: str | None
    canonical_file_name: str | None
    canonical_sha256: str | None
    adapter_fingerprint: str | None
    audit_fingerprint: str | None
    row_count: int
    expected_row_count: int
    first_open_time_match: bool
    last_open_time_match: bool
    detected_gap_count: int
    missing_candle_count: int
    status: str
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class DiscoveryCorpusManifest:
    status: str
    reasons: tuple[str, ...]
    symbol: str
    timeframe: str
    start_month: str
    end_month: str
    expected_month_count: int
    passed_month_count: int
    total_row_count: int
    months: tuple[CorpusMonthReceipt, ...]
    p00_evaluation_performed: bool
    network_access_performed: bool
    exchange_mutation_performed: bool
    fingerprint: str


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _fingerprint(manifest: DiscoveryCorpusManifest) -> str:
    payload = asdict(manifest)
    payload.pop("fingerprint", None)
    return hashlib.sha256(_canonical_json(payload)).hexdigest()


def _month_dt(value: str) -> datetime:
    parsed = datetime.strptime(value, "%Y-%m")
    return parsed.replace(tzinfo=timezone.utc)


def _month_sequence(start_month: str, end_month: str) -> list[str]:
    start = _month_dt(start_month)
    end = _month_dt(end_month)
    if start > end:
        raise ValueError("start month after end month")
    months: list[str] = []
    cursor = start
    while cursor <= end:
        months.append(cursor.strftime("%Y-%m"))
        year = cursor.year + (1 if cursor.month == 12 else 0)
        month = 1 if cursor.month == 12 else cursor.month + 1
        cursor = cursor.replace(year=year, month=month, day=1)
    return months


def _next_month_start(month: str) -> datetime:
    current = _month_dt(month)
    year = current.year + (1 if current.month == 12 else 0)
    next_month = 1 if current.month == 12 else current.month + 1
    return current.replace(year=year, month=next_month, day=1)


def _iso_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _symbol_prefix(symbol: str) -> str:
    if not symbol.endswith("USDT") or len(symbol) <= 4:
        raise ValueError("only frozen USDT symbols are accepted")
    return f"{symbol[:-4]}_USDT"


def _read_first_last_open_time(canonical_path: Path) -> tuple[int | None, int | None]:
    first: int | None = None
    last: int | None = None
    with canonical_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        next(reader, None)
        for row in reader:
            if not row:
                continue
            value = int(row[0])
            if first is None:
                first = value
            last = value
    return first, last


def _empty_manifest(*, status: str, reasons: list[str], symbol: str, start_month: str, end_month: str, expected_month_count: int = 0, months: tuple[CorpusMonthReceipt, ...] = ()) -> DiscoveryCorpusManifest:
    provisional = DiscoveryCorpusManifest(
        status=status,
        reasons=tuple(sorted(set(reasons))),
        symbol=symbol,
        timeframe="15m",
        start_month=start_month,
        end_month=end_month,
        expected_month_count=expected_month_count,
        passed_month_count=sum(1 for item in months if item.status == "PASS_MONTH"),
        total_row_count=sum(item.row_count for item in months),
        months=months,
        p00_evaluation_performed=False,
        network_access_performed=False,
        exchange_mutation_performed=False,
        fingerprint="",
    )
    return replace(provisional, fingerprint=_fingerprint(provisional))


def build_discovery_corpus(raw_dir: str | Path, output_dir: str | Path, *, symbol: str, start_month: str, end_month: str) -> DiscoveryCorpusManifest:
    """Adapt and provenance-audit a contiguous monthly MEXC Discovery corpus.

    This is an offline data-integrity operation only. It does not evaluate P00,
    contact MEXC, perform exchange mutations, interpolate candles, or unlock 2025/2026.
    All expected monthly files must be present before any market-data file is read.
    """

    raw_root = Path(raw_dir)
    output_root = Path(output_dir)
    reasons: list[str] = []

    try:
        months = _month_sequence(start_month, end_month)
        if _month_dt(start_month) < _month_dt(DISCOVERY_MIN_MONTH) or _month_dt(end_month) > _month_dt(DISCOVERY_MAX_MONTH):
            reasons.append("CORPUS_RANGE_OUTSIDE_FROZEN_DISCOVERY")
        prefix = _symbol_prefix(symbol)
    except (TypeError, ValueError):
        return _empty_manifest(status="BLOCKED_CORPUS", reasons=["INVALID_CORPUS_DECLARATION"], symbol=symbol, start_month=start_month, end_month=end_month)

    if reasons:
        return _empty_manifest(status="BLOCKED_CORPUS", reasons=reasons, symbol=symbol, start_month=start_month, end_month=end_month, expected_month_count=len(months))

    expected_paths = [raw_root / f"{prefix}-Min15-{month}-01.csv" for month in months]
    missing = [path.name for path in expected_paths if not path.is_file()]
    if missing:
        return _empty_manifest(
            status="BLOCKED_CORPUS",
            reasons=[f"MISSING_EXPECTED_MONTH:{name}" for name in missing],
            symbol=symbol,
            start_month=start_month,
            end_month=end_month,
            expected_month_count=len(months),
        )

    canonical_dir = output_root / "canonical"
    receipt_dir = output_root / "adapter_receipts"
    month_receipts: list[CorpusMonthReceipt] = []

    for month, raw_path in zip(months, expected_paths):
        canonical_path = canonical_dir / f"{raw_path.stem}.canonical.csv"
        adapter_receipt_path = receipt_dir / f"{raw_path.stem}.adapter.json"
        adapter = adapt_mexc_bulk_csv(raw_path, canonical_path)
        write_receipt(adapter_receipt_path, adapter)

        month_reasons: list[str] = []
        if adapter.status != PASS_ADAPTER:
            month_reasons.extend(adapter.blocked_reasons or ("ADAPTER_NOT_PASS",))
            month_receipts.append(
                CorpusMonthReceipt(
                    month=month,
                    source_file_name=raw_path.name,
                    source_sha256=adapter.source_sha256,
                    canonical_file_name=adapter.canonical_file_name,
                    canonical_sha256=adapter.canonical_sha256,
                    adapter_fingerprint=adapter.fingerprint,
                    audit_fingerprint=None,
                    row_count=adapter.raw_row_count,
                    expected_row_count=calendar.monthrange(int(month[:4]), int(month[5:7]))[1] * 96,
                    first_open_time_match=False,
                    last_open_time_match=False,
                    detected_gap_count=0,
                    missing_candle_count=0,
                    status="BLOCKED_MONTH",
                    reasons=tuple(sorted(set(month_reasons))),
                )
            )
            break

        start_dt = _month_dt(month)
        next_start = _next_month_start(month)
        declared_start = _iso_utc(start_dt)
        declared_end = _iso_utc(next_start - timedelta(milliseconds=1))
        audit = audit_adapter_bound_dataset(
            raw_path,
            canonical_path,
            adapter_receipt_path,
            symbol=symbol,
            declared_start_utc=declared_start,
            declared_end_utc=declared_end,
        )
        manifest = audit.manifest
        if manifest.status not in PASS_AUDIT:
            month_reasons.extend(manifest.reasons or ("ADAPTER_BOUND_AUDIT_NOT_PASS",))

        expected_rows = calendar.monthrange(start_dt.year, start_dt.month)[1] * 96
        if manifest.row_count != expected_rows or manifest.returned_candle_count != expected_rows:
            month_reasons.append("MONTH_ROW_COUNT_MISMATCH")
        if manifest.detected_gap_count != 0 or manifest.missing_candle_count != 0:
            month_reasons.append("MONTH_HAS_GAPS")

        first_open, last_open = _read_first_last_open_time(canonical_path)
        expected_first = int(start_dt.timestamp() * 1000)
        expected_last = int((next_start - timedelta(milliseconds=TIMEFRAME_MS)).timestamp() * 1000)
        first_match = first_open == expected_first
        last_match = last_open == expected_last
        if not first_match:
            month_reasons.append("MONTH_START_BOUNDARY_MISMATCH")
        if not last_match:
            month_reasons.append("MONTH_END_BOUNDARY_MISMATCH")

        month_status = "PASS_MONTH" if not month_reasons else "BLOCKED_MONTH"
        month_receipts.append(
            CorpusMonthReceipt(
                month=month,
                source_file_name=raw_path.name,
                source_sha256=adapter.source_sha256,
                canonical_file_name=adapter.canonical_file_name,
                canonical_sha256=adapter.canonical_sha256,
                adapter_fingerprint=adapter.fingerprint,
                audit_fingerprint=manifest.fingerprint,
                row_count=manifest.row_count,
                expected_row_count=expected_rows,
                first_open_time_match=first_match,
                last_open_time_match=last_match,
                detected_gap_count=manifest.detected_gap_count,
                missing_candle_count=manifest.missing_candle_count,
                status=month_status,
                reasons=tuple(sorted(set(month_reasons))),
            )
        )
        if month_status != "PASS_MONTH":
            break

    corpus_reasons: list[str] = []
    if len(month_receipts) != len(months):
        corpus_reasons.append("CORPUS_STOPPED_EARLY")
    for item in month_receipts:
        if item.status != "PASS_MONTH":
            corpus_reasons.extend(f"{item.month}:{reason}" for reason in item.reasons)

    status = "PASS_CORPUS_AUDIT_ONLY" if not corpus_reasons and len(month_receipts) == len(months) else "BLOCKED_CORPUS"
    return _empty_manifest(
        status=status,
        reasons=corpus_reasons,
        symbol=symbol,
        start_month=start_month,
        end_month=end_month,
        expected_month_count=len(months),
        months=tuple(month_receipts),
    )


def write_manifest(path: str | Path, manifest: DiscoveryCorpusManifest) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(asdict(manifest), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _main() -> int:
    parser = argparse.ArgumentParser(description="Phase B offline MEXC Discovery corpus adapter/auditor")
    parser.add_argument("raw_dir")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--start-month", required=True)
    parser.add_argument("--end-month", required=True)
    parser.add_argument("--receipt")
    args = parser.parse_args()

    result = build_discovery_corpus(args.raw_dir, args.output_dir, symbol=args.symbol, start_month=args.start_month, end_month=args.end_month)
    if args.receipt:
        write_manifest(args.receipt, result)
    print(json.dumps(asdict(result), indent=2, sort_keys=True))
    return 0 if result.status == "PASS_CORPUS_AUDIT_ONLY" else 2


if __name__ == "__main__":
    raise SystemExit(_main())
