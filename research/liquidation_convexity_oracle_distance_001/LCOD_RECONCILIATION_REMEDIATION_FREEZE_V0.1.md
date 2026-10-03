# LCOD FULL-CENSUS RECONCILIATION REMEDIATION PROBE FREEZE V0.1

Frozen: 2026-09-24
Stage: SOURCE / REPRESENTATION ONLY
Market and liquidation outcomes: CLOSED

## Trigger

The four-group source scale produced:
- 2,386 debt-bearing indexed borrowers;
- 2,146 eligible under the frozen <=5e-5 HF error rule;
- 89.941324% overall coverage;
- 234 HF_RECONCILIATION_FAIL;
- 6 component-incomplete exclusions.

The existing 90% coverage gate and 5e-5 HF tolerance are NOT changed.

## Two source-level failure mechanisms to test

A. PRICE STALENESS
The V0.1 full-group engine caches get_reserve_details, including priceUsd,
while official per-position health factor is read borrower-by-borrower. A long
group run can therefore compare a later official HF with earlier cached prices.

B. USER DYNAMIC CONFIGURATION
Aave V4 source code computes health factor using each collateral
UserPosition.dynamicConfigKey and then
getDynamicReserveConfig(reserveId, dynamicConfigKey).collateralFactor.
Using only the reserve's current collateralFactor may therefore disagree with
the user's stored configuration.

## Frozen diagnostic cohort

- deterministic group: 4567
- enumerate borrowers exactly as in the existing full-census engine
- sort lowercase wallets lexicographically
- select the first 24 borrower-position cases that fail the existing cached
  current-factor reconstruction at relative error > 5e-5.

No market outcome participates in cohort selection.

## Frozen reconstructions

For each selected failure compute:

R0 BASELINE:
cached reserve price + current reserve collateralFactor

R1 FRESH_CURRENT:
fresh get_reserve_details immediately after that borrower's component reads +
current reserve collateralFactor

R2 FRESH_DYNAMIC:
same fresh prices + collateralFactor read on-chain from:
getUserPosition(reserveNumericId,user).dynamicConfigKey
then
getDynamicReserveConfig(reserveNumericId,dynamicConfigKey).collateralFactor

Debt remains principal + interest with fresh reserve price.

## Interpretation

- PRICE_STALENESS_CONFIRMED if >=90% of diagnosed baseline failures pass the
  unchanged 5e-5 tolerance under R1.
- DYNAMIC_CONFIG_CONFIRMED if R1 does not reach 90% but >=90% pass under R2.
- MIXED_SOURCE_REMEDIATION if neither alone reaches 90% but R2 materially
  improves and at least 75% pass.
- SOURCE_RECONCILIATION_UNRESOLVED otherwise.

No result permits tolerance widening or market-outcome access.
