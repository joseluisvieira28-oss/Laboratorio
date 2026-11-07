# LCOD CANONICAL COLLATERAL STRESS CURVE — INTEGER/RATIONAL IMPLEMENTATION ADDENDUM V0.1A

Frozen: 2026-09-25
Parent: LCOD_CANONICAL_COLLATERAL_STRESS_CURVE_FREEZE_V0.1
Canonical curve values seen before this addendum: NO.

## Purpose

The parent freeze applies one identical proportional negative shock to every
collateral-leg oracle contribution while debt and protocol parameters remain
fixed at block N.

Because this is a mechanical solvency stress object rather than a simulated
onchain oracle update, V0.1A freezes the exact arithmetic and removes ambiguity
about per-oracle integer rounding.

## Canonical reconstructed state per included borrower

Persisted component quantities:
- W = sum(collateralFactorBps * collateralValue_N)
  in Value * BPS units;
- D = official/reconstructed totalDebtValueRay_N
  in ValueRay units;
- HF_official_N;
- HF_reconstructed_N.

The component gate already requires exact D equality and HF reconstruction
within <=5e-5.

## Uniform collateral multiplier

For each frozen stress magnitude x, use an exact integer multiplier m / 10000:

0.00% -> 10000
0.25% -> 9975
0.50% -> 9950
0.75% -> 9925
1.00% -> 9900
1.50% -> 9850
2.00% -> 9800
3.00% -> 9700
5.00% -> 9500

No floating point is permitted in borrower crossing decisions.

## Stressed health factor

For multiplier m:

HF_x =
floor(
  W * m * 1e14 * 1e27
  /
  (10000 * D)
)

This scales the complete collateral-side weighted numerator by the exact common
rational shock. It is mathematically the frozen uniform collateral-price stress
before introducing any fictitious per-feed EVM integer rounding.

Do NOT:
- floor each individual oracle feed first;
- shock debt prices;
- refresh dynamic configs;
- use market prices outside block N;
- introduce asset-specific correlations.

## Baseline authority and crossing

Baseline underwater status uses official block-N health factor:
HF_official_N < 1e18.

Only borrowers with HF_official_N >= 1e18 are eligible to become
NEWLY_ELIGIBLE.

At stress x:
NEWLY_ELIGIBLE iff canonical stressed HF_x < 1e18 and no smaller frozen stress
already crossed.

Debt attached to a crossing:
official block-N totalDebtValueRay D.

## Aggregate arithmetic

Counts are exact integers.
Debt sums remain exact ValueRay integers.

For human-readable USD only:
1 USD = 1e26 Value and therefore 1e53 ValueRay.
Any displayed USD conversion is descriptive and cannot be used for a gate.

Slope and curvature use the parent non-uniform stress grid and exact debt sums.
Implementations should retain rational numerator/denominator internally and
only format decimals for presentation.

## Gate boundary

This addendum changes no source threshold, population, shock grid or outcome.
It exists solely to make the already-frozen mechanical curve deterministic
before the first canonical curve is opened.
