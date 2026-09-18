from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Literal

Direction = Literal[-1, 0, 1]


@dataclass(frozen=True)
class FrozenRule:
    metric_interval_minutes: int = 5
    z_lookback_days: int = 30
    min_lookback_coverage: float = 0.99
    divergence_abs_z: float = 1.5
    entry_delay_minutes: int = 5
    primary_hold_minutes: int = 60
    diagnostic_holds_minutes: tuple[int, ...] = (30, 120)
    base_cost_bps: float = 14.0
    stress_cost_bps: float = 20.0
    min_pooled_events: int = 300
    min_events_per_asset: int = 30


FROZEN = FrozenRule()


def log_ratio(x: float) -> float:
    if not math.isfinite(x) or x <= 0:
        raise ValueError("ratio must be finite and > 0")
    return math.log(x)


def top_global_divergence(
    top_position_long_short_ratio: float,
    global_account_long_short_ratio: float,
) -> float:
    return log_ratio(top_position_long_short_ratio) - log_ratio(global_account_long_short_ratio)


def top_account_global_diagnostic(
    top_account_long_short_ratio: float,
    global_account_long_short_ratio: float,
) -> float:
    return log_ratio(top_account_long_short_ratio) - log_ratio(global_account_long_short_ratio)


def top_size_skew_diagnostic(
    top_position_long_short_ratio: float,
    top_account_long_short_ratio: float,
) -> float:
    return log_ratio(top_position_long_short_ratio) - log_ratio(top_account_long_short_ratio)


def threshold_cross_direction(
    z_now: float,
    z_prev: float,
    rule: FrozenRule = FROZEN,
) -> Direction:
    if z_now >= rule.divergence_abs_z and z_prev < rule.divergence_abs_z:
        return 1
    if z_now <= -rule.divergence_abs_z and z_prev > -rule.divergence_abs_z:
        return -1
    return 0


def aligned_return(direction: Direction, raw_log_return: float) -> float:
    if direction == 0:
        raise ValueError("no-trade direction has no aligned return")
    return float(direction) * raw_log_return


def net_bps(direction: Direction, raw_log_return: float, cost_bps: float) -> float:
    return aligned_return(direction, raw_log_return) * 10_000.0 - cost_bps


def source_gate(
    *,
    top_position_coverage: float,
    global_account_coverage: float,
    price_coverage: float,
    checksums_ok: bool,
    threshold: float = 0.99,
) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    if not checksums_ok:
        reasons.append("checksum_failure")
    if top_position_coverage < threshold:
        reasons.append("top_position_coverage")
    if global_account_coverage < threshold:
        reasons.append("global_account_coverage")
    if price_coverage < threshold:
        reasons.append("price_coverage")
    return (not reasons, tuple(reasons))
