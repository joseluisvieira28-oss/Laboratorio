"""Research-only three-gate audit; never an authority to trade or arm an executor.

Diagnostic inputs are externally prepared evidence summaries, NOT trusted authority
tokens. Synthetic PASS means only that a review package is internally complete.
The live executor must never import this module to grant entry permission.
"""
from __future__ import annotations

from datetime import datetime, timezone
import math
import re
from typing import Any, Mapping

SHA256 = re.compile(r"^[a-fA-F0-9]{64}$")
FINAL_SCIENCE_PASS = "INDEPENDENT_FORWARD_ECONOMIC_PASS"


def _sha(value: Any) -> bool:
    return isinstance(value, str) and SHA256.fullmatch(value) is not None


def _true(row: Mapping[str, Any], key: str) -> bool:
    return row.get(key) is True


def _finite(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        val = float(value)
    except (ValueError, TypeError):
        return None
    return val if math.isfinite(val) else None


def audit_three_gates(candidate_id: str, evidence: Mapping[str, Any]) -> dict[str, Any]:
    """Assess a preexisting evidence package without reading prices, accounts or secrets."""
    flags: dict[str, list[str]] = {"science": [], "economics": [], "execution": []}
    if not isinstance(evidence, Mapping):
        evidence = {}
    if not candidate_id or evidence.get("candidate_id") != candidate_id:
        flags["science"].append("CANDIDATE_IDENTITY_NOT_BOUND")

    scientific = evidence.get("science")
    if not isinstance(scientific, Mapping):
        scientific = {}
    if scientific.get("verdict") != FINAL_SCIENCE_PASS:
        flags["science"].append("NO_INDEPENDENT_FORWARD_ECONOMIC_PASS")
    for field in ("first_freeze_sha256", "forward_receipt_sha256"):
        if not _sha(scientific.get(field)):
            flags["science"].append(field.upper() + "_MISSING")
    for field in ("receipt_provenance_verified", "sample_and_date_gate_pass",
                  "holdout_and_no_lookahead_pass", "independent_forward_gate_pass"):
        if not _true(scientific, field):
            flags["science"].append(field.upper() + "_NOT_PROVEN")

    economics = evidence.get("economics")
    if not isinstance(economics, Mapping):
        economics = {}
    if economics.get("route_status") != "COMPLETE_ACCOUNT_AND_EXECUTION_COST_RECEIPT":
        flags["economics"].append("ACCOUNT_ROUTE_COSTS_NOT_VERIFIED")
    for field in ("fees_from_account_readonly", "spread_and_slippage_included",
                  "funding_included", "market_impact_included", "venue_minimums_pass",
                  "cost_receipt_pre_outcome_frozen", "captured_at_frozen_entry_boundary"):
        if not _true(economics, field):
            flags["economics"].append(field.upper() + "_NOT_VERIFIED")
    edge = _finite(economics.get("independent_forward_net_expectancy_bps"))
    if edge is None or edge <= 0:
        flags["economics"].append("POSITIVE_FORWARD_NET_EXPECTANCY_NOT_PROVEN")
    cost = _finite(economics.get("all_in_roundtrip_cost_bps"))
    if cost is None or cost < 0:
        flags["economics"].append("VALID_ALL_IN_ROUTE_COST_MISSING")
    if not _sha(economics.get("account_route_receipt_sha256")):
        flags["economics"].append("ROUTE_RECEIPT_HASH_MISSING")

    execution = evidence.get("execution")
    if not isinstance(execution, Mapping):
        execution = {}
    for field in ("pc_running_readonly_verified", "current_account_positions_orders_tpsl_reconciled",
                  "supervisor_and_scheduled_task_fresh", "single_owner_no_duplicate_writers",
                  "global_slot_persistent_and_consistent", "order_ack_and_recovery_verified",
                  "exchange_hosted_exit_if_required", "current_risk_firewall_pass",
                  "no_unresolved_intents", "symbol_leverage_notional_minimums_pass",
                  "protective_loss_bounds_explicit", "bundle_integrity_verified"):
        if not _true(execution, field):
            flags["execution"].append(field.upper() + "_NOT_VERIFIED")
    if not _sha(execution.get("installed_exe_sha256")):
        flags["execution"].append("INSTALLED_EXE_HASH_NOT_VERIFIED")
    if not _sha(execution.get("approved_exe_sha256")):
        flags["execution"].append("APPROVED_EXE_HASH_NOT_VERIFIED")
    if execution.get("installed_exe_sha256") != execution.get("approved_exe_sha256"):
        flags["execution"].append("DEPLOYED_BINARY_DIFFERS_FROM_APPROVED")
    if execution.get("live_account_state") != "FRESH_AUTHENTICATED_READ_ONLY":
        flags["execution"].append("ACTUAL_ACCOUNT_STATE_UNKNOWN")
    # Historical interruption receipts must be independently adjudicated; current
    # bucket CONTINUOUS cannot erase earlier missing windows.
    if execution.get("historical_gap_review") != "COMPLETE_EVIDENCE_RECONCILIATION":
        flags["execution"].append("HISTORICAL_RUNTIME_GAPS_NOT_RECONCILED")

    states = {gate: ("DOCUMENTED" if not reasons else "BLOCKED")
              for gate, reasons in flags.items()}
    all_documented = all(x == "DOCUMENTED" for x in states.values())
    return {
        "schema": "CRYPTO_RADAR_THREE_GATE_AUDIT_V0.1",
        "candidate_id": candidate_id,
        "gates": states,
        "blockers": {key: reasons for key, reasons in flags.items() if reasons},
        "status": "REVIEW_PACKAGE_COMPLETE__NO_TRADE_AUTHORITY"
                  if all_documented else "NO_GO__EVIDENCE_INCOMPLETE",
        "automatic_live_authorization": False,
        "orders_created": False,
        "exchange_mutation_performed": False,
        "account_read_performed": False,
        "scientific_rules_changed": False,
        "main_merge": False,
    }


def classify_public_shadow_health(*, cycle_errors: Mapping[str, Any],
                                  ced1d_status: str | None,
                                  persisted_gap_receipts: int | None) -> dict[str, Any]:
    """Pure visibility classifier; does not modify scientific timing or signals."""
    reasons: list[str] = []
    if cycle_errors:
        reasons.append("CURRENT_CYCLE_ERRORS")
    if ced1d_status in {"FAIL_CLOSED", "SOURCE_BLOCKED", "ERROR"}:
        reasons.append("CED1D_COLLECTOR_FAIL_CLOSED")
    if persisted_gap_receipts is None:
        reasons.append("GAP_HISTORY_UNVERIFIED")
    elif persisted_gap_receipts > 0:
        reasons.append("HISTORICAL_LIVENESS_GAP_RECEIPTS_REQUIRE_REVIEW")
    return {
        "status": "OK" if not reasons else "DEGRADED_FAIL_CLOSED",
        "operational_attention_required": bool(reasons),
        "reasons": reasons,
        "persisted_gap_receipts": persisted_gap_receipts,
        "automatic_live_authorization": False,
        "scientific_rules_changed": False,
    }
