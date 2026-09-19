# AAVE-LIQUIDATION-OVERHANG-001 — R1 SCALED-LEDGER AUDIT SHARDED REMEDIATION V0.2

Date: 2026-09-19
Branch: `aave-liquidation-overhang-v0.1`
Status: **FROZEN BEFORE V0.2 EXECUTION / OPERATIONAL-ONLY / OUTCOME-BLIND**

## Trigger

The exact V0.1 deterministic audit was attempted twice without a scientific verdict:

- run `35226616121`: cancelled at the explicit 45-minute workflow wall-clock ceiling;
- run `35355395431`: cancelled at the remediated 120-minute wall-clock ceiling.

Both runs were terminated while executing the same monolithic historical source scan. Neither produced a canonical R1 audit receipt. No health factor, overhang, future liquidation outcome, market return or PnL was opened.

These are operational wall-clock failures, not reconstruction failures and not economic evidence.

## Frozen scientific identity

V0.2 MUST preserve the R1 Execution Protocol V0.2 exactly:

- global historical envelope: blocks `16,490,000..21,525,890`;
- reserve universe: exact canonical 37-reserve R0 bootstrap;
- borrower universe: every unique `Borrow.onBehalfOf` address in the frozen envelope;
- sample rule: `keccak256(raw 20-byte borrower address)`, sort by `(digest,address)`, first exactly 16;
- audit blocks: `17,748,972`, `19,007,945`, `20,266,917`, `21,525,890`;
- token-native Mint/Burn/BalanceTransfer semantics;
- exact Aave round-half-up RAY arithmetic;
- variable-debt non-transferability requirement;
- exact five frozen independent archive RPC endpoints;
- at least two usable RPC endpoints per target;
- exact endpoint agreement and exact replay equality;
- no failed target, user, token, reserve or endpoint may be removed after inspection.

## Operational-only remediation

The canonical Source Census run `35214027573` already contains eight immutable outcome-blind shard receipts covering the exact same frozen block envelope. Those receipts include the structural `Borrow.onBehalfOf` participant identities used by the frozen sample rule.

V0.2 is authorized to:

1. reconstruct the same borrower universe from those eight canonical census shard receipts rather than rescanning the entire Pool Borrow history serially;
2. prove the union contains exactly the canonical `30,691` unique borrowers;
3. derive the exact frozen 16-borrower sample by the unchanged hash/sort rule;
4. split only the token-native event acquisition across the same eight disjoint contiguous block ranges;
5. aggregate all token deltas before replay;
6. run the unchanged replay target construction and unchanged independent RPC validation;
7. if and only if the resulting audit classification is `R1_AUDIT_PASS`, continue to the already-prepared global-state/oracle gate, eight reserve replay shards, and canonical R1 adjudication.

The eight transport ranges are:
- 16,490,000..17,119,486
- 17,119,487..17,748,973
- 17,748,974..18,378,460
- 18,378,461..19,007,946
- 19,007,947..19,637,432
- 19,637,433..20,266,918
- 20,266,919..20,896,404
- 20,896,405..21,525,890

They are execution partitions only. No scientific subgroup result may be computed or selected from a shard.

## Equivalence requirements

V0.2 must fail closed unless:

- all eight canonical Source Census shard receipts are present and `SHARD_PASS`;
- their ranges exactly equal the frozen eight ranges with no gap/overlap;
- the union of `participants_by_event.Borrow` contains exactly 30,691 unique addresses;
- the derived sample has exactly 16 addresses;
- every token-acquisition shard uses the identical sample SHA256;
- the eight token-acquisition ranges exactly cover the frozen global envelope;
- all token deltas are combined before any audit-block replay value is evaluated;
- no market/outcome data is opened.

## Terminal semantics

The final scaled-ledger audit may emit only the classifications already allowed by R1 Execution Protocol V0.2:

- `R1_AUDIT_PASS`
- `RECONSTRUCTION_ACQUISITION_TECHNICAL_FAILURE`
- `RECONSTRUCTION_PROVENANCE_FAILURE`
- `RECONSTRUCTION_RECONCILIATION_FAILURE`
- `RECONSTRUCTION_INSUFFICIENT_COVERAGE`

Only `R1_AUDIT_PASS` authorizes the remaining R1 reconstruction components.

## Safety

Still forbidden:

- health factor;
- liquidation-overhang predictor;
- adverse-shock threshold;
- future liquidation outcome;
- market-return prices;
- returns, PnL, PF, win-rate or drawdown;
- 2025/2026 access;
- live trading, orders, wallets, exchange mutation or execution webhooks;
- merge to main.

This amendment changes transport topology only. It does not weaken or replace a scientific gate.
