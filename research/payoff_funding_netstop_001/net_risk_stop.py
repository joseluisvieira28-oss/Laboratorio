"""Pure, offline math for a separately frozen PAYOFF funding-aware stop.

RESEARCH ONLY. No imports for network, no orders, no portfolio mutations.
No BTC historical outcomes evaluated. Historical 4R remains untouched.
"""
from __future__ import annotations
import math

RISK_BUDGET_ON_INITIAL_MARGIN = 0.10
FROZEN_EXIT_FEE_FRACTION = 0.001
FROZEN_ADVERSE_EXIT_SLIPPAGE = 0.0005

class RiskInputBlocked(ValueError):
    pass

def _validate(entry_fill, qty, initial_margin, entry_fee_cash, accrued_funding_cash,
              exit_fee_fraction, exit_slippage_fraction):
    values=(entry_fill,qty,initial_margin,entry_fee_cash,accrued_funding_cash,
            exit_fee_fraction,exit_slippage_fraction)
    if any(not isinstance(v,(int,float)) or not math.isfinite(v) for v in values):
        raise RiskInputBlocked("NON_FINITE_OR_NON_NUMERIC_INPUT")
    if entry_fill<=0 or qty<=0 or initial_margin<=0 or entry_fee_cash<0:
        raise RiskInputBlocked("INVALID_PRICE_QTY_MARGIN_OR_FEE")
    if not(0<=exit_fee_fraction<=0.05 and 0<=exit_slippage_fraction<=0.05):
        raise RiskInputBlocked("EXCESSIVE_OR_NEGATIVE_ASSUMPTION")
    if initial_margin>entry_fill*qty:
        raise RiskInputBlocked("MARGIN_GREATER_THAN_NOTIONAL")

def hypothetical_net_from_raw_exit(raw_price, *, entry_fill,qty,entry_fee_cash,
                                   accrued_funding_cash,exit_fee_fraction,
                                   exit_slippage_fraction):
    if not isinstance(raw_price,(int,float)) or not math.isfinite(raw_price) or raw_price<=0:
        raise RiskInputBlocked("INVALID_RAW_EXIT_PRICE")
    _validate(entry_fill,qty,entry_fill*qty,entry_fee_cash,accrued_funding_cash,
              exit_fee_fraction,exit_slippage_fraction)
    realized_exit=raw_price*(1-exit_slippage_fraction)
    return (qty*(realized_exit-entry_fill)-entry_fee_cash
            -qty*realized_exit*exit_fee_fraction+accrued_funding_cash)

def funding_adjusted_raw_stop(*,entry_fill,qty,initial_margin,entry_fee_cash,
                              accrued_funding_cash,
                              exit_fee_fraction=FROZEN_EXIT_FEE_FRACTION,
                              exit_slippage_fraction=FROZEN_ADVERSE_EXIT_SLIPPAGE):
    """Raw market price corresponding to *hypothetical* -10% initial margin net.

    The stop cannot guarantee fills. Negative funding moves this stop upward.
    """
    _validate(entry_fill,qty,initial_margin,entry_fee_cash,accrued_funding_cash,
              exit_fee_fraction,exit_slippage_fraction)
    denominator=qty*(1-exit_fee_fraction)*(1-exit_slippage_fraction)
    raw=(qty*entry_fill+entry_fee_cash-accrued_funding_cash
         -RISK_BUDGET_ON_INITIAL_MARGIN*initial_margin)/denominator
    if not math.isfinite(raw) or raw<=0:
        raise RiskInputBlocked("STOP_PRICE_NON_POSITIVE")
    return raw

def next_observation_exit(open_price,low_price,raw_stop):
    """Synthetic price-path classifier; NEVER an order or fill guarantee."""
    vals=(open_price,low_price,raw_stop)
    if any(not isinstance(v,(int,float)) or not math.isfinite(v) or v<=0 for v in vals):
        raise RiskInputBlocked("BAD_OBSERVATION")
    if low_price>open_price:
        raise RiskInputBlocked("INVALID_BAR_LOW")
    if open_price<=raw_stop:
        return {"decision":"ADVERSE_STOP_GAP_AT_OPEN","hypothetical_raw_fill":open_price}
    if low_price<=raw_stop:
        return {"decision":"STOP_TOUCHED_NO_FILL_GUARANTEE","hypothetical_raw_fill":raw_stop}
    return {"decision":"NOT_TOUCHED","hypothetical_raw_fill":None}
