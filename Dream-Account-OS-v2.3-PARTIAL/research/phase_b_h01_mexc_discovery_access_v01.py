from __future__ import annotations

"""Fail-closed local-file boundary for H01 Discovery.

This module does NOT itself authorize 2025 access. It requires a separately frozen,
valid machine-readable authorization before it will inspect bytes from an allowed
market-data file. It never enumerates the source directory: only exact filenames for
H01 Discovery provider partitions 2025-01..2025-08 are constructed.

P00 ingestion code is intentionally untouched.
"""

import hashlib
import json
import shutil
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any


HYPOTHESIS_ID = "H01_PROTECT_AFTER_TP1_NEXT_BAR"
FAMILY_ID = "PBR02_MANAGED_BREAKOUT_RETEST_LONG"
FROZEN_UNIVERSE = (
    "BTCUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "BNBUSDT",
    "XRPUSDT",
    "DOGEUSDT",
)
DISCOVERY_START_MONTH = "2025-01"
DISCOVERY_END_MONTH = "2025-08"
EXPECTED_MONTHS = (
    "2025-01",
    "2025-02",
    "2025-03",
    "2025-04",
    "2025-05",
    "2025-06",
    "2025-07",
    "2025-08",
)
VALIDATION_START_MONTH = "2025-09"
VALIDATION_END_MONTH = "2025-12"
HOLDOUT_START_MONTH = "2026-01"
AUTHORIZATION_DOCUMENT_TYPE = "PHASE_B_H01_2025_DISCOVERY_DATA_ACCESS_AUTHORIZATION"
AUTHORIZATION_STATUS = "AUTHORIZED_OFFLINE_H01_DISCOVERY_ONLY"
DEFAULT_AUTHORIZATION_PATH = Path(__file__).with_name(
    "PHASE_B_H01_2025_DISCOVERY_DATA_ACCESS_AUTHORIZATION_V0.1.json"
)


@dataclass(frozen=True)
class H01IntakeMonth:
    month: str
    file_name: str
    status: str
    source_sha256: str | None
    destination_sha256: str | None


@dataclass(frozen=True)
class H01DiscoveryAccessReceipt:
    status: str
    reasons: tuple[str, ...]
    hypothesis_id: str
    symbol: str
    requested_start_month: str
    requested_end_month: str
    expected_file_names: tuple[str, ...]
    authorization_file_name: str
    authorization_fingerprint: str | None
    authorization_verified: bool
    source_directory_enumerated: bool
    source_market_bytes_read: bool
    validation_2025_market_bytes_read: bool
    holdout_2026_market_bytes_read: bool
    network_access_performed: bool
    exchange_mutation_performed: bool
    submitted_to_exchange: bool
    copied_count: int
    already_present_count: int
    missing_count: int
    conflict_count: int
    months: tuple[H01IntakeMonth, ...]
    fingerprint: str


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _hash_payload(payload: dict[str, Any]) -> str:
    clone = dict(payload)
    clone.pop("fingerprint", None)
    return hashlib.sha256(_canonical_json(clone)).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _prefix(symbol: str) -> str:
    if symbol not in FROZEN_UNIVERSE:
        raise ValueError("symbol outside frozen H01 universe")
    return f"{symbol[:-4]}_USDT"


def _expected_file_names(symbol: str) -> tuple[str, ...]:
    prefix = _prefix(symbol)
    return tuple(f"{prefix}-Min15-{month}-01.csv" for month in EXPECTED_MONTHS)


