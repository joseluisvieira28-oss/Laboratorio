"""Build the final MRCR pretarget protocol from immutable frozen inputs.

This builder cannot authorize target observation. It assembles a target-locked
protocol only after a complete official calendar manifest exists.
"""

from __future__ import annotations

from typing import Any, Mapping

from h02_calendar_binding import validate_h02_calendar_manifest
from pretarget_gate import protocol_fingerprint, validate_for_freeze


def build_final_protocol(
    *,
    ruleset: Mapping[str, Any],
    calendar_manifest: Mapping[str, Any],
    implementation_head_sha: str,
    calendar_frozen_at_utc: str,
    protocol_frozen_at_utc: str,
    authority_receipt_sha256: str,
) -> dict[str, Any]:
    calendar_ready, blockers = validate_h02_calendar_manifest(
        calendar_manifest,
        ruleset=ruleset,
    )
    if not calendar_ready:
        raise ValueError("CALENDAR_NOT_READY:" + ",".join(blockers))

    if ruleset.get("status") != "FROZEN_RULESET__CALENDAR_BINDING_PENDING":
        raise ValueError("frozen H02 ruleset is required")
    if ruleset.get("authority_receipt_sha256") != authority_receipt_sha256:
        raise ValueError("authority receipt does not match frozen ruleset")
    if not isinstance(implementation_head_sha, str) or len(implementation_head_sha) != 40:
        raise ValueError("implementation_head_sha must be a 40-character commit SHA")
    if not calendar_frozen_at_utc or not protocol_frozen_at_utc:
        raise ValueError("freeze timestamps are required")

    event_scope = ruleset["event_scope"]
    if calendar_manifest.get("event_families") != event_scope["event_families"]:
        raise ValueError("calendar event families differ from frozen ruleset")

    market = ruleset["market_scope"]
    state = ruleset["decision_state"]
    hypothesis = ruleset["hypothesis"]
    outcome = ruleset["outcome"]
    economics = ruleset["economics"]

    native_symbols = []
    for venue in ("BINANCE_SPOT", "COINBASE_ADVANCED_SPOT"):
        mapping = market["venues"][venue]
        for asset in market["assets"]:
            native_symbols.append({
                "asset": asset,
                "venue": venue,
                "symbol": mapping[asset],
            })

    protocol = {
        "document_type": "MRCR_PRETARGET_PROTOCOL_V01",
        "lab_id": "MARKET-REVEAL-CONFIRMATION-REACTION-001",
        "status": "FROZEN_PRETARGET_PROTOCOL__TARGET_LOCKED",
        "protocol_version": "0.1",
        "governance": {
            "h02_authorized": True,
            "target_observation_authorized": False,
            "historical_contaminated_data_allowed_for_selection": False,
            "earliest_target_period": "2027",
        },
        "calendar": {
            "complete_official_calendar": True,
            "calendar_source_manifest_sha256": calendar_manifest["manifest_sha256"],
            "calendar_frozen_at_utc": calendar_frozen_at_utc,
            "event_families": list(event_scope["event_families"]),
        },
        "market_scope": {
            "venues": ["BINANCE_SPOT", "COINBASE_ADVANCED_SPOT"],
            "native_symbols": native_symbols,
            "cross_venue_merge_allowed": False,
        },
        "decision_state": {
            "anchor_definition": state["pre_anchor_definition"],
            "decision_clock_seconds": state["decision_clock_seconds"],
            "availability_rule": state["availability_rule"],
            "depth_definition": dict(state["depth_definition"]),
            "measurement_catalog_sha256": state["measurement_catalog_sha256"],
            "implementation_head_sha": implementation_head_sha,
        },
        "hypothesis": {
            "causal_statement": hypothesis["causal_statement"],
            "classifier_definition": (
                "H02_CLASSIFIER_SPEC_V01:"
                + state["classifier_spec_sha256"]
            ),
            "classifier_sha256": state["classifier_spec_sha256"],
            "abstention_rule": hypothesis["abstention_rule"],
        },
        "outcome": {
            "future_horizon_seconds": outcome["future_horizon_seconds"],
            "outcome_definition": (
                outcome["venue_outcome"]
                + "; asset aggregation: "
                + outcome["asset_outcome"]
            ),
            "benchmark_definition": (
                "Primary benchmark is frozen REJECTION state in the same "
                "event/asset universe; statistic = "
                + outcome["primary_statistic"]
            ),
        },
        "economics": {
            "tested": economics["tested"],
            "fee_model": economics["fee_model"],
            "slippage_model": economics["slippage_model"],
            "latency_model": economics["latency_model"],
        },
        "freeze": {
            "protocol_fingerprint_sha256": None,
            "ruleset_sha256": ruleset["ruleset_sha256"],
            "frozen_at_utc": protocol_frozen_at_utc,
            "operator_authority_receipt": authority_receipt_sha256,
        },
    }
    protocol["freeze"]["protocol_fingerprint_sha256"] = protocol_fingerprint(protocol)

    result = validate_for_freeze(protocol)
    if not result.ready:
        raise RuntimeError("built protocol failed structural gate:" + ",".join(result.blockers))
    return protocol
