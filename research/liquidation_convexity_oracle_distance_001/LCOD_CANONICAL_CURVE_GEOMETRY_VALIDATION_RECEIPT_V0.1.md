# LCOD CANONICAL CURVE GEOMETRY VALIDATION RECEIPT V0.1

Date: 2026-09-25
Scope: pure offline mathematics; no protocol or market outcome data.

Tests:
- linear function on irregular grid -> constant slope, zero curvature: PASS;
- quadratic y = 2x^2 + 4x + 1 -> recovered curvature = 4 at every interior point: PASS;
- non-increasing x grid rejected by implementation contract.

Result: PASS.

This validates only the non-uniform-grid slope/curvature arithmetic frozen in
LCOD_CANONICAL_COLLATERAL_STRESS_CURVE_FREEZE_V0.1.
It earns zero predictive or promotion credit.
