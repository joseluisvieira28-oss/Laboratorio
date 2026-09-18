# AAVE-LIQUIDATION-OVERHANG-001 — R1 V0.3 RECONSTRUCTION STOP

Date: 2026-09-18
Branch: aave-liquidation-overhang-v0.1
Continuation run: 35378904880
Pinned canonical audit: run 35378692311 / R1_AUDIT_PASS

## Terminal scientific state for this reconstruction route

RECONSTRUCTION_RECONCILIATION_FAILURE — STOP / NO RESCUE

The canonical R1 audit gate passed and the V0.3 continuation legitimately entered full reserve reconstruction. Mandatory reserve replay components then produced reconciliation failures.

Confirmed failed mandatory shards:
- shard 2 — artifact 10562781589 — digest sha256:515cb02d80874d57f557a303b5ab811fcb7becadf1d8c5714f3cd73d2055588f
- shard 4 — artifact 10562447071 — digest sha256:5e6c2761951f055968e22c0ad16998bce34b5130aab153c394fd384fe65dd782
- shard 5 — artifact 10562210914 — digest sha256:c0e422f2e3feb54e0d9509067e20ac4d3968ffd4645bbc3430abebb2b90064cd

Observed failure family:
collateral_flag_true_with_zero_scaled_atoken_at_tx_end

Known counts from preserved receipts:
- shard 2: 100 recorded flag violations (receipt cap reached)
- shard 5: 3 flag violations
- shard 4: mandatory component also classified RECONSTRUCTION_RECONCILIATION_FAILURE

For shards 2 and 5:
- negative scaled states = 0
- reserve index decreases = 0
- outcome access = false

## Protocol semantics check

Aave V3 official contract logic requires a positive aToken balance to enable an asset as collateral, and explicitly disables collateral when a full withdrawal, full validated transfer, or full liquidation removes the collateral position.

Therefore reconstructed collateral flag = true together with reconstructed scaled aToken balance = 0 violates the frozen reconstruction invariant.

This is not:
- wall-clock timeout;
- missing decimals;
- archive-RPC quorum failure;
- market-outcome failure;
- economic NO_EDGE.

It is a reconstruction reconciliation failure.

## Governance adjudication

The handoff governance requires STOP on provenance/reconciliation failure.

Do not:
- weaken the invariant;
- ignore violating users;
- drop failed reserves;
- select passing shards only;
- alter replay arithmetic after seeing failures;
- proceed to health factor;
- compute liquidation overhang;
- open future liquidation outcomes;
- open market returns/PnL;
- open 2025/2026 protected outcomes;
- claim RECONSTRUCTION_DATA_PASS.

The running orchestration may finish and emit a canonical aggregate failure receipt, but no possible later success of another component can restore RECONSTRUCTION_DATA_PASS while these mandatory shard failures remain.

## Safety

health_factor_computed=false
overhang_computed=false
future_liquidation_outcome_computed=false
market_returns_opened=false
pnl_opened=false
2025_2026_outcomes_opened=false
live_trading=false
exchange_mutation=false
main_merge=false
