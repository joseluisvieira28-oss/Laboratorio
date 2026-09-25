"""Machine-checkable MRCR authority transition receipts.

This module validates future operator-issued authority receipts. It does not issue
authority and the canonical template remains UNISSUED_TEMPLATE.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping

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
