# DUAL-LST-RV-001 — PREDICTOR-ONLY CENSUS FREEZE V0.1

Frozen: 2026-09-27
Prerequisite authority:
DUAL_LST_RV_001_SOURCE_GATE_RECEIPT_V0.1B.json with classification SOURCE_PASS.

Stage: PREDICTOR-ONLY / OUTCOME-BLIND.

## Pool selection frozen before predictor distribution

If exactly one direct rETH/wstETH Uniswap V3 pool passes all four source sentinels, use it.

If multiple pools pass all four sentinels, choose deterministically by:

1. highest MINIMUM raw Uniswap V3 liquidity across the four sentinels;
2. if tied, lower fee tier;
3. if still tied, lexicographically lower pool address.

No market-dislocation statistic or later outcome may influence pool selection.

## Common-numeraire protocol NAV

For every block N:

rETH protocol accounting anchor:
R_N = getExchangeRate / 1e18
units: ETH per rETH.

Lido common-numeraire proof:
stETH totalSupply == getTotalPooledEther > 0.

wstETH protocol accounting anchor:
W_N =
(stEthPerToken / 1e18)
* (getTotalPooledEther / stETH totalSupply)

units: protocol-accounting ETH per wstETH.

Relative protocol NAV:
NAV_N = R_N / W_N
units: wstETH per rETH.

No market stETH/ETH price is used in NAV_N.

## Direct market price

Use only the selected direct rETH/wstETH Uniswap V3 pool.

Both assets use 18 decimals.

If token0 == rETH and token1 == wstETH:

M_N = sqrtPriceX96^2 / 2^192

units: wstETH per rETH.

If token0 == wstETH and token1 == rETH:

M_N = 2^192 / sqrtPriceX96^2

units: wstETH per rETH.

Any other token ordering is invalid.

## Frozen predictor

Signed direct relative-NAV dislocation:

d_N = M_N / NAV_N - 1.

Interpretation only:
- d_N < 0: rETH is cheaper versus wstETH than the protocol-accounting relative NAV;
- d_N > 0: rETH is richer versus wstETH than the protocol-accounting relative NAV.

No convergence assumption is opened by this census.

## Frozen calibration census grid

Start:
20,000,000

End boundary:
24,000,000

Cadence:
N_k = 20,000,000 + 7,200*k
for all integer k with N_k <= 24,000,000.

Expected count:
556.

The cadence is an operational daily approximation and is not a fitted market parameter.

## Valid point

A point is valid only if:
- exact block N and canonical hash H are retained;
- all historical state calls are EIP-1898 blockHash-pinned with requireCanonical=true;
- rETH anchor >0;
- wstETH anchor >0;
- stETH totalSupply == getTotalPooledEther >0;
- selected pool pair identity exact;
- slot0 succeeds;
- liquidity >0;
- no latest fallback.

No imputation, nearest-block substitution or alternate-pool substitution.

## Census gate

PREDICTOR_CENSUS_PASS requires:
- 556 / 556 valid;
- zero block-hash/source/decode errors;
- one selected pool fixed by the pre-frozen rule;
- deterministic row-set SHA-256;
- all outcome/PnL/trading flags false.

If not 556/556 after transport-only retry:
PREDICTOR_CENSUS_BLOCKED.

## Durable predictor-only output

May contain:
- block/hash/timestamp;
- protocol anchors;
- pool state;
- exact market relative price;
- exact relative NAV;
- exact d_N;
- source/pool selection evidence;
- descriptive d_N distribution.

Forbidden:
- future d outcomes;
- returns;
- convergence labels;
- threshold selection after future outcomes;
- PnL;
- OOS/holdout;
- live trading.

Promotion credit = 0.
