"""Offline accounting validation. No clients, credentials or order submission."""
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path


class AccountingError(ValueError):
    pass


def number(value, name):
    if value is None or isinstance(value, bool):
        raise AccountingError(f"{name}: missing/invalid")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise AccountingError(f"{name}: invalid") from exc
    if not result.is_finite():
        raise AccountingError(f"{name}: nonfinite")
    return result


def order_fee(order):
    """Signed expense: negative maker fees are rebates, never absolute values.

    Component amounts are authoritative. A placeholder zero total is ignored;
    a conflicting nonzero total blocks reconciliation. Zero without component
    evidence is unknown, rather than a promotional zero-fee assumption.
    """
    if order.get("feeCurrency", "USDT") != "USDT":
        raise AccountingError("fee currency is not USDT")
    keys = ("makerFee", "takerFee")
    present = [key for key in keys if key in order]
    total = number(order["totalFee"], "totalFee") if "totalFee" in order else None
    if present:
        components = sum((number(order[key], key) for key in present), Decimal(0))
        if total not in (None, Decimal(0)) and abs(total - components) > Decimal("0.00000001"):
            raise AccountingError("totalFee/component disagreement")
        if components == 0 and len(present) != 2:
            raise AccountingError("incomplete zero-fee components")
        return components
    if total is not None and total != 0:
        return total
    raise AccountingError("fee unverified")


def fill_evidence(order, contract_size):
    """Validate one attributable execution record, retaining both actual rates."""
    if not order.get("orderId") or not order.get("positionId"):
        raise AccountingError("fill identity missing")
    if order.get("feeCurrency") != "USDT":
        raise AccountingError("fill fee currency missing/non-USDT")
    price = number(order.get("dealAvgPriceStr", order.get("dealAvgPrice")), "fill price")
    volume = number(order.get("dealVol"), "fill volume")
    size = number(contract_size, "contract size")
    if min(price, volume, size) <= 0:
        raise AccountingError("fill quantities must be positive")
    fee = order_fee(order)
    maker = number(order.get("makerFee"), "makerFee")
    taker = number(order.get("takerFee"), "takerFee")
    maker_rate = number(order.get("makerFeeRate"), "makerFeeRate")
    taker_rate = number(order.get("takerFeeRate"), "takerFeeRate")
    notional = price * volume * size
    # Split maker/taker orders cannot be checked using average price and total
    # volume: require individual deal records instead of guessing the split.
    if maker != 0 and taker != 0:
        raise AccountingError("mixed maker/taker order requires individual fills")
    rate = maker_rate if maker != 0 else taker_rate
    if abs(fee - notional * rate) > Decimal("0.00000001"):
        raise AccountingError("fill amount/rate mismatch or unproven zero fee")
    return {"order_id": str(order["orderId"]), "position_id": str(order["positionId"]),
            "fee_usdt": str(fee), "notional_usdt": str(notional),
            "maker_fee_rate": str(maker_rate), "taker_fee_rate": str(taker_rate)}


def reconcile_position(*, active, entry_orders, exit_orders, history):
    """Only finalized exchange history can prove funding and realized net PnL."""
    if not isinstance(history, dict) or history.get("state") != 3:
        raise AccountingError("closed exchange position history required")
    pid = str(active["position_id"])
    if str(history.get("positionId")) != pid or history.get("symbol") != active["symbol"]:
        raise AccountingError("historical position identity mismatch")
    if not entry_orders or not exit_orders:
        raise AccountingError("entry and exit executions required")
    ids = set()
    evidence = []
    for phase, orders in (("entry", entry_orders), ("exit", exit_orders)):
        expected_side = {("SHORT", "entry"): 3, ("SHORT", "exit"): 2,
                         ("LONG", "entry"): 1, ("LONG", "exit"): 4}[(active["direction"], phase)]
        for order in orders:
            item = fill_evidence(order, active["contract_size"])
            if item["order_id"] in ids:
                raise AccountingError("duplicate execution")
            ids.add(item["order_id"])
            if item["position_id"] != pid or order.get("symbol") != active["symbol"] or order.get("side") != expected_side:
                raise AccountingError("execution position/symbol/side mismatch")
            evidence.append({"phase": phase, **item})
    entry_volume = sum(number(o["dealVol"], "entry volume") for o in entry_orders)
    exit_volume = sum(number(o["dealVol"], "exit volume") for o in exit_orders)
    if entry_volume != exit_volume or entry_volume != number(active["volume_contracts"], "position volume"):
        raise AccountingError("execution volume mismatch")
    entry_fee = sum(order_fee(o) for o in entry_orders)
    exit_fee = sum(order_fee(o) for o in exit_orders)
    gross = sum(number(o.get("profit"), "exit profit") for o in exit_orders)
    funding = number(history.get("holdFee"), "final funding")
    exchange_gross = number(history.get("closeProfitLoss"), "exchange gross")
    exchange_fee = number(history.get("totalFee"), "exchange position fee")
    exchange_net = number(history.get("realised"), "exchange realized")
    net = gross + funding - entry_fee - exit_fee
    for label, delta in (("gross", gross-exchange_gross), ("fees", entry_fee+exit_fee-exchange_fee), ("net", net-exchange_net)):
        if abs(delta) > Decimal("0.00000001"):
            raise AccountingError(f"exchange {label} mismatch")
    return {"accounting_verified": True, "accounting_source": "FINAL_EXCHANGE_POSITION_AND_EXECUTIONS",
            "gross_close_profit_usdt": float(gross), "funding_hold_fee_usdt": float(funding),
            "entry_fee_usdt": float(entry_fee), "exit_fee_usdt": float(exit_fee),
            "total_position_fee_usdt": float(entry_fee+exit_fee), "realized_net_pnl_usdt": float(exchange_net),
            "execution_fee_evidence": evidence}


def reconcile_session(session):
    session = Path(session)
    def load(name):
        return json.loads((session / name).read_text(encoding="utf-8"))
    return reconcile_position(active=load("ACTIVE_TRADE_STATE.json"),
                              entry_orders=[load("FILL_RECEIPT.json")["order"]],
                              exit_orders=load("EXIT_FILL_RECEIPT.json")["orders"],
                              history=load("FINAL_POSITION_HISTORY.json")["history"])
