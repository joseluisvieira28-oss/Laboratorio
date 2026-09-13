from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from research.phase_b_mexc_offline_ingest_v01 import (
    CANONICAL_SCHEMA,
    IDENTITY_ADAPTER,
    SIDECAR_SCHEMA,
    audit_canonical_dataset,
    file_sha256,
)


CONTRACT_PATH = Path(__file__).with_name("PHASE_B_MEXC_ADAPTER_AUDIT_BINDING_V0.1.json")
PASS_BASE_STATUSES = {"PASS", "PASS_WITH_GAPS"}


@dataclass(frozen=True)
class AdapterBoundAuditManifest:
    status: str
    reasons: tuple[str, ...]
    stage: str
    symbol: str
    timeframe: str
    declared_start_utc: str
    declared_end_utc: str
    adapter_id: str | None
    adapter_receipt_fingerprint: str | None
    mapping_fingerprint: str | None
    raw_source_file_name: str | None
    raw_source_sha256: str | None
    raw_source_byte_size: int | None
    canonical_file_name: str | None
    canonical_sha256: str | None
    canonical_byte_size: int | None
    base_audit_status: str | None
    base_audit_fingerprint: str | None
    row_count: int
    detected_gap_count: int
    missing_candle_count: int
    returned_candle_count: int
    p00_evaluation_performed: bool
    network_access_performed: bool
    exchange_mutation_performed: bool
    fingerprint: str


@dataclass(frozen=True)
class AdapterBoundAuditPackage:
    manifest: AdapterBoundAuditManifest
    candles: tuple[Any, ...]


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _manifest_fingerprint(manifest: AdapterBoundAuditManifest) -> str:
    payload = asdict(manifest)
    payload.pop("fingerprint", None)
    return _sha256(_canonical_json(payload))


def _receipt_fingerprint(receipt: dict[str, Any]) -> str:
    payload = dict(receipt)
    payload.pop("fingerprint", None)
    return _sha256(_canonical_json(payload))


def _load_contract() -> dict[str, Any]:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _valid_sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ValueError("timestamp must be UTC")
    return parsed.astimezone(timezone.utc)


def _empty_manifest(
    *,
    status: str,
    reasons: list[str],
    stage: str,
    symbol: str,
    timeframe: str,
    declared_start_utc: str,
    declared_end_utc: str,
    adapter_receipt: dict[str, Any] | None = None,
    raw_sha: str | None = None,
    raw_size: int | None = None,
    canonical_sha: str | None = None,
    canonical_size: int | None = None,
    base_manifest: Any | None = None,
) -> AdapterBoundAuditManifest:
    receipt = adapter_receipt or {}
    provisional = AdapterBoundAuditManifest(
        status=status,
        reasons=tuple(sorted(set(reasons))),
        stage=stage,
        symbol=symbol,
        timeframe=timeframe,
        declared_start_utc=declared_start_utc,
        declared_end_utc=declared_end_utc,
        adapter_id=receipt.get("adapter_id"),
        adapter_receipt_fingerprint=receipt.get("fingerprint"),
        mapping_fingerprint=receipt.get("mapping_fingerprint"),
        raw_source_file_name=receipt.get("source_file_name"),
        raw_source_sha256=raw_sha if raw_sha is not None else receipt.get("source_sha256"),
        raw_source_byte_size=raw_size if raw_size is not None else receipt.get("source_byte_size"),
        canonical_file_name=receipt.get("canonical_file_name"),
        canonical_sha256=canonical_sha if canonical_sha is not None else receipt.get("canonical_sha256"),
        canonical_byte_size=canonical_size if canonical_size is not None else receipt.get("canonical_byte_size"),
        base_audit_status=getattr(base_manifest, "status", None),
        base_audit_fingerprint=getattr(base_manifest, "audit_fingerprint", None),
        row_count=getattr(base_manifest, "row_count", 0),
        detected_gap_count=getattr(base_manifest, "detected_gap_count", 0),
        missing_candle_count=getattr(base_manifest, "missing_candle_count", 0),
        returned_candle_count=getattr(base_manifest, "returned_candle_count", 0),
        p00_evaluation_performed=False,
        network_access_performed=False,
        exchange_mutation_performed=False,
        fingerprint="",
    )
    return replace(provisional, fingerprint=_manifest_fingerprint(provisional))


