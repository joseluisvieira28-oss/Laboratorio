# AAVE-LIQUIDATION-OVERHANG-001 — R1 SHARDED TRANSPORT REMEDIATION V0.2

Date: 2026-09-18
Branch: `aave-liquidation-overhang-v0.1`
Status: **FROZEN BEFORE FIRST SHARDED AUDIT EXECUTION / OPERATIONAL-ONLY / OUTCOME-BLIND**

## Trigger for remediation

Two executions of the exact R1 scaled-ledger audit were terminated solely by GitHub Actions wall-clock limits:

- run `35226616121`: cancelled at the frozen 45-minute workflow ceiling;
- run `35355395431`: cancelled at the remediated 120-minute workflow ceiling.

Neither run produced a scientific reconstruction verdict. Both terminated while executing the same deterministic source-replay step.

## Frozen remediation

Transport over the exact block envelope `16,490,000..21,525,890` is split into the same eight fixed contiguous ranges already used successfully by the canonical AAVE source census:

1. 16,490,000..17,119,486
2. 17,119,487..17,748,973
3. 17,748,974..18,378,460
4. 18,378,461..19,007,946
5. 19,007,947..19,637,432
6. 19,637,433..20,266,918
7. 20,266,919..20,896,404
8. 20,896,405..21,525,890

Phase A runs the exact Borrow identity extraction independently per fixed range. The aggregate unions canonical Borrow log identities and borrower addresses, requires the canonical total Borrow count of `204,952`, and then applies the **unchanged** frozen sample rule:

`keccak256(raw 20-byte borrower address)`, sort by `(digest,address)`, first exactly 16.

Phase B distributes only transport of token-native Mint/Burn/BalanceTransfer events for those exact 16 borrowers across the same fixed ranges. Each shard emits deterministic block-level ledger deltas and canonical event identities.

Phase C aggregates the eight delta receipts, sums deltas by exact `(user,token,block)`, performs the unchanged replay across the four frozen audit blocks, and executes the unchanged independent historical `scaledBalanceOf()` validation against the exact same five frozen RPC endpoints.

## Scientific invariance

The remediation must not change:

- borrower universe;
- canonical Borrow count requirement;
- sample size or sample ranking;
- reserve universe;
- audit blocks;
- aToken/variable-debt event definitions;
- Aave ray arithmetic;
- Mint/Burn/BalanceTransfer semantics;
- variable-debt non-transferability rule;
- negative-balance failure rule;
- validation target construction;
- RPC endpoint set;
- minimum two-endpoint quorum;
- exact equality requirement;
- pass/fail classifications;
- protected 2023-2024 envelope.

Block sharding is transport parallelization only. No event may be omitted because of shard boundaries, and canonical `(transactionHash,logIndex)` identities must remain globally unique.

## Required aggregate checks

Before any `R1_AUDIT_PASS`:

- exactly eight Borrow shard receipts;
- exact contiguous no-gap/no-overlap envelope;
- global Borrow identities = 204,952;
- borrower sample produced only after global union;
- exactly eight token-delta shard receipts using the same sample digest;
- no duplicate canonical token-event identity across shards;
- exact delta aggregation;
- zero variable-debt BalanceTransfer;
- zero negative replay states;
- all validation targets satisfy the existing RPC quorum/equality rules.

## Firewall

Still forbidden:

- health factor;
- liquidation-overhang calculation;
- adverse-shock selection;
- future liquidation outcome;
- market-return prices;
- returns, PnL, PF, win rate or drawdown;
- 2025/2026 access;
- live trading, orders, wallets, exchange mutation or execution webhooks;
- merge to main.

This remediation may emit only the terminal classes already allowed by R1 Execution Protocol V0.2.