def _load_and_verify_authorization(path: Path) -> tuple[dict[str, Any] | None, list[str], str | None]:
    reasons: list[str] = []
    if not path.is_file():
        return None, ["H01_DISCOVERY_ACCESS_AUTHORIZATION_MISSING"], None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None, ["H01_DISCOVERY_ACCESS_AUTHORIZATION_UNREADABLE"], None
    if not isinstance(payload, dict):
        return None, ["H01_DISCOVERY_ACCESS_AUTHORIZATION_NOT_OBJECT"], None

    supplied_fingerprint = payload.get("fingerprint")
    calculated_fingerprint = _hash_payload(payload)
    if not isinstance(supplied_fingerprint, str) or supplied_fingerprint != calculated_fingerprint:
        reasons.append("H01_DISCOVERY_ACCESS_AUTHORIZATION_FINGERPRINT_MISMATCH")

    expected_pairs = {
        "document_type": AUTHORIZATION_DOCUMENT_TYPE,
        "status": AUTHORIZATION_STATUS,
        "hypothesis_id": HYPOTHESIS_ID,
        "family_id": FAMILY_ID,
        "source": "OFFICIAL_MEXC_SPOT_HISTORICAL_ONLY",
        "timeframe": "15m",
        "source_partition_timezone": "UTC+08:00",
        "allowed_start_month": DISCOVERY_START_MONTH,
        "allowed_end_month": DISCOVERY_END_MONTH,
    }
    for key, expected in expected_pairs.items():
        if payload.get(key) != expected:
            reasons.append(f"H01_DISCOVERY_ACCESS_AUTHORIZATION_FIELD_MISMATCH:{key}")

    if tuple(payload.get("universe", ())) != FROZEN_UNIVERSE:
        reasons.append("H01_DISCOVERY_ACCESS_AUTHORIZATION_UNIVERSE_MISMATCH")
    if payload.get("cross_exchange_backfill_allowed") is not False:
        reasons.append("H01_DISCOVERY_ACCESS_AUTHORIZATION_BACKFILL_NOT_FALSE")
    if payload.get("interpolation_allowed") is not False:
        reasons.append("H01_DISCOVERY_ACCESS_AUTHORIZATION_INTERPOLATION_NOT_FALSE")
    if payload.get("validation_2025_access_authorized") is not False:
        reasons.append("H01_DISCOVERY_ACCESS_AUTHORIZATION_VALIDATION_NOT_LOCKED")
    if payload.get("holdout_2026_access_authorized") is not False:
        reasons.append("H01_DISCOVERY_ACCESS_AUTHORIZATION_HOLDOUT_NOT_LOCKED")
    if payload.get("network_download_authorized") is not False:
        reasons.append("H01_DISCOVERY_ACCESS_AUTHORIZATION_NETWORK_NOT_FALSE")
    if payload.get("exchange_mutation_authorized") is not False:
        reasons.append("H01_DISCOVERY_ACCESS_AUTHORIZATION_MUTATION_NOT_FALSE")
    if payload.get("live_trading_authorized") is not False:
        reasons.append("H01_DISCOVERY_ACCESS_AUTHORIZATION_LIVE_NOT_FALSE")

    return payload, reasons, supplied_fingerprint if isinstance(supplied_fingerprint, str) else None


def _receipt(
    *,
    status: str,
    reasons: list[str],
    symbol: str,
    start_month: str,
    end_month: str,
    expected_file_names: tuple[str, ...],
    authorization_path: Path,
    authorization_fingerprint: str | None,
    authorization_verified: bool,
    source_market_bytes_read: bool,
    months: list[H01IntakeMonth],
) -> H01DiscoveryAccessReceipt:
    provisional = H01DiscoveryAccessReceipt(
        status=status,
        reasons=tuple(sorted(set(reasons))),
        hypothesis_id=HYPOTHESIS_ID,
        symbol=symbol,
        requested_start_month=start_month,
        requested_end_month=end_month,
        expected_file_names=expected_file_names,
        authorization_file_name=authorization_path.name,
        authorization_fingerprint=authorization_fingerprint,
        authorization_verified=authorization_verified,
        source_directory_enumerated=False,
        source_market_bytes_read=source_market_bytes_read,
        validation_2025_market_bytes_read=False,
        holdout_2026_market_bytes_read=False,
        network_access_performed=False,
        exchange_mutation_performed=False,
        submitted_to_exchange=False,
        copied_count=sum(item.status == "COPIED" for item in months),
        already_present_count=sum(item.status == "ALREADY_PRESENT" for item in months),
        missing_count=sum(item.status == "MISSING" for item in months),
        conflict_count=sum(item.status == "BLOCKED_CONFLICT" for item in months),
        months=tuple(months),
        fingerprint="",
    )
    return replace(provisional, fingerprint=_hash_payload(asdict(provisional)))


