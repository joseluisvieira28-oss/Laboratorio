from __future__ import annotations

import json
import math
import statistics
from pathlib import Path
from typing import Any

BASE_COST_BPS = 10.0
STRESS_COST_BPS = 20.0
OOS_NET10_BPS = 5.0427663334
OOS_NET20_BPS = -4.6759378383
BTC_USDT_CONTRACT_SIZE_BTC = 0.0001
CURRENT_MEXC_API_TAKER_BPS_PER_FILL = 8.0
MIN_EXECUTION_ECONOMICS_TRADES = 10


class ExecutionEconomicsError(RuntimeError):
    pass


def _load(path: Path) -> dict[str, Any]:
    row = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(row, dict):
        raise ExecutionEconomicsError(f"object required: {path}")
    return row


def _load_optional(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return _load(path)


def _finite_float(value: Any, default: float | None = None) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    return out if math.isfinite(out) else default


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
    total_fee: float | None = None
    if order.get("totalFee") is not None:
        try:
            total_fee = abs(float(order.get("totalFee") or 0))
            if total_fee > 0:
                return total_fee
        except (TypeError, ValueError):
            total_fee = None

    component_total = 0.0
    for key in ("takerFee", "makerFee"):
        try:
            component_total += abs(float(order.get(key, 0) or 0))
        except (TypeError, ValueError):
            pass
    if component_total > 0:
        return component_total
    return total_fee or 0.0


def _order_notional(order: dict[str, Any], contract_size_btc: float) -> float:
    px = float(order.get("dealAvgPrice") or order.get("price") or 0)
    vol = float(order.get("dealVol") or order.get("vol") or 0)
    if px <= 0 or vol <= 0 or contract_size_btc <= 0:
        raise ExecutionEconomicsError("order/contract size missing positive dealAvgPrice/dealVol")
    return px * vol * contract_size_btc


def _slippage_bps(*, direction: str, leg: str, actual: float, bid: float, ask: float) -> float:
    if min(actual, bid, ask) <= 0:
        raise ExecutionEconomicsError("invalid slippage prices")
    if direction not in {"LONG", "SHORT"} or leg not in {"entry", "exit"}:
        raise ExecutionEconomicsError("invalid direction/leg for slippage")
    if leg == "entry":
        expected = ask if direction == "LONG" else bid
        return ((actual - expected) / expected * 10000.0) if direction == "LONG" else ((expected - actual) / expected * 10000.0)
    expected = bid if direction == "LONG" else ask
    return ((expected - actual) / expected * 10000.0) if direction == "LONG" else ((actual - expected) / expected * 10000.0)


def _spread_bps(bid: float, ask: float) -> float:
    if min(bid, ask) <= 0 or ask < bid:
        raise ExecutionEconomicsError("invalid spread prices")
    mid = (bid + ask) / 2.0
    return (ask - bid) / mid * 10000.0


def _snapshot_prices(row: dict[str, Any] | None) -> tuple[float, float] | None:
    if not row or row.get("capture_error") is not None:
        return None
    bid = _finite_float(row.get("bid"))
    ask = _finite_float(row.get("ask"))
    if bid is None or ask is None or bid <= 0 or ask <= 0:
        return None
    return bid, ask


def _mean(values: list[float]) -> float | None:
    return statistics.fmean(values) if values else None


def _median(values: list[float]) -> float | None:
    return statistics.median(values) if values else None


def _p90(values: list[float]) -> float | None:
    if not values:
        return None
    xs = sorted(values)
    if len(xs) == 1:
        return xs[0]
    pos = 0.90 * (len(xs) - 1)
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return xs[lo]
    frac = pos - lo
    return xs[lo] * (1.0 - frac) + xs[hi] * frac


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
            "per_trade_economic_decomposition_allowed": False,
            "strategy_economic_verdict_allowed": False,
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
    pre_entry = _load_optional(root / "PRE_ENTRY_MARKET_SNAPSHOT.json")

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
            "per_trade_economic_decomposition_allowed": False,
            "strategy_economic_verdict_allowed": False,
        }

    direction = str(active.get("direction"))
    if direction not in {"LONG", "SHORT"}:
        raise ExecutionEconomicsError("active receipt has invalid direction")

    dynamic_contract_size = _finite_float(active.get("contract_size"), _finite_float(pre.get("contract_size")))
    resolved_contract_size = dynamic_contract_size or float(contract_size_btc)

    entry_order = _order(entry_receipt)
    exit_order = _order(exit_receipt)
    entry_notional = _order_notional(entry_order, resolved_contract_size)
    exit_notional = _order_notional(exit_order, resolved_contract_size)
    average_fill_notional = (entry_notional + exit_notional) / 2.0

    entry_fee = _order_fee(entry_order)
    exit_fee = _order_fee(exit_order)
    entry_fee_bps = fee_bps(entry_fee, entry_notional)
    exit_fee_bps = fee_bps(exit_fee, exit_notional)
    round_trip_fee_bps = entry_fee_bps + exit_fee_bps

    entry_price = float(entry_order.get("dealAvgPrice"))
    exit_price = float(exit_order.get("dealAvgPrice"))

    entry_snap = _snapshot_prices(pre_entry)
    if entry_snap is not None:
        entry_bid, entry_ask = entry_snap
        entry_reference_source = "PRE_ENTRY_MARKET_SNAPSHOT"
    else:
        entry_bid, entry_ask = float(pre["bid"]), float(pre["ask"])
        entry_reference_source = "PRE_ORDER_GATE_FALLBACK"

    entry_slippage = _slippage_bps(
        direction=direction,
        leg="entry",
        actual=entry_price,
        bid=entry_bid,
        ask=entry_ask,
    )
    entry_spread = _spread_bps(entry_bid, entry_ask)

    exit_snap = _snapshot_prices(pre_exit)
    exit_slippage = None
    exit_spread = None
    if exit_snap is not None:
        exit_bid, exit_ask = exit_snap
        exit_slippage = _slippage_bps(
            direction=direction,
            leg="exit",
            actual=exit_price,
            bid=exit_bid,
            ask=exit_ask,
        )
        exit_spread = _spread_bps(exit_bid, exit_ask)

    funding_usdt = float(recon.get("funding_hold_fee_usdt", 0) or 0)
    net_usdt = float(recon.get("realized_net_pnl_usdt", 0) or 0)
    gross_close_usdt = float(recon.get("gross_close_profit_usdt", 0) or 0)
    funding_effect_bps = funding_usdt / entry_notional * 10000.0
    gross_bps = gross_close_usdt / entry_notional * 10000.0
    realized_net_bps = net_usdt / entry_notional * 10000.0

    expected_net = gross_close_usdt + funding_usdt - entry_fee - exit_fee
    identity_error = net_usdt - expected_net
    accounting_identity_pass = abs(identity_error) <= 1e-9

    fee_bucket = (
        "FEE_ONLY_AT_OR_BELOW_BASE10"
        if round_trip_fee_bps <= BASE_COST_BPS
        else "FEE_ONLY_BETWEEN_BASE10_AND_STRESS20"
        if round_trip_fee_bps <= STRESS_COST_BPS
        else "FEE_ONLY_ABOVE_STRESS20"
    )

    status = "COMPLETE_EXECUTION_ECONOMICS" if accounting_identity_pass else "ACCOUNTING_IDENTITY_MISMATCH"
    per_trade_allowed = accounting_identity_pass

    return {
        "status": status,
        "session": str(root),
        "per_trade_economic_decomposition_allowed": per_trade_allowed,
        "strategy_economic_verdict_allowed": False,
        "economic_verdict_scope": "TRADE_ONLY" if per_trade_allowed else "NONE",
        "signal_identity": next(iter(identities)),
        "direction": direction,
        "contract_size_btc": resolved_contract_size,
        "contract_size_source": "EXECUTOR_RECEIPT" if dynamic_contract_size else "FROZEN_BTC_USDT_FALLBACK",
        "entry_order_id": entry_order.get("orderId"),
        "exit_order_id": exit_order.get("orderId"),
        "entry_external_oid": intent.get("external_oid"),
        "exit_external_oid": exit_intent.get("external_oid"),
        "entry_notional_usdt": entry_notional,
        "exit_notional_usdt": exit_notional,
        "average_fill_notional_usdt": average_fill_notional,
        "pnl_reference_notional_usdt": entry_notional,
        "entry_fee_usdt": entry_fee,
        "exit_fee_usdt": exit_fee,
        "entry_fee_bps": entry_fee_bps,
        "exit_fee_bps": exit_fee_bps,
        "round_trip_fee_bps_on_position": round_trip_fee_bps,
        "entry_reference_source": entry_reference_source,
        "entry_spread_bps_at_reference": entry_spread,
        "entry_slippage_bps_vs_touch": entry_slippage,
        "exit_spread_bps_at_reference": exit_spread,
        "exit_slippage_bps_vs_touch": exit_slippage,
        "funding_effect_usdt": funding_usdt,
        "funding_effect_bps_on_entry_notional": funding_effect_bps,
        "gross_close_profit_usdt": gross_close_usdt,
        "gross_realized_bps_on_entry_notional": gross_bps,
        "realized_net_pnl_usdt": net_usdt,
        "realized_net_bps_on_entry_notional": realized_net_bps,
        "accounting_identity_expected_net_usdt": expected_net,
        "accounting_identity_error_usdt": identity_error,
        "accounting_identity_pass": accounting_identity_pass,
        "fee_bucket": fee_bucket,
        "oos_reference": {
            **oos_reference(),
            "net10_bps_per_parent_opportunity": OOS_NET10_BPS,
            "net20_bps_per_parent_opportunity": OOS_NET20_BPS,
            "implied_net_at_16bps_full_notional_cost": oos_net_at_full_notional_cost(16.0),
        },
        "note": "Fees are normalized per fill to that fill's actual notional; gross/net/funding bps use entry notional. Slippage is diagnostic and is not added again to realized PnL.",
    }