def _preflight(
    *,
    contract: dict[str, Any],
    stage: str,
    symbol: str,
    timeframe: str,
    declared_start_utc: str,
    declared_end_utc: str,
) -> list[str]:
    rule = contract["binding_rule"]
    reasons: list[str] = []
    if stage != rule["stage"]:
        reasons.append("STAGE_NOT_UNLOCKED")
    if symbol not in rule["allowed_symbols"]:
        reasons.append("SYMBOL_OUTSIDE_FROZEN_UNIVERSE")
    if timeframe != rule["timeframe"]:
        reasons.append("TIMEFRAME_OUTSIDE_FROZEN_UNIVERSE")
    try:
        declared_start = _utc(declared_start_utc)
        declared_end = _utc(declared_end_utc)
        discovery_start = _utc(rule["discovery_start_utc"])
        discovery_end = _utc(rule["discovery_end_utc"])
    except (TypeError, ValueError, OverflowError):
        reasons.append("INVALID_DECLARED_UTC_RANGE")
        return reasons
    if declared_start > declared_end:
        reasons.append("DECLARED_RANGE_REVERSED")
    if declared_start < discovery_start or declared_end > discovery_end:
        reasons.append("DECLARED_RANGE_OUTSIDE_DISCOVERY")
    return reasons


def _load_and_validate_adapter_receipt(path: str | Path, contract: dict[str, Any]) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        receipt = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return None, ["INVALID_ADAPTER_RECEIPT"]
    if not isinstance(receipt, dict):
        return None, ["INVALID_ADAPTER_RECEIPT"]

    rule = contract["binding_rule"]
    reasons: list[str] = []
    required_fields = (
        "status",
        "adapter_id",
        "source_file_name",
        "source_sha256",
        "source_byte_size",
        "canonical_file_name",
        "canonical_sha256",
        "canonical_byte_size",
        "mapping_fingerprint",
        "amount_field_ignored",
        "amount_semantics_authorized",
        "market_values_returned_in_receipt",
        "p00_evaluation_performed",
        "network_access_performed",
        "exchange_mutation_performed",
        "blocked_reasons",
        "fingerprint",
    )
    for field in required_fields:
        if field not in receipt:
            reasons.append(f"MISSING_ADAPTER_RECEIPT_FIELD:{field}")

    if reasons:
        return receipt, reasons
    if receipt["status"] != rule["required_adapter_status"]:
        reasons.append("ADAPTER_STATUS_NOT_PASS")
    if receipt["adapter_id"] != rule["adapter_id"]:
        reasons.append("ADAPTER_ID_MISMATCH")
    if receipt["mapping_fingerprint"] != rule["mapping_fingerprint"]:
        reasons.append("ADAPTER_MAPPING_FINGERPRINT_MISMATCH")
    if receipt["fingerprint"] != _receipt_fingerprint(receipt):
        reasons.append("ADAPTER_RECEIPT_FINGERPRINT_MISMATCH")
    if not _valid_sha256(receipt["source_sha256"]):
        reasons.append("INVALID_RAW_SOURCE_SHA256")
    if not _valid_sha256(receipt["canonical_sha256"]):
        reasons.append("INVALID_CANONICAL_SHA256")
    if receipt["amount_field_ignored"] is not True:
        reasons.append("AMOUNT_FIELD_NOT_IGNORED")
    if receipt["amount_semantics_authorized"] is not False:
        reasons.append("AMOUNT_SEMANTICS_UNEXPECTEDLY_AUTHORIZED")
    if receipt["market_values_returned_in_receipt"] is not False:
        reasons.append("MARKET_VALUES_EXPOSED_IN_ADAPTER_RECEIPT")
    if receipt["p00_evaluation_performed"] is not False:
        reasons.append("ADAPTER_RECEIPT_CLAIMS_P00")
    if receipt["network_access_performed"] is not False:
        reasons.append("ADAPTER_RECEIPT_CLAIMS_NETWORK_ACCESS")
    if receipt["exchange_mutation_performed"] is not False:
        reasons.append("ADAPTER_RECEIPT_CLAIMS_EXCHANGE_MUTATION")
    if receipt["blocked_reasons"] not in ([], ()):
        reasons.append("ADAPTER_RECEIPT_HAS_BLOCK_REASONS")
    return receipt, reasons


