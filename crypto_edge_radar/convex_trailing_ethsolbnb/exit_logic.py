"""Frozen original BTC-CONVEX nonlatched Parent trailing, PURE state transition.
No exchange connector, account, orders, or credentials.
Uses previous confirmed-close active stop for this bar, never current-bar high.
"""
from __future__ import annotations
from dataclasses import dataclass
from math import isfinite

STOP_PCT=.04
ACTIVATE_PCT=.05
TRAIL_PCT=.12

@dataclass(frozen=True)
class OpenLong:
    entry:float
    initial_stop:float
    active_stop:float
    observed_peak:float

def at_entry(executed_entry:float)->OpenLong:
    if not isfinite(executed_entry) or executed_entry<=0:raise ValueError("INVALID_ENTRY")
    return OpenLong(entry=executed_entry,initial_stop=executed_entry*(1-STOP_PCT),active_stop=executed_entry*(1-STOP_PCT),observed_peak=executed_entry)

def after_closed_hour(position:OpenLong, *, candle_open:float,candle_high:float,candle_low:float,candle_close:float):
    numbers=(position.entry,position.initial_stop,position.active_stop,position.observed_peak,
             candle_open,candle_high,candle_low,candle_close)
    if not all(isfinite(x) and x>0 for x in numbers):raise ValueError("INVALID_CANDLE_OR_STATE")
    if candle_low>min(candle_open,candle_close) or candle_high<max(candle_open,candle_close) or candle_low>candle_high:raise ValueError("INCOHERENT_OHLC")
    # The STOP is the order known from previous completed candle.
    if candle_open<=position.active_stop:
        return {"action":"STOP_GAP_EXIT","exit_raw":candle_open,"next_state":None}
    if candle_low<=position.active_stop:
        return {"action":"STOP_EXIT","exit_raw":position.active_stop,"next_state":None}
    # Stop was not touched. Only now, at confirmed close, update peak and next bar stop.
    peak=max(position.observed_peak,candle_high)
    next_stop=max(position.initial_stop,peak*(1-TRAIL_PCT)) if (candle_close-position.entry)/position.entry>=ACTIVATE_PCT else position.initial_stop
    return {"action":"HOLD","exit_raw":None,"next_state":OpenLong(
        entry=position.entry,initial_stop=position.initial_stop,
        active_stop=next_stop,observed_peak=peak)}

def no_order_authority()->bool:
    return False
