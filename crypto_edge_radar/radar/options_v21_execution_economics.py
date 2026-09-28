from __future__ import annotations

import json
from pathlib import Path
from typing import Any

BASE_COST_BPS = 10.0
STRESS_COST_BPS = 20.0
OOS_NET10_BPS = 5.0427663334
OOS_NET20_BPS = -4.6759378383
BTC_USDT_CONTRACT_SIZE_BTC = 0.0001
CURRENT_MEXC_API_TAKER_BPS_PER_FILL = 8.0


class ExecutionEconomicsError(RuntimeError):
    pass


def _load(path: Path) -> dict[str, Any]:
    row = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(row, dict):
        raise ExecutionEconomicsError(f"object required: {path}")
    return row


def oos_reference() -> dict[str, float]:
    avg_weight = (OOS_NET10_BPS - OOS_NET20_BPS) / (STRESS_COST_BPS - BASE_COST_BPS)
    gross_mean = OOS_NET10_BPS + BASE_COST_BPS * avg_weight
    return {
        "average_executed_weight_implied": avg_weight,
        "gross_mean_bps_per_parent_opportunity_implied": gross_mean,
    }


def oos_net_at_full_notional_cost(cost_bps: float) -> float:
    ref = oos_reference()
    return ref["gross_mean_bps_per_parent_opportunity_implied"] - cost_bps * ref["average_executed_weight_implied"]


def fee_bps(fee_usdt: float, notional_usdt: float) -> float:
    if notional_usdt > 0:
        return abs(float(fee_usdt)) / float(notional_usdt) * 10000.0
    raise ExecutionEconomicsError("notional must be positive")


def _order(payload: dict[str, Any]) -> dict[str, Any]:
    row = payload.get("order")
    if not isinstance(row, dict):
        raise ExecutionEconomicsError("receipt missing order object")
    return row


def _order_fee(order: dict[str, Any]) -> float:
    if order.get("totalFee") is not None:
        return abs(float(order.get("totalFee") or 0))
    return abs(float(order.get("takerFee", 0) or 0)) + abs(float(order.get("makerFee", 0) or 0))


def _order_notional(order: dict[str, Any], contract_size_btc: float) -> float:
    px = float(order.get("dealAvgPrice") or order.get("price") or 0)
    vol = float(order.get("dealVol") or order.get("vol") or 0)
    if px <= 0 or vol <= 0:
        raise ExecutionEconomicsError("order missing positive dealAvgPrice/dealVol")
    return px * vol * contract_size_btc


def _slippage_bps(*, direction: str, leg: str, actual: float, bid: float, ask: float) -> float:
    if min(actual, bid, ask) <= 0:
        raise ExecutionEconomicsError("invalid slippage prices")
    if leg == "entry":
        expected = ask if direction == "LONG" else bid
        return ((actual - expected) / expected * 10000.0) if direction == "LONG" else ((expected - actual) / expected * 10000.0)
    expected = bid if direction == "LONG" else ask
    return ((expected - actual) / expected * 10000.0) if direction == "LONG" else ((actual - expected) / expected * 10000.0)


