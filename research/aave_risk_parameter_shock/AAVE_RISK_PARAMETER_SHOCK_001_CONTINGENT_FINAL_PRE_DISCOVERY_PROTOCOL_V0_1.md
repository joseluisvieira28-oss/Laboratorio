# AAVE-RISK-PARAMETER-SHOCK-001 — CONTINGENT FINAL PRE-DISCOVERY PROTOCOL V0.1

Date: 2026-09-18
Status: FROZEN BEFORE PRIMARY MECHANISM CENSUS RESULT / CONTINGENT ON MECHANISM_CENSUS_PASS
MVE: ARPS-LT-DOWN-LIQCOUNT-H24-001

## Activation condition

This protocol may execute only if the exact primary mechanism census returns MECHANISM_CENSUS_PASS under its frozen independence/sample gate.

If the mechanism census returns INSUFFICIENT_PRIMARY_MECHANISM_SAMPLE or any provenance/technical failure, this Discovery does not execute.

## Scientific question

After a prospectively defined Aave V3 Ethereum liquidationThreshold decrease episode, do LiquidationCall events using the affected assets as collateral increase in the following 24 hours relative to the preceding 24 hours?

## Economic mechanism

A lower liquidationThreshold mechanically reduces the collateral contribution allowed before liquidation eligibility. If materially binding for existing borrowers, threshold tightening should increase forced deleveraging/liquidation pressure after execution. The main failure mode is anticipation: borrowers can repay/add collateral before governance execution, making execution-time forced flow negligible.

## Event population

Use only the exact independent threshold-decrease episodes emitted by AAVE-RISK-PARAMETER-SHOCK-001_PRIMARY_MECHANISM_CENSUS.
No asset, magnitude, direction or subgroup selection.

## Clean episode eligibility

For each episode:
- episode_start = earliest threshold-decrease transaction timestamp in the episode;
- episode_end = latest threshold-decrease transaction timestamp in the episode;
- affected_assets = union of all collateral assets with a frozen threshold decrease inside the episode.

An episode is Discovery-eligible only if:
- there is no other frozen threshold-decrease transaction in [episode_start - 24h, episode_start);
- there is no other frozen threshold-decrease transaction in (episode_end, episode_end + 24h];
- both complete 24-hour windows are inside the frozen historical envelope.

This exclusion uses treatment timing only and is applied before LiquidationCall counts are inspected.

Discovery sample gate: at least 12 eligible clean episodes, at least 4 unique affected assets across them, and at least 2 UTC calendar years. Failure => DISCOVERY_INSUFFICIENT_SAMPLE, not NO_EDGE.

## Outcome source

Canonical Aave V3 Ethereum Pool:
0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2

Event:
LiquidationCall(address,address,address,uint256,uint256,address,bool)

Use canonical on-chain logs only. Deduplicate by transactionHash + logIndex.

## Primary outcome — fixed

For each eligible episode i:
- PRE_i = number of canonical LiquidationCall events whose collateralAsset is in affected_assets during [episode_start - 24h, episode_start);
- POST_i = number of canonical LiquidationCall events whose collateralAsset is in affected_assets during (episode_end, episode_end + 24h];
- D_i = POST_i - PRE_i.

Events inside the governance episode itself are not counted in PRE or POST.
No liquidation notional, oracle price or USD conversion is required for the primary MVE.

Frozen expected direction: mean(D_i) > 0.

## Primary inference

Primary statistic: arithmetic mean of D_i across eligible episodes.
Primary null: post and pre labels are exchangeable within episode.
Use a one-sided paired randomization test:
- if N <= 20, enumerate all 2^N pre/post swaps exactly;
- if N > 20, use 100,000 Monte Carlo within-episode swaps;
- Monte Carlo seed: 20260918.

Also report a 10,000-resample episode bootstrap percentile 95% CI for mean(D_i), seed 20260919.

## Frozen Discovery PASS gates — all required

1. Discovery sample gate passes.
2. Mean D_i > 0.
3. Median D_i >= 0.
4. One-sided paired randomization p < 0.05.
5. Bootstrap 95% lower bound for mean D_i > 0.
6. At least 2 represented calendar years have non-negative mean D_i.
7. No single episode contributes more than 35% of total positive D_i.
8. Source/provenance/firewall clean.

If sample gate passes but any PASS gate fails:
DISCOVERY_NO_FORCED_FLOW_MECHANISM

If all pass:
DISCOVERY_FORCED_FLOW_MECHANISM_PASS_REQUIRES_SEPARATE_MARKET_MVE

A pass is not a trading edge, not Tier 2/Tier 1, and does not authorize market-return testing automatically.

## Hard firewall

Forbidden in this Discovery:
- BTC/ETH/alt market prices;
- spot/perp returns;
- PnL/PF/win rate/drawdown;
- execution costs;
- 2025/2026 outcomes;
- changing horizon after results;
- threshold magnitude filters;
- asset/subgroup rescue;
- switching to repay counts or another outcome after seeing results;
- live trading/orders/wallets/exchange mutation/main merge.

Only a mechanism PASS may justify a separate prospectively frozen market-impact MVE.
