# DEX-LIQUIDITY-PROVISION-001 — PRE-SOURCE AUTHORITY V0.1

Date: 2026-09-19
Status: **FROZEN / SOURCE-ONLY / OUTCOME-BLIND**
Branch: `dex-liquidity-provision-v0.1`

## 1. Mechanism

Primary edge family: **MICRO**. Secondary: **VOL**.

Economic hypothesis for a later, separately frozen Discovery: Uniswap V3 liquidity providers actively add/remove capital in response to adverse-selection and volatility risk. A persistent net withdrawal state reduces available AMM liquidity and may contain information about higher subsequent volatility/price-impact risk.

This is not CEX order-book refill, not stablecoin-peg stress, not taker-flow imbalance, not funding/OI, and not a price-indicator mutation.

Recent empirical work reports predictive information in Uniswap net liquidity provision for future volatility. That motivates a source gate only; it is not imported as a result for this lab.

## 2. Anti-duplication

Drive/GitHub search on 2026-09-19 found no canonical executed lab for WETH/USDC Uniswap V3 LP Mint/Burn net-liquidity state.

Closest prior lines:
- ORDERBOOK-RESILIENCE-001: CEX aggregated bookDepth refill; source-resolution failed.
- STABLECOIN-DEX-STRESS-001: stablecoin peg/liquidity stress; different asset/mechanism.
- AAVE-LIQUIDATION-OVERHANG-001: credit/liquidation inventory; terminal replication no-signal.

Overlap classification: **NONE / MATERIALLY DISTINCT MECHANISM**.

## 3. Frozen source target

Chain: Ethereum mainnet.
Protocol: Uniswap V3.
Pair: USDC/WETH.
Fee tier: **500 (0.05%)**.
Expected canonical pool: `0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640`.
Factory: `0x1F98431c8aD98523631AE4a59f267346ea31F984`.
USDC: `0xA0b86991c6218b36c1d19d4a2e9eb0ce3606eB48`.
WETH: `0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2`.

Pool identity must be independently confirmed by at least two frozen public Ethereum RPC endpoints using factory `getPool(USDC,WETH,500)`. No source substitution after inspection.

Historical structural source: SQD Ethereum mainnet Portal.
Frozen block transport envelope: `13,900,000..21,525,890`.
Scientific timestamp window: `2022-01-01T00:00:00Z..2024-12-31T23:59:59Z`.

2025 and 2026 are forbidden.

## 4. Source fields allowed

This gate may read only:
- block number and timestamp;
- pool address;
- topic0/event family;
- transaction hash;
- log index.

Allowed event families:
- Uniswap V3 Pool `Mint`;
- `Burn`;
- `Swap`.

Forbidden at this phase:
- log.data;
- liquidity amount;
- token amounts;
- sqrtPrice;
- tick;
- prices;
- returns;
- realized volatility;
- direction;
- PnL;
- fees/slippage;
- any post-2024 data.

## 5. Prospectively frozen source adequacy gate

`SOURCE_DATA_PASS` requires ALL:

1. >=2 independent frozen RPC endpoints return the exact expected pool address.
2. All usable RPC endpoints agree on pool identity.
3. Zero duplicate canonical `(transactionHash,logIndex)` identities.
4. At least **1,000 unique UTC days** with one or more Swap events in 2022-2024.
5. At least **100,000 Swap** events in-window.
6. At least **500 Mint** events in-window.
7. At least **500 Burn** events in-window.
8. Mint activity occurs in at least **30 distinct calendar months**.
9. Burn activity occurs in at least **30 distinct calendar months**.
10. Swap activity occurs in all three calendar years 2022, 2023 and 2024.
11. No 2025/2026 timestamp is requested or admitted.
12. No economic field/value is decoded.

Permitted terminal states:
- `SOURCE_DATA_PASS`
- `SOURCE_IDENTITY_FAILURE`
- `SOURCE_INSUFFICIENT_COVERAGE`
- `SOURCE_ACQUISITION_TECHNICAL_FAILURE`
- `PROVENANCE_FAILURE`

No source-stage state is `NO_EDGE`.

## 6. Post-source rule

A pass authorizes only a separate FINAL PRE-DISCOVERY protocol.

Before opening Mint/Burn amounts or future volatility, that protocol must freeze:
- exact net-liquidity transform;
- observation cadence/lookback;
- future volatility definition/horizon;
- timing/leakage rules;
- inference;
- costs/execution only if an executable strategy is later proposed;
- Discovery/replication split and promotion gates.

No post-outcome threshold, horizon, pool, direction or regime rescue.

## 7. Safety

Research only. No live trading, orders, wallets, authenticated exchange APIs, exchange mutation, alerts/webhooks, capital deployment, main merge, 2025/2026 market data, returns or PnL.
