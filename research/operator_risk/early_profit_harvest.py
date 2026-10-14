"""Early-profit 001: pure hypothetical plans; NEVER sends exchange orders.

The user selected early REALIZED reductions. The stop after partial execution is
a separate, later proposal (not an exchange ACK). Research only.
"""
from dataclasses import dataclass
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR

from monotonic_protection import (
    D, ONE, ZERO, RiskRejected, positive, fraction_bps,
    round_step_down, cost_adjusted_breakeven,
)


@dataclass(frozen=True)
class PartialProposal:
    action: str                  # FULL_CLOSE or HALF_CLOSE
    quantity: Decimal
    assumed_exit_fill: Decimal
    expected_realized_net: Decimal
    minimum_realized_net: Decimal
    remaining_units_if_filled: Decimal
    stage: str = "PROPOSAL_ONLY_NO_EXCHANGE_ORDER"


def _valid_price_side(side, entry, initial_stop):
    if side not in ("LONG", "SHORT"):
        raise RiskRejected("INVALID_SIDE")
    if side == "LONG" and initial_stop >= entry:
        raise RiskRejected("INVALID_LONG_STOP")
    if side == "SHORT" and initial_stop <= entry:
        raise RiskRejected("INVALID_SHORT_STOP")


def _is_exact_step(quantity, step):
    return round_step_down(quantity, step) == quantity


def _realized_net(side, entry, exit_fill, closed_qty, original_qty,
                  original_entry_fee, settled_signed_funding, exit_fee):
    q = closed_qty
    gross = q * (exit_fill - entry) if side == "LONG" else q * (entry - exit_fill)
    ratio = closed_qty / original_qty
    return gross - D(original_entry_fee) * ratio + D(settled_signed_funding) * ratio - exit_fee


def propose_early_profit_close(
    *, side, entry_fill, initial_stop, full_quantity,
    original_entry_fee, settled_signed_funding, modeled_initial_risk_cash,
    fresh_exit_quote, exit_fee_bps, exit_slip_bps,
    quantity_step, minimum_close_quantity, minimum_close_notional,
    quote_is_verified_fresh, broker_protective_stop_acknowledged,
):
    """Propose first +1R quote-witness partial; if split invalid, FULL close.

    Quote is bid for LONG and ask for SHORT. No price high-as-fill logic.
    Funding may be signed. Fee+slippage projected, NOT measured after fill.
    """
    entry = positive(entry_fill, "ENTRY")
    stop = positive(initial_stop, "STOP")
    _valid_price_side(side, entry, stop)
    qty = positive(full_quantity, "QTY")
    step = positive(quantity_step, "STEP")
    min_qty = positive(minimum_close_quantity, "MIN_QTY")
    min_notional = positive(minimum_close_notional, "MIN_NOTIONAL")
    quote = positive(fresh_exit_quote, "BBO")
    risk_cash = positive(modeled_initial_risk_cash, "MODEL_RISK")
    paid_fee = D(original_entry_fee)
    funding = D(settled_signed_funding)
    if paid_fee < ZERO:
        raise RiskRejected("NEGATIVE_ENTRY_FEE")
    if not _is_exact_step(qty, step):
        raise RiskRejected("FULL_QTY_NOT_VENUE_STEP")
    if not quote_is_verified_fresh or not broker_protective_stop_acknowledged:
        raise RiskRejected("UNVERIFIED_QUOTE_OR_BROKER_STOP")
    distance = abs(entry - stop)
    if risk_cash < distance * qty:  # risk must include price loss plus friction
        raise RiskRejected("MODEL_RISK_BELOW_PRICE_RISK")
    favored = (quote - entry) if side == "LONG" else (entry - quote)
    if favored < distance:
        return None
    exit_fee = fraction_bps(exit_fee_bps)
    slip = fraction_bps(exit_slip_bps)
    assumed_exit_fill = quote*(ONE-slip) if side == "LONG" else quote*(ONE+slip)

    half = round_step_down(qty / Decimal("2"), step)
    rest = qty - half
    split_possible = (
        half >= min_qty and rest >= min_qty and
        half*quote >= min_notional and rest*quote >= min_notional and
        _is_exact_step(rest, step)
    )
    closed_qty = half if split_possible else qty
    if closed_qty < min_qty or closed_qty*quote < min_notional:
        raise RiskRejected("CLOSE_QUANTITY_BELOW_EXCHANGE_MIN")
    closing_fee = closed_qty * assumed_exit_fill * exit_fee
    net = _realized_net(side, entry, assumed_exit_fill, closed_qty, qty,
                        paid_fee, funding, closing_fee)
    net_floor = risk_cash * Decimal("0.25")
    # This gate means positive REALIZED projected cash, not just a mark.
    if net < net_floor:
        return None
    return PartialProposal(
        action="HALF_CLOSE" if split_possible else "FULL_CLOSE",
        quantity=closed_qty,
        assumed_exit_fill=assumed_exit_fill,
        expected_realized_net=net,
        minimum_realized_net=net_floor,
        remaining_units_if_filled=qty-closed_qty,
    )


