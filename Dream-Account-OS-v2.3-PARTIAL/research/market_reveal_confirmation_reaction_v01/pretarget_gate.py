"""Fail-closed pre-target protocol validation for MRCR V0.1.

This module can validate whether a future protocol is structurally ready to freeze.
It does not authorize H02 or target observation and cannot create those authorities.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping


LAB_ID = "MARKET-REVEAL-CONFIRMATION-REACTION-001"
DOC_TYPE = "MRCR_PRETARGET_PROTOCOL_V01"
REQUIRED_AVAILABILITY_MODE = "SOURCE_AND_COLLECTOR_ARRIVAL"


@dataclass(frozen=True)
class GateResult:
    ready: bool
    blockers: tuple[str, ...]


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def sha256_hex(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def protocol_fingerprint(protocol: Mapping[str, Any]) -> str:
    clean = json.loads(json.dumps(protocol))
    freeze = clean.get("freeze")
    if isinstance(freeze, dict):
        freeze["protocol_fingerprint_sha256"] = None
    return sha256_hex(clean)


def _missing(value: Any) -> bool:
    return value is None or value == "" or value == [] or value == {}


def validate_for_freeze(protocol: Mapping[str, Any]) -> GateResult:
    blockers: list[str] = []

    if protocol.get("document_type") != DOC_TYPE:
        blockers.append("DOCUMENT_TYPE_MISMATCH")
    if protocol.get("lab_id") != LAB_ID:
        blockers.append("LAB_ID_MISMATCH")

    gov = protocol.get("governance") or {}
    if gov.get("h02_authorized") is not True:
        blockers.append("H02_NOT_AUTHORIZED")
    if gov.get("target_observation_authorized") is not False:
        blockers.append("TARGET_OBSERVATION_MUST_REMAIN_LOCKED_DURING_FREEZE")
    if gov.get("historical_contaminated_data_allowed_for_selection") is not False:
        blockers.append("CONTAMINATED_SELECTION_POLICY_INVALID")
    if str(gov.get("earliest_target_period")) < "2027":
        blockers.append("TARGET_PERIOD_BEFORE_2027")

    calendar = protocol.get("calendar") or {}
    if calendar.get("complete_official_calendar") is not True:
        blockers.append("OFFICIAL_CALENDAR_INCOMPLETE")
    for field in (
        "calendar_source_manifest_sha256",
        "calendar_frozen_at_utc",
        "event_families",
    ):
        if _missing(calendar.get(field)):
            blockers.append(f"CALENDAR_{field.upper()}_MISSING")

    scope = protocol.get("market_scope") or {}
    if _missing(scope.get("venues")):
        blockers.append("VENUES_MISSING")
    if _missing(scope.get("native_symbols")):
        blockers.append("NATIVE_SYMBOLS_MISSING")
    if scope.get("cross_venue_merge_allowed") is not False:
        blockers.append("CROSS_VENUE_MERGE_POLICY_INVALID")

    state = protocol.get("decision_state") or {}
    for field in (
        "anchor_definition",
        "decision_clock_seconds",
        "measurement_catalog_sha256",
        "implementation_head_sha",
    ):
        if _missing(state.get(field)):
            blockers.append(f"DECISION_STATE_{field.upper()}_MISSING")

    availability = state.get("availability_rule")
    if availability != REQUIRED_AVAILABILITY_MODE:
        blockers.append("AVAILABILITY_RULE_INVALID_OR_MISSING")

    depth = state.get("depth_definition") or {}
    if depth.get("mode") not in {"TOP_N", "BPS_BAND"}:
        blockers.append("DEPTH_MODE_INVALID_OR_MISSING")
    value = depth.get("value")
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
        blockers.append("DEPTH_VALUE_INVALID_OR_MISSING")
    if depth.get("mode") == "TOP_N" and isinstance(value, float) and not value.is_integer():
        blockers.append("DEPTH_TOP_N_NOT_INTEGER")

    hypothesis = protocol.get("hypothesis") or {}
    for field in (
        "causal_statement",
        "classifier_definition",
        "classifier_sha256",
        "abstention_rule",
    ):
        if _missing(hypothesis.get(field)):
            blockers.append(f"HYPOTHESIS_{field.upper()}_MISSING")

    outcome = protocol.get("outcome") or {}
    for field in (
        "future_horizon_seconds",
        "outcome_definition",
        "benchmark_definition",
    ):
        if _missing(outcome.get(field)):
            blockers.append(f"OUTCOME_{field.upper()}_MISSING")
    horizon = outcome.get("future_horizon_seconds")
    if horizon is not None and (
        not isinstance(horizon, (int, float))
        or isinstance(horizon, bool)
        or horizon <= 0
    ):
        blockers.append("OUTCOME_HORIZON_INVALID")

    economics = protocol.get("economics") or {}
    if economics.get("tested") not in {True, False}:
        blockers.append("ECONOMICS_TESTED_FLAG_MISSING")
    if economics.get("tested") is True:
        for field in ("fee_model", "slippage_model", "latency_model"):
            if _missing(economics.get(field)):
                blockers.append(f"ECONOMICS_{field.upper()}_MISSING")

    freeze = protocol.get("freeze") or {}
    for field in ("frozen_at_utc", "operator_authority_receipt"):
        if _missing(freeze.get(field)):
            blockers.append(f"FREEZE_{field.upper()}_MISSING")

    claimed = freeze.get("protocol_fingerprint_sha256")
    if _missing(claimed):
        blockers.append("PROTOCOL_FINGERPRINT_MISSING")
    else:
        expected = protocol_fingerprint(protocol)
        if claimed != expected:
            blockers.append("PROTOCOL_FINGERPRINT_MISMATCH")

    return GateResult(
        ready=len(blockers) == 0,
        blockers=tuple(sorted(set(blockers))),
    )