def validate_h01_discovery_access_request(
    *,
    symbol: str,
    start_month: str,
    end_month: str,
    authorization_path: str | Path = DEFAULT_AUTHORIZATION_PATH,
) -> H01DiscoveryAccessReceipt:
    """Validate authority and exact H01 Discovery scope without touching market files."""

    auth_path = Path(authorization_path)
    reasons: list[str] = []
    expected: tuple[str, ...] = ()
    try:
        expected = _expected_file_names(symbol)
    except (TypeError, ValueError):
        reasons.append("H01_SYMBOL_OUTSIDE_FROZEN_UNIVERSE")

    # Scope is checked before source paths or market bytes are inspected.
    if start_month != DISCOVERY_START_MONTH or end_month != DISCOVERY_END_MONTH:
        reasons.append("H01_REQUEST_OUTSIDE_EXACT_DISCOVERY_PROVIDER_PARTITIONS")
    if start_month >= VALIDATION_START_MONTH or end_month >= VALIDATION_START_MONTH:
        reasons.append("H01_VALIDATION_2025_RANGE_BLOCKED")
    if start_month >= HOLDOUT_START_MONTH or end_month >= HOLDOUT_START_MONTH:
        reasons.append("H01_HOLDOUT_2026_RANGE_BLOCKED")

    payload, auth_reasons, auth_fingerprint = _load_and_verify_authorization(auth_path)
    reasons.extend(auth_reasons)
    verified = payload is not None and not auth_reasons
    status = "PASS_H01_DISCOVERY_ACCESS_PREFLIGHT" if not reasons else "BLOCKED_H01_DISCOVERY_ACCESS"
    return _receipt(
        status=status,
        reasons=reasons,
        symbol=symbol,
        start_month=start_month,
        end_month=end_month,
        expected_file_names=expected,
        authorization_path=auth_path,
        authorization_fingerprint=auth_fingerprint,
        authorization_verified=verified,
        source_market_bytes_read=False,
        months=[],
    )


def intake_h01_discovery_downloads(
    source_dir: str | Path,
    destination_dir: str | Path,
    *,
    symbol: str,
    start_month: str,
    end_month: str,
    authorization_path: str | Path = DEFAULT_AUTHORIZATION_PATH,
) -> H01DiscoveryAccessReceipt:
    """Copy only exact H01 Discovery files after authorization preflight passes.

    The source directory is never listed or globbed. Validation/holdout filenames are
    never constructed by this function. Market bytes are read only for the exact
    eight authorized Discovery provider files for the one requested frozen symbol.
    """

    preflight = validate_h01_discovery_access_request(
        symbol=symbol,
        start_month=start_month,
        end_month=end_month,
        authorization_path=authorization_path,
    )
    if preflight.status != "PASS_H01_DISCOVERY_ACCESS_PREFLIGHT":
        return preflight

    source_root = Path(source_dir)
    destination_root = Path(destination_dir)
    destination_root.mkdir(parents=True, exist_ok=True)
    results: list[H01IntakeMonth] = []
    bytes_read = False

    for month, file_name in zip(EXPECTED_MONTHS, preflight.expected_file_names):
        source = source_root / file_name
        destination = destination_root / file_name
        if not source.is_file():
            destination_sha = None
            if destination.is_file():
                destination_sha = _file_sha256(destination)
                bytes_read = True
            results.append(H01IntakeMonth(month, file_name, "MISSING", None, destination_sha))
            continue

        source_sha = _file_sha256(source)
        bytes_read = True
        if destination.is_file():
            destination_sha = _file_sha256(destination)
            if destination_sha == source_sha:
                results.append(H01IntakeMonth(month, file_name, "ALREADY_PRESENT", source_sha, destination_sha))
            else:
                results.append(H01IntakeMonth(month, file_name, "BLOCKED_CONFLICT", source_sha, destination_sha))
            continue

        temporary = destination.with_suffix(destination.suffix + ".tmp")
        temporary.unlink(missing_ok=True)
        shutil.copyfile(source, temporary)
        copied_sha = _file_sha256(temporary)
        if copied_sha != source_sha:
            temporary.unlink(missing_ok=True)
            results.append(H01IntakeMonth(month, file_name, "BLOCKED_CONFLICT", source_sha, copied_sha))
            continue
        temporary.replace(destination)
        results.append(H01IntakeMonth(month, file_name, "COPIED", source_sha, copied_sha))

    reasons: list[str] = []
    if any(item.status == "BLOCKED_CONFLICT" for item in results):
        status = "BLOCKED_H01_DISCOVERY_INTAKE"
        reasons.append("H01_DESTINATION_HASH_CONFLICT")
    elif any(item.status == "MISSING" for item in results):
        status = "INCOMPLETE_H01_DISCOVERY_INTAKE"
    else:
        status = "PASS_H01_DISCOVERY_INTAKE_COMPLETE"

    return _receipt(
        status=status,
        reasons=reasons,
        symbol=symbol,
        start_month=start_month,
        end_month=end_month,
        expected_file_names=preflight.expected_file_names,
        authorization_path=Path(authorization_path),
        authorization_fingerprint=preflight.authorization_fingerprint,
        authorization_verified=True,
        source_market_bytes_read=bytes_read,
        months=results,
    )


def write_receipt(path: str | Path, receipt: H01DiscoveryAccessReceipt) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(asdict(receipt), indent=2, sort_keys=True) + "\n", encoding="utf-8")
