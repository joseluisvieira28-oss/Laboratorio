# RETH-NAV-DISLOCATION-001 — SOURCE GATE FREEZE V0.1

Frozen: 2026-09-26
Lab ID: RETH-NAV-DISLOCATION-001
Primary family: MR
Secondary family: RV
Governance: RESEARCH-ONLY / OUTCOME-BLIND SOURCE GATE

## Scientific question

Can a defensible historical point-in-time series be reconstructed for the dislocation between:
1. Rocket Pool's own rETH/ETH protocol exchange-rate anchor; and
2. an executable on-chain rETH/WETH market price surface;

without opening future returns, liquidation outcomes, direction labels, PnL, or trading results?

This source gate tests DATA FEASIBILITY ONLY.
It does not test whether a premium/discount mean-reverts.

## Mechanism statement

rETH is backed by ETH at a variable protocol exchange rate.
A market price that deviates from the protocol anchor may represent a conversion/liquidity dislocation.

The existence, sign, speed, or profitability of any reversion is NOT assumed at this stage.

## Canonical protocol anchor

Token:
rETH mainnet
0xae78736Cd615f374D3085123A210448E74Fc6393

Authority:
Rocket Pool rETH contract method:
getExchangeRate()(uint256)

Historical protocol-anchor requirement:
- query the exact rETH contract at explicit historical Ethereum block numbers;
- retain block number + block hash + block timestamp;
- no latest/current substitution for historical points;
- raw return/PnL series forbidden.

## Canonical market-source probe

Primary source candidate:
Uniswap V3 Ethereum rETH/WETH pools discovered directly from the canonical factory.

Factory:
0x1F98431c8aD98523631AE4a59f267346ea31F984

WETH:
0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2

Probe fee tiers:
100, 500, 3000, 10000.

For each discovered non-zero pool:
- read token0/token1;
- read current liquidity;
- query slot0 at explicit historical blocks;
- derive raw rETH/WETH price from sqrtPriceX96 only when token ordering is unambiguous;
- preserve block-pinned source evidence.

No pool is selected because its historical dislocation looks attractive.
Source selection, if multiple pools pass, must be based on pre-outcome source quality/liquidity criteria only.

## Historical coverage probe

The initial MVE uses fixed block numbers:
18,000,000
20,000,000
22,000,000
24,000,000

and one current finalized block resolved during the run.

These blocks are source-coverage sentinels only.
They are not Discovery observations and earn zero promotion credit.

## Source PASS

PASS requires:
- rETH getExchangeRate succeeds at every sentinel block;
- exact block hash/timestamp retrieved for every sentinel;
- at least one canonical rETH/WETH Uniswap V3 pool is discovered;
- at least one discovered pool returns slot0 successfully at >=3 historical sentinel blocks;
- token ordering is verified;
- zero silent latest fallbacks;
- no market returns, future outcomes, PnL, or mutation opened.

## Source BLOCKED

SOURCE_BLOCKED if:
- historical archive state cannot be read defensibly from public/free infrastructure;
- rETH protocol anchor cannot be reconstructed block-pinned;
- no usable historical rETH/WETH pool state can be reconstructed;
- provenance cannot be tied to exact block numbers/hashes.

## Forbidden

- selecting a premium/discount threshold;
- choosing a holding horizon;
- looking at subsequent ETH/rETH returns;
- labeling mean reversion success/failure;
- fitting direction;
- fee rescue;
- opening PnL;
- live trading;
- exchange/wallet mutation;
- main merge.

If this gate passes, the next allowed step is a separate pre-outcome mechanism/data freeze.
