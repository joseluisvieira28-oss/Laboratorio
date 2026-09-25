"""Exact-integer canonical LCOD collateral stress curve.

Pure mechanism math. No RPC, no future outcomes, no PnL.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Iterable

RAY = 10**27
WAD = 10**18
BPS_TO_WAD = 10**14
DEN = 10_000
STRESS_BPS = (0, 25, 50, 75, 100, 150, 200, 300, 500)


@dataclass(frozen=True)
class Borrower:
    pair_hash: str
    official_hf_wad: int
    reconstructed_hf_wad: int
    debt_value_ray: int
    weighted_collateral_bps_value: int


@dataclass(frozen=True)
class Point:
    stress_bps: int
    newly_count: int
    newly_debt_value_ray: int
    cumulative_new_count: int
    cumulative_new_debt_value_ray: int
    total_eligible_count: int
    total_eligible_debt_value_ray: int


def stressed_hf_wad(b: Borrower, stress_bps: int) -> int:
    if not 0 <= stress_bps < DEN:
        raise ValueError("stress_bps outside [0,10000)")
    if b.debt_value_ray <= 0:
        raise ValueError("debt must be positive")
    multiplier = DEN - stress_bps
    return (
        b.weighted_collateral_bps_value
        * multiplier
        * BPS_TO_WAD
        * RAY
        // (DEN * b.debt_value_ray)
    )


def canonical_curve(borrowers: Iterable[Borrower]) -> tuple[list[Point], dict]:
    rows = tuple(borrowers)
    if not rows:
        raise ValueError("empty borrower set")

    baseline_underwater = [b for b in rows if b.official_hf_wad < WAD]
    healthy = [b for b in rows if b.official_hf_wad >= WAD]

    disagree = [
        b.pair_hash
        for b in healthy
        if b.reconstructed_hf_wad < WAD
    ]
    if disagree:
        raise ValueError("BASELINE_THRESHOLD_SIDE_DISAGREEMENT")

    baseline_debt = sum(b.debt_value_ray for b in baseline_underwater)
    crossed: set[str] = set()
    cumulative_count = 0
    cumulative_debt = 0
    points: list[Point] = []

    for stress in STRESS_BPS:
        new = []
        if stress > 0:
            for b in healthy:
                if b.pair_hash in crossed:
                    continue
                if stressed_hf_wad(b, stress) < WAD:
                    new.append(b)
        for b in new:
            crossed.add(b.pair_hash)

        new_debt = sum(b.debt_value_ray for b in new)
        cumulative_count += len(new)
        cumulative_debt += new_debt

        points.append(
            Point(
                stress_bps=stress,
                newly_count=len(new),
                newly_debt_value_ray=new_debt,
                cumulative_new_count=cumulative_count,
                cumulative_new_debt_value_ray=cumulative_debt,
                total_eligible_count=len(baseline_underwater) + cumulative_count,
                total_eligible_debt_value_ray=baseline_debt + cumulative_debt,
            )
        )

    meta = {
        "baseline_underwater_count": len(baseline_underwater),
        "baseline_underwater_debt_value_ray": baseline_debt,
        "healthy_baseline_count": len(healthy),
        "threshold_side_disagreement_count": 0,
    }
    return points, meta


def exact_geometry(points: Iterable[Point]) -> dict:
    pts = tuple(points)
    if len(pts) < 3:
        raise ValueError("need >=3 curve points")
    x = [Fraction(p.stress_bps, 100) for p in pts]  # percentage points
    y = [Fraction(p.cumulative_new_debt_value_ray, 1) for p in pts]
    if any(b <= a for a, b in zip(x, x[1:])):
        raise ValueError("stress grid must increase")

    slopes = [
        (y[i] - y[i - 1]) / (x[i] - x[i - 1])
        for i in range(1, len(x))
    ]
    curvatures = []
    for i in range(1, len(x) - 1):
        left = (y[i] - y[i - 1]) / (x[i] - x[i - 1])
        right = (y[i + 1] - y[i]) / (x[i + 1] - x[i])
        curvatures.append(Fraction(2, 1) * (right - left) / (x[i + 1] - x[i - 1]))

    def pack(v: Fraction) -> dict:
        return {"numerator": v.numerator, "denominator": v.denominator}

    return {
        "interval_slopes_value_ray_per_percentage_point": [pack(v) for v in slopes],
        "interior_curvatures_value_ray_per_percentage_point_squared": [pack(v) for v in curvatures],
    }
