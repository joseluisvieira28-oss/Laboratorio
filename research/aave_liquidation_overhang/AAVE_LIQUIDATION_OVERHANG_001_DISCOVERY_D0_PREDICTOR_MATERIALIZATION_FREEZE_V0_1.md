# AAVE-LIQUIDATION-OVERHANG-001 — DISCOVERY D0 PREDICTOR MATERIALIZATION FREEZE V0.1

Date: 2026-09-18
Branch: `aave-liquidation-overhang-discovery-v0.1`
Parent protocol commit: `28d585c643d9fa17c7d300f4bc9c7921eff52f75`
Status: **FROZEN BEFORE D0 SOURCE EXECUTION / OUTCOME-BLIND**

## Authority

This freeze implements only the predictor side of:

`AAVE_LIQUIDATION_OVERHANG_001_FINAL_PRE_DISCOVERY_PROTOCOL_V0_1.md`

The parent protocol was frozen after canonical reconstruction run `35384529037`
emitted `RECONSTRUCTION_DATA_PASS`.

Canonical R1 binding:
- run: `35384529037`
- artifact: `AAVE_R1_SEMANTIC_RECONCILIATION_V0_5`
- artifact id: `10565941203`
- digest: `sha256:acbc1d647e2a7861ce52e219a118ef10f7b021859ec4fd21502aeda96251a219`
- audit: `R1_AUDIT_PASS`
- reserve shards: 8/8 `R1_RESERVE_SHARD_PASS`
- global: `R1_GLOBAL_STATE_PASS`
- audit targets: 77/77
- oracle price targets: 119 / failures 0

## D0 purpose

Materialize the complete 2023 Discovery predictor series before opening any
future liquidation outcome.

D0 MUST NOT decode, aggregate, inspect or serialize:
- future `LiquidationCall.debtToCover`;
- next-24h liquidation notional;
- market returns;
- PnL or trading performance.

D0 may reconstruct only source state required for the frozen predictor.

## Exact snapshot universe

Discovery dates:
- 2023-02-01 through 2023-12-31 inclusive.

Clock:
- one snapshot at the first canonical Ethereum block with timestamp >= 00:00:00 UTC.

Expected snapshot count:
- exactly 334.

No alternate hour, missing-day substitution, interpolation or event-conditioned clock.

## Exact reserve universe and partition

Use the exact 37 reserves from the canonical R0/R1 reconstruction.

For transport only, reserve work is partitioned into exactly 8 deterministic
shards using the already-audited rule:

`sorted(reserves)[index % 8]`.

Sharding changes only execution transport. It must not alter account arithmetic
or snapshot semantics.

## Required source-state replay

For every reserve and every D0 snapshot, reconstruct point-in-time:

- scaled aToken balances;
- scaled variable-debt balances;
- collateral-enabled flags;
- liquidity index;
- variable-borrow index;
- reserve decimals;
- reserve liquidation threshold;
- reserve eMode category;
- active Aave oracle and point-in-time asset price.

Global state must reconstruct point-in-time:
- each user's eMode category;
- eMode category liquidation threshold configuration;
- provider/oracle transitions required by the parent protocol.

No present-day state substitution is allowed.

## Exact arithmetic

Aave ray:
- `RAY = 10**27`
- `rayMul(a,b) = (a*b + RAY//2)//RAY`

Underlying collateral and debt use the parent protocol's exact formulas.

Valuation must remain integer/fixed-point until final reported diagnostics.

For a collateral position:
- use eMode liquidation threshold iff user eMode is non-zero AND the reserve
  belongs to that exact contemporaneous category;
- otherwise use the contemporaneous reserve liquidation threshold.

## D0 per-user partial output

Each reserve shard may emit, per snapshot/user, only the exact additive state
needed by the predictor:

- total collateral oracle value contribution;
- weighted liquidation-collateral contribution;
- total debt oracle value contribution.

The global D0 aggregator sums the 8 shard contributions by
`(snapshot_date,user)`.

## Frozen predictor

For users with total debt > 0:

`HF = weighted_liquidation_collateral / total_debt_value`.

Primary 10% stress is exactly:

`stressed_HF = 0.90 * weighted_liquidation_collateral / total_debt_value`.

Primary latent borrower:
- baseline `HF > 1.0`;
- stressed 10% `HF <= 1.0`.

Primary D0 series:

`OVERHANG_DEBT_10_t = sum(total_debt_value of latent borrowers)`.

Diagnostics already frozen by the parent protocol:
- latent borrower count;
- latent collateral value;
- baseline already-liquidatable debt;
- `OVERHANG_DEBT_5`;
- `OVERHANG_DEBT_20`.

No z-score, percentile, moving average, threshold sweep or regime filter.

## D0 PASS gate

D0 may emit `PREDICTOR_MATERIALIZATION_PASS` only if ALL hold:

- exactly 334 snapshot rows;
- exact 37-reserve union across 8 shards;
- no protected-period access;
- no unresolved negative scaled balances;
- no variable-debt BalanceTransfer provenance violation;
- no reserve-index regression;
- all required oracle prices available point-in-time;
- all user/reserve eMode semantics resolved;
- no liquidation outcome field opened;
- deterministic predictor-series SHA-256 persisted.

Otherwise terminal class must be one of:
- `PREDICTOR_MATERIALIZATION_TECHNICAL_FAILURE`
- `PREDICTOR_MATERIALIZATION_PROVENANCE_FAILURE`
- `PREDICTOR_MATERIALIZATION_RECONSTRUCTION_FAILURE`
- `PREDICTOR_MATERIALIZATION_INSUFFICIENT_COVERAGE`.

## D1 firewall

Only `PREDICTOR_MATERIALIZATION_PASS` may authorize a separate D1 workflow that
opens 2023 `LiquidationCall` outcome values and executes the exact frozen
Spearman/bootstrap Discovery.

2024 remains sealed until a canonical 2023 Discovery receipt exists.

## Safety

No 2024 outcomes.
No 2025/2026 scientific data.
No market returns.
No trading PnL.
No live trading.
No orders/wallets/exchange mutation.
No capital deployment.
No main merge.
No post-outcome tuning.
