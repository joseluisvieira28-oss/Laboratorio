# CBETH-REDEMPTION-BASIS-001 — SOURCE GATE FREEZE V0.1

Frozen: 2026-09-27
Lab ID: CBETH-REDEMPTION-BASIS-001
Primary family: MR
Secondary family: RV
Governance: RESEARCH-ONLY / OUTCOME-BLIND SOURCE GATE

## Economic object

Coinbase Wrapped Staked ETH (cbETH) has an explicit protocol conversion rate representing underlying staked ETH units per cbETH.

The market price of cbETH is not pegged by Coinbase and may differ from the protocol conversion rate.

Coinbase redemption is access-constrained and may involve a material waiting period. Therefore a cbETH/ETH market-vs-conversion basis can exist without implying frictionless instantaneous arbitrage.

This gate tests only whether both sides of that basis can be reconstructed historically and canonically.

It does NOT test convergence, direction, holding period, trading returns or PnL.

## Canonical protocol anchor

Official Ethereum cbETH contract:
0xBe9895146f7AF43049ca1c1AE358B0541Ea49704

Primary historical protocol state:
exchangeRate()(uint256)

Interpretation:
protocol ETH-units-per-cbETH conversion anchor.

For every source observation:
- query exact historical Ethereum block N;
- retain block number, block hash and timestamp;
- no latest/current substitution;
- no mutable webpage/API value may substitute for historical on-chain state.

The source gate may additionally read totalSupply() descriptively, but total supply is not part of the basis definition.

## Canonical market-source probe

Primary market venue:
Uniswap V3 Ethereum direct cbETH/WETH pools discovered from the canonical factory.

Uniswap V3 factory:
0x1F98431c8aD98523631AE4a59f267346ea31F984

WETH:
0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2

Probe fee tiers:
100, 500, 3000, 10000.

For every non-zero pool discovered:
- verify token0/token1 exactly equals cbETH/WETH;
- read liquidity;
- read slot0 at exact historical blocks;
- derive exact WETH-per-cbETH market price from sqrtPriceX96;
- retain exact block number/hash/timestamp.

No pool may be selected because its later basis/outcomes look favorable.

## Fixed historical source sentinels

The source-only MVE uses:

16,000,000
18,000,000
20,000,000
22,000,000
24,000,000

plus one current finalized block resolved during the run.

These are source-coverage sentinels only.
They are not Discovery observations and earn zero promotion credit.

## Source PASS

SOURCE_PASS requires ALL:
- cbETH exchangeRate succeeds at every fixed sentinel and finalized;
- exact block hash/timestamp exists for every point;
- exchangeRate > 0;
- at least one canonical direct cbETH/WETH Uniswap V3 pool is discovered;
- one and the same direct pool has positive liquidity and valid slot0 at >=4 of the 5 fixed historical sentinels plus finalized;
- token ordering is verified;
- zero silent latest fallback;
- zero decode ambiguity;
- no future outcome, return or PnL opened.

## Source BLOCKED

SOURCE_BLOCKED if:
- official historical exchangeRate cannot be reconstructed block-pinned;
- no direct cbETH/WETH pool has the frozen historical coverage;
- archive state is unavailable from defensible free/public infrastructure;
- provenance cannot be tied to exact canonical blocks.

No synthetic cbETH/USD ÷ ETH/USD ratio may rescue a direct-pool failure inside this LAB_ID.

## Mechanism firewall

SOURCE_PASS does NOT establish edge.

If Source PASSes, the next permissible stage is a separately frozen predictor-only basis census.

Before any outcome is opened that future freeze must define:
- one fixed market pool based only on source coverage/liquidity quality;
- exact signed basis formula;
- calibration interval;
- threshold rule;
- future Discovery/OOS/holdout partitions;
- no-rescue decision tree.

## Forbidden

- selecting a discount/premium threshold now;
- choosing a holding horizon now;
- looking at future cbETH/ETH or ETH returns;
- choosing a pool from profitable outcomes;
- synthetic venue rescue;
- PnL;
- live trading;
- exchange/wallet mutation;
- main merge.

Promotion credit = 0.
