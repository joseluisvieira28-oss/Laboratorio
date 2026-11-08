from component_snapshot import (
    BorrowLeg, ComponentPosition, SupplyLeg,
    collateral_capacity_usd, debt_usd,
    reconstructed_health_factor, relative_reconciliation_error,
)


def fixture(official=1.25):
    return ComponentPosition(
        "x",
        official,
        (
            SupplyLeg("weth", 1.0, 100.0, 80.0, True),
            SupplyLeg("idle", 10.0, 1.0, 90.0, False),
        ),
        (BorrowLeg("usdc", 64.0, 0.0, 1.0),),
    )


def test_non_collateral_supply_is_excluded():
    p=fixture()
    assert collateral_capacity_usd(p) == 80.0


def test_debt_uses_principal_plus_interest():
    p=ComponentPosition(
        "x", 1.0,
        (SupplyLeg("weth",1,100,80,True),),
        (BorrowLeg("usdc",60,4,1),),
    )
    assert debt_usd(p) == 64.0


def test_reconstructed_hf():
    assert reconstructed_health_factor(fixture()) == 1.25
    assert relative_reconciliation_error(fixture()) == 0.0


def test_invalid_collateral_factor_fails_closed():
    p=ComponentPosition(
        "x",1.0,
        (SupplyLeg("bad",1,1,101,True),),
        (BorrowLeg("d",1,0,1),),
    )
    try:
        collateral_capacity_usd(p)
        raise AssertionError("expected failure")
    except ValueError as e:
        assert "INVALID_COLLATERAL_FACTOR" in str(e)


def test_zero_debt_is_not_a_liquidation_position():
    p=ComponentPosition(
        "x",1.0,
        (SupplyLeg("c",1,1,80,True),),
        (),
    )
    try:
        reconstructed_health_factor(p)
        raise AssertionError("expected failure")
    except ValueError as e:
        assert "NO_POSITIVE_DEBT" in str(e)
