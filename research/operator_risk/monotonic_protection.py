"""OFFLINE ONLY: proposed monotonic stop/risk maths. No exchange calls or trading permissions.

Synthetic safety invariants, NOT a broker stop order, risk guarantee or alpha test.
"""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_FLOOR, ROUND_CEILING

ZERO = Decimal("0")
ONE = Decimal("1")
BPS = Decimal("10000")


class RiskRejected(ValueError):
    pass


def D(v):
    try:
        out = Decimal(str(v))
    except (InvalidOperation, ValueError):
        raise RiskRejected("INVALID_DECIMAL")
    if not out.is_finite():
        raise RiskRejected("NONFINITE")
    return out


def positive(v, label):
    v = D(v)
    if v <= ZERO:
        raise RiskRejected("NONPOSITIVE_" + label)
    return v


def fraction_bps(v):
    v = D(v)
    if v < ZERO or v >= BPS:
        raise RiskRejected("INVALID_BPS")
    return v / BPS


def round_step_down(q, step):
    step = positive(step, "STEP")
    return (D(q) / step).to_integral_value(rounding=ROUND_FLOOR) * step


def round_price(v, tick, side):
    tick = positive(tick, "TICK")
    v = D(v)
    rounding = ROUND_FLOOR if side == "LONG" else ROUND_CEILING
    return (v / tick).to_integral_value(rounding=rounding) * tick


def model_unit_stop_loss(
    side, raw_entry, raw_stop,
    entry_fee_bps, exit_fee_bps, entry_slip_bps, exit_slip_bps,
    funding_reserve_bps
):
    """Worst ASSUMED per-unit cash stop loss, never a maximum gap loss."""
    e, stop = positive(raw_entry, "ENTRY"), positive(raw_stop, "STOP")
    fe, fx = fraction_bps(entry_fee_bps), fraction_bps(exit_fee_bps)
    se, sx = fraction_bps(entry_slip_bps), fraction_bps(exit_slip_bps)
    funding = fraction_bps(funding_reserve_bps)
    if side == "LONG":
        if stop >= e:
            raise RiskRejected("INVALID_LONG_STOP")
        fill_in, fill_out = e*(ONE+se), stop*(ONE-sx)
        price_loss = fill_in-fill_out
    elif side == "SHORT":
        if stop <= e:
            raise RiskRejected("INVALID_SHORT_STOP")
        fill_in, fill_out = e*(ONE-se), stop*(ONE+sx)
        price_loss = fill_out-fill_in
    else:
        raise RiskRejected("INVALID_SIDE")
    risk = price_loss + fill_in*fe + fill_out*fx + fill_in*funding
    if risk <= ZERO:
        raise RiskRejected("NONPOSITIVE_LOSS_MODEL")
    return risk


@dataclass(frozen=True)
class Sizing:
    units: Decimal
    modeled_stop_loss_cash: Decimal
    entry_notional: Decimal
    initial_margin_estimate: Decimal
    budget_cash: Decimal


def size_with_stop(
    side, equity, remaining_global_risk, risk_fraction,
    entry, stop, unit_step, min_notional, available_margin, leverage,
    fee_entry_bps, fee_exit_bps, slip_entry_bps, slip_exit_bps,
    funding_reserve_bps
):
    """Fail closed if minimum tradable quantity/margin exceeds selected risk envelope."""
    eq = positive(equity, "EQUITY")
    residual = positive(remaining_global_risk, "GLOBAL_RISK")
    fr = D(risk_fraction)
    if fr <= ZERO or fr > Decimal("0.02"):
        raise RiskRejected("POLICY_FRACTION_NOT_APPROVED")
    lev = positive(leverage, "LEVERAGE")
    if lev > Decimal("5"):
        raise RiskRejected("LEVERAGE_CAP_POLICY_EXAMPLE")
    e = positive(entry, "ENTRY")
    min_n = positive(min_notional, "MIN_NOTIONAL")
    margin = positive(available_margin, "AVAILABLE_MARGIN")
    budget = min(eq*fr, residual)
    unitloss = model_unit_stop_loss(
        side, e, stop, fee_entry_bps, fee_exit_bps,
        slip_entry_bps, slip_exit_bps, funding_reserve_bps
    )
    quantity = round_step_down(budget/unitloss, unit_step)
    # Conservative margin notional includes possible adverse entry execution.
    entry_execution_upper_bound = e*(ONE+fraction_bps(slip_entry_bps))
    quantity = min(quantity, round_step_down(margin*lev/entry_execution_upper_bound, unit_step))
    if quantity <= ZERO:
        raise RiskRejected("STEP_EXCEEDS_BUDGET")
    notional = quantity * e
    if notional < min_n:
        raise RiskRejected("EXCHANGE_MIN_NOTIONAL_EXCEEDS_SAFE_SIZE")
    modeled_loss = quantity*unitloss
    if modeled_loss > budget or quantity*entry_execution_upper_bound/lev > margin:
        raise RiskRejected("INTERNAL_SIZING_BREACH")
    return Sizing(quantity, modeled_loss, notional, quantity*entry_execution_upper_bound/lev, budget)