def analyze_receipt_root(receipt_root: str | Path) -> dict[str, Any]:
    root = Path(receipt_root)
    sessions = sorted({p.parent for p in root.rglob("POST_TRADE_RECONCILIATION.json")}) if root.exists() else []
    rows = [analyze_session(session) for session in sessions]
    complete = [r for r in rows if r.get("status") == "COMPLETE_EXECUTION_ECONOMICS"]
    incomplete = [r for r in rows if r.get("status") != "COMPLETE_EXECUTION_ECONOMICS"]

    fees = [float(r["round_trip_fee_bps_on_position"]) for r in complete]
    funding = [float(r["funding_effect_bps_on_entry_notional"]) for r in complete]
    net = [float(r["realized_net_bps_on_entry_notional"]) for r in complete]

    if not complete:
        status = "NO_ATTRIBUTABLE_CLOSED_TRADES"
    elif len(complete) < MIN_EXECUTION_ECONOMICS_TRADES:
        status = "INSUFFICIENT_EXECUTION_ECONOMICS_SAMPLE"
    else:
        status = "EXECUTION_ECONOMICS_SAMPLE_READY_FOR_REVIEW"

    return {
        "gate_id": "OPTIONS-SPOTPERP-001-V2.1-EXECUTION-ECONOMICS-TRUTH-GATE-V0.1",
        "status": status,
        "minimum_complete_trades_for_review": MIN_EXECUTION_ECONOMICS_TRADES,
        "closed_sessions_found": len(sessions),
        "complete_trade_count": len(complete),
        "incomplete_or_failed_count": len(incomplete),
        "strategy_economic_verdict_allowed": False,
        "scientific_parent_changed": False,
        "fee_bps": {
            "mean": _mean(fees),
            "median": _median(fees),
            "p90": _p90(fees),
            "max": max(fees) if fees else None,
        },
        "funding_effect_bps_on_entry_notional": {
            "mean": _mean(funding),
            "median": _median(funding),
        },
        "realized_net_bps_on_entry_notional": {
            "mean": _mean(net),
            "median": _median(net),
        },
        "fee_only_base10_compatible_trades": sum(1 for x in fees if x <= BASE_COST_BPS),
        "fee_only_stress20_or_better_trades": sum(1 for x in fees if x <= STRESS_COST_BPS),
        "sessions": rows,
        "note": "Ten complete trades makes the execution-economics sample reviewable; it does not promote the strategy or authorize production.",
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
    "analyze_receipt_root",
    "observed_fill_fee_summary",
    "oos_reference",
    "oos_net_at_full_notional_cost",
    "fee_bps",
]
