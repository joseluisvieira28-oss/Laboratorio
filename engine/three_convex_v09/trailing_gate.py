"""Exact V5 nonlatched trailing stop transition assessor.

No order creation, cancel, amendment or replay. This is pure math on completed
own-timeframe candles, after the broker stop for the current bar was already
processed. Trigger uses fair/mark in MEXC while V5 uses Binance OHLC lows:
execution equivalence is therefore NOT demonstrated by passing this gate.
"""
from decimal import Decimal, InvalidOperation, ROUND_FLOOR

STOP=Decimal("0.04")
TRAIL=Decimal("0.12")
ACT=Decimal("0.05")

class TrailHalt(ValueError):pass

def D(v,label):
    if isinstance(v,bool) or v is None:raise TrailHalt("BAD_"+label)
    try:x=Decimal(str(v))
    except (ValueError,InvalidOperation,TypeError):raise TrailHalt("BAD_"+label) from None
    if not x.is_finite():raise TrailHalt("BAD_"+label)
    return x

def calc_v5_trail(*,actual_fill,completed_tf_close,peak_5m_high_so_far,
                  previous_broker_stop,price_tick,closed_tf_confirmed):
    if closed_tf_confirmed is not True:
        raise TrailHalt("INCOMPLETE_TIMEFRAME_BAR")
    entry=D(actual_fill,"ENTRY")
    close=D(completed_tf_close,"CLOSE")
    peak=D(peak_5m_high_so_far,"PEAK")
    previous=D(previous_broker_stop,"BROKER_STOP")
    tick=D(price_tick,"PRICE_TICK")
    if min(entry,close,peak,previous,tick)<=0 or peak<max(entry,close):
        raise TrailHalt("INVALID_PRICE_GEOMETRY")
    initial=entry*(Decimal("1")-STOP)
    activation=(close-entry)/entry>=ACT
    raw=max(initial,peak*(Decimal("1")-TRAIL)) if activation else initial
    proposed=(raw/tick).to_integral_value(rounding=ROUND_FLOOR)*tick
    if proposed<=0:raise TrailHalt("INVALID_PROPOSED_STOP")
    # Previous broker stop must not be inferred from an earlier request; GET it.
    action="KEEP" if proposed==previous else (
        "TIGHTEN" if proposed>previous else "WEAKEN")
    return {
        "activation_on_completed_tf_close":activation,
        "v5_initial_unrounded":str(initial),
        "proposed_broker_stop_tick_floor":str(proposed),
        "readback_previous_broker_stop":str(previous),
        "action":action,
        "requires_venue_mutation":action!="KEEP",
        "protective_weaken_requested":action=="WEAKEN",
        # No stop-amend atomic/reduced risk evidence in live MEXC yet.
        "real_broker_amend_allowed":False,
        "live_go":False,
    }
