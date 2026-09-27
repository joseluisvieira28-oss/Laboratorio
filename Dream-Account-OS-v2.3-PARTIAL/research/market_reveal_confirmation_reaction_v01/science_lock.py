"""MRCR pretarget science lock.

This is a chronology/authority guard, not a scientific classifier.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from h02_ruleset import validate_h02_ruleset


HERE = Path(__file__).resolve().parent
PROTOCOL = HERE / "PRETARGET_PROTOCOL_TEMPLATE_V01.json"
CALENDAR = HERE / "OFFICIAL_CALENDAR_MANIFEST_TEMPLATE_V01.json"
READINESS = HERE / "PRETARGET_READINESS_MATRIX_2026-09-24.json"
AUTHORITY = HERE / "H02_DESIGN_FREEZE_AUTHORITY_V01.json"
RULESET = HERE / "H02_SCIENTIFIC_RULESET_V01.json"
CLASSIFIER = HERE / "H02_CLASSIFIER_SPEC_V01.json"
MEASUREMENT_CATALOG = HERE / "MEASUREMENT_CATALOG_V01.md"


def _is_populated(value: Any) -> bool:
    return value not in (None, "", [], {})


def evaluate_science_lock(
    protocol: dict[str, Any],
    calendar: dict[str, Any],
    readiness: dict[str, Any],
    authority: dict[str, Any] | None = None,
    ruleset: dict[str, Any] | None = None,
    classifier: dict[str, Any] | None = None,
    measurement_catalog_bytes: bytes | None = None,
) -> tuple[bool, tuple[str, ...]]:
    violations: list[str] = []

    gov = protocol.get("governance") or {}
    if gov.get("h02_authorized") is not False:
        violations.append("H02_ARMED_WITHOUT_AUTHORITY_TRANSITION")
    if gov.get("target_observation_authorized") is not False:
        violations.append("TARGET_OBSERVATION_ARMED_WITHOUT_AUTHORITY_TRANSITION")

    if calendar.get("complete_official_calendar") is not False:
        violations.append("CALENDAR_TEMPLATE_MARKED_COMPLETE")
    if _is_populated(calendar.get("event_families")):
        violations.append("CALENDAR_TEMPLATE_EVENT_FAMILIES_PRESELECTED")
    if _is_populated(calendar.get("events")):
        violations.append("CALENDAR_TEMPLATE_EVENTS_PREPOPULATED")

    if _is_populated(protocol.get("calendar", {}).get("event_families")):
        violations.append("PROTOCOL_EVENT_FAMILIES_PRESELECTED")

    scope = protocol.get("market_scope") or {}
    if _is_populated(scope.get("venues")):
        violations.append("TARGET_VENUES_PRESELECTED")
    if _is_populated(scope.get("native_symbols")):
        violations.append("TARGET_SYMBOLS_PRESELECTED")
    if scope.get("cross_venue_merge_allowed") is not False:
        violations.append("CROSS_VENUE_MERGE_POLICY_CHANGED")

    state = protocol.get("decision_state") or {}
    for field in ("anchor_definition", "decision_clock_seconds", "availability_rule"):
        if _is_populated(state.get(field)):
            violations.append(f"{field.upper()}_PRESELECTED")
    depth = state.get("depth_definition") or {}
    if _is_populated(depth.get("mode")) or _is_populated(depth.get("value")):
        violations.append("DEPTH_RULE_PRESELECTED")

    hyp = protocol.get("hypothesis") or {}
    for field in (
        "causal_statement",
        "classifier_definition",
        "classifier_sha256",
        "abstention_rule",
    ):
        if _is_populated(hyp.get(field)):
            violations.append(f"{field.upper()}_PRESELECTED")

    outcome = protocol.get("outcome") or {}
    for field in (
        "future_horizon_seconds",
        "outcome_definition",
        "benchmark_definition",
    ):
        if _is_populated(outcome.get(field)):
            violations.append(f"{field.upper()}_PRESELECTED")

    economics = protocol.get("economics") or {}
    if economics.get("tested") is not None:
        violations.append("ECONOMICS_TEST_FLAG_PRESELECTED")
    for field in ("fee_model", "slippage_model", "latency_model"):
        if _is_populated(economics.get(field)):
            violations.append(f"{field.upper()}_PRESELECTED")

    freeze = protocol.get("freeze") or {}
    for field in (
        "protocol_fingerprint_sha256",
        "frozen_at_utc",
        "operator_authority_receipt",
    ):
        if _is_populated(freeze.get(field)):
            violations.append(f"{field.upper()}_POPULATED_WITHOUT_TRANSITION")

    design_authorized = authority is not None
    expected = {
        "H02": (
            "DESIGN_FREEZE_AUTHORIZED"
            if design_authorized
            else "NOT_AUTHORIZED"
        ),
        "TARGET_OBSERVATION": "NOT_AUTHORIZED",
        "LIVE_TRADING": "PROHIBITED",
    }
    statuses = {
        row.get("gate"): row.get("status")
        for row in readiness.get("gates", [])
        if isinstance(row, dict)
    }
    for gate, status in expected.items():
        if statuses.get(gate) != status:
            violations.append(f"READINESS_{gate}_STATUS_CHANGED")

    if design_authorized:
        if ruleset is None or classifier is None or measurement_catalog_bytes is None:
            violations.append("H02_DESIGN_AUTHORITY_WITHOUT_FROZEN_RULESET_EVIDENCE")
        else:
            ready, blockers = validate_h02_ruleset(
                ruleset,
                authority,
                classifier,
                measurement_catalog_bytes,
            )
            if not ready:
                violations.extend(f"H02_RULESET:{b}" for b in blockers)

    return len(violations) == 0, tuple(sorted(set(violations)))


def main() -> int:
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    calendar = json.loads(CALENDAR.read_text(encoding="utf-8"))
    readiness = json.loads(READINESS.read_text(encoding="utf-8"))
    authority = json.loads(AUTHORITY.read_text(encoding="utf-8"))
    ruleset = json.loads(RULESET.read_text(encoding="utf-8"))
    classifier = json.loads(CLASSIFIER.read_text(encoding="utf-8"))
    locked, violations = evaluate_science_lock(
        protocol,
        calendar,
        readiness,
        authority,
        ruleset,
        classifier,
        MEASUREMENT_CATALOG.read_bytes(),
    )
    print(json.dumps({
        "lock": "MRCR_PRETARGET_SCIENCE_LOCK_V01",
        "locked": locked,
        "mode": "H02_DESIGN_FROZEN__TARGET_LOCKED",
        "violations": list(violations),
    }, sort_keys=True))
    return 0 if locked else 2


if __name__ == "__main__":
    raise SystemExit(main())
