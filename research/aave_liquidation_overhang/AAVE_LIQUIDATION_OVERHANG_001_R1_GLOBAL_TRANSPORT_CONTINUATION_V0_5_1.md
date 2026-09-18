# AAVE-LIQUIDATION-OVERHANG-001 — R1 GLOBAL TRANSPORT CONTINUATION V0.5.1

Status: **FROZEN BEFORE V0.4.1 RESULT / OUTCOME-BLIND / FAIL-CLOSED**

## Purpose

Prepare deterministic canonical R1 adjudication using the prospectively hardened
V0.4.1 global-state transport lineage without changing any reconstruction rule.

This continuation is frozen while V0.4.1 run `35389082810` is still in progress.
No V0.4.1 global result has been inspected.

## Exact upstream bindings

Canonical scaled-ledger audit:

- run `35378692311`;
- artifact `AAVE_R1_AUDIT_CANONICAL_V0_2E`;
- required classification: `R1_AUDIT_PASS`;
- target digest:
  `eb5a5e929ec7479989bdb5a4eabc478cce2404b443d67990b44a6b6a14483510`.

Reserve replay corpus:

- run `35378904880`;
- exact 8 V0.3 reserve receipts only.

Collateral-flag semantics authority:

- probe run `35384176433`;
- artifact `10563825131`;
- digest
  `sha256:14714b00d328f7f9b946b564b5836a2b2c31b9de7a054aed9ce34393bc0b3429`;
- only
  `collateral_flag_true_with_zero_scaled_atoken_at_tx_end`
  is eligible for the already-frozen semantic reconciliation.

Global-state/oracle gate:

- V0.4.1 run `35389082810`;
- head `95bef7382b0dd4e2780be93f15260e3c7df4eca4`;
- artifact `AAVE_R1_GLOBAL_STATE_DIAGNOSTIC_V0_4_1`;
- transport authority
  `AAVE_LIQUIDATION_OVERHANG_001_R1_GLOBAL_STREAM_TRANSPORT_REMEDIATION_V0_4_1`.

R0 bootstrap:

- run `35218275356`;
- artifact `AAVE_RECON_R0_BOOTSTRAP`.

## Reserve reconciliation rule

Use the existing
`reconcile_r1_reserve_shards_flag_v01.py` unchanged.

A reserve shard may be reclassified only under its frozen exact stale-flag
criteria. Every original receipt, classification, failure and diagnostic remains
preserved in lineage fields.

No other reserve failure is eligible for override.

## Global gate rule

No semantic override is permitted.

The exact V0.4.1 artifact is consumed as emitted.

Canonical PASS requires its classification to be exactly:

`R1_GLOBAL_STATE_PASS`.

Any provenance, reconciliation, coverage or technical failure remains terminal
under the existing canonical adjudicator.

## Canonical adjudication

Use `aggregate_r1_reconstruction_v02.py` unchanged.

Only if all are true:

- canonical audit = `R1_AUDIT_PASS`;
- all 8 reconciled reserve shards = `R1_RESERVE_SHARD_PASS`;
- V0.4.1 global = `R1_GLOBAL_STATE_PASS`;

may the canonical artifact emit:

`RECONSTRUCTION_DATA_PASS`.

Only that result authorizes:

`FINAL_PRE_DISCOVERY_PROTOCOL`.

## Firewalls

Until `RECONSTRUCTION_DATA_PASS`:

- no health factor;
- no liquidation distance or liquidation overhang;
- no adverse-shock threshold;
- no future liquidation outcomes;
- no market returns;
- no PnL / PF / win rate / Sharpe / drawdown;
- no scientific 2025/2026 data;
- no live trading, orders, wallets, exchange mutation, alerts/webhooks;
- no capital deployment;
- no merge to main.
