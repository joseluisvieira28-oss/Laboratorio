# AAVE-LIQUIDATION-OVERHANG-001 — FINAL PRE-DISCOVERY PROTOCOL V0.1

Status: **FROZEN BEFORE DISCOVERY OUTCOMES / OUTCOME-BLIND**
Date: **2026-09-18**
Repository: `joseluisvieira28-oss/Laboratorio`
Branch: `aave-liquidation-overhang-v0.1`

This protocol is activated only because the canonical R1 reconstruction receipt
from run `35384529037` emitted **RECONSTRUCTION_DATA_PASS**.

Canonical reconstruction artifact:
- run: `35384529037`
- artifact: `AAVE_R1_SEMANTIC_RECONCILIATION_V0_5`
- artifact ID: `10565941203`
- artifact digest:
  `sha256:acbc1d647e2a7861ce52e219a118ef10f7b021859ec4fd21502aeda96251a219`
- canonical R1 classification: `RECONSTRUCTION_DATA_PASS`
- audit component: `R1_AUDIT_PASS`
- global component: `R1_GLOBAL_STATE_PASS`
- reserve components: 8/8 `R1_RESERVE_SHARD_PASS`
- audit targets: 77/77 validated
- Aave-oracle price targets: 119
- Aave-oracle price failures: 0

No health factor, liquidation overhang, future liquidation outcome, market return
or PnL was opened before this freeze.

## 1. Economic hypothesis

Aave V3 Ethereum borrowers whose point-in-time collateral/debt state is close to
the protocol liquidation boundary create latent forced-flow inventory.

Primary hypothesis:

> Higher borrower-level liquidation overhang measured at a daily snapshot should
> precede higher realized Aave liquidation debt notional during the next 24 hours.

This is a **mechanism-validation** study.

It does not predict BTC, ETH or any market return.
It does not authorize a trading strategy.
A later executable-market study requires a separate prospective protocol.

## 2. Frozen chain, protocol and source period

Chain:
- Ethereum mainnet only.

Protocol:
- Aave V3 Ethereum Pool lineage rooted at
  `0x2f39d218133AFaB8F2B819B1066c7E434Ad94E9e`.

Canonical Pool:
- `0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2`.

Canonical reconstructed reserve universe:
- exact 37 reserves proven by R1.

Source envelope:
- block `16,490,000` through `21,525,890`;
- hard ceiling `2024-12-31T23:59:59Z`.

Protected periods:
- 2025 locked;
- 2026 locked.

No present-day state substitution is permitted.

## 3. Frozen study split

### Discovery
- snapshots from 2023-02-01 through 2023-12-31 inclusive.

### Replication
- snapshots from 2024-01-01 through 2024-12-31 inclusive.

The 2024 replication outcomes MUST remain unopened until the complete 2023
Discovery receipt has been emitted and cryptographically persisted.

No 2024-informed parameter selection is allowed.

## 4. Frozen snapshot clock

One snapshot per UTC calendar day.

Snapshot block:
- the first canonical Ethereum block with timestamp >= `00:00:00 UTC` for that
  calendar day.

No alternate hour.
No best-time search.
No intraday threshold search.
No event-conditioned snapshot clock.

Each primary outcome window is:
- strictly after the snapshot block;
- through the last block before the next day's snapshot timestamp.

Thus primary outcome windows are non-overlapping 24-hour UTC windows.

## 5. Point-in-time borrower state

At snapshot `t`, include every Aave V3 Ethereum user with non-zero reconstructed
variable debt or collateral state at `t`.

For each reserve `i` and user `u`:

### Collateral balance

`underlying_collateral_i,u,t =
rayMul(scaled_aToken_balance_i,u,t, liquidityIndex_i,t)`

using the exact frozen R1 round-half-up Aave ray arithmetic.

### Variable debt

`underlying_debt_i,u,t =
rayMul(scaled_variable_debt_i,u,t, variableBorrowIndex_i,t)`

