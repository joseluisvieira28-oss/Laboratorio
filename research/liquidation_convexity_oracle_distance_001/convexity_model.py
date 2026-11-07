"""Outcome-blind liquidation convexity calculator.

Pure arithmetic over a fully specified snapshot. No RPC, no market returns and
no execution. Values are normalized to one quote currency before use.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping


@dataclass(frozen=True)
class CollateralLeg:
    asset: str
    value: float
    liquidation_threshold: float


@dataclass(frozen=True)
class Position:
    position_id: str
    collateral: tuple[CollateralLeg, ...]
    debt_value: float


@dataclass(frozen=True)
class CurvePoint:
    shock: float
    newly_eligible_count: int
    newly_eligible_debt: float
    cumulative_eligible_debt: float


def health_factor(position: Position, shocks: Mapping[str, float] | None = None) -> float:
    if position.debt_value <= 0:
        return float("inf")
    shocks = shocks or {}
    adjusted = 0.0
    for leg in position.collateral:
        factor = 1.0 + float(shocks.get(leg.asset, 0.0))
        if factor < 0:
            raise ValueError("shock makes collateral value negative")
        adjusted += leg.value * factor * leg.liquidation_threshold
    return adjusted / position.debt_value


def liquidation_curve(
    positions: Iterable[Position],
    *,
    shocked_asset: str,
    shock_grid: Iterable[float],
) -> list[CurvePoint]:
    positions = tuple(positions)
    prior_eligible: set[str] = {
        p.position_id for p in positions if health_factor(p) < 1.0
    }
    cumulative_prior = sum(
        p.debt_value for p in positions if p.position_id in prior_eligible
    )

    out: list[CurvePoint] = []
    seen = set(prior_eligible)
    cumulative = cumulative_prior

    for shock in shock_grid:
        eligible_now = {
            p.position_id
            for p in positions
            if health_factor(p, {shocked_asset: shock}) < 1.0
        }
        new_ids = eligible_now - seen
        new_debt = sum(p.debt_value for p in positions if p.position_id in new_ids)
        cumulative += new_debt
        out.append(
            CurvePoint(
                shock=float(shock),
                newly_eligible_count=len(new_ids),
                newly_eligible_debt=new_debt,
                cumulative_eligible_debt=cumulative,
            )
        )
        seen |= eligible_now
    return out


def first_differences(points: Iterable[CurvePoint]) -> list[float]:
    values = [p.cumulative_eligible_debt for p in points]
    return [b - a for a, b in zip(values, values[1:])]


def second_differences(points: Iterable[CurvePoint]) -> list[float]:
    first = first_differences(points)
    return [b - a for a, b in zip(first, first[1:])]
