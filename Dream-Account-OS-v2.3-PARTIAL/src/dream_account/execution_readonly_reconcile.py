from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from enum import Enum

from .execution_mexc_readonly import ReadOnlyReconciliationSnapshot, SpotOrder, SpotTrade


LAB_CLIENT_ORDER_PREFIX = "DAOS-"
MAX_RECONCILIATION_CLOCK_SKEW_MS = 5_000


class ReconciliationVerdict(str, Enum):
    CLEAR = "CLEAR"
    DIVERGENCE = "DIVERGENCE"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class ReadOnlyReconciliationReport:
    verdict: ReconciliationVerdict
    symbol: str
    snapshot_fingerprint: str
    reasons: tuple[str, ...]
    lab_open_order_ids: tuple[str, ...]
    lab_trade_ids: tuple[str, ...]

    def fingerprint(self) -> str:
        payload = asdict(self)
        payload["verdict"] = self.verdict.value
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()


def _is_lab_order(order: SpotOrder) -> bool:
    return bool(order.client_order_id) and order.client_order_id.startswith(LAB_CLIENT_ORDER_PREFIX)


def _is_lab_trade(trade: SpotTrade) -> bool:
    return bool(trade.client_order_id) and trade.client_order_id.startswith(LAB_CLIENT_ORDER_PREFIX)


def assess_shadow_exchange_state(snapshot: ReadOnlyReconciliationSnapshot) -> ReadOnlyReconciliationReport:
    """Compare Gate K's SHADOW invariant with authenticated exchange state.

    In Gate K no Dream Account order may exist on MEXC. We therefore reserve a
    client-order namespace and fail closed if any exchange order/fill bearing that
    namespace is observed. Account-level canTrade/canWithdraw flags are deliberately
    not treated as API-key permissions because the account response describes account
    capabilities, not a proof that the supplied API key has write scope.
    """
    reasons: list[str] = []

    if snapshot.account.account_type.upper() != "SPOT":
        reasons.append("unexpected_account_type")
    if abs(snapshot.clock_skew_ms) > MAX_RECONCILIATION_CLOCK_SKEW_MS:
        reasons.append("clock_skew_exceeds_gate")

    lab_orders = [order for order in snapshot.open_orders if _is_lab_order(order)]
    if snapshot.queried_order is not None and _is_lab_order(snapshot.queried_order):
        if all(order.order_id != snapshot.queried_order.order_id for order in lab_orders):
            lab_orders.append(snapshot.queried_order)
    lab_trades = [trade for trade in snapshot.recent_trades if _is_lab_trade(trade)]

    if lab_orders:
        reasons.append("unexpected_lab_exchange_order")
    if lab_trades:
        reasons.append("unexpected_lab_exchange_fill")

    hard_divergence = {
        "unexpected_lab_exchange_order",
        "unexpected_lab_exchange_fill",
    }
    if any(reason in hard_divergence for reason in reasons):
        verdict = ReconciliationVerdict.DIVERGENCE
    elif reasons:
        verdict = ReconciliationVerdict.BLOCKED
    else:
        verdict = ReconciliationVerdict.CLEAR

    return ReadOnlyReconciliationReport(
        verdict=verdict,
        symbol=snapshot.symbol,
        snapshot_fingerprint=snapshot.fingerprint(),
        reasons=tuple(reasons),
        lab_open_order_ids=tuple(sorted({order.order_id for order in lab_orders})),
        lab_trade_ids=tuple(sorted({trade.trade_id for trade in lab_trades})),
    )
