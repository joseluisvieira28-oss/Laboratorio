# STABLECOIN-EXCHANGE-FLOW-001 — SOURCE REMEDIATION 001

STATUS: FROZEN PRE-OUTCOME / SOURCE GATE ONLY

## Why remediation is allowed

The original Coin Metrics route failed before any BTC outcome was opened. Community timeseries did not support the requested USDT exchange-flow metrics at 1d; the Pro route required authorization. Coin Metrics reference metadata also states that the exchange-flow series reflects addresses currently known to belong to the entity, which does not satisfy this lab's strict point-in-time label requirement by itself.

This remediation changes the SOURCE/MEASUREMENT SCOPE before outcomes. It does not rescue or reinterpret any economic result because no economic result exists.

## New MVE ID

`SEF-BINANCE-PUBLIC-USDT-ETH-1D-001`

## Frozen point-in-time entity universe

Authority: Binance public transparency post first published 2022-11-10, listing hot/cold wallet addresses and a snapshot at 2022-11-10 00:00 UTC. Binance explicitly states that the list is not complete.

Only the ETH-network addresses explicitly listed in the USDT rows of that publication are in the frozen basket:

1. `0x47ac0fb4f2d84898e4d9e7b4dab3c24507a6d503`
2. `0xf977814e90da44bfa03b6295a0616a897441acec`
3. `0xa344c7ada83113b3b56941f6e85bf2eb425949f3`
4. `0x28c6c06298d514db089934071355e5743bf21d60`
5. `0x21a31ee1afc51d94c2efccaa2092ad1028285549`
6. `0x56eddb7aa87536c09ccc2793473599fd21a8b17f`
7. `0xdfd5293d8e347dfe59e90efd55b2956a1343963d`
8. `0x9696f59e4d72e237be84ffd425dcad154bf96976`
9. `0x4976a4a02f38326660d17bf34b431dc6e2eb2327`

USDT Ethereum contract: `0xdac17f958d2ee523a2206206994597c13d831ec7`.

The basket may NOT be expanded using labels discovered after 2022-11-10 under this MVE.

## Frozen source window concept

Earliest eligible source activity: 2022-11-11 00:00 UTC.
Latest possible Discovery source date: 2024-12-31.
2025 and 2026 are forbidden.

## Frozen flow semantics

For each UTC day t:

- `external_in_t`: USDT transferred from a non-basket address to a basket address.
- `external_out_t`: USDT transferred from a basket address to a non-basket address.
- basket-to-basket transfers are excluded as internal sweeps.
- `net_flow_t = external_in_t - external_out_t`.

This is NOT total Binance flow and NOT aggregate all-exchange flow. It is flow through the prospectively defendable public address basket only.

## Economic direction

- positive `net_flow_t` -> expected positive subsequent BTC return;
- negative `net_flow_t` -> expected negative subsequent BTC return.

No threshold, percentile, z-score, winsorization, price filter, funding/OI filter, ETF filter, sentiment filter or ML model is authorized in MVE0.

## Raw-chain source candidate

Preferred zero/low-cost candidate for source gate: Blockchair Ethereum ERC-20 transaction API, filtered to the USDT token contract, the frozen address basket, and a strictly protected pre-2025 block/time range.

Blockchair documentation states Ethereum has full historical data and exposes an ERC-20 transactions infinitable endpoint with SQL-like filters. The source gate may make only a small protected-period probe and must not fetch 2025/2026 rows.

If Blockchair access is blocked, incomplete, or impractical for reproducible full acquisition, classify `SOURCE_AUTH_BLOCKED` or `DATA_FAILURE` and stop. Do not silently switch to current third-party exchange labels.

## Next authorized action

Run an outcome-blind Blockchair source feasibility gate only. No BTC price, return, PnL, signal-performance statistic or 2025/2026 data may be opened.
