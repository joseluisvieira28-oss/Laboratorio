# AAVE-LIQUIDATION-OVERHANG-001 — R1 AUDIT CANONICAL-CENSUS REUSE REMEDIATION V0.2

Date: 2026-09-19
Branch: `aave-liquidation-overhang-v0.1`
Status: **FROZEN BEFORE V0.2 EXECUTION / OPERATIONAL-ONLY / OUTCOME-BLIND**

## Trigger

Two executions of the unchanged R1 scaled-ledger audit V0.1 terminated only at explicit GitHub Actions wall-clock ceilings:
- run `35226616121`: 45-minute ceiling;
- run `35355395431`: 120-minute ceiling.

Neither run produced a scientific reconstruction verdict or canonical audit receipt. No health factor, overhang, future liquidation outcome, market return or PnL was opened.

## Frozen remediation

V0.2 removes only one redundant network operation: re-enumerating the entire historical Pool `Borrow` log population to recover the deterministic borrower universe.

Instead, V0.2 must reconstruct the exact same borrower universe from the eight byte-authoritative source-census shard receipts produced by canonical Source Census run `35214027573`.

Those receipts were generated from the same frozen Ethereum mainnet block envelope and already contain `participants_by_event.Borrow` using the same indexed `Borrow.onBehalfOf` identity.

Required invariants:
- exactly eight canonical shard receipts;
- every shard classification = `SHARD_PASS`;
- union of `participants_by_event.Borrow` = exactly 30,691 unique borrowers;
- deterministic sample remains exactly first 16 addresses sorted by `(keccak256(raw 20-byte address), address)`;
- no borrower may be added, removed, substituted or selected from economic outcomes.

After sample reconstruction, the existing V0.1 implementation remains authoritative and unchanged for:
- 37-reserve token map;
- aToken/variable-debt Mint/Burn/BalanceTransfer acquisition;
- ray arithmetic;
- four audit blocks;
- replay target construction;
- negative-state checks;
- variable-debt non-transferability;
- five frozen archive RPC endpoints;
- >=2 usable endpoint quorum;
- exact endpoint agreement;
- exact replay equality;
- all terminal classifications.

Canonical R0 bootstrap remains pinned to run `35218275356`.

## Scientific consequence

This is transport/work reuse, not a hypothesis or validation change. It may only reduce redundant source acquisition time.

V0.2 must emit the same scientific classifications already authorized by R1 Execution Protocol V0.2:
- `R1_AUDIT_PASS`;
- `RECONSTRUCTION_ACQUISITION_TECHNICAL_FAILURE`;
- `RECONSTRUCTION_PROVENANCE_FAILURE`;
- `RECONSTRUCTION_RECONCILIATION_FAILURE`;
- `RECONSTRUCTION_INSUFFICIENT_COVERAGE`.

No threshold, reserve, wallet, block, arithmetic, RPC quorum or pass condition changes.

## Firewalls

Still forbidden:
- health factor;
- liquidation-overhang predictor;
- adverse-shock selection;
- future liquidation outcomes;
- market-return prices;
- returns/PnL/PF/win rate/drawdown;
- 2025/2026 access;
- live trading, orders, wallets, exchange mutation, alerts/webhooks;
- merge to main.
