from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Direction = Literal[-1, 0, 1]


@dataclass(frozen=True)
class FrozenRule:
    observation_seconds: int = 180
    entry_offset_seconds: int = 180
    btc_trigger_z: float = 0.75
    beta_window_days: int = 30
    alt_gap_z: float = 1.0
    primary_horizon_minutes: int = 5
    diagnostic_horizons_minutes: tuple[int, ...] = (1, 3, 10, 15)
    fee_per_fill_bps: float = 4.0
    slippage_per_fill_base_bps: float = 2.0
    slippage_per_fill_low_bps: float = 1.0
    slippage_per_fill_stress_bps: float = 3.0


FROZEN = FrozenRule()


def gap_return(alt_ret180: float, beta: float, btc_ret180: float) -> float:
    """Legacy residual definition: ALT_180 - beta * BTC_180."""
    return alt_ret180 - beta * btc_ret180


def baseline_direction(
    btc_z: float, gap_z: float, rule: FrozenRule = FROZEN
) -> Direction:
    """Model A. Symmetric follower rule, no dominance information."""
    if btc_z >= rule.btc_trigger_z and gap_z <= -rule.alt_gap_z:
        return 1
    if btc_z <= -rule.btc_trigger_z and gap_z >= rule.alt_gap_z:
        return -1
    return 0


def regime_flags(
    direction: Direction,
    delta_btc_d: float,
    delta_usdt_d: float,
    total3_return: float,
) -> dict[str, bool]:
    """Nested legacy ablation A -> B -> C -> D."""
    if direction == 0:
        return {"A": False, "B": False, "C": False, "D": False}

    b = delta_btc_d < 0 if direction > 0 else delta_btc_d > 0
    c = b and (delta_usdt_d < 0 if direction > 0 else delta_usdt_d > 0)
    d = c and (total3_return > 0 if direction > 0 else total3_return < 0)
    return {"A": True, "B": b, "C": c, "D": d}


def aligned_forward_return(direction: Direction, alt_forward_return: float) -> float:
    if direction == 0:
        raise ValueError("No-trade direction cannot have an aligned return")
    return float(direction) * alt_forward_return


def round_trip_cost_bps(
    slip_per_fill_bps: float, rule: FrozenRule = FROZEN
) -> float:
    return 2.0 * (rule.fee_per_fill_bps + slip_per_fill_bps)


def net_return_bps(
    gross_aligned_return: float,
    slip_per_fill_bps: float,
    rule: FrozenRule = FROZEN,
) -> float:
    return gross_aligned_return * 10_000.0 - round_trip_cost_bps(
        slip_per_fill_bps, rule
    )


def source_gate(
    *,
    btc_d_present: bool,
    usdt_d_present: bool,
    total3_present: bool,
    binance_present: bool,
) -> tuple[bool, tuple[str, ...]]:
    """Fail closed before any ARQ-001 market outcome if a frozen source is absent."""
    missing: list[str] = []
    if not binance_present:
        missing.append("binance_usdm_1m")
    if not btc_d_present:
        missing.append("tradingview_btc_d")
    if not usdt_d_present:
        missing.append("tradingview_usdt_d")
    if not total3_present:
        missing.append("tradingview_total3")
    return (not missing, tuple(missing))
