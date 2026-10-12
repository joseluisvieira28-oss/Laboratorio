#!/usr/bin/env python3
"""Pure research arithmetic / causal first-touch invariants for MEXC-CONVEX-ETHSOL-4R-001.

NO network, auth, orders, strategy optimization, credential handling or paper forward activation.
Not an exchange emulator: mark liquidation, filling and funding require external evidence.
Every first touch result is an observed quote BARRIER, not an assured executable fill.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_DOWN

FEE = Decimal("0.0008")
STOP_PRICE_FRACTION = Decimal("0.04")
TARGET_MULTIPLE = Decimal("4")
MAX_HOLD_MS = 60 * 24 * 3600 * 1000
QUOTE_AGE_LIMIT_MS = 2000
OBSERVATION_GAP_LIMIT_MS = 30000
PER_TRADE_RISK_FRACTION = Decimal("0.0025")
AGGREGATE_RISK_FRACTION = Decimal("0.005")


def D(value):
    d = Decimal(str(value))
    if not d.is_finite():
        raise ValueError("NON_FINITE_NUMBER")
    return d


def positive(value):
    d = D(value)
    if d <= 0:
        raise ValueError("NON_POSITIVE_NUMBER")
    return d


def fee_only_stop_loss_fraction():
    """Accounted with fee on initial and the lower exit price notionals."""
    return STOP_PRICE_FRACTION * (1 - FEE) + 2 * FEE


def fee_only_target_fraction():
    """Price appreciation from entry ASK reference giving exactly +4/-1 fee-only."""
    return (TARGET_MULTIPLE * fee_only_stop_loss_fraction() + 2 * FEE) / (1 - FEE)


def barriers_from_entry(entry_ask_vwap):
    e = positive(entry_ask_vwap)
    return {"entry": e, "stop_bid": e * (1 - STOP_PRICE_FRACTION),
            "target_bid": e * (1 + fee_only_target_fraction())}


def fee_only_return_per_initial_notional(entry, exit_price):
    e = positive(entry)
    x = positive(exit_price) / e
    return (x - 1) - FEE - (FEE * x)


def net_usdt(quantity_underlying, entry_price, exit_price,
             funding_cash=0, extra_slippage_cash=0):
    """Entry/exit prices represent observed marketable VWAP; do not re-charge spread.

    funding_cash > 0 when received, < 0 when paid; extra_slippage_cash nonnegative.
    """
    qty = positive(quantity_underlying)
    entry = positive(entry_price)
    exit_ = positive(exit_price)
    fund = D(funding_cash)
    slip = D(extra_slippage_cash)
    if slip < 0:
        raise ValueError("NEGATIVE_SLIPPAGE")
    initial_notional = qty * entry
    gross = qty * (exit_ - entry)
    entrance_fee = FEE * initial_notional
    exit_fee = FEE * qty * exit_
    return {"gross_usdt": gross, "entry_fee_usdt": entrance_fee,
            "exit_fee_usdt": exit_fee, "funding_usdt": fund,
            "extra_slippage_usdt": slip,
            "net_usdt": gross - entrance_fee - exit_fee + fund - slip}


def risk_limited_contracts(equity, entry_ask_vwap, contract_size, min_vol,
                           vol_unit, max_vol, current_open_planned_risk_usdt=0):
    """Return REJECT or DOWN-rounded contracts; never force the exchange minimum.

    Hypothetical wallet equity shared across both tracked assets. No leverage in sizing.
    """
    eq = positive(equity)
    ask = positive(entry_ask_vwap)
    size = positive(contract_size)
    minimum = positive(min_vol)
    step = positive(vol_unit)
    maximum = positive(max_vol)
    opened = D(current_open_planned_risk_usdt)
    if opened < 0 or maximum < minimum:
        return {"status": "INVALID_CONTRACT_OR_RISK"}
    total_left = eq * AGGREGATE_RISK_FRACTION - opened
    trade_allowed = min(eq * PER_TRADE_RISK_FRACTION, total_left)
    if trade_allowed <= 0:
        return {"status": "AGGREGATE_RISK_BLOCKED"}
    planned_stop_fraction = fee_only_stop_loss_fraction()
    allowed_notional = trade_allowed / planned_stop_fraction
    raw_vol = allowed_notional / (ask * size)
    vol = (raw_vol / step).to_integral_value(rounding=ROUND_DOWN) * step
    if vol < minimum or vol > maximum:
        return {"status": "LOT_LIMIT_BLOCKED",
                "max_notional_usdt": str(allowed_notional)}
    notional = vol * size * ask
    risk = notional * planned_stop_fraction
    if risk > trade_allowed:
        raise AssertionError("RISK_ROUNDING_ESCAPED")
    return {"status": "HYPOTHETICAL_SIZE_PASS",
            "contracts": str(vol), "notional_usdt": str(notional),
            "planned_stop_risk_usdt": str(risk),
            "max_notional_usdt": str(allowed_notional),
            "caveat": "No executable fill/margin/funding/liquidation proof"}


def _quote_valid(tick, previous_ms):
    """Tick timestamp is received_at UTC ms; exchange source stamp is book_ms."""
    try:
        received = int(tick["received_ms"])
        stamped = int(tick["book_ms"])
        bid = positive(tick["bid"])
        ask = positive(tick["ask"])
    except (KeyError, TypeError, ValueError):
        return False
    if received <= previous_ms or stamped > received:
        return False
    if received - stamped > QUOTE_AGE_LIMIT_MS or bid >= ask:
        return False
    return True


def observed_first_touch(entry_ms, entry_ask_vwap, ticks,
                         leverage=1, liquidation_mark_price=None):
    """Chronological public-BID first-touch (NOT stop/target order fills).

    Mandatory dense quote / mark evidence for every elapsed interval.
    No raw OHLC high/low, post-hoc gap interpolation, or stop fill guarantees.
    """
    try:
        t0 = int(entry_ms)
        level = barriers_from_entry(entry_ask_vwap)
        lev = positive(leverage)
        liq = positive(liquidation_mark_price) if liquidation_mark_price is not None else None
    except (TypeError, ValueError):
        return {"status": "INVALID_ENTRY"}
    if lev > 1 and liq is None:
        return {"status": "LIQUIDATION_UNIDENTIFIABLE"}
    previous = t0
    until = t0 + MAX_HOLD_MS
    for tick in ticks:
        if not _quote_valid(tick, previous):
            return {"status": "PATH_UNIDENTIFIABLE", "reason": "INVALID_OR_NONCAUSAL_QUOTE"}
        now = int(tick["received_ms"])
        if now - previous > OBSERVATION_GAP_LIMIT_MS:
            return {"status": "PATH_UNIDENTIFIABLE", "reason": "UNOBSERVED_QUOTE_GAP"}
        bid = positive(tick["bid"])
        liquidation_seen = False
        if lev > 1:
            if "mark_price" not in tick:
                return {"status": "LIQUIDATION_UNIDENTIFIABLE"}
            try:
                mark = positive(tick["mark_price"])
            except ValueError:
                return {"status": "LIQUIDATION_UNIDENTIFIABLE"}
            liquidation_seen = mark <= liq
        stop_seen = bid <= level["stop_bid"]
        target_seen = bid >= level["target_bid"]
        if liquidation_seen and (stop_seen or target_seen):
            return {"status": "AMBIGUOUS_LIQUIDATION_ORDER",
                    "observed_at_ms": now}
        if liquidation_seen:
            return {"status": "MARK_LIQUIDATION_TOUCH_NO_FILL_GUARANTEE",
                    "observed_at_ms": now}
        if stop_seen:
            return {"status": "STOP_BID_TOUCH_NO_FILL_GUARANTEE",
                    "observed_at_ms": now, "bid": str(bid)}
        if target_seen:
            return {"status": "TARGET_BID_TOUCH_NO_FILL_GUARANTEE",
                    "observed_at_ms": now, "bid": str(bid)}
        if now >= until:
            return {"status": "TIME_LIMIT_BID_REFERENCE_NO_FILL_GUARANTEE",
                    "observed_at_ms": now, "bid": str(bid)}
        previous = now
    return {"status": "OPEN_NO_VERDICT", "last_received_ms": previous,
            "scoreable_closed_trade": False}
