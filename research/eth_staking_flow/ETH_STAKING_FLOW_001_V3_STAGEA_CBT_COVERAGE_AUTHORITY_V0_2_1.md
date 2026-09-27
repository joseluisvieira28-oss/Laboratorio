# ETH-STAKING-FLOW-001 — V3 STAGE-A CBT COVERAGE AUTHORITY V0.2.1

Date frozen: 2026-09-27
Status: FROZEN BEFORE NETWORK EXECUTION / SOURCE-METADATA ONLY / OUTCOME-BLIND

## Purpose

Use the official public CBT management coverage API to determine whether
`mainnet.dim_validator_status` has processed slot coverage at the exact
V3 Stage-A control and missing-date target positions.

No validator rows are opened.

## Official route

Base:
`https://cbt.mainnet.ethpandaops.io/api/v1`

Allowed endpoints only:
- `GET /models/transformations/mainnet.dim_validator_status/coverage`
- `GET /models/transformations/mainnet.dim_validator_status/coverage/{position}`

The CBT source code documents the first endpoint as returning processed
(position, interval) ranges from `admin_incremental`, and the second as
the canonical coverage/dependency debug for a specific position.

## Frozen position semantics

`dim_validator_status` is an incremental model with interval type `slot`.

For the already-frozen target epoch E:
`target_slot = E * 32`.

Controls:
- 2025-02-24 epoch 347738 => slot 11127616
- 2025-03-02 epoch 349088 => slot 11170816
- 2025-10-17 epoch 400613 => slot 12819616

Missing dates:
- 2025-02-25 epoch 347963 => slot 11134816
- 2025-02-26 epoch 348188 => slot 11142016
- 2025-02-27 epoch 348413 => slot 11149216
- 2025-02-28 epoch 348638 => slot 11156416
- 2025-03-01 epoch 348863 => slot 11163616
- 2025-10-18 epoch 400838 => slot 12826816
- 2025-10-19 epoch 401063 => slot 12834016

Frozen full source range:
- first epoch 335588 => slot 10738816
- last epoch 472163 => slot 15109216

## Decision

`CBT_COVERAGE_TARGETS_PASS` only if:
- the coverage response is valid;
- all 10 exact target slots are inside processed ranges with no gap;
- the debug endpoint reports full coverage (or equivalent non-blocking complete state)
  for all 10 positions;
- no ambiguity exists about position units.

`CBT_COVERAGE_TARGETS_FAIL` if one or more exact target slots is explicitly
outside coverage / in a processed gap.

`CBT_COVERAGE_METADATA_INCONCLUSIVE` for transport/schema ambiguity.

A coverage PASS is NOT Stage-A source PASS. It only authorizes a separately
frozen data-access remediation against the same CBT model.

## Firewall

No validator rows.
No queue counts.
No signal evaluation.
No ETH/BTC market data.
No returns/PnL.
No source after 2026-08-31.
No live trading/orders/wallets/exchange mutation.
No main merge.
No tuning.
