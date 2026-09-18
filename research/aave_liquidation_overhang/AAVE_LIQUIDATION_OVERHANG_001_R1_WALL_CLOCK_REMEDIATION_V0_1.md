# AAVE-LIQUIDATION-OVERHANG-001 — R1 WALL-CLOCK REMEDIATION V0.1

Date: 2026-09-18
Branch: `aave-liquidation-overhang-v0.1`
Status: **FROZEN BEFORE REMEDIATED R1 EXECUTION / OPERATIONAL-ONLY / OUTCOME-BLIND**

## Finding

The first deterministic R1 scaled-ledger audit run (GitHub Actions run `35226616121`) did not produce a scientific or reconstruction verdict.

The job reached the frozen audit execution step and was terminated at the workflow's explicit `timeout-minutes: 45` ceiling. The runner log records `The operation was canceled` at approximately 45 minutes after audit execution began. No canonical audit receipt was produced.

Classification of that run: **OPERATIONAL_WALL_CLOCK_CANCELLATION / NO SCIENTIFIC VERDICT**.

## Frozen remediation

The only permitted remediation is to increase the GitHub Actions wall-clock ceiling for the existing workflow from **45 minutes to 120 minutes**.

Everything else remains byte-identical or semantically unchanged:

- audit implementation: `research/aave_liquidation_overhang/r1_scaled_ledger_audit_v01.py`;
- frozen borrower sample rule: first 16 unique Borrow.onBehalfOf addresses by `keccak256(raw 20-byte address)`, sorted by `(digest,address)`;
- audit blocks: 17,748,972; 19,007,945; 20,266,917; 21,525,890;
- exact 37-reserve R0 bootstrap;
- exact token-native ray arithmetic;
- exact event semantics;
- exact archive RPC set;
- exact quorum and equality requirements;
- frozen 2023-2024 block envelope;
- protected-period firewall.

This remediation must not shard, filter, replace borrowers, skip targets, loosen RPC quorum, alter arithmetic, alter source identities, or change any pass/fail condition.

## Safety

Still forbidden:

- health factor calculation;
- liquidation-overhang calculation;
- adverse-shock selection;
- future liquidation outcomes;
- market-return prices;
- returns or PnL;
- 2025/2026 access;
- live trading, orders, wallets, exchange mutation or execution webhooks;
- merge to main.

A successful rerun may emit only the classifications already allowed by R1 Execution Protocol V0.2.
