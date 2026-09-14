# STABLECOIN-EXCHANGE-FLOW-001 — DATA ACQUISITION PROTOCOL V0.1

STATUS: FROZEN PRE-OUTCOME / ACTIVATION CONDITIONAL ON SOURCE CROSSCHECK PASS

LAB: `STABLECOIN-EXCHANGE-FLOW-001`
MVE: `SEF-BINANCE-PUBLIC-USDT-ETH-1D-001`

## Scope

Construct a reproducible daily USDT external-flow series for the prospectively frozen nine-address Binance Ethereum basket published on 2022-11-10. This protocol is source/data construction only. BTC price, returns, PnL and signal-performance statistics remain forbidden.

## Frozen protected window

- first complete eligible UTC day: `2022-11-11`;
- last complete eligible UTC day: `2024-12-30`;
- `2025` and `2026` MUST NOT be queried, inferred, downloaded or opened.

The end date is deliberately one full UTC day before 2025 so the acquisition implementation never needs a 2025 block/timestamp to establish a terminal day boundary.

## Frozen source authority

Primary extraction source: Ethereum canonical USDT `Transfer` logs through historical `eth_getLogs` served by `https://rpc.mevblocker.io`.

Independent source-validation authority: Blockchair Ethereum ERC-20 daily dump files under `https://gz.blockchair.com/ethereum/erc-20/transactions/`.

The source basket and USDT contract are frozen in `SOURCE_REMEDIATION_001_BINANCE_PUBLIC_BASKET.md` and may not be expanded using later labels.

## Activation gate

Full acquisition is authorized only if the one-day 2022-11-11 source cross-check classifies `SOURCE_CROSSCHECK_EXACT_PASS`, requiring exact equality between MEV Blocker and Blockchair for external inbound/outbound transfer counts and raw integer USDT amounts after internal basket-to-basket sweeps are excluded.

If the cross-check mismatches, STOP. No full acquisition and no outcomes.

## Flow semantics

For UTC day `t`:

- `external_in_raw_t`: sum of USDT raw integer values where sender is outside the frozen basket and recipient is inside it;
- `external_out_raw_t`: sum where sender is inside the frozen basket and recipient is outside it;
- internal basket-to-basket transfers are excluded;
- `net_flow_raw_t = external_in_raw_t - external_out_raw_t`;
- `net_flow_usdt_t = net_flow_raw_t / 1_000_000` is a pure token-decimal unit conversion, not normalization.

No thresholds, z-scores, percentiles, winsorization, clipping or feature engineering are permitted during acquisition.

## Daily block-boundary rule

Each UTC day must be represented by the canonical Ethereum block interval whose timestamps fall within `[00:00:00 UTC, next 00:00:00 UTC)`.

Block boundaries must be resolved using `eth_getBlockByNumber` only within the protected pre-2025 range. Acquisition must fail closed if a boundary cannot be proven or if any returned timestamp is outside the protected period.

## Log extraction rule

- contract: USDT Ethereum `0xdac17f958d2ee523a2206206994597c13d831ec7`;
- event topic0: ERC-20 `Transfer(address,address,uint256)`;
- inbound filter: topic2 is OR over the nine padded basket addresses;
- outbound filter: topic1 is OR over the nine padded basket addresses;
- base chunk size: **3,200 blocks**;
- if a provider returns a result-limit/range error, recursively split the affected chunk until it succeeds or reaches one block;
- never accept a truncated response;
- deduplicate by `(transactionHash, logIndex)` within each directional stream;
- parse both indexed addresses and exclude basket-to-basket transfers before aggregation.

The 3,200-block base is frozen from the pre-outcome MEV Blocker range profile: it succeeded in both protected endpoints while denser 6,400-block queries could exceed the provider's 10,000-result cap.

## Coverage / fail-closed checks

Acquisition MUST stop with `DATA_FAILURE` or `TECHNICAL_FAILURE_PREOUTCOME` if any of the following occurs:

1. a day has an unresolved first/last block boundary;
2. block intervals overlap or leave a gap;
3. an RPC chunk cannot be resolved by adaptive splitting;
4. the provider reports more-results/truncation semantics that cannot be deterministically resolved;
5. duplicate `(transactionHash, logIndex)` entries disagree in content;
6. any queried or returned block timestamp is in 2025/2026;
7. an event topic/address/value cannot be decoded deterministically;
8. the output does not contain one row for every protected UTC day (zero-flow days included).

## Required outputs

1. `daily_binance_public_usdt_flow_20221111_20241230.csv`
   - date_utc
   - external_in_count
   - external_out_count
   - external_in_raw
   - external_out_raw
   - net_flow_raw
   - external_in_usdt
   - external_out_usdt
   - net_flow_usdt
   - first_block
   - last_block

2. `extraction_manifest.json`
   - source endpoint;
   - repository commit;
   - frozen basket/contract;
   - protected dates;
   - each successful/adaptively split query block range, direction, result count, response SHA256 and byte count;
   - boundary metadata and coverage checks;
   - explicit `access_2025=false`, `access_2026=false`, `btc_market_data_accessed=false`, `returns_computed=false`, `pnl_computed=false`.

3. `DATA_ACQUISITION_RECEIPT.json`
   - final classification;
   - row count and expected row count;
   - first/last date;
   - aggregate transfer counts only (not market outcomes);
   - CSV SHA256;
   - manifest SHA256;
   - all fail-closed assertions.

## Storage posture

Do not persist full multi-year raw log payloads in Git. The canonical blockchain is the raw source; reproducibility is anchored by exact block ranges, query semantics, response hashes, code revision and independent Blockchair source cross-checks. Store the compact daily series and immutable manifests/artifacts.

## Governance

Research-only. No live trading. No exchange mutation. No merge to main. No deployment. No post-outcome tuning. No BTC outcomes. No 2025/2026. Source/data construction may not be altered after BTC outcomes are opened.
