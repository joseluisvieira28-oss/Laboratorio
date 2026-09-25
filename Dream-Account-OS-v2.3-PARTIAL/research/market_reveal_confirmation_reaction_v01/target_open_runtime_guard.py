"""Fail-closed runtime gate for future MRCR prospective target capture.

This module cannot issue authority. It only verifies that a future capture
process is bound to an already-frozen protocol, complete official calendar,
implementation manifest and ACTIVE TARGET_OBSERVATION_OPEN authority.

It does not open or reveal future-return outcomes.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from authority_transition import (
    TARGET_OBSERVATION_OPEN,
    validate_target_open_binding,
)
from calendar_manifest import validate_calendar_manifest


@dataclass(frozen=True)
class TargetOpenGuardResult:
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


def validate_target_capture_open(
    *,
    protocol: Mapping[str, Any],
    calendar_manifest: Mapping[str, Any],
    implementation_manifest: Mapping[str, Any],
    authority_receipt: Mapping[str, Any],
    now_utc: str,
) -> TargetOpenGuardResult:
    blockers: list[str] = []

    if authority_receipt.get("authority_type") != TARGET_OBSERVATION_OPEN:
        blockers.append("TARGET_OBSERVATION_OPEN_AUTHORITY_REQUIRED")

    implementation_hash = implementation_manifest.get("manifest_sha256")
    if not isinstance(implementation_hash, str) or len(implementation_hash) != 64:
        blockers.append("IMPLEMENTATION_MANIFEST_SHA256_INVALID_OR_MISSING")

    implementation_head = implementation_manifest.get("implementation_head_sha")
    protocol_head = (protocol.get("decision_state") or {}).get("implementation_head_sha")
    if implementation_head != protocol_head:
        blockers.append("IMPLEMENTATION_HEAD_PROTOCOL_BINDING_MISMATCH")

    calendar_ok, calendar_blockers = validate_calendar_manifest(calendar_manifest)
    if not calendar_ok:
        blockers.extend(f"CALENDAR:{x}" for x in calendar_blockers)

    if isinstance(implementation_hash, str) and len(implementation_hash) == 64:
        bound = validate_target_open_binding(
            protocol,
            calendar_manifest,
            implementation_hash,
            authority_receipt,
        )
        blockers.extend(bound.blockers)

    now = _parse_utc(now_utc)
    earliest = _parse_utc((authority_receipt.get("bindings") or {}).get("earliest_target_utc"))
    if now is None:
        blockers.append("NOW_UTC_INVALID")
    if earliest is None:
        blockers.append("EARLIEST_TARGET_UTC_INVALID")
    if now is not None and earliest is not None and now < earliest:
        blockers.append("TARGET_WINDOW_NOT_STARTED")

    gov = protocol.get("governance") or {}
    if gov.get("h02_authorized") is not True:
        blockers.append("PROTOCOL_H02_NOT_FROZEN")
    if gov.get("target_observation_authorized") is not False:
        blockers.append("PROTOCOL_MUST_REMAIN_TARGET_LOCKED")
    if protocol.get("status") != "FROZEN_PRETARGET_PROTOCOL__TARGET_LOCKED":
        blockers.append("PROTOCOL_STATUS_NOT_FROZEN_TARGET_LOCKED")

    return TargetOpenGuardResult(
        ready=len(blockers) == 0,
        blockers=tuple(sorted(set(blockers))),
    )