Stable-rate debt is not silently omitted. Any stable-rate Borrow population that
contradicts the frozen Ethereum V3 reconstruction assumption is a provenance
failure requiring explicit review.

### Base-currency valuation

Each collateral and debt balance is valued using:
- the exact Aave oracle instance active at snapshot `t`;
- the exact point-in-time asset/source mapping;
- the Aave oracle price valid at `t`;
- point-in-time reserve decimals.

No CEX price.
No DEX price.
No current oracle mapping.

## 6. Frozen health-factor reconstruction

For every borrower with total debt value > 0:

`weighted_liquidation_collateral_u,t =
sum_i(collateral_value_i,u,t * LT_i,u,t / 10000)`

where `LT_i,u,t` is the point-in-time liquidation threshold applicable to that
collateral reserve and user.

eMode handling is point-in-time:
- if the user has an active eMode category and the collateral reserve belongs to
  that category under the contemporaneous configuration, use the category
  liquidation threshold;
- otherwise use the reserve liquidation threshold.

Baseline health factor:

`HF_u,t =
weighted_liquidation_collateral_u,t / total_debt_value_u,t`

No float approximation is permitted in canonical state arithmetic. Integer /
fixed-point arithmetic must preserve Aave-compatible rounding until the final
reported decimal diagnostic.

## 7. Frozen adverse-shock definition

Primary stress is a **10.00% collateral-valuation haircut**.

For the stress calculation only:

`stressed_collateral_value_i,u,t = collateral_value_i,u,t * 0.90`

Debt values remain unchanged.

The stress is deliberately synthetic and uniform:
- it is not an assertion that all assets fall together;
- it is not selected from observed liquidation outcomes;
- it is a fixed prospective distance-to-liquidation stress metric.

No asset-specific shock.
No volatility scaling.
No regime adjustment.
No post-outcome shock optimization.

Secondary diagnostic-only shock ladder:
- 5%;
- 20%.

The 5% and 20% series may be reported only as diagnostics and cannot rescue the
primary 10% result.

## 8. Frozen primary predictor

A borrower contributes to latent liquidation overhang at snapshot `t` if:

1. total debt value > 0;
2. baseline `HF_u,t > 1.0`;
3. stressed 10% `HF_u,t <= 1.0`.

Borrowers already liquidatable at baseline (`HF <= 1`) are excluded from the
primary latent-overhang predictor and recorded separately as a diagnostic.

Primary predictor:

`OVERHANG_DEBT_10_t =
sum(total_debt_value_u,t for latent-crossing borrowers)`

reported in the Aave oracle base currency.

This is the frozen primary signal.

Secondary diagnostics:
- count of latent-crossing borrowers;
- total collateral value of latent-crossing borrowers;
- baseline already-liquidatable debt;
- `OVERHANG_DEBT_5_t`;
- `OVERHANG_DEBT_20_t`.

No percentile threshold, z-score, moving average or regime filter is part of
V0.1.

## 9. Frozen primary outcome

Primary outcome:

`NEXT24H_LIQUIDATION_DEBT_NOTIONAL_t`

= sum of realized Aave V3 Ethereum `LiquidationCall.debtToCover` during the
non-overlapping 24-hour window after snapshot `t`, valued in Aave oracle base
currency using the point-in-time Aave oracle active at each liquidation event
block.

For each LiquidationCall:
- decode the canonical debt asset;
- decode `debtToCover`;
- use point-in-time reserve decimals;
- use the Aave oracle price available at the liquidation event block.

No market-return price series may be opened.

Secondary outcome diagnostics:
- liquidation event count;
- liquidated borrower count;
- collateral-seized oracle notional.

These diagnostics cannot replace the primary debt-notional outcome.

## 10. Frozen statistical transform

Primary statistical variables:

`X_t = log1p(OVERHANG_DEBT_10_t)`

`Y_t = log1p(NEXT24H_LIQUIDATION_DEBT_NOTIONAL_t)`

Primary association statistic:
- Spearman rank correlation `rho(X,Y)`.