def cost_adjusted_breakeven(
    side, entry_fill, quantity, already_paid_entry_fee,
    signed_paid_funding, assumed_exit_fee_bps, assumed_exit_slip_bps,
):
    """Broker trigger stop where ASSUMED cash PnL ~=0 after known funding & costs.

    Exit fee/slippage are hypotheticals. A missed/gapped execution can lose.
    """
    e = positive(entry_fill, "ENTRY")
    q = positive(quantity, "QTY")
    paid = D(already_paid_entry_fee)
    if paid < ZERO:
        raise RiskRejected("NEGATIVE_ENTRY_FEE")
    f = D(signed_paid_funding)
    fee = fraction_bps(assumed_exit_fee_bps)
    slip = fraction_bps(assumed_exit_slip_bps)
    if side == "LONG":
        raw = (q*e+paid-f)/(q*(ONE-slip)*(ONE-fee))
    elif side == "SHORT":
        raw = (q*e-paid+f)/(q*(ONE+slip)*(ONE+fee))
    else:
        raise RiskRejected("INVALID_SIDE")
    return positive(raw, "BREAKEVEN")


def propose_completed_bar_trail(
    side, entry_fill, initial_stop, acknowledged_stop, fresh_bbo,
    observed_favorable_extreme, atr_confirmed, atr_multiple,
    activation_r, breakeven, tick
):
    """PURE candidate price; NEVER a broker-side stop or modification acknowledgment.

    Input high-water/low-water must come from post-entry completed bars ONLY.
    If candidate would already be crossed by executable BBO -> HALT/RECONCILE.
    """
    e = positive(entry_fill, "ENTRY")
    initial = positive(initial_stop, "INITIAL_STOP")
    old = positive(acknowledged_stop, "ACK_STOP")
    current = positive(fresh_bbo, "FRESH_BBO")
    extreme = positive(observed_favorable_extreme, "EXTREME")
    atr = positive(atr_confirmed, "ATR")
    multiple = positive(atr_multiple, "ATR_MULTIPLE")
    threshold = positive(activation_r, "ACTIVATION_R")
    break_even = positive(breakeven, "BREAK_EVEN")
    if side == "LONG":
        if not(initial < e and old >= initial and old < current):
            raise RiskRejected("UNPROTECTED_OR_CROSSED_LONG_STOP")
        price_r = e-initial
        if extreme-e < threshold*price_r:
            return old
        candidate = round_price(max(old, break_even, extreme-multiple*atr), tick, side)
        if candidate < old:
            raise RiskRejected("PROTECTION_LOOSENED")
        if candidate >= current:
            raise RiskRejected("NEW_STOP_ALREADY_CROSSED")
        return candidate
    if side == "SHORT":
        if not(initial > e and old <= initial and old > current):
            raise RiskRejected("UNPROTECTED_OR_CROSSED_SHORT_STOP")
        price_r = initial-e
        if e-extreme < threshold*price_r:
            return old
        candidate = round_price(min(old, break_even, extreme+multiple*atr), tick, side)
        if candidate > old:
            raise RiskRejected("PROTECTION_LOOSENED")
        if candidate <= current:
            raise RiskRejected("NEW_STOP_ALREADY_CROSSED")
        return candidate
    raise RiskRejected("INVALID_SIDE")
