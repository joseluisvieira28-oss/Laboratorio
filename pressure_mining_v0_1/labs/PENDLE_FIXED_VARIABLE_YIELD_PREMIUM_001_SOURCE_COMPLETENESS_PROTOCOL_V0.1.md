# PENDLE-FIXED-VARIABLE-YIELD-PREMIUM-001 — SOURCE COMPLETENESS PROTOCOL V0.1

Date: 2026-09-27
Status: FROZEN_SOURCE_ONLY / OUTCOMES LOCKED
Primary family: RV
Secondary family: CARRY

## Purpose

Determine whether a scientifically usable, point-in-time source population exists for a future fixed-versus-variable yield test without computing any yield premium, trade return or PnL.

## Economic-definition correction

The raw PT-maturity-convergence question is already adjudicated MECHANISM_DESCRIPTIVE. This protocol applies only to the materially distinct fixed-versus-future-variable yield question.

Pendle's documented `underlyingApy` includes underlying interest plus tokenized underlying reward APR. The v3 historical endpoint can expose APY breakdowns. Off-chain / non-tokenized points remain a separate economic component and must not be silently valued at zero.

## Objective metadata population

For this source gate only:

1. chainId = 1 (Ethereum);
2. market expiry strictly before 2025-01-01 UTC;
3. immutable market address and expiry present;
4. accountingAsset metadata present;
5. PT and YT identity metadata present where exposed by the public API;
6. non-empty `points` metadata => POINTS_CONTAMINATED for the future economic question;
7. empty/no `points` metadata => POINTS_FREE_SOURCE_CANDIDATE.

No market is included/excluded because of implied APY, future realized yield, return, profitability, protocol performance or any post-expiry outcome.

## Historical-source probe

Sort POINTS_FREE_SOURCE_CANDIDATE markets deterministically by market address and probe the first 10 only.

For each probe:
- call the official v3 historical endpoint with `includeApyBreakdown=true`;
- preserve HTTP/source hash;
- record only source-coverage metadata and schema keys;
- do not emit APY values, prices, premium values, returns or PnL.

## What this gate may decide

- SOURCE_COMPLETENESS_PASS
- SOURCE_COMPLETENESS_PARTIAL
- SOURCE_BLOCKED
- INSUFFICIENT_POINTS_FREE_POPULATION
- PROVENANCE_FAILURE

It cannot decide NO_EDGE, Tier status, direction, entry timing or economic profitability.

## What remains forbidden

- computing fixed-minus-realized-variable premium;
- choosing a T-30/T-60/T-90 observation horizon after seeing economic outcomes;
- choosing a winning protocol/accounting asset;
- treating hourly/daily rows as independent trades;
- using markets with economically material unpriced points unless a later prospectively frozen point-in-time valuation method exists;
- opening 2025+ confirmation outcomes;
- live trading, orders, wallets, exchange mutation, capital or paid data.

## Future gate

Only if source completeness passes may a separate pre-outcome Discovery contract be frozen. That future contract must define one mechanism-based observation horizon, the variable-yield accumulation convention, independence unit, protocol/default impairment treatment, execution/friction model and an untouched validation block before any outcome is opened.
