# ETH-STAKING-FLOW-001 — V3 STAGE-A CBT MODEL COVERAGE PROBE V0.2.0

Date frozen: 2026-09-27
Status: FROZEN BEFORE NETWORK EXECUTION / SOURCE-METADATA ONLY / OUTCOME-BLIND

## Purpose

Determine whether the public ethPandaOps CBT model registry reports historical coverage for `mainnet.dim_validator_status` sufficient to cover the frozen V3 Stage-A source range.

This probe does not open validator rows or market outcomes.

## Frozen metadata endpoints

Primary:
https://cbt.mainnet.ethpandaops.io/api/v1/models/mainnet.dim_validator_status

Fallback list-only:
https://cbt.mainnet.ethpandaops.io/api/v1/models

## Required question

Does model metadata establish that `mainnet.dim_validator_status` has processed coverage reaching at least:
- first frozen target epoch: 335588
- last frozen target epoch: 472163

If model metadata does not expose trustworthy processed min/max bounds, classification is metadata-inconclusive; do not infer row coverage.

## Allowed outputs

- HTTP status/content type
- model id/name/type/database/table
- dependency names
- model status
- any published min/max/processed position metadata
- response byte length / SHA256
- top-level keys

## Forbidden

No validator-level records.
No queue counts.
No signal evaluation.
No ETH/BTC prices or returns.
No PnL.
No source after 2026-08-31.
No live trading/mutation/main merge.
