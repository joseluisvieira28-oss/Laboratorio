"""Frozen fee hurdle helpers. Fee references are documented in COST_GATE_V0_1.md."""

FEE_BPS_PER_SIDE={
    "MEXC_API":{"maker":6.0,"taker":8.0},
    "BYBIT_VIP0_REF":{"maker":2.0,"taker":5.5},
    "BINANCE_USDSM_REGULAR_REF":{"maker":2.0,"taker":5.0},
}


def round_trip_fee_bps(venue: str, entry: str, exit: str) -> float:
    fees=FEE_BPS_PER_SIDE[venue]
    return float(fees[entry])+float(fees[exit])


def taker_net_bps(executable_gross_bps: float, venue: str, slippage_bps_total: float=0.0) -> float:
    return executable_gross_bps-round_trip_fee_bps(venue,"taker","taker")-float(slippage_bps_total)
