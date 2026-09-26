# DUAL-LST-RV-001 — SOURCE / DATA GATE FREEZE V0.1

Frozen: 2026-09-27
Stage: SOURCE-ONLY / OUTCOME-BLIND

## Economic mechanism

Test feasibility of a naturally hedged relative-value state between two liquid staking tokens:

- Rocket Pool rETH;
- Lido wstETH.

The future research object, if a later freeze authorizes it, is the deviation between:

1. market rETH/wstETH relative price; and
2. protocol-native relative NAV implied by the two independent staking-token conversion rates.

This is economically distinct from closed RETH-NAV-DISLOCATION-001:
- parent compared rETH market value against rETH NAV;
- this child requires TWO independent protocol anchors and a directly tradable cross-LST relative market;
- the target is relative mispricing with common ETH beta substantially cancelled.

No threshold, direction, holding horizon or outcome test is defined at this source gate.

## Canonical contracts

Ethereum mainnet.

rETH:
0xae78736Cd615f374D3085123A210448E74Fc6393

wstETH:
0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0

Uniswap V3 factory:
0x1F98431c8aD98523631AE4a59f267346ea31F984

Multicall3:
0xcA11bde05977b3631167028862bE2a173976CA11

## Protocol-native anchors

rETH anchor:
getExchangeRate() -> ETH value per rETH.

wstETH anchor:
stEthPerToken() or getStETHByWstETH(1e18) -> stETH value per wstETH.

At SOURCE stage, stETH is treated only as the protocol accounting unit of wstETH.
No assumption that stETH=ETH for market PnL is permitted.

## Market discovery

Query Uniswap V3 factory getPool(rETH,wstETH,fee) for:
100, 500, 3000, 10000.

Do not preselect a fee tier based on later price behavior.

A market candidate is source-usable only if:
- pool address nonzero;
- token0/token1 exactly the two frozen tokens;
- slot0 readable;
- liquidity > 0 at required historical sentinels.

## Historical sentinels

Exact blocks:
20,000,000
22,000,000
24,000,000
finalized at run start.

For each usable pool and both protocol anchors:
- exact block-pinned reads;
- retain block number/hash/timestamp;
- no latest fallback.

## SOURCE_PASS

Requires:
- rETH anchor valid at all sentinels;
- wstETH anchor valid at all sentinels;
- >=1 rETH/wstETH pool valid with positive liquidity at all sentinels where that pool already exists;
- exact token ordering proven;
- no decode/source errors on the selected source path;
- no market returns, future outcomes or PnL opened.

If no direct cross-LST pool has sufficient historical existence/liquidity:
SOURCE_BLOCKED for this exact direct-market design.

No rescue through synthetic rETH/ETH divided by wstETH/ETH is allowed inside this exact source gate.

## Boundary

SOURCE_PASS earns zero edge/promotion credit.

Forbidden at this stage:
- future returns;
- convergence outcomes;
- direction;
- threshold mining;
- PnL;
- execution mutation;
- live trading;
- merge to main.