Dependence-aware inference:
- stationary block bootstrap;
- mean block length = 7 daily observations;
- 10,000 resamples;
- deterministic RNG seed = `20260918`;
- one-sided 95% lower confidence bound for rho.

No alternative block length may replace the primary result after outcomes.

## 11. Frozen Discovery eligibility

2023 Discovery is eligible for a mechanism verdict only if all are true:

- >= 300 valid daily snapshots;
- >= 30 snapshots with `OVERHANG_DEBT_10 > 0`;
- >= 20 daily outcome windows with realized liquidation debt notional > 0;
- zero protected-period violations;
- zero unresolved reconstruction/provenance failures.

Otherwise:
`DISCOVERY_INSUFFICIENT_SAMPLE` or the appropriate provenance/technical class.

## 12. Frozen Discovery pass gate

2023 Discovery passes only if ALL are true:

1. Spearman rho between primary X and Y is > 0;
2. stationary-block-bootstrap one-sided 95% lower confidence bound for rho is > 0;
3. removing the single largest realized-liquidation-notional day leaves rho > 0;
4. zero provenance/leakage violations.

No threshold rescue.
No shock rescue.
No horizon rescue.
No subgroup rescue.
No sign flip.
No regime rescue.

If eligible but any gate fails:
`DISCOVERY_NO_SIGNAL`.

## 13. Frozen replication gate

2024 remains sealed until the 2023 Discovery receipt is finalized.

Replication uses exactly the same:
- snapshot clock;
- borrower reconstruction;
- 10% stress;
- primary predictor;
- 24h outcome;
- log1p transforms;
- Spearman statistic;
- bootstrap method;
- block length;
- seed policy.

Replication passes only if:

1. >= 330 valid 2024 daily snapshots;
2. >= 30 snapshots with primary overhang > 0;
3. >= 20 daily windows with realized liquidation debt notional > 0;
4. rho > 0;
5. one-sided 95% lower bootstrap bound for rho > 0;
6. rho remains > 0 after removing the single largest liquidation-notional day;
7. zero provenance/leakage violations.

Failure = `REPLICATION_FAIL`.
No rescue mutation is authorized.

## 14. Permitted terminal states

Discovery:
- `DISCOVERY_MECHANISM_PASS`
- `DISCOVERY_NO_SIGNAL`
- `DISCOVERY_INSUFFICIENT_SAMPLE`
- `DISCOVERY_ACQUISITION_TECHNICAL_FAILURE`
- `DISCOVERY_PROVENANCE_FAILURE`
- `DISCOVERY_RECONSTRUCTION_FAILURE`

Replication, only after Discovery pass:
- `REPLICATION_MECHANISM_PASS`
- `REPLICATION_FAIL`
- `REPLICATION_INSUFFICIENT_SAMPLE`
- `REPLICATION_ACQUISITION_TECHNICAL_FAILURE`
- `REPLICATION_PROVENANCE_FAILURE`

A mechanism pass is NOT a trading-edge promotion.

## 15. Post-mechanism firewall

Even if both Discovery and Replication pass, this lab has proven only:

> borrower-level latent Aave liquidation inventory predicts subsequent realized
> Aave liquidation flow.

It has NOT yet proven:
- BTC direction;
- ETH direction;
- altcoin direction;
- executable market impact;
- PnL after fees/slippage/funding;
- a live trading strategy.

Any market-impact or executable strategy study requires a new separately frozen
prospective protocol with costs, venue, asset, direction, execution timing and
holdout rules fixed before outcomes.

## 16. Hard safety firewall

Forbidden under this protocol:

- 2025 scientific data;
- 2026 scientific data;
- live trading;
- orders;
- wallets;
- authenticated exchange mutation;
- alerts/webhooks;
- capital deployment;
- merge to main;
- post-outcome tuning.

Discovery implementation may access only the already-authorized 2023 source and
2023 realized Aave liquidation-flow outcome required by this protocol.

The 2024 outcome partition remains locked until a canonical 2023 Discovery
receipt exists.
