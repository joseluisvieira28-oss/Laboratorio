"""Fail-closed event capture runtime guard V0.2 for MRCR H02.

Requires:
- frozen target-locked protocol V0.2;
- valid annual-plan manifest V0.2;
- valid implementation manifest;
- ACTIVE TARGET_OBSERVATION_OPEN authority bound to protocol/plan/implementation;
- valid official event activation receipt for the exact event before T0.

This module never computes outcomes and never issues authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from authority_transition import (
    TARGET_OBSERVATION_OPEN,
    validate_authority_receipt,
)
from freeze_manifest import validate_implementation_manifest_structure
from h02_calendar_binding_v02 import (
    validate_annual_plan_manifest,
    validate_event_activation_receipt,
)
from h02_ruleset import EXPECTED_RULESET_HASH
from pretarget_gate import protocol_fingerprint


@dataclass(frozen=True)
class EventCaptureGuardV02Result:
    ready: bool
    blockers: tuple[str, ...]


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


def validate_event_capture_open_v02(
    *,
    protocol: Mapping[str, Any],
    annual_plan: Mapping[str, Any],
    implementation_manifest: Mapping[str, Any],
    target_open_authority: Mapping[str, Any],
    event_activation_receipt: Mapping[str, Any],
    ruleset: Mapping[str, Any],
    now_utc: str,
) -> EventCaptureGuardV02Result:
    blockers: list[str] = []

    if target_open_authority.get("authority_type") != TARGET_OBSERVATION_OPEN:
        blockers.append("TARGET_OBSERVATION_OPEN_AUTHORITY_REQUIRED")

    auth = validate_authority_receipt(target_open_authority)
    blockers.extend(f"AUTHORITY:{x}" for x in auth.blockers)

    plan_ok, plan_blockers = validate_annual_plan_manifest(
        annual_plan,
        ruleset=ruleset,
    )
    if not plan_ok:
        blockers.extend(f"ANNUAL_PLAN:{x}" for x in plan_blockers)

    impl_ok, impl_blockers = validate_implementation_manifest_structure(
        dict(implementation_manifest)
    )
    if not impl_ok:
        blockers.extend(f"IMPLEMENTATION:{x}" for x in impl_blockers)

    freeze = protocol.get("freeze") or {}
    calendar = protocol.get("calendar") or {}
    gov = protocol.get("governance") or {}
    state = protocol.get("decision_state") or {}

    protocol_hash = freeze.get("protocol_fingerprint_sha256")
    if protocol_hash != protocol_fingerprint(protocol):
        blockers.append("PROTOCOL_FINGERPRINT_NOT_SELF_CONSISTENT")
    if freeze.get("ruleset_sha256") != EXPECTED_RULESET_HASH:
        blockers.append("PROTOCOL_RULESET_HASH_MISMATCH")
    if gov.get("h02_authorized") is not True:
        blockers.append("PROTOCOL_H02_NOT_FROZEN")
    if gov.get("target_observation_authorized") is not False:
        blockers.append("PROTOCOL_MUST_REMAIN_TARGET_LOCKED")
    if protocol.get("status") != "FROZEN_PRETARGET_PROTOCOL__TARGET_LOCKED":
        blockers.append("PROTOCOL_STATUS_NOT_FROZEN_TARGET_LOCKED")
    if protocol.get("protocol_version") != "0.2":
        blockers.append("PROTOCOL_VERSION_NOT_V02")
    if calendar.get("calendar_binding_mode") != "ANNUAL_PLAN_PLUS_EVENT_ACTIVATION_V02":
        blockers.append("CALENDAR_BINDING_MODE_NOT_V02")
    if calendar.get("event_activation_receipt_required") is not True:
        blockers.append("EVENT_ACTIVATION_REQUIREMENT_MISSING")

    annual_hash = annual_plan.get("annual_plan_sha256")
    if calendar.get("annual_plan_manifest_sha256") != annual_hash:
        blockers.append("PROTOCOL_ANNUAL_PLAN_BINDING_MISMATCH")
    if calendar.get("calendar_source_manifest_sha256") != annual_hash:
        blockers.append("PROTOCOL_CALENDAR_ALIAS_BINDING_MISMATCH")

    impl_hash = implementation_manifest.get("manifest_sha256")
    if state.get("implementation_head_sha") != implementation_manifest.get(
        "implementation_head_sha"
    ):
        blockers.append("IMPLEMENTATION_HEAD_PROTOCOL_BINDING_MISMATCH")

    bindings = target_open_authority.get("bindings") or {}
    if bindings.get("protocol_fingerprint_sha256") != protocol_hash:
        blockers.append("TARGET_AUTHORITY_PROTOCOL_BINDING_MISMATCH")
    if bindings.get("calendar_source_manifest_sha256") != annual_hash:
        blockers.append("TARGET_AUTHORITY_ANNUAL_PLAN_BINDING_MISMATCH")
    if bindings.get("implementation_manifest_sha256") != impl_hash:
        blockers.append("TARGET_AUTHORITY_IMPLEMENTATION_BINDING_MISMATCH")

    earliest = _parse_utc(bindings.get("earliest_target_utc"))
    issued = _parse_utc(target_open_authority.get("issued_at_utc"))
    protocol_frozen = _parse_utc(freeze.get("frozen_at_utc"))
    calendar_frozen = _parse_utc(calendar.get("calendar_frozen_at_utc"))
    now = _parse_utc(now_utc)

    if earliest is None:
        blockers.append("EARLIEST_TARGET_UTC_INVALID")
    if now is None:
        blockers.append("NOW_UTC_INVALID")
    if now is not None and earliest is not None and now < earliest:
        blockers.append("TARGET_WINDOW_NOT_STARTED")

    for label, boundary in (
        ("AUTHORITY_ISSUED", issued),
        ("PROTOCOL_FROZEN", protocol_frozen),
        ("CALENDAR_FROZEN", calendar_frozen),
    ):
        if boundary is None:
            blockers.append(f"{label}_UTC_INVALID")
        elif earliest is not None and earliest <= boundary:
            blockers.append(f"EARLIEST_TARGET_NOT_AFTER_{label}")

    activation_ok, activation_blockers = validate_event_activation_receipt(
        event_activation_receipt,
        annual_plan=annual_plan,
        now_utc=now_utc,
    )
    if not activation_ok:
        blockers.extend(f"EVENT_ACTIVATION:{x}" for x in activation_blockers)

    if event_activation_receipt.get("target_observation_authorized") is not False:
        blockers.append("EVENT_ACTIVATION_MUST_NOT_SELF_AUTHORIZE_TARGET")
    if event_activation_receipt.get("outcomes_authorized") is not False:
        blockers.append("EVENT_ACTIVATION_MUST_NOT_AUTHORIZE_OUTCOMES")

    return EventCaptureGuardV02Result(
        ready=len(blockers) == 0,
        blockers=tuple(sorted(set(blockers))),
    )
