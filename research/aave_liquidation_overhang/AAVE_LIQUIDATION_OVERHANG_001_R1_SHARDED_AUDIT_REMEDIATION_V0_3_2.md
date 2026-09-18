# AAVE-LIQUIDATION-OVERHANG-001 — R1 SHARDED AUDIT REMEDIATION V0.3.2

Date: 2026-09-18
Branch: `aave-liquidation-overhang-v0.1`
Status: **FROZEN BEFORE EXECUTION / OPERATIONAL-ONLY / OUTCOME-BLIND**

## Trigger

The monolithic deterministic R1 scaled-ledger audit was executed twice without producing a scientific receipt:

- run `35226616121`: terminated exactly at the then-frozen 45-minute workflow ceiling;
- run `35355395431`: terminated exactly at the remediated 120-minute workflow ceiling.

Both terminations occurred while `r1_scaled_ledger_audit_v01.py` was still executing. Neither run uploaded a canonical audit receipt. Therefore neither run produced a reconstruction verdict or scientific result.

Classification of both runs: **OPERATIONAL_WALL_CLOCK_CANCELLATION / NO SCIENTIFIC VERDICT**.

## Scientific invariants — unchanged

This remediation preserves the R1 Execution Protocol V0.2 and current V0.3.1 transport hardening.

Unchanged:

- Ethereum mainnet envelope: blocks `16,490,000..21,525,890`;
- canonical R0 bootstrap and 37-reserve universe;
- borrower universe definition: every unique `Borrow.onBehalfOf` in the frozen envelope;
- sample rule: keccak256(raw 20-byte borrower address), sort by `(digest,address)`, first exactly 16;
- audit blocks: `17,748,972`, `19,007,945`, `20,266,917`, `21,525,890`;
- token-native Mint/Burn/BalanceTransfer semantics;
- Aave round-half-up ray arithmetic;
- variable-debt non-transferability rule;
- replay ordering and negative-state fail rule;
- independent archive RPC set;
- >=2 usable RPC endpoints per target;
- exact endpoint agreement;
- exact equality between replayed and historical `scaledBalanceOf(address)`;
- all existing terminal classifications and precedence;
- all protected-period and no-outcome firewalls.

## Operational remediation

### A. Deterministic sample derivation from canonical census receipts

Do not re-query 204,952 Borrow logs.

Derive the exact frozen borrower universe from the eight canonical Source Census shard receipts produced by run `35214027573`.

Those receipts already contain every unique `Borrow.onBehalfOf` identity per exact disjoint source shard and were used to establish the canonical Source Census PASS.

The derivation must verify:

- exactly 8 canonical census shard receipts;
- exact expected block ranges with no gap or overlap;
- every receipt = `SHARD_PASS`;
- summed Borrow log count = `204,952`;
- union unique borrower count = `30,691`;
- sample selection is exactly the frozen keccak rule.

No borrower may be added, removed or substituted.

### B. Token-event acquisition shards

Reuse the same eight exact disjoint block ranges as the canonical census:

1. 16,490,000..17,119,486
2. 17,119,487..17,748,973
3. 17,748,974..18,378,460
4. 18,378,461..19,007,946
5. 19,007,947..19,637,432
6. 19,637,433..20,266,918
7. 20,266,919..20,896,404
8. 20,896,405..21,525,890

Each shard may acquire only the same token-native event filters used by the monolithic audit for the exact frozen 16-address sample.

Each shard emits block-aggregated scaled-balance deltas plus provenance/event counters. It does not calculate health factor, overhang, future outcomes or market returns.

### C. Single canonical aggregation/adjudication

The aggregator must:

- verify all eight exact shard receipts and exact ranges;
- verify identical sample hash across all shards;
- merge block deltas without dropping any shard;
- replay every touched user/token pair chronologically across the full frozen envelope;
- create targets at the same four audit blocks;
- preserve zero-balance targets after a pair was touched;
- apply the same negative-state and variable-debt-transfer rules;
- call the same five frozen archive RPC endpoints;
- apply the same quorum, agreement and exact-replay equality rules.

Only the aggregator may emit `R1_AUDIT_PASS`.

## Forbidden rescue

The remediation must not:

- choose a different sample;
- use fewer audit blocks;
- drop slow borrowers, tokens, reserves, shards or targets;
- relax RPC quorum;
- replace a failed RPC with a newly selected provider;
- alter ray arithmetic or token event semantics;
- skip zero-balance touched pairs;
- change any terminal classification;
- inspect health factor, overhang, future liquidations, market outcomes, returns or PnL;
- access 2025/2026;
- merge to main.

## Safety

Research/source reconstruction only.
No live trading.
No exchange mutation.
No wallet use.
No alerts/webhooks.
No capital.
No post-outcome tuning.

A successful `R1_AUDIT_PASS` authorizes only the already-frozen downstream R1 reconstruction components. It does not authorize Discovery.
