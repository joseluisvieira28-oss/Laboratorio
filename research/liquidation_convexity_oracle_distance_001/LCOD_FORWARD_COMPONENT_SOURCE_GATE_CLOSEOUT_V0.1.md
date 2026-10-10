# LCOD-001 FORWARD COMPONENT SOURCE GATE CLOSEOUT V0.1

Date: 2026-09-24
Lab: LIQUIDATION-CONVEXITY-ORACLE-DISTANCE-001

## Frozen verdict

FORWARD_COMPONENT_SOURCE_RECONCILIATION_PASS
FULL_PROTOCOL_POPULATION_COVERAGE_UNPROVEN
HISTORICAL_STATE_RECONSTRUCTION_UNPROVEN
MARKET EDGE NOT TESTED

## Evidence chain

1. Official Aave MCP source capability:
   - 92 V4 reserves observed;
   - get_reserve_holders, get_user_positions, get_position_items, get_user_summary and get_reserve_details available.

2. Live component source probe:
   - 6 sampled borrowers;
   - component fields include principal, interest, balance, balanceUsd, isCollateral and reserveId;
   - reserve details include collateralFactorPct and priceUsd;
   - classification SOURCE_COMPONENT_FIELDS_PRESENT_RECONCILIATION_REQUIRED.

3. HF reconstruction V0.1:
   - 35 borrowers;
   - 47 complete debt-bearing positions;
   - sample minimum >=25 PASS;
   - display-USD precision produced a dust-related maximum relative error of 1.3178%.

4. Source-precision remediation V0.2:
   - supply valuation uses balance(main units) * priceUsd;
   - debt valuation uses (principal + interest) * priceUsd;
   - collateral capacity uses collateralFactorPct only on collateral-enabled supply;
   - 47 complete positions / 1 required-field exclusion = 97.9167% completeness;
   - no runtime call errors;
   - median relative HF error 3.532621e-6;
   - p95 2.357332e-5;
   - max 2.999854e-5;
   - max balance vs principal+interest identity error 5.684342e-14 main units.

5. Tolerance freeze:
   - canonical acceptance threshold relative_hf_error <= 5e-5 (0.005%);
   - frozen from source representation evidence only, before any liquidation or market outcome.

## Bounded curve diagnostic

The source-calibration sample can produce a deterministic liquidation-eligibility curve.
A zero-promotion-credit diagnostic on the already frozen shock grid found one bounded-sample cliff at the -3% uniform-collateral shock, corresponding to approximately 304,030.89 USD debt from one sampled position.

This is NOT a protocol-wide amount-at-risk estimate and NOT a trading signal.

## What SOURCE PASS means here

Proven:
- current V4 component data can be read prospectively;
- raw debt and collateral valuation can be reconstructed;
- protocol liquidation-boundary parameter can be bound;
- reconstructed HF agrees with Aave official health semantics inside a frozen source tolerance.

Not proven:
- every borrower is covered by the present holder sampling route;
- complete pagination/census across every reserve;
- point-in-time historical positions/parameters/oracles;
- liquidation outcomes;
- predictive relationship to CEX/DEX prices;
- profitability.

## Next authorized source action

Build an outcome-blind borrower census contract:
- paginate get_reserve_holders deterministically;
- deduplicate borrowers across reserves;
- prove cursor termination and coverage counts;
- decide before outcomes whether canonical LCOD population is full indexed census or a predeclared bounded cohort;
- then run the frozen component reconstruction over that population.

No market/liquidation outcomes may be opened by this closeout.
