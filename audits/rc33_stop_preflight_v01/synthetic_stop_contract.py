"""Synthetic MEXC RC3.3 native-stop risk contract (NOT installed-engine tests).

No network, broker client, authenticated GET, POST, order, import of engine.py,
or local execution side effect. An accepted MOCK never certifies real protection.
"""
from __future__ import annotations
from dataclasses import dataclass
import math
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class Evidence:
    code: str
    mock_readback_accepted: bool
    live_go: bool = False
    brokerage_certified: bool = False


def reconcile_mock_snapshot(
    *,
    position: Mapping[str, Any] | None,
    stops: Sequence[Mapping[str, Any]],
    symbol: str,
    position_id: int,
    expected_volume: float,
    expected_stop_price: float,
    price_unit: float,
    snapshot_age_seconds: float,
    partial_fill: bool = False,
    pending_mutation: bool = False,
    ambiguous_exchange_response: bool = False,
    after_restart: bool = False,
) -> Evidence:
    """Reference safety invariants for future adapter-specific regression tests."""
    def fail(code: str) -> Evidence:
        return Evidence(code, False)

    if after_restart and pending_mutation:
        return fail("RESTART_UNRESOLVED_MUTATION_NO_RESEND")
    if ambiguous_exchange_response or pending_mutation:
        return fail("UNKNOWN_BROKER_OUTCOME_NO_BLIND_RETRY")
    if not math.isfinite(float(snapshot_age_seconds)) or snapshot_age_seconds < 0 or snapshot_age_seconds > 5:
        return fail("BROKER_SNAPSHOT_STALE")
    if partial_fill:
        return fail("PARTIAL_FILL_REQUIRES_EXPLICIT_COVERAGE_RECONCILIATION")
    if (position is None or not all(math.isfinite(x) and x > 0 for x in
            (float(expected_volume), float(expected_stop_price), float(price_unit)))
            or position_id <= 0):
        return fail("UNVERIFIED_POSITION_OR_GEOMETRY")
    if position.get("symbol") != symbol or position.get("positionId") != position_id:
        return fail("BROKER_POSITION_IDENTITY_MISMATCH")
    if position.get("positionType") != 1:  # This reference model covers LONG only.
        return fail("UNSUPPORTED_POSITION_SIDE")
    try:
        hold = float(position.get("holdVol", 0))
    except (ValueError, TypeError):
        return fail("POSITION_VOLUME_INVALID")
    if not math.isfinite(hold) or hold <= 0 or abs(hold - expected_volume) > 1e-9:
        return fail("POSITION_VOLUME_MISMATCH")
    matching = [s for s in stops if s.get("positionId") == position_id
                and s.get("symbol") == symbol and s.get("isFinished") == 0]
    if len(matching) != 1:
        return fail("BROKER_STOP_MISSING_OR_MULTIPLE")
    st = matching[0]
    try:
        vol = float(st.get("vol", 0))
        price = float(st.get("stopLossPrice", 0))
        tp = float(st.get("takeProfitPrice", 0) or 0)
    except (ValueError, TypeError):
        return fail("STOP_FIELDS_INVALID")
    if not all(math.isfinite(x) for x in (vol, price, tp)):
        return fail("STOP_FIELDS_INVALID")
    if vol <= 0 or vol < hold:
        return fail("STOP_NOT_COVERING_FULL_POSITION")
    if vol > hold + 1e-9:
        return fail("STOP_VOLUME_EXCEEDS_POSITION")
    if price <= 0 or abs(price - expected_stop_price) > max(price_unit * .501, expected_stop_price * 1e-7):
        return fail("STOP_READBACK_PRICE_MISMATCH")
    if tp != 0:
        return fail("UNEXPECTED_TAKE_PROFIT")
    # This is deliberately not a LIVE certification; only a MOCK shape invariant.
    return Evidence("MOCK_STOP_READBACK_SHAPE_ACCEPTED_ONLY", True)


def uncertain_post_action(response_category: str, *, pending_journal: bool) -> str:
    """A missed, timed-out or ambiguous write must never trigger a blind resend."""
    if pending_journal or response_category not in ("DEFINITIVELY_NOT_SENT", "RECONCILED_BROKER_RECEIPT"):
        return "HALT_AND_RECONCILE_NO_RESEND"
    if response_category == "DEFINITIVELY_NOT_SENT":
        return "FRESH_INDEPENDENT_PREFLIGHT_REQUIRED"
    return "RECEIPT_REVIEW_REQUIRED"


def required_external_proofs() -> list[str]:
    return [
        "VENUE_NATIVE_STOP_NOT_ATOMICALLY_CERTIFIED",
        "FILLED_AND_PARTIALLY_FILLED_VOLUMES",
        "POSITION_ID_AND_SIDE_WITH_STOP_READBACK",
        "NETWORK_TIMEOUT_AND_UNKNOWN_POST_OUTCOME",
        "RESTART_RECONCILIATION_WITH_NO_BLIND_RESEND",
        "STOP_AMEND_AND_STOP_TRIGGER_SETTLEMENT",
        "INDEPENDENT_BROKER_ACCOUNT_AND_ORDER_RECONCILIATION",
        "STOP_PROTECTED_BEFORE_ANY_LIVE_AUTHORITY",
    ]
