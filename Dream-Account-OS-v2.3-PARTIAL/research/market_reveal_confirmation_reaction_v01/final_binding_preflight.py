"""Offline final-binding preflight for MRCR H02.

This tool assembles and validates a target-locked final protocol candidate from
already-frozen science plus a complete official calendar and implementation
manifest. It cannot issue TARGET_OBSERVATION_OPEN and cannot open target capture.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from authority_transition import validate_freeze_binding
from freeze_manifest import validate_implementation_manifest_structure
from h02_calendar_binding import validate_h02_calendar_manifest
from h02_ruleset import EXPECTED_RULESET_HASH
from protocol_builder import build_final_protocol


@dataclass(frozen=True)
class FinalBindingPreflightResult:
    ready_for_target_open_authority: bool
    blockers: tuple[str, ...]
    protocol: dict[str, Any] | None


def run_final_binding_preflight(
    *,
    ruleset: Mapping[str, Any],
    calendar_manifest: Mapping[str, Any],
    implementation_manifest: Mapping[str, Any],
    h02_authority_receipt: Mapping[str, Any],
    calendar_frozen_at_utc: str,
    protocol_frozen_at_utc: str,
) -> FinalBindingPreflightResult:
    blockers: list[str] = []

    if ruleset.get("ruleset_sha256") != EXPECTED_RULESET_HASH:
        blockers.append("CANONICAL_RULESET_HASH_MISMATCH")

    calendar_ok, calendar_blockers = validate_h02_calendar_manifest(
        calendar_manifest,
        ruleset=ruleset,
    )
    if not calendar_ok:
        blockers.extend(f"CALENDAR:{x}" for x in calendar_blockers)

    impl_ok, impl_blockers = validate_implementation_manifest_structure(
        dict(implementation_manifest)
    )
    if not impl_ok:
        blockers.extend(f"IMPLEMENTATION:{x}" for x in impl_blockers)

    implementation_head = implementation_manifest.get("implementation_head_sha")
    if blockers:
        return FinalBindingPreflightResult(
            ready_for_target_open_authority=False,
            blockers=tuple(sorted(set(blockers))),
            protocol=None,
        )

    try:
        protocol = build_final_protocol(
            ruleset=ruleset,
            calendar_manifest=calendar_manifest,
            implementation_head_sha=str(implementation_head),
            calendar_frozen_at_utc=calendar_frozen_at_utc,
            protocol_frozen_at_utc=protocol_frozen_at_utc,
            authority_receipt_sha256=str(h02_authority_receipt.get("receipt_sha256")),
        )
    except Exception as exc:
        blockers.append(f"PROTOCOL_BUILD:{type(exc).__name__}:{exc}")
        return FinalBindingPreflightResult(
            ready_for_target_open_authority=False,
            blockers=tuple(sorted(set(blockers))),
            protocol=None,
        )

    freeze_result = validate_freeze_binding(protocol, h02_authority_receipt)
    if not freeze_result.ready:
        blockers.extend(f"FREEZE_BINDING:{x}" for x in freeze_result.blockers)

    if (
        protocol.get("freeze", {}).get("ruleset_sha256")
        != ruleset.get("ruleset_sha256")
    ):
        blockers.append("PROTOCOL_RULESET_BINDING_MISMATCH")

    if (
        protocol.get("calendar", {}).get("calendar_source_manifest_sha256")
        != calendar_manifest.get("manifest_sha256")
    ):
        blockers.append("PROTOCOL_CALENDAR_BINDING_MISMATCH")

    if (
        protocol.get("decision_state", {}).get("implementation_head_sha")
        != implementation_manifest.get("implementation_head_sha")
    ):
        blockers.append("PROTOCOL_IMPLEMENTATION_HEAD_BINDING_MISMATCH")

    return FinalBindingPreflightResult(
        ready_for_target_open_authority=len(blockers) == 0,
        blockers=tuple(sorted(set(blockers))),
        protocol=protocol if not blockers else None,
    )
