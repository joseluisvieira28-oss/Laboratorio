# LCOD CANONICAL COLLATERAL-SIDE STRESS CURVE FREEZE V0.1

Frozen: 2026-09-25
Stage: MECHANISM / PRE-CURVE
Real curve values seen before this freeze: NO canonical block-pinned protocol-wide curve.

## Mechanical stress object

This is a protocol solvency sensitivity curve, not a forecast of an actual
market move.

At one exact finalized Ethereum block N:

- borrower population = exact block-N active-debt universe from the passing
  Borrow-event population gate;
- all reserve parameters, user dynamic configs, supplies, debts and oracle
  prices are read at the same block N;
- baseline official/reconstructed HF must satisfy existing source tolerances.

Shock semantics:
apply the same proportional negative shock ONLY to every collateral-leg oracle
value used in the HF numerator.

Debt-leg oracle values remain fixed at their block-N values.
Protocol parameters remain fixed at block N.

This intentionally measures collateral-side solvency sensitivity. It must not
be described as a realistic joint asset-price scenario.

## Frozen stress grid

Stress magnitude in percentage points:
0.00, 0.25, 0.50, 0.75, 1.00, 1.50, 2.00, 3.00, 5.00

Equivalent collateral multipliers:
1.0000, 0.9975, 0.9950, 0.9925, 0.9900, 0.9850, 0.9800, 0.9700, 0.9500

No grid modification after the canonical curve is opened.

## Borrower transition

Baseline-underwater:
HF_N < 1 before any stress.

A borrower is NEWLY_ELIGIBLE at stress x when:
- baseline HF_N >= 1;
- stressed HF_x < 1;
- and this is the first grid point at which the borrower crosses.

No borrower is counted twice.

Debt attached to a crossing is its block-N total debt value, unchanged across
the stress grid.

## Aggregate curve

For each x report:
- baseline underwater borrower count and debt;
- newly eligible borrower count at x;
- newly eligible debt at x;
- cumulative newly eligible count through x;
- cumulative newly eligible debt through x;
- total eligible debt = baseline underwater debt + cumulative newly eligible debt.

## Non-uniform-grid slope

Let x be stress magnitude in percentage points and
Y(x) = cumulative newly eligible debt.

For adjacent grid points:
slope_i = [Y(x_i) - Y(x_{i-1})] / [x_i - x_{i-1}]

Units:
debt-value units per 1 percentage-point collateral shock.

## Non-uniform-grid curvature

For interior grid point x_i:
left_slope  = [Y_i - Y_{i-1}] / [x_i - x_{i-1}]
right_slope = [Y_{i+1} - Y_i] / [x_{i+1} - x_i]

curvature_i =
2 * (right_slope - left_slope) / (x_{i+1} - x_{i-1})

Units:
debt-value units per percentage-point squared.

This replaces any naive raw second-difference interpretation on the irregular
grid. Earlier synthetic second-difference tests retain engineering value only
and have ZERO canonical-curve authority.

## Data-quality gate

A canonical curve may be computed only if:
- Borrow-event block population source PASS;
- same-block component reconstruction is available for the active population;
- every included borrower passes frozen HF reconstruction tolerance <=5e-5;
- exclusions and their debt share are reported;
- no current/latest fallback is used.

If included borrower coverage falls below 90% of block-N active-debt pairs:
CANONICAL_CURVE_SOURCE_BLOCKED.

## Scientific boundary

This curve contains no future market outcome and earns no predictive promotion.
Any later attempt to relate curve state to future returns/liquidations requires
a new pre-outcome hypothesis and separate time-series snapshots.