@dataclass(frozen=True)
class RemainingStopProposal:
    proposed_stop: Decimal
    still_unacknowledged: bool = True
    stage: str = "AMEND_REQUEST_NOT_BROKER_ACK"


def propose_post_fill_breakeven_stop(
    *, side, entry_fill, initial_quantity, actually_closed_quantity,
    original_entry_fee, signed_settled_funding_for_entire_trade,
    broker_acknowledged_prior_stop, actual_fresh_exit_quote,
    future_exit_fee_bps, future_exit_slip_bps, price_tick,
    close_fill_independently_confirmed, remaining_stop_coverage_verified,
    quote_is_verified_fresh,
):
    """No new protection credit until separately confirmed by venue.

    Return a proposed price only; caller MUST verify true broker amend/stop
    quantity acknowledgment and keep previous stop covered meanwhile.
    """
    if not close_fill_independently_confirmed or not remaining_stop_coverage_verified or not quote_is_verified_fresh:
        raise RiskRejected("FILL_COVERAGE_OR_QUOTE_NOT_VERIFIED")
    qty = positive(initial_quantity, "ORIGINAL_QTY")
    closed = positive(actually_closed_quantity, "CLOSED_QTY")
    if closed >= qty:
        raise RiskRejected("NO_REMAINING_POSITION")
    remain = qty-closed
    entry = positive(entry_fill, "ENTRY")
    old = positive(broker_acknowledged_prior_stop, "PRIOR_STOP")
    quote = positive(actual_fresh_exit_quote, "BBO")
    fee = D(original_entry_fee)
    funding = D(signed_settled_funding_for_entire_trade)
    if fee < ZERO:
        raise RiskRejected("NEGATIVE_ENTRY_FEE")
    ratio = remain/qty
    be = cost_adjusted_breakeven(side, entry, remain, fee*ratio,
                                 funding*ratio, future_exit_fee_bps, future_exit_slip_bps)
    tick = positive(price_tick, "TICK")
    # Rounding TOWARD guaranteed modeled net breakeven, unlike conservative
    # Chandelier trail rounding, which intentionally gives more space.
    if side == "LONG":
        candidate = (be/tick).to_integral_value(rounding=ROUND_CEILING)*tick
        candidate = max(candidate, old)
        if candidate >= quote:
            raise RiskRejected("CANDIDATE_STOP_ALREADY_CROSSED")
    elif side == "SHORT":
        candidate = (be/tick).to_integral_value(rounding=ROUND_FLOOR)*tick
        candidate = min(candidate, old)
        if candidate <= quote:
            raise RiskRejected("CANDIDATE_STOP_ALREADY_CROSSED")
    else:
        raise RiskRejected("INVALID_SIDE")
    if candidate <= ZERO:
        raise RiskRejected("INVALID_PROPOSED_STOP")
    return RemainingStopProposal(candidate)
