# AAVE-RISK-PARAMETER-SHOCK-001 — PRIMARY MECHANISM FREEZE V0.1

Freeze timestamp: 2026-09-18 UTC

## Status

PRE-OUTCOME / SOURCE-CENSUS IN PROGRESS / NO ECONOMIC OUTCOMES AUTHORIZED.

This file is committed before the first source-census result is known. Its purpose is to prevent post-census event-family selection.

## Primary family

CREDIT, secondary EVENT / forced-flow.

## Frozen primary mechanism

The only primary mechanism eligible for a later protocol is a **decrease in Aave V3 collateral liquidationThreshold** emitted through:

`CollateralConfigurationChanged(address,uint256,uint256,uint256)`

for the canonical Ethereum V3 PoolConfigurator.

The shock is:

`new_liquidation_threshold < immediately_pre_shock_liquidation_threshold`

for the same collateral asset.

BorrowCapChanged, SupplyCapChanged, ReserveFrozen, ReservePaused, DebtCeilingChanged, eMode changes, reserve-factor changes and other configurator events remain source-census context only. They may NOT be substituted as the primary mechanism after census counts are observed.

## Economic rationale fixed before counts/outcomes

A lower liquidation threshold mechanically reduces the collateral value that can support an existing debt position under Aave's health-factor construction. Holding borrower balances and oracle prices constant, this can move affected borrowers closer to, or through, liquidation eligibility. The hypothesized transmission is therefore:

risk-parameter tightening
→ lower borrower solvency margin
→ deleveraging / repayment and/or liquidation pressure
→ only after mechanism validation, a separately frozen market-impact MVE may be considered.

This is materially different from AAVE-LIQUIDATION-OVERHANG-001, where the predictor is borrower state near liquidation under the prevailing configuration. Here the causal input is an exogenous protocol configuration change.

## Known failure mode fixed before counts/outcomes

Aave governance/risk changes are often public before execution. Borrowers may pre-emptively repay, add collateral or migrate positions before the on-chain configuration change. If so, execution-time threshold reductions can contain little incremental forced-flow information. Deep liquidity or small affected balances can also absorb the shock.

## Current gate

The running source census is structural only and requests no log.data. It is allowed to answer only whether the historical configurator event population exists and is auditable through 2024-12-31.

No threshold value, borrower state, liquidation outcome, market price, return or PnL may be opened from the census.

## If source sample is sufficient

A separate FINAL_PRE_DISCOVERY_PROTOCOL must be created prospectively before any outcome. It must freeze:
- exact reconstruction of the immediately pre-shock liquidation threshold;
- exact rule for identifying decreases;
- borrower/state exposure snapshot timing;
- treatment of governance announcement vs execution timing;
- on-chain mechanism target and horizon;
- sample gates and inference;
- any later market-impact MVE;
- costs/execution only if a market MVE is eventually authorized;
- multiple-testing policy;
- 2025/2026 firewall.

## If source sample is insufficient

Close as INSUFFICIENT_SOURCE_SAMPLE. Do not switch the primary mechanism to another configurator event family to rescue the lab.

## Hard firewall

No market prices.
No returns.
No PnL.
No health factor.
No liquidation-overhang predictor.
No future liquidation outcomes.
No 2025/2026.
No live trading.
No orders.
No wallets.
No exchange mutation.
No main merge.
