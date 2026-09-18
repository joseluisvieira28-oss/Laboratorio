# AAVE-LIQUIDATION-OVERHANG-001 — R1 SEMANTIC RECONCILIATION ORCHESTRATION V0.5

Date: 2026-09-18
Status: FROZEN BEFORE RECONCILIATION
Scope: reconstruction-only / outcome-blind / fail-closed

## Exact upstreams

Canonical audit:
- run 35378692311
- classification required: R1_AUDIT_PASS
- target digest required: eb5a5e929ec7479989bdb5a4eabc478cce2404b443d67990b44a6b6a14483510

V0.3 full reserve/global execution:
- run 35378904880
- head SHA 1ec8c78b492b10108c92472f3bbcb49f99e3b9ec
- reserve artifacts only are eligible for semantic reconciliation
- its V0.3 global artifact is NOT canonical because the wrapper destroyed the original error cause

Collateral-flag semantics evidence:
- run 35384176433
- artifact 10563825131
- digest sha256:14714b00d328f7f9b946b564b5836a2b2c31b9de7a054aed9ce34393bc0b3429
- classification STALE_COLLATERAL_FLAG_ZERO_SCALED_STATE_OBSERVED

Global-state diagnostic:
- run 35384377212
- head SHA ca871e1d55a18c0a058e1c45ae5b397b6afec15b
- exact V0.4 diagnostic-preserving logic

## Reserve receipt reconciliation rule

For each of exactly 8 V0.3 reserve shard receipts:

PASS unchanged if already R1_RESERVE_SHARD_PASS.

A receipt may be reclassified from RECONSTRUCTION_RECONCILIATION_FAILURE to R1_RESERVE_SHARD_PASS only if ALL are true:
- collateral_flag_violations is non-empty;
- every violation reason is exactly collateral_flag_true_with_zero_scaled_atoken_at_tx_end;
- negative_states is empty;
- index_decreases is empty;
- VARIABLE_DEBT_BALANCE_TRANSFER count is zero.

The original classification, failure and all diagnostic rows must be preserved in lineage fields.

Any other failure remains terminal exactly as emitted.

## Global gate rule

Consume only the exact V0.4 global diagnostic artifact.
No semantic override is permitted.
It must be R1_GLOBAL_STATE_PASS for canonical reconstruction to pass.

## Canonical adjudication

Only if:
- exact canonical audit is R1_AUDIT_PASS;
- all 8 reconciled reserve shards are R1_RESERVE_SHARD_PASS;
- global V0.4 is R1_GLOBAL_STATE_PASS;

may the existing aggregate_r1_reconstruction_v02.py emit RECONSTRUCTION_DATA_PASS.

Otherwise preserve the terminal component failure class.

## Firewall

No health factor.
No liquidation overhang.
No future liquidation outcomes.
No market returns.
No PnL.
No 2025/2026 outcomes.
No live trading.
No orders/wallets/exchange mutation.
No main merge.
