# AAVE-LIQUIDATION-OVERHANG-001 — R1 SHARDED AUDIT REMEDIATION FREEZE V0.2

Date: 2026-09-19
Branch: `aave-liquidation-overhang-v0.1`
Status: **FROZEN BEFORE EXECUTION / OPERATIONAL-ONLY / OUTCOME-BLIND**

## Why this remediation exists

The deterministic R1 scaled-ledger audit V0.1 was executed twice without producing a scientific/reconstruction verdict:

- run `35226616121`: cancelled by the explicit 45-minute workflow ceiling;
- run `35355395431`: cancelled by the explicit 120-minute workflow ceiling.

Neither run produced the canonical audit receipt. Neither opened health factor, liquidation overhang, future liquidation outcomes, market returns, PnL, 2025 or 2026.

The repeated wall-clock failures prove that the monolithic acquisition architecture is operationally unsuitable. They do **not** constitute a reconstruction failure.

## Scientific contract unchanged

The controlling R1 scientific protocol remains:
`AAVE_LIQUIDATION_OVERHANG_001_R1_EXECUTION_PROTOCOL_V0_2`.

V0.2 remediation changes only acquisition/orchestration topology.

Unchanged:
- Ethereum mainnet block envelope `16,490,000..21,525,890`;
- exact 37-reserve R0 bootstrap;
- borrower universe = all unique `Borrow.onBehalfOf` identities in the frozen envelope;
- deterministic sample = first exactly 16 borrowers sorted by `(keccak256(raw 20-byte address), address)`;
- audit blocks = `17,748,972; 19,007,945; 20,266,917; 21,525,890`;
- token-native Mint/Burn/BalanceTransfer semantics;
- exact Aave ray rounding;
- variable-debt non-transferability rule;
- independent archive-RPC set and >=2 endpoint exact-agreement rule;
- exact replay equality;
- all pass/fail classifications and firewalls.

## Canonical borrower-sample recovery

The V0.2 sample selector MUST derive the borrower universe only from the eight preserved canonical Source Census shard receipts created by run `35214027573`.

Those receipts were produced before economic reconstruction and already contain the complete source-only `participants_by_event["Borrow"]` sets for eight exact disjoint ranges.

The selector must prove:
- exactly 8 canonical Source Census shard receipts;
- every shard = `SHARD_PASS`;
- exact frozen contiguous block coverage;
- aggregate Borrow event count = **204,952**;
- unique Borrow participant count = **30,691**;
- no protected-period or safety violation in any receipt.

It then applies the **identical** V0.1 sample sort. No borrower may be added, removed, substituted or selected based on reconstruction fit.

## Token-event acquisition sharding

The exact frozen global block envelope is split into the same eight canonical Source Census ranges:

1. 16,490,000..17,119,486
2. 17,119,487..17,748,973
3. 17,748,974..18,378,460
4. 18,378,461..19,007,946
5. 19,007,947..19,637,432
6. 19,637,433..20,266,918
7. 20,266,919..20,896,404
8. 20,896,405..21,525,890

Every shard uses the same token addresses, event topics, participant filters and decoding rules as V0.1.

Shard outputs may contain only reconstruction-source material:
- deterministic scaled-balance deltas;
- canonical event counts/deduplication diagnostics;
- source transport diagnostics;
- variable-debt BalanceTransfer count;
- sample and source hashes.

No shard may calculate a health factor, overhang, adverse shock, future liquidation outcome, market return or PnL.

## Canonical aggregate

Only the aggregate step may adjudicate the audit.

It MUST:
- verify exact 8-shard coverage with no gap/overlap;
- verify every shard used the identical frozen sample SHA;
- combine scaled deltas across all eight ranges;
- replay balances through the same four frozen audit blocks;
- apply the identical negative-balance and variable-debt-transfer fail rules;
- validate every touched user/token target with the same frozen archive-RPC set;
- apply the identical >=2 endpoint quorum, provider-agreement and exact replay-equality rules.

Allowed final audit classifications remain exactly:
- `R1_AUDIT_PASS`
- `RECONSTRUCTION_ACQUISITION_TECHNICAL_FAILURE`
- `RECONSTRUCTION_PROVENANCE_FAILURE`
- `RECONSTRUCTION_RECONCILIATION_FAILURE`
- `RECONSTRUCTION_INSUFFICIENT_COVERAGE`

No shard result alone is a scientific pass.

## Post-audit continuation

Only `R1_AUDIT_PASS` may release the already-prepared:
- R1 global state/oracle gate;
- eight R1 reserve replay shards;
- canonical R1 adjudicator V0.2.

Only the canonical R1 aggregate may emit `RECONSTRUCTION_DATA_PASS`.

## Hard firewalls

Still forbidden:
- health factor;
- liquidation-overhang predictor;
- adverse-shock threshold;
- future liquidation outcome;
- market-return prices;
- returns, PnL, PF, win rate or drawdown;
- 2025/2026 access;
- live trading, orders, wallets, exchange mutation, alerts/webhooks;
- merge to main.

This amendment is a wall-clock/parallelization remediation only. It is not a hypothesis change, source-rule rescue or scientific threshold change.
