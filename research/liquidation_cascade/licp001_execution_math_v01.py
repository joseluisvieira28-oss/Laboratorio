"""Executable return math for LICP-001. Pure functions; no exchange access."""

MEXC_TAKER_ROUND_TRIP_BPS=16.0
MEXC_MAKER_ROUND_TRIP_BPS=12.0

def executable_returns(entry_bid,entry_ask,future_bid,future_ask,pressure):
    vals=(entry_bid,entry_ask,future_bid,future_ask)
    if any(float(x)<=0 for x in vals):
        raise ValueError("NONPOSITIVE_BBO")
    if entry_bid>=entry_ask or future_bid>=future_ask:
        raise ValueError("CROSSED_OR_LOCKED_BBO")
    if pressure=="SELL":
        taker=(entry_bid-future_ask)/entry_bid*10000.0
        maker=(entry_ask-future_bid)/entry_ask*10000.0
    elif pressure=="BUY":
        taker=(future_bid-entry_ask)/entry_ask*10000.0
        maker=(future_ask-entry_bid)/entry_bid*10000.0
    else:
        raise ValueError("INVALID_PRESSURE")
    return {
      "taker_gross_bps":taker,
      "mexc_taker_net_bps":taker-MEXC_TAKER_ROUND_TRIP_BPS,
      "maker_ceiling_gross_bps":maker,
      "mexc_maker_ceiling_net_bps":maker-MEXC_MAKER_ROUND_TRIP_BPS,
    }