def audit_adapter_bound_dataset(
    raw_source_path: str | Path,
    canonical_path: str | Path,
    adapter_receipt_path: str | Path,
    *,
    symbol: str,
    declared_start_utc: str,
    declared_end_utc: str,
    stage: str = "DISCOVERY",
    timeframe: str = "15m",
) -> AdapterBoundAuditPackage:
    """Bind a validated adapter receipt to the unchanged canonical integrity auditor.

    Stage/symbol/time-range authorization is checked before raw/canonical market-data
    bytes are read. P00, network access, live integration and exchange mutation remain
    absent. The base auditor is reused unchanged after provenance is proven.
    """

    contract = _load_contract()
    preflight_reasons = _preflight(
        contract=contract,
        stage=stage,
        symbol=symbol,
        timeframe=timeframe,
        declared_start_utc=declared_start_utc,
        declared_end_utc=declared_end_utc,
    )
    if preflight_reasons:
        return AdapterBoundAuditPackage(
            manifest=_empty_manifest(
                status="BLOCKED_METADATA",
                reasons=preflight_reasons,
                stage=stage,
                symbol=symbol,
                timeframe=timeframe,
                declared_start_utc=declared_start_utc,
                declared_end_utc=declared_end_utc,
            ),
            candles=(),
        )

    adapter_receipt, receipt_reasons = _load_and_validate_adapter_receipt(adapter_receipt_path, contract)
    if receipt_reasons or adapter_receipt is None:
        return AdapterBoundAuditPackage(
            manifest=_empty_manifest(
                status="BLOCKED_ADAPTER_RECEIPT",
                reasons=receipt_reasons or ["INVALID_ADAPTER_RECEIPT"],
                stage=stage,
                symbol=symbol,
                timeframe=timeframe,
                declared_start_utc=declared_start_utc,
                declared_end_utc=declared_end_utc,
                adapter_receipt=adapter_receipt,
            ),
            candles=(),
        )

    raw = Path(raw_source_path)
    canonical = Path(canonical_path)
    if not raw.is_file() or not canonical.is_file():
        return AdapterBoundAuditPackage(
            manifest=_empty_manifest(
                status="BLOCKED_SOURCE",
                reasons=["RAW_OR_CANONICAL_SOURCE_NOT_FOUND"],
                stage=stage,
                symbol=symbol,
                timeframe=timeframe,
                declared_start_utc=declared_start_utc,
                declared_end_utc=declared_end_utc,
                adapter_receipt=adapter_receipt,
            ),
            candles=(),
        )

    raw_sha, raw_size = file_sha256(raw)
    canonical_sha, canonical_size = file_sha256(canonical)
    provenance_reasons: list[str] = []
    if raw.name != adapter_receipt["source_file_name"]:
        provenance_reasons.append("RAW_SOURCE_FILENAME_MISMATCH")
    if raw_sha != adapter_receipt["source_sha256"]:
        provenance_reasons.append("RAW_SOURCE_SHA256_MISMATCH")
    if raw_size != adapter_receipt["source_byte_size"]:
        provenance_reasons.append("RAW_SOURCE_BYTE_SIZE_MISMATCH")
    if canonical.name != adapter_receipt["canonical_file_name"]:
        provenance_reasons.append("CANONICAL_FILENAME_MISMATCH")
    if canonical_sha != adapter_receipt["canonical_sha256"]:
        provenance_reasons.append("CANONICAL_SHA256_MISMATCH")
    if canonical_size != adapter_receipt["canonical_byte_size"]:
        provenance_reasons.append("CANONICAL_BYTE_SIZE_MISMATCH")

    if provenance_reasons:
        return AdapterBoundAuditPackage(
            manifest=_empty_manifest(
                status="BLOCKED_PROVENANCE",
                reasons=provenance_reasons,
                stage=stage,
                symbol=symbol,
                timeframe=timeframe,
                declared_start_utc=declared_start_utc,
                declared_end_utc=declared_end_utc,
                adapter_receipt=adapter_receipt,
                raw_sha=raw_sha,
                raw_size=raw_size,
                canonical_sha=canonical_sha,
                canonical_size=canonical_size,
            ),
            candles=(),
        )

    identity_sidecar = {
        "schema_version": SIDECAR_SCHEMA,
        "source_exchange": "MEXC",
        "market_type": "SPOT",
        "source_authority": "OFFICIAL_MEXC_SOURCE_ONLY",
        "stage": stage,
        "symbol": symbol,
        "timeframe": timeframe,
        "declared_start_utc": declared_start_utc,
        "declared_end_utc": declared_end_utc,
        "raw_source_filename": canonical.name,
        "raw_source_sha256": canonical_sha,
        "canonical_schema": CANONICAL_SCHEMA,
        "adapter_id": IDENTITY_ADAPTER,
    }

    with tempfile.TemporaryDirectory() as tmp:
        sidecar_path = Path(tmp) / "verified_canonical_identity_sidecar.json"
        sidecar_path.write_text(json.dumps(identity_sidecar, sort_keys=True), encoding="utf-8")
        base_package = audit_canonical_dataset(sidecar_path, canonical)

    base = base_package.manifest
    if base.status not in PASS_BASE_STATUSES:
        reasons = [f"BASE_AUDIT:{reason}" for reason in base.reasons]
        if not reasons:
            reasons = [f"BASE_AUDIT_STATUS:{base.status}"]
        return AdapterBoundAuditPackage(
            manifest=_empty_manifest(
                status="BLOCKED_BASE_AUDIT",
                reasons=reasons,
                stage=stage,
                symbol=symbol,
                timeframe=timeframe,
                declared_start_utc=declared_start_utc,
                declared_end_utc=declared_end_utc,
                adapter_receipt=adapter_receipt,
                raw_sha=raw_sha,
                raw_size=raw_size,
                canonical_sha=canonical_sha,
                canonical_size=canonical_size,
                base_manifest=base,
            ),
            candles=(),
        )

    status = "PASS_ADAPTER_BOUND_AUDIT" if base.status == "PASS" else "PASS_WITH_GAPS_ADAPTER_BOUND_AUDIT"
    manifest = _empty_manifest(
        status=status,
        reasons=[],
        stage=stage,
        symbol=symbol,
        timeframe=timeframe,
        declared_start_utc=declared_start_utc,
        declared_end_utc=declared_end_utc,
        adapter_receipt=adapter_receipt,
        raw_sha=raw_sha,
        raw_size=raw_size,
        canonical_sha=canonical_sha,
        canonical_size=canonical_size,
        base_manifest=base,
    )
    return AdapterBoundAuditPackage(manifest=manifest, candles=base_package.candles)


def write_manifest(path: str | Path, manifest: AdapterBoundAuditManifest) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(asdict(manifest), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _main() -> int:
    parser = argparse.ArgumentParser(description="Phase B offline MEXC adapter-to-audit provenance binding")
    parser.add_argument("raw_source")
    parser.add_argument("canonical")
    parser.add_argument("adapter_receipt")
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--declared-start", required=True)
    parser.add_argument("--declared-end", required=True)
    parser.add_argument("--receipt-out")
    args = parser.parse_args()

    package = audit_adapter_bound_dataset(
        args.raw_source,
        args.canonical,
        args.adapter_receipt,
        symbol=args.symbol,
        declared_start_utc=args.declared_start,
        declared_end_utc=args.declared_end,
    )
    if args.receipt_out:
        write_manifest(args.receipt_out, package.manifest)
    print(json.dumps(asdict(package.manifest), indent=2, sort_keys=True))
    return 0 if package.manifest.status.startswith("PASS") else 2


if __name__ == "__main__":
    raise SystemExit(_main())