def analyze_session(session_dir: str | Path, *, contract_size_btc: float = BTC_USDT_CONTRACT_SIZE_BTC) -> dict[str, Any]:
    root = Path(session_dir)
    names = {
        "signal": "CANONICAL_EXECUTION_SIGNAL.json",
        "intent": "ORDER_INTENT.json",
        "pre_order": "PRE_ORDER_GATE.json",
        "entry_fill": "FILL_RECEIPT.json",
        "active": "ACTIVE_TRADE_STATE.json",
        "exit_intent": "EXIT_INTENT.json",
        "pre_exit": "PRE_EXIT_MARKET_SNAPSHOT.json",
        "exit_fill": "EXIT_FILL_RECEIPT.json",
        "recon": "POST_TRADE_RECONCILIATION.json",
    }
    missing = [name for name in names.values() if not (root / name).exists()]
    if missing:
        return {
            "status": "EVIDENCE_INCOMPLETE",
            "session": str(root),
            "missing_receipts": missing,
            "economic_verdict_allowed": False,
        }

    signal = _load(root / names["signal"])
    intent = _load(root / names["intent"])
    pre = _load(root / names["pre_order"])
    entry_receipt = _load(root / names["entry_fill"])
    active = _load(root / names["active"])
    exit_intent = _load(root / names["exit_intent"])
    pre_exit = _load(root / names["pre_exit"])
    exit_receipt = _load(root / names["exit_fill"])
    recon = _load(root / names["recon"])

    identities = {
        str(signal.get("immutable_signal_key")),
        str(intent.get("signal_identity")),
        str(active.get("signal_identity")),
        str(exit_intent.get("signal_identity")),
        str(recon.get("signal_identity")),
    }
    if len(identities) != 1 or "None" in identities:
        return {
            "status": "EVIDENCE_IDENTITY_MISMATCH",
            "session": str(root),
            "identities": sorted(identities),
            "economic_verdict_allowed": False,
        }

    direction = str(active.get("direction"))
    entry_order = _order(entry_receipt)
    exit_order = _order(exit_receipt)
    entry_notional = _order_notional(entry_order, contract_size_btc)
    exit_notional = _order_notional(exit_order, contract_size_btc)
    reference_notional = (entry_notional + exit_notional) / 2.0

    entry_fee = _order_fee(entry_order)
    exit_fee = _order_fee(exit_order)
    total_fee = entry_fee + exit_fee
    round_trip_fee_bps = total_fee / reference_notional * 10000.0

    entry_price = float(entry_order.get("dealAvgPrice"))
    exit_price = float(exit_order.get("dealAvgPrice"))
    entry_slippage = _slippage_bps(
        direction=direction,
        leg="entry",
        actual=entry_price,
        bid=float(pre["bid"]),
        ask=float(pre["ask"]),
    )

    exit_slippage = None
    if pre_exit.get("capture_error") is None and pre_exit.get("bid") and pre_exit.get("ask"):
        exit_slippage = _slippage_bps(
            direction=direction,
            leg="exit",
            actual=exit_price,
            bid=float(pre_exit["bid"]),
            ask=float(pre_exit["ask"]),
        )

    funding_usdt = float(recon.get("funding_hold_fee_usdt", 0) or 0)
    net_usdt = float(recon.get("realized_net_pnl_usdt", 0) or 0)
    gross_close_usdt = float(recon.get("gross_close_profit_usdt", 0) or 0)

    fee_bucket = (
        "FEE_ONLY_AT_OR_BELOW_BASE10"
        if round_trip_fee_bps <= BASE_COST_BPS
        else "FEE_ONLY_BETWEEN_BASE10_AND_STRESS20"
        if round_trip_fee_bps <= STRESS_COST_BPS
        else "FEE_ONLY_ABOVE_STRESS20"
    )

    return {
        "status": "COMPLETE_EXECUTION_ECONOMICS",
        "economic_verdict_allowed": True,
        "signal_identity": identities.pop(),
        "direction": direction,
        "entry_order_id": entry_order.get("orderId"),
        "exit_order_id": exit_order.get("orderId"),
        "entry_external_oid": intent.get("external_oid"),
        "exit_external_oid": exit_intent.get("external_oid"),
        "entry_notional_usdt": entry_notional,
        "exit_notional_usdt": exit_notional,
        "reference_notional_usdt": reference_notional,
        "entry_fee_usdt": entry_fee,
        "exit_fee_usdt": exit_fee,
        "round_trip_fee_bps_on_position": round_trip_fee_bps,
        "entry_slippage_bps_vs_preorder_touch": entry_slippage,
        "exit_slippage_bps_vs_preexit_touch": exit_slippage,
        "funding_effect_usdt": funding_usdt,
        "funding_effect_bps": funding_usdt / reference_notional * 10000.0,
        "gross_close_profit_usdt": gross_close_usdt,
        "realized_net_pnl_usdt": net_usdt,
        "realized_net_bps_on_position": net_usdt / reference_notional * 10000.0,
        "fee_bucket": fee_bucket,
        "oos_reference": {
            **oos_reference(),
            "net10_bps_per_parent_opportunity": OOS_NET10_BPS,
            "net20_bps_per_parent_opportunity": OOS_NET20_BPS,
            "implied_net_at_16bps_full_notional_cost": oos_net_at_full_notional_cost(16.0),
        },
        "note": "Slippage diagnostics are not added again to realized PnL; realized fill prices already embody execution price effects.",
    }


def observed_fill_fee_summary(rows: list[dict[str, float]]) -> dict[str, float]:
    if not rows:
        raise ExecutionEconomicsError("at least one row required")
    total_notional = sum(float(r["notional_usdt"]) for r in rows)
    total_fee = sum(abs(float(r["fee_usdt"])) for r in rows)
    if total_notional <= 0:
        raise ExecutionEconomicsError("total notional must be positive")
    weighted_fill_fee_bps = total_fee / total_notional * 10000.0
    return {
        "fills": float(len(rows)),
        "total_notional_usdt": total_notional,
        "total_fee_usdt": total_fee,
        "weighted_fill_fee_bps": weighted_fill_fee_bps,
        "two_fill_round_trip_equivalent_bps": weighted_fill_fee_bps * 2.0,
    }


__all__ = [
    "analyze_session",
    "observed_fill_fee_summary",
    "oos_reference",
    "oos_net_at_full_notional_cost",
    "fee_bps",
]
