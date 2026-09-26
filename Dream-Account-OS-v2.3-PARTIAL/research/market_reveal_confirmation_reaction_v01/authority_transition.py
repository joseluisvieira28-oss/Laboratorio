"""Machine-checkable MRCR authority transition receipts.

This module validates future operator-issued authority receipts. It does not issue
authority and the canonical template remains UNISSUED_TEMPLATE.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from calendar_manifest import validate_calendar_manifest
from pretarget_gate import protocol_fingerprint, validate_for_freeze

LAB_ID = "MARKET-REVEAL-CONFIRMATION-REACTION-001"
DOC_TYPE = "MRCR_AUTHORITY_TRANSITION_V01"
GOVERNANCE_POLICY_ID = "CRYPTO-LAB-GOVERNANCE-V4.0-DEATH-FROZEN"
H02_DESIGN_FREEZE = "H02_DESIGN_FREEZE"
TARGET_OBSERVATION_OPEN = "TARGET_OBSERVATION_OPEN"


@dataclass(frozen=True)
class AuthorityResult:
    ready: bool
    blockers: tuple[str, ...]


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def receipt_fingerprint(receipt: Mapping[str, Any]) -> str:
    clean = json.loads(json.dumps(receipt))
    clean["receipt_sha256"] = None
    return hashlib.sha256(_canonical_json_bytes(clean)).hexdigest()


def _is_sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    return all(ch in "0123456789abcdef" for ch in value.lower())


def validate_authority_receipt(receipt: Mapping[str, Any]) -> AuthorityResult:
    blockers: list[str] = []

    if receipt.get("document_type") != DOC_TYPE:
        blockers.append("DOCUMENT_TYPE_MISMATCH")
    if receipt.get("lab_id") != LAB_ID:
        blockers.append("LAB_ID_MISMATCH")
    if receipt.get("status") != "ACTIVE":
        blockers.append("AUTHORITY_NOT_ACTIVE")
    if receipt.get("governance_policy_id") != GOVERNANCE_POLICY_ID:
        blockers.append("GOVERNANCE_POLICY_MISMATCH")
    if not receipt.get("issued_at_utc"):
        blockers.append("ISSUED_AT_MISSING")

    scope = receipt.get("scope") or {}
    forbidden_true = (
        "historical_contaminated_outcome_inspection",
        "live_trading",
        "paper_trading",
        "exchange_mutation",
        "paid_data_purchase",
        "render_deployment",
        "main_merge",
    )
    for field in forbidden_true:
        if scope.get(field) is not False:
            blockers.append(f"FORBIDDEN_SCOPE_{field.upper()}")

    chronology = receipt.get("chronology") or {}
    if chronology.get("requires_freeze_before_target_open") is not True:
        blockers.append("FREEZE_BEFORE_TARGET_OPEN_NOT_REQUIRED")
    if chronology.get("authority_may_not_inherit_promotion_credit") is not True:
        blockers.append("PROMOTION_CREDIT_BOUNDARY_MISSING")
    if chronology.get("contaminated_history_may_not_select_parameters") is not True:
        blockers.append("CONTAMINATION_SELECTION_BOUNDARY_MISSING")

    authority_type = receipt.get("authority_type")
    bindings = receipt.get("bindings") or {}

    if authority_type == H02_DESIGN_FREEZE:
        if scope.get("h02_design_and_freeze") is not True:
            blockers.append("H02_DESIGN_FREEZE_SCOPE_MISSING")
        if scope.get("target_observation") is not False:
            blockers.append("TARGET_OBSERVATION_MUST_REMAIN_LOCKED")
        if bindings.get("earliest_target_utc") not in (None, ""):
            blockers.append("EARLIEST_TARGET_SET_BEFORE_TARGET_OPEN")
    elif authority_type == TARGET_OBSERVATION_OPEN:
        if scope.get("target_observation") is not True:
            blockers.append("TARGET_OBSERVATION_SCOPE_MISSING")
        for field in (
            "protocol_fingerprint_sha256",
            "calendar_source_manifest_sha256",
            "implementation_manifest_sha256",
        ):
            if not _is_sha256(bindings.get(field)):
                blockers.append(f"BINDING_{field.upper()}_INVALID_OR_MISSING")
        if not bindings.get("earliest_target_utc"):
            blockers.append("EARLIEST_TARGET_UTC_MISSING")
    else:
        blockers.append("AUTHORITY_TYPE_INVALID_OR_MISSING")

    claimed = receipt.get("receipt_sha256")
    if not _is_sha256(claimed):
        blockers.append("RECEIPT_SHA256_INVALID_OR_MISSING")
    elif claimed != receipt_fingerprint(receipt):
        blockers.append("RECEIPT_SHA256_MISMATCH")

    return AuthorityResult(
        ready=len(blockers) == 0,
        blockers=tuple(sorted(set(blockers))),
    )


def _parse_utc(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        return None
    return dt.astimezone(timezone.utc)


def validate_freeze_binding(
    protocol: Mapping[str, Any],
    authority_receipt: Mapping[str, Any],
) -> AuthorityResult:
    blockers: list[str] = []

    authority = validate_authority_receipt(authority_receipt)
    blockers.extend(authority.blockers)
    if authority_receipt.get("authority_type") != H02_DESIGN_FREEZE:
        blockers.append("FREEZE_AUTHORITY_TYPE_INVALID")

    structural = validate_for_freeze(protocol)
    blockers.extend(structural.blockers)

    gov = protocol.get("governance") or {}
    if gov.get("h02_authorized") is not True:
        blockers.append("PROTOCOL_H02_NOT_AUTHORIZED")
    if gov.get("target_observation_authorized") is not False:
        blockers.append("PROTOCOL_TARGET_OBSERVATION_NOT_LOCKED")

    freeze = protocol.get("freeze") or {}
    if freeze.get("operator_authority_receipt") != authority_receipt.get("receipt_sha256"):
        blockers.append("FREEZE_AUTHORITY_RECEIPT_BINDING_MISMATCH")

    return AuthorityResult(
        ready=len(blockers) == 0,
        blockers=tuple(sorted(set(blockers))),
    )


def validate_target_open_binding(
    protocol: Mapping[str, Any],
    calendar_manifest: Mapping[str, Any],
    implementation_manifest_sha256: str,
    authority_receipt: Mapping[str, Any],
) -> AuthorityResult:
    blockers: list[str] = []

    authority = validate_authority_receipt(authority_receipt)
    blockers.extend(authority.blockers)
    if authority_receipt.get("authority_type") != TARGET_OBSERVATION_OPEN:
        blockers.append("TARGET_OPEN_AUTHORITY_TYPE_INVALID")

    structural = validate_for_freeze(protocol)
    blockers.extend(structural.blockers)

    calendar_ok, calendar_blockers = validate_calendar_manifest(calendar_manifest)
    if not calendar_ok:
        blockers.extend(calendar_blockers)

    freeze = protocol.get("freeze") or {}
    protocol_hash = freeze.get("protocol_fingerprint_sha256")
    if protocol_hash != protocol_fingerprint(protocol):
        blockers.append("PROTOCOL_FINGERPRINT_NOT_SELF_CONSISTENT")

    calendar_hash = calendar_manifest.get("manifest_sha256")
    protocol_calendar = protocol.get("calendar") or {}
    if protocol_calendar.get("calendar_source_manifest_sha256") != calendar_hash:
        blockers.append("PROTOCOL_CALENDAR_BINDING_MISMATCH")

    bindings = authority_receipt.get("bindings") or {}
    if bindings.get("protocol_fingerprint_sha256") != protocol_hash:
        blockers.append("TARGET_AUTHORITY_PROTOCOL_BINDING_MISMATCH")
    if bindings.get("calendar_source_manifest_sha256") != calendar_hash:
        blockers.append("TARGET_AUTHORITY_CALENDAR_BINDING_MISMATCH")
    if (
        not _is_sha256(implementation_manifest_sha256)
        or bindings.get("implementation_manifest_sha256")
        != implementation_manifest_sha256
    ):
        blockers.append("TARGET_AUTHORITY_IMPLEMENTATION_BINDING_MISMATCH")

    earliest = _parse_utc(bindings.get("earliest_target_utc"))
    issued = _parse_utc(authority_receipt.get("issued_at_utc"))
    frozen = _parse_utc(freeze.get("frozen_at_utc"))
    calendar_frozen = _parse_utc(protocol_calendar.get("calendar_frozen_at_utc"))
    if earliest is None:
        blockers.append("EARLIEST_TARGET_UTC_INVALID")
    for label, boundary in (
        ("AUTHORITY_ISSUED", issued),
        ("PROTOCOL_FROZEN", frozen),
        ("CALENDAR_FROZEN", calendar_frozen),
    ):
        if boundary is None:
            blockers.append(f"{label}_UTC_INVALID")
        elif earliest is not None and earliest <= boundary:
            blockers.append(f"EARLIEST_TARGET_NOT_AFTER_{label}")

    return AuthorityResult(
        ready=len(blockers) == 0,
        blockers=tuple(sorted(set(blockers))),
    )
