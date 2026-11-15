import pytest

from canonical_stress_curve import (
    Borrower,
    STRESS_BPS,
    WAD,
    canonical_curve,
    exact_geometry,
    stressed_hf_wad,
)


def b(name, hf_num, debt=10**53):
    # Choose weighted numerator so reconstructed HF at zero is exactly hf_num.
    weighted = hf_num * debt // (10**14 * 10**27)
    return Borrower(name, hf_num, hf_num, debt, weighted)


def test_zero_stress_never_creates_new_crossing():
    pts, meta = canonical_curve([b("a", WAD), b("b", WAD - 1)])
    assert pts[0].stress_bps == 0
    assert pts[0].newly_count == 0
    assert meta["baseline_underwater_count"] == 1


def test_uniform_stress_crosses_once():
    x = b("a", WAD)
    pts, _ = canonical_curve([x])
    crossings = [p for p in pts if p.newly_count]
    assert len(crossings) == 1
    assert crossings[0].stress_bps == 25


def test_threshold_side_disagreement_blocks():
    x = Borrower("x", WAD, WAD - 1, 10**53, 10**53)
    with pytest.raises(ValueError, match="BASELINE_THRESHOLD_SIDE_DISAGREEMENT"):
        canonical_curve([x])


def test_stressed_hf_is_monotone_nonincreasing():
    x = b("a", int(1.2 * WAD))
    vals = [stressed_hf_wad(x, s) for s in STRESS_BPS]
    assert all(a >= b for a, b in zip(vals, vals[1:]))


def test_exact_geometry_uses_rationals():
    pts, _ = canonical_curve([b("a", WAD), b("b", int(1.01 * WAD), 2 * 10**53)])
    g = exact_geometry(pts)
    assert len(g["interval_slopes_value_ray_per_percentage_point"]) == len(STRESS_BPS) - 1
    assert len(g["interior_curvatures_value_ray_per_percentage_point_squared"]) == len(STRESS_BPS) - 2
    assert all(x["denominator"] > 0 for x in g["interval_slopes_value_ray_per_percentage_point"])
