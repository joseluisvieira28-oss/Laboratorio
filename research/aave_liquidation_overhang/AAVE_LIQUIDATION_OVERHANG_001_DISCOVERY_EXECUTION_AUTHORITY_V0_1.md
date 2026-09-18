# AAVE-LIQUIDATION-OVERHANG-001 — DISCOVERY EXECUTION AUTHORITY V0.1

Status: **FROZEN BEFORE DISCOVERY OUTCOMES / 2023 ONLY / FAIL-CLOSED**
Date: **2026-09-18**

Authority:
- `AAVE_LIQUIDATION_OVERHANG_001_FINAL_PRE_DISCOVERY_PROTOCOL_V0_1.md`
- canonical R1 run `35384529037`
- canonical R1 artifact `AAVE_R1_SEMANTIC_RECONCILIATION_V0_5`
- canonical R1 classification `RECONSTRUCTION_DATA_PASS`

This document fixes execution details that were not materialized in the final
pre-Discovery protocol. It does not alter the hypothesis, primary stress,
predictor, outcome, split, statistical gate, or promotion rule.

## Frozen Discovery partition

Only:
- 2023-02-01 through 2023-12-31 UTC.

2024 predictor/outcome data remains unopened until a canonical 2023 Discovery
receipt is persisted.

2025/2026 remain forbidden.

## Snapshot state convention

For each UTC day, the snapshot block is the first canonical Ethereum block with
timestamp >= 00:00:00 UTC.

Snapshot account state is the **post-state of that snapshot block**, matching the
historical `eth_call` semantics at that block number.

The primary outcome window is strictly after the snapshot block and ends before
the next daily snapshot block. An event inside the snapshot block is therefore
not a future outcome for that snapshot.

For 2023-12-31 only, a single 2024-01-01 boundary block header may be read solely
to identify the last canonical 2023 block. No Aave state, event, predictor or
outcome from 2024 may be opened.

## Daily block provenance

A primary archive RPC may be used to locate the candidate daily block.

Every accepted snapshot block and the previous block MUST then be verified by
the frozen public archive set:
- https://eth-mainnet.public.blastapi.io
- https://rpc.mevblocker.io
- https://ethereum.blinklabs.xyz/

Requirements:
- minimum 2 usable endpoints;
- all usable block number/timestamp/hash tuples agree exactly;
- previous timestamp < target UTC midnight <= snapshot timestamp.

## Daily reserve state

Do not approximate accrued reserve indices from the last
`ReserveDataUpdated` event.

At every snapshot, for every active canonical reserve, query:
- `Pool.getReserveNormalizedIncome(asset)`;
- `Pool.getReserveNormalizedVariableDebt(asset)`;
- active Aave oracle `getAssetPrice(asset)`.

Each target requires:
- minimum 2 usable archive endpoints;
- all usable integer results agree exactly;
- positive oracle price;
- positive normalized indices.

The active Aave oracle is reconstructed from the canonical
PoolAddressesProvider transition history and cross-checked at the snapshot.

## Token-native borrower state

Borrower collateral/debt scaled principals are reconstructed only from the
already-proven token-native Aave event semantics used by R1:
- aToken Mint/Burn/BalanceTransfer;
- variable-debt Mint/Burn;
- exact Aave rayDiv round-half-up accounting.

Collateral-enabled flags and reserve configuration are replayed point-in-time.

The replay is deterministically partitioned into exactly 8 reserve shards using
the existing sorted-reserve modulo-8 topology.

No borrower sampling is allowed in Discovery.

## Exact valuation arithmetic

All canonical state values remain integer/fixed-point.

- `rayMul(a,b) = (a*b + RAY//2)//RAY`
- base-currency reserve value:
  `underlying_amount * oracle_price // 10**decimals`
- Aave percentage multiplication:
  `percentMul(value,pct) = (value*pct + 5000)//10000`

For the primary 10% stress:
- stressed reserve collateral value =
  `collateral_base_value * 9000 // 10000`
- then apply the applicable liquidation threshold with `percentMul`.

This order is frozen before outcomes.

## eMode

User eMode is replayed from `UserEModeSet`.
Category configuration is replayed from `EModeCategoryAdded`.
Reserve category is replayed from `EModeAssetCategoryChanged`.

If an active eMode category uses a non-zero dedicated category price source and
the exact historical valuation semantics are not implemented, Discovery fails
closed with `DISCOVERY_PROVENANCE_FAILURE`. The implementation must not silently
fall back to the ordinary reserve oracle.

## Stable-rate debt firewall

Before the primary Discovery outcome is adjudicated, every 2023
`Borrow` event in the Discovery source interval is decoded for
`interestRateMode`.

The frozen Ethereum V3 reconstruction assumes variable-rate debt only.

If any Borrow event uses a mode other than the canonical variable mode (=2),
Discovery fails closed for explicit provenance review. It must not silently
discard that debt.

## Source/outcome separation

The pipeline MUST persist a predictor-only artifact before acquiring the
primary future liquidation outcome.

The predictor artifact may contain:
- calendar/snapshot provenance;
- reconstructed borrower state;
- HF/overhang metrics authorized by the final protocol;
- primary `OVERHANG_DEBT_10`;
- 5%/20% diagnostics;
- integrity statistics.

It must contain no future liquidation outcome.

Only after predictor persistence may the 2023 `LiquidationCall` outcome be
opened.

## Liquidation outcome valuation

For each 2023 LiquidationCall:
- debt asset from canonical indexed topic;
- `debtToCover` from canonical ABI data;
- debt-asset decimals from the reconstructed reserve identity;
- Aave oracle active at the event block;
- exact `getAssetPrice(debtAsset)` historical call with minimum 2 usable
  endpoints and exact agreement.

Debt notional:
`debtToCover * oracle_price // 10**decimals`.

No CEX/DEX price is permitted.

## Statistical execution details

Primary:
- X = log1p(OVERHANG_DEBT_10)
- Y = log1p(NEXT24H_LIQUIDATION_DEBT_NOTIONAL)
- Spearman rho with average ranks for ties.

Stationary bootstrap:
- n = number of valid daily rows;
- mean block length = 7;
- restart probability = 1/7;
- 10,000 resamples;
- RNG seed = 20260918;
- circular continuation within the observed 2023 sequence;
- one-sided lower 95% bound = empirical 5th percentile of valid bootstrap rho.

An undefined primary rho is a Discovery failure, not zero.

Largest-outcome sensitivity:
- remove exactly one day;
- choose the maximum primary realized liquidation notional;
- if tied, remove the earliest UTC date among tied maxima.

No alternative statistic or bootstrap definition may replace the primary result
after outcomes.

## Firewalls

No:
- 2024 predictor/outcome opening;
- 2025/2026 scientific data;
- market returns;
- BTC/ETH/alt direction;
- trading PnL;
- threshold/shock/horizon/regime rescue;
- live trading/orders/wallets/exchange mutation;
- alerts/webhooks;
- merge to main.

The first legitimate scientific stop is the canonical 2023 Discovery verdict.
