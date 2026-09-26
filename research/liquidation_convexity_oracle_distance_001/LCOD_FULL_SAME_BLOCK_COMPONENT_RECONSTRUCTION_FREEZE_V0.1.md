# LCOD FULL SAME-BLOCK COMPONENT RECONSTRUCTION GATE V0.1

Frozen: 2026-09-25
Stage: SOURCE / COMPONENT RECONSTRUCTION
Curve: CLOSED
Market/liquidation outcomes: CLOSED

## Prerequisite

A durable LCOD block-pinned active-population receipt must classify PASS and
provide:
- finalized Ethereum block N and block hash;
- canonical active borrower×Spoke set SHA256;
- active pair count.

The component run MUST reproduce the exact same active-set SHA before any
component result is accepted.

## Source authority

Aave V4 source:
aave/aave-v4 @ 40232a0a91150d8ee5cab42bd3ddd0baf4ffff9f

Relevant exact semantics:

1. SpokeUtils.toValue:
amount * price * 10 ** (18 - assetDecimals)

Value units:
1e26 Value = 1 USD.

2. Collateral:
Spoke.getUserSuppliedAssets(reserveId,user) is exactly
Hub.previewRemoveByShares(assetId, suppliedShares).

3. Weighted collateral:
sum(collateralFactorBps * collateralValue).

4. Debt:
debtRay = drawnShares * drawnIndex + premiumDebtRay
totalDebtValueRay += toValue(debtRay, decimals, price)

5. Health factor:
floor(weightedCollateralBpsValue * 1e14 * 1e27 / totalDebtValueRay)

All reads must use exactly block N.

## Required per-active-pair reads

For each active (Spoke,user) pair:
- getUserAccountData(user);
- getReserveCount();
- ORACLE();
- getUserReserveStatus(reserveId,user);
- getReserve(reserveId);
- getUserPosition(reserveId,user);
- getReservePrice(reserveId);
- getUserSuppliedAssets(reserveId,user) for active collateral;
- getDynamicReserveConfig(reserveId,userDynamicConfigKey) for active collateral;
- getUserPremiumDebtRay(reserveId,user) for borrowing reserves;
- Hub.getAssetDrawnIndex(assetId) for borrowing reserves.

Static reserve/oracle/index values may be cached only inside the same block-N
run.

## Exact reconstruction checks

For an included pair:
- reconstructed component totalDebtValueRay MUST equal official
  getUserAccountData.totalDebtValueRay exactly;
- reconstructed HF relative error versus official HF MUST be <= 5e-5
  (existing frozen tolerance);
- all scientific calls must be block-pinned to N;
- no latest/current fallback.

A pair failing any read or equality/tolerance check is EXCLUDED with an explicit
reason. No imputation.

## Durable row

Persist only:
- SHA256(Spoke::user);
- official HF WAD;
- reconstructed HF WAD;
- official totalDebtValueRay;
- reconstructed totalDebtValueRay;
- weightedCollateralBpsValue;
- active collateral count;
- borrow count;
- pass/exclusion reason.

Raw wallet addresses are forbidden in durable receipts/artifacts.

## Coverage gates

Let ACTIVE be the exact active-pair population from the prerequisite receipt.

COUNT_COVERAGE =
included active pairs / total active pairs.

DEBT_COVERAGE =
sum official totalDebtValueRay of included pairs /
sum official totalDebtValueRay of all active pairs.

FULL_SAME_BLOCK_COMPONENT_PASS requires:
- reproduced active-set SHA == prerequisite active-set SHA;
- 100% of active pairs receive block-N UAD classification;
- COUNT_COVERAGE >= 0.90;
- DEBT_COVERAGE >= 0.90;
- every included pair satisfies exact debt equality and HF tolerance;
- zero raw-wallet persistence.

Because Aave Value uses one chain-wide USD Value unit (1e26 per USD), debt
coverage is comparable across the pinned Ethereum V4 Spokes. Ratios are computed
directly in ValueRay integer units; no floating conversion is required.

## Output boundary

Passing this gate authorizes opening the already-frozen canonical
collateral-side stress curve only.

It does NOT authorize:
- future liquidation outcomes;
- market returns;
- predictive thresholds;
- PnL;
- orders, wallets, exchange mutation or live trading.
