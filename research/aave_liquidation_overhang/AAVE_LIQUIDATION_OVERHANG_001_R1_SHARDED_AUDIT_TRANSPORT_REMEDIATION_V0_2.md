# AAVE-LIQUIDATION-OVERHANG-001 — R1 SHARDED AUDIT TRANSPORT REMEDIATION V0.2

Date: 2026-09-18
Branch: `aave-liquidation-overhang-v0.1`
Status: **FROZEN BEFORE SHARDED EXECUTION / TRANSPORT-ONLY / OUTCOME-BLIND**

## Trigger

The same deterministic R1 scaled-ledger audit was killed twice by explicit CI wall-clock ceilings:

- run `35226616121`: cancelled at the original 45-minute ceiling;
- run `35355395431`: cancelled at the remediated 120-minute ceiling.

Neither run produced a canonical audit receipt or a reconstruction/scientific verdict. Both terminations occurred while executing the unchanged token-ledger acquisition/replay script.

Classification of both: **OPERATIONAL_WALL_CLOCK_CANCELLATION / NO SCIENTIFIC VERDICT**.

## Transport-only remediation

V0.2 preserves the exact R1 Execution Protocol V0.2 scientific contract while parallelizing transport.

### Sample identity

Do not rescan Borrow logs from the network. Reconstruct the exact borrower universe from the eight immutable canonical Source Census shard receipts produced by run `35214027573`.

Those receipts already contain every unique `Borrow.onBehalfOf` participant by fixed disjoint block shard and were created before R1.

Required invariants:

- exactly 8 canonical census shard receipts;
- exact source-census ranges;
- every shard classification = `SHARD_PASS`;
- union of `participants_by_event.Borrow` = exactly 30,691 unique borrowers;
- frozen selection remains: sort by `(keccak256(raw 20-byte address), address)` and take the first 16;
- sample SHA256 is persisted before token-ledger acquisition.

This produces the same deterministic sample rule as R1 V0.1 while removing a redundant 204,952-log network traversal.

### Token-ledger acquisition

Use the exact eight fixed disjoint block ranges already proven by Source Census:

1. 16,490,000..17,119,486
2. 17,119,487..17,748,973
3. 17,748,974..18,378,460
4. 18,378,461..19,007,946
5. 19,007,947..19,637,432
6. 19,637,433..20,266,918
7. 20,266,919..20,896,404
8. 20,896,405..21,525,890

Each shard must use the identical token identities, event signatures, participant filters, ray arithmetic and duplicate rules from `r1_scaled_ledger_audit_v01.py`.

Shards may only emit source-derived scaled deltas and transport diagnostics. They may not independently adjudicate balance conservation because pre-shard state is not known.

### Canonical aggregation

The aggregate step must:

- prove the exact eight ranges with no gap/overlap;
- prove every shard used the frozen sample SHA and the canonical 37-reserve bootstrap;
- merge block deltas chronologically;
- call the ORIGINAL V0.1 `build_token_maps()`, `replay_targets()` and `validate_targets()` functions for canonical replay and archive-RPC validation;
- preserve the original terminal classifications and precedence.

No failed target, wallet, token, reserve, RPC or event may be removed/replaced.

## No scientific changes

Unchanged:

- 16 borrowers;
- 37 reserves;
- four audit blocks;
- all event semantics;
- round-half-up ray arithmetic;
- aToken / variable-debt rules;
- five archive RPC endpoints;
- >=2 exact-agreement RPC quorum;
- exact replay equality;
- negative-state rule;
- variable-debt non-transferability;
- 2023-2024 block envelope;
- every pass/fail classification.

## Firewalls

Still forbidden:

- health factor;
- liquidation-overhang predictor;
- adverse-shock threshold;
- future liquidation outcomes;
- market return prices;
- returns, PnL, PF, win rate or drawdown;
- 2025/2026;
- live trading, orders, wallets, exchange mutation, execution webhooks;
- merge to main.

Only `R1_AUDIT_PASS` from the canonical V0.2 aggregate may unlock the already-frozen downstream R1 components.
