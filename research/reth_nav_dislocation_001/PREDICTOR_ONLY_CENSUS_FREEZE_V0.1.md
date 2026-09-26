# RETH-NAV-DISLOCATION-001 — PREDICTOR-ONLY CENSUS FREEZE V0.1

Frozen: 2026-09-26
Parent: SOURCE_GATE_FREEZE_V0.1 + SOURCE_TRANSPORT_REMEDIATION_V0.1A
Source status at freeze: SOURCE_PASS, independently confirmed and durably persisted.
Stage: PREDICTOR-ONLY / OUTCOME-BLIND.

## Purpose

Build a dense historical series of the rETH market-vs-protocol-anchor state WITHOUT opening any subsequent return, direction label, holding-period outcome, PnL, or trading result.

This stage measures only whether the proposed mechanical dislocation state can be reconstructed densely and how the predictor itself is distributed.

## Fixed protocol source

rETH:
0xae78736Cd615f374D3085123A210448E74Fc6393

For every observation block N:
- getExchangeRate() at block N;
- getTotalCollateral() at block N.

Protocol NAV:
nav_weth_per_reth = getExchangeRate / 1e18.

getTotalCollateral is retained as protocol burn-capacity state only.
No assumption is made that all collateral is frictionlessly executable at arbitrary notional.

## Fixed market source

Canonical market pool is frozen BEFORE the dense census:

Uniswap V3 rETH/WETH fee 100:
0x553e9C493678d8606d6a5ba284643dB2110Df823

Reason for selection:
- canonical Uniswap V3 factory discovery;
- exact rETH/WETH token order verified;
- complete historical state coverage across all four frozen source sentinels plus finalized in the durable SOURCE_GATE_RECEIPT;
- zero pool-source errors in that durable receipt.

No switching to another fee tier based on observed dislocation is permitted.

At every observation block N:
- slot0() at N;
- liquidity() at N;
- exact WETH/rETH market price from sqrtPriceX96.

Both tokens use 18 decimals, so:
market_weth_per_reth = sqrtPriceX96^2 / 2^192.

## Frozen predictor

Signed raw dislocation:
d_N = market_weth_per_reth / nav_weth_per_reth - 1.

Interpretation only:
- d_N < 0 means market price below protocol backing rate;
- d_N > 0 means market price above protocol backing rate.

This stage does NOT assert that either sign predicts subsequent performance.

No absolute threshold, z-score threshold, quantile trigger, or preferred sign is selected in this census.

## Frozen census blocks

Start block:
20,000,000

End boundary:
24,000,000

Cadence:
N_k = 20,000,000 + 7,200 * k
for every integer k with N_k <= 24,000,000.

This block cadence is an operational approximation to one Ethereum day and has no market-hypothesis meaning.

Blocks above 24,000,000 are not opened by this census.

## Point validity

A point is VALID only if all are true:
- exact block N exists and block hash/timestamp are retained;
- getExchangeRate succeeds at N;
- getTotalCollateral succeeds at N;
- fee-100 slot0 succeeds at N;
- fee-100 liquidity succeeds at N;
- pool liquidity > 0;
- no latest fallback;
- exact rational price components are retained.

Invalid points are not imputed and are not replaced with another pool.

## Census gate

PREDICTOR_SOURCE_CENSUS_PASS requires:
- expected grid generated exactly;
- 100% VALID block coverage after technical retry;
- zero latest fallbacks;
- zero block-number/hash mismatches;
- all outcome-closure flags false.

Transient RPC timeout/rate-limit retries are technical only and may not alter blocks or source definitions.

If 100% cannot be achieved with the frozen public source after technical retry:
PREDICTOR_SOURCE_CENSUS_BLOCKED.

## Durable output

Persist aggregate/source-safe fields only:
- expected/valid/invalid point counts;
- block range/cadence;
- protocol and pool addresses;
- min/max timestamps;
- source error counts;
- deterministic row-set SHA-256;
- descriptive predictor-only statistics for d_N;
- descriptive getTotalCollateral and liquidity statistics;
- outcome-closure flags.

Per-block rows may be retained as research evidence because they contain only public block/source/predictor state and no future outcomes.

## Forbidden

- future rETH/ETH returns;
- ETH returns;
- direction labels;
- holding horizon selection;
- PnL;
- fees/slippage optimization;
- event threshold selection after seeing future outcomes;
- live trading;
- mutation;
- main merge.

If this census passes, the next allowed step is a separate pre-outcome hypothesis/threshold freeze.
