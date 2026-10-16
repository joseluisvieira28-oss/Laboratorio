"""Offline final-binding preflight V0.2 for MRCR H02.

Binds frozen H02 science to a complete official annual date plan. Exact T0 is
not inferred here; each event later requires an official activation receipt.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from authority_transition import validate_freeze_binding
from freeze_manifest import validate_implementation_manifest_structure
from h02_calendar_binding_v02 import validate_annual_plan_manifest
from h02_ruleset import EXPECTED_RULESET_HASH
from protocol_builder_v02 import build_final_protocol_v02


@dataclass(frozen=True)
class FinalBindingPreflightV02Result:
    ready_for_target_open_authority: bool
    blockers: tuple[str, ...]
    protocol: dict[str, Any] | None


def run_final_binding_preflight_v02(
    *,
    ruleset: Mapping[str, Any],
    annual_plan: Mapping[str, Any],
    implementation_manifest: Mapping[str, Any],
    h02_authority_receipt: Mapping[str, Any],
    calendar_frozen_at_utc: str,
    protocol_frozen_at_utc: str,
) -> FinalBindingPreflightV02Result:
    blockers: list[str] = []

    if ruleset.get("ruleset_sha256") != EXPECTED_RULESET_HASH:
        blockers.append("CANONICAL_RULESET_HASH_MISMATCH")

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

    if blockers:
        return FinalBindingPreflightV02Result(
            ready_for_target_open_authority=False,
            blockers=tuple(sorted(set(blockers))),
            protocol=None,
        )

    try:
        protocol = build_final_protocol_v02(
            ruleset=ruleset,
            annual_plan=annual_plan,
            implementation_head_sha=str(
                implementation_manifest.get("implementation_head_sha")
            ),
            calendar_frozen_at_utc=calendar_frozen_at_utc,
            protocol_frozen_at_utc=protocol_frozen_at_utc,
            authority_receipt_sha256=str(
                h02_authority_receipt.get("receipt_sha256")
            ),
        )
    except Exception as exc:
        return FinalBindingPreflightV02Result(
            ready_for_target_open_authority=False,
            blockers=(f"PROTOCOL_BUILD:{type(exc).__name__}:{exc}",),
            protocol=None,
        )

    freeze_result = validate_freeze_binding(protocol, h02_authority_receipt)
    blockers.extend(f"FREEZE_BINDING:{x}" for x in freeze_result.blockers)

    if (
        protocol.get("freeze", {}).get("ruleset_sha256")
        != ruleset.get("ruleset_sha256")
    ):
        blockers.append("PROTOCOL_RULESET_BINDING_MISMATCH")

    if (
        protocol.get("calendar", {}).get("annual_plan_manifest_sha256")
        != annual_plan.get("annual_plan_sha256")
    ):
        blockers.append("PROTOCOL_ANNUAL_PLAN_BINDING_MISMATCH")

    if (
        protocol.get("decision_state", {}).get("implementation_head_sha")
        != implementation_manifest.get("implementation_head_sha")
    ):
        blockers.append("PROTOCOL_IMPLEMENTATION_HEAD_BINDING_MISMATCH")

    if (
        protocol.get("calendar", {}).get("event_activation_receipt_required")
        is not True
    ):
        blockers.append("EVENT_ACTIVATION_REQUIREMENT_MISSING")

    return FinalBindingPreflightV02Result(
        ready_for_target_open_authority=len(blockers) == 0,
        blockers=tuple(sorted(set(blockers))),
        protocol=protocol if not blockers else None,
    )
