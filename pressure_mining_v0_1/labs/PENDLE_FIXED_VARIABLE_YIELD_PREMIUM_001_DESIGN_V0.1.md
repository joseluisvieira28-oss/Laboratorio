# PENDLE-FIXED-VARIABLE-YIELD-PREMIUM-001 — OUTCOME-BLIND DESIGN V0.1

Date: 2026-09-27  
Status: DESIGN_ONLY / SOURCE-METADATA REVIEW / OUTCOMES LOCKED  
Primary family: RV  
Secondary family: CARRY

## Materially new economic question

This is NOT a test that PT converges to par.

Question:
**Does the fixed yield embedded in a PT, observed point-in-time before maturity, contain a persistent economic premium versus the future variable-yield alternative represented by the same accounting-asset exposure?**

The economic object is the fixed-versus-future-variable yield differential, not contractual maturity convergence.

## Who pays / why could a premium exist?

Potential payers/forces must be treated as hypotheses, not facts:
- investors may pay for variable-yield / YT / points exposure;
- PT buyers may earn compensation for maturity lock, protocol complexity, liquidity and smart-contract risk;
- yield expectations can be wrong, creating a fixed-versus-realized-variable spread.

## Direct observables already source-verified

Pendle historical market state exposes timestamped fields including:
- impliedApy
- underlyingApy
- baseApy
- tvl

Market metadata exposes:
- chainId
- expiry
- accountingAsset
- PT / YT identities
- protocol
- points / reward metadata

## Mandatory blocker before scientific freeze

A fixed-versus-variable comparison is invalid if economically material points/rewards are silently omitted.

Before any Discovery:
1. quantify markets carrying points/reward metadata;
2. define an objective, pre-outcome economically complete population;
3. prove whether points/rewards can be valued point-in-time or exclude only through a mechanism-based rule frozen before outcomes;
4. define one primary observation horizon without looking at premium outcomes;
5. define how future variable yield is accumulated from point-in-time source data;
6. define protocol/credit/redemption impairment handling;
7. define independence unit (market/maturity, not hourly pseudo-observations);
8. preserve an untouched future/prospective confirmation path.

## Forbidden shortcuts

- raw "PT goes to par" as alpha;
- best market / best protocol / best maturity selection;
- choosing T-30/T-60/T-90 after viewing results;
- ignoring points because they are hard to value;
- treating thousands of hourly rows as thousands of independent trades;
- converting a yield-spread diagnostic directly into PnL without executable quote/fee/slippage evidence.

## Current routing

SOURCE_METADATA_FIRST.

No Discovery authority is created by this document.

## Firewall

market_outcomes_opened=false  
yield_premium_outcome_computed=false  
pnl_computed=false  
protected_holdout_opened=false  
live_trading=false  
orders=false  
exchange_mutation=false  
main_merge=false
