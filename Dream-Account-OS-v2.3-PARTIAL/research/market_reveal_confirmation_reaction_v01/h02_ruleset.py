"""Validation for the frozen MRCR H02 scientific ruleset."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from authority_transition import H02_DESIGN_FREEZE, validate_authority_receipt


HERE = Path(__file__).resolve().parent
RULESET_PATH = HERE / "H02_SCIENTIFIC_RULESET_V01.json"
AUTHORITY_PATH = HERE / "H02_DESIGN_FREEZE_AUTHORITY_V01.json"
CLASSIFIER_SPEC_PATH = HERE / "H02_CLASSIFIER_SPEC_V01.json"
MEASUREMENT_CATALOG_PATH = HERE / "MEASUREMENT_CATALOG_V01.md"

EXPECTED_RULESET_HASH = "28b01887b73298bae5ffa695599c49af5c40355392ae64255abe06d9f0d6849e"
EXPECTED_CLASSIFIER_HASH = "d92029514a512dd5db1bb91431ab4df1887169f46545bfa81c692456e9f715ff"
EXPECTED_MEASUREMENT_HASH = "5f329ddcd7ba7438885e0936a522b5a4b08248fa6e7c7b76b7c4ef9be489cc97"


def canonical_hash(value: Mapping[str, Any], hash_field: str) -> str:
    clean = json.loads(json.dumps(value))
    clean[hash_field] = None
    raw = json.dumps(
        clean,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_h02_ruleset(
    ruleset: Mapping[str, Any],
    authority: Mapping[str, Any],
    classifier_spec: Mapping[str, Any],
    measurement_catalog_bytes: bytes,
) -> tuple[bool, tuple[str, ...]]:
    blockers: list[str] = []

    if ruleset.get("document_type") != "MRCR_H02_SCIENTIFIC_RULESET_V01":
        blockers.append("RULESET_DOCUMENT_TYPE_MISMATCH")
    if ruleset.get("lab_id") != "MARKET-REVEAL-CONFIRMATION-REACTION-001":
        blockers.append("RULESET_LAB_ID_MISMATCH")
    if ruleset.get("h02_id") != "MRCR-H02-ACCEPTANCE-REJECTION-V01":
        blockers.append("RULESET_H02_ID_MISMATCH")
    if ruleset.get("status") != "FROZEN_RULESET__CALENDAR_BINDING_PENDING":
        blockers.append("RULESET_STATUS_INVALID")

    claimed = ruleset.get("ruleset_sha256")
    actual = canonical_hash(ruleset, "ruleset_sha256")
    if claimed != EXPECTED_RULESET_HASH or actual != claimed:
        blockers.append("RULESET_FINGERPRINT_MISMATCH")

    authority_result = validate_authority_receipt(authority)
    if not authority_result.ready:
        blockers.extend(f"AUTHORITY:{b}" for b in authority_result.blockers)
    if authority.get("authority_type") != H02_DESIGN_FREEZE:
        blockers.append("H02_DESIGN_FREEZE_AUTHORITY_REQUIRED")
    if (authority.get("scope") or {}).get("target_observation") is not False:
        blockers.append("TARGET_OBSERVATION_MUST_REMAIN_LOCKED")
    if ruleset.get("authority_receipt_sha256") != authority.get("receipt_sha256"):
        blockers.append("RULESET_AUTHORITY_BINDING_MISMATCH")

    classifier_claimed = classifier_spec.get("spec_sha256")
    classifier_actual = canonical_hash(classifier_spec, "spec_sha256")
    if (
        classifier_claimed != EXPECTED_CLASSIFIER_HASH
        or classifier_actual != classifier_claimed
        or (ruleset.get("decision_state") or {}).get("classifier_spec_sha256")
        != classifier_claimed
    ):
        blockers.append("CLASSIFIER_SPEC_FINGERPRINT_MISMATCH")

    measurement_hash = hashlib.sha256(measurement_catalog_bytes).hexdigest()
    if (
        measurement_hash != EXPECTED_MEASUREMENT_HASH
        or (ruleset.get("decision_state") or {}).get("measurement_catalog_sha256")
        != measurement_hash
    ):
        blockers.append("MEASUREMENT_CATALOG_FINGERPRINT_MISMATCH")

    event_scope = ruleset.get("event_scope") or {}
    if event_scope.get("event_families") != [
        "US_CPI",
        "US_EMPLOYMENT_SITUATION",
        "FOMC_STATEMENT",
    ]:
        blockers.append("EVENT_FAMILY_MUTATION")
    if event_scope.get("calendar_year") != 2027:
        blockers.append("TARGET_CALENDAR_YEAR_MUTATION")
    if event_scope.get("actual_vs_consensus_used") is not False:
        blockers.append("CONSENSUS_REINTRODUCED")

    market = ruleset.get("market_scope") or {}
    if market.get("assets") != ["BTC", "ETH"]:
        blockers.append("ASSET_SCOPE_MUTATION")
    if market.get("cross_venue_price_merge_allowed") is not False:
        blockers.append("CROSS_VENUE_PRICE_MERGE_FORBIDDEN")
    if market.get("cross_venue_state_confirmation_required") is not True:
        blockers.append("CROSS_VENUE_CONFIRMATION_REQUIRED")

    state = ruleset.get("decision_state") or {}
    if state.get("decision_clock_seconds") != 180:
        blockers.append("DECISION_CLOCK_MUTATION")
    if state.get("availability_rule") != "SOURCE_AND_COLLECTOR_ARRIVAL":
        blockers.append("AVAILABILITY_RULE_MUTATION")
    if state.get("depth_definition") != {"mode": "BPS_BAND", "value": 10}:
        blockers.append("DEPTH_RULE_MUTATION")

    outcome = ruleset.get("outcome") or {}
    if outcome.get("future_horizon_seconds") != 900:
        blockers.append("OUTCOME_HORIZON_MUTATION")
    inference = outcome.get("inference") or {}
    if inference.get("replicates") != 10_000 or inference.get("seed") != 1729:
        blockers.append("INFERENCE_CONFIG_MUTATION")
    if inference.get("confidence_level") != 0.95:
        blockers.append("CONFIDENCE_LEVEL_MUTATION")

    sample = ruleset.get("sample_and_reveal") or {}
    if sample.get("first_checkpoint_event_family_minima") != {
        "US_CPI": 10,
        "US_EMPLOYMENT_SITUATION": 10,
        "FOMC_STATEMENT": 6,
    }:
        blockers.append("EVENT_SAMPLE_GATE_MUTATION")
    if sample.get("classified_state_minima") != {
        "ACCEPTANCE_event_asset_units": 10,
        "REJECTION_event_asset_units": 10,
        "distinct_classified_events": 20,
    }:
        blockers.append("STATE_SAMPLE_GATE_MUTATION")
    if sample.get("repeated_outcome_looks_allowed") is not False:
        blockers.append("REPEATED_OUTCOME_LOOKS_FORBIDDEN")

    economics = ruleset.get("economics") or {}
    if economics.get("tested") is not False or economics.get("pnl") is not False:
        blockers.append("ECONOMICS_NOT_AUTHORIZED")
    if economics.get("trading_actions") is not False:
        blockers.append("TRADING_ACTIONS_NOT_AUTHORIZED")

    contamination = ruleset.get("contamination") or {}
    for field in (
        "historical_internal_macro_outcomes_allowed_for_selection",
        "post_outcome_threshold_tuning_allowed",
        "subgroup_rescue_allowed",
        "alternative_horizon_rescue_allowed",
        "promotion_credit_inherited",
    ):
        if contamination.get(field) is not False:
            blockers.append(f"CONTAMINATION_BOUNDARY_CHANGED:{field}")

    return not blockers, tuple(sorted(set(blockers)))


def main() -> int:
    ruleset = json.loads(RULESET_PATH.read_text(encoding="utf-8"))
    authority = json.loads(AUTHORITY_PATH.read_text(encoding="utf-8"))
    classifier = json.loads(CLASSIFIER_SPEC_PATH.read_text(encoding="utf-8"))
    ready, blockers = validate_h02_ruleset(
        ruleset,
        authority,
        classifier,
        MEASUREMENT_CATALOG_PATH.read_bytes(),
    )
    print(json.dumps({
        "gate": "MRCR_H02_FROZEN_RULESET_V01",
        "ready": ready,
        "ruleset_sha256": ruleset.get("ruleset_sha256"),
        "blockers": list(blockers),
        "target_observation_authorized": False,
    }, sort_keys=True))
    return 0 if ready else 2


if __name__ == "__main__":
    raise SystemExit(main())
