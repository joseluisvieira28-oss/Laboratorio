from convexity_model import (
    CollateralLeg,
    Position,
    health_factor,
    liquidation_curve,
    second_differences,
)


def test_health_factor_formula():
    p = Position(
        "p1",
        (CollateralLeg("WETH", 100.0, 0.80),),
        64.0,
    )
    assert health_factor(p) == 1.25


def test_shock_can_cross_liquidation_boundary():
    p = Position(
        "p1",
        (CollateralLeg("WETH", 100.0, 0.80),),
        79.0,
    )
    assert health_factor(p) > 1.0
    assert health_factor(p, {"WETH": -0.02}) < 1.0


def test_curve_counts_new_crossings_once():
    positions = [
        Position("a", (CollateralLeg("WETH", 100.0, 0.80),), 79.0),
        Position("b", (CollateralLeg("WETH", 100.0, 0.80),), 76.0),
    ]
    curve = liquidation_curve(
        positions,
        shocked_asset="WETH",
        shock_grid=[0.0, -0.02, -0.06],
    )
    assert curve[0].newly_eligible_count == 0
    assert curve[1].newly_eligible_count == 1
    assert curve[2].newly_eligible_count == 1
    assert curve[2].cumulative_eligible_debt == 155.0


def test_second_difference_exposes_acceleration():
    positions = [
        Position("a", (CollateralLeg("WETH", 100.0, 0.80),), 79.0),
        Position("b", (CollateralLeg("WETH", 100.0, 0.80),), 76.0),
    ]
    curve = liquidation_curve(
        positions,
        shocked_asset="WETH",
        shock_grid=[0.0, -0.02, -0.04, -0.06],
    )
    assert len(second_differences(curve)) == 2
