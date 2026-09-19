# AAVE-LIQUIDATION-OVERHANG-001 — R1 AUDIT SHARDING REMEDIATION V0.2

Date: 2026-09-19
Branch: `aave-liquidation-overhang-v0.1`
Status: **FROZEN BEFORE EXECUTION / OPERATIONAL-ONLY / OUTCOME-BLIND**

## Trigger

Two executions of the exact deterministic R1 scaled-ledger audit were terminated only by explicit GitHub Actions wall-clock ceilings:

- run `35226616121`: cancelled at 45 minutes;
- run `35355395431`: cancelled at 120 minutes.

Neither run produced an audit receipt or a reconstruction/scientific verdict. These are operational wall-clock cancellations only.

## Permitted remediation

V0.2 changes only acquisition topology.

1. The frozen borrower universe is recovered from the eight **canonical SOURCE_CENSUS_PASS shard receipts** produced by run `35214027573`.
2. Borrower selection is unchanged: union every canonical `Borrow.onBehalfOf` identity, compute `keccak256(raw 20-byte address)`, sort by `(digest,address)`, select exactly the first 16.
3. The selected sample must equal the sample that the original V0.1 algorithm would derive from the same canonical Borrow population. No borrower may be added, removed or replaced.
4. Token-native Mint/Burn/BalanceTransfer acquisition is split across the exact eight contiguous canonical source-census block ranges. Sharding is transport-only.
5. Each shard emits only source/replay deltas and provenance diagnostics. No shard can adjudicate R1.
6. A single aggregator recombines all eight exact ranges, replays balances at the unchanged four frozen audit blocks, performs the unchanged five-endpoint historical `scaledBalanceOf()` validation, and emits the same allowed R1 audit classifications.

## Exact unchanged scientific/reconstruction rules

- global block envelope: `16,490,000..21,525,890`;
- sample size: 16;
- audit blocks: `17,748,972`, `19,007,945`, `20,266,917`, `21,525,890`;
- R0 bootstrap: canonical `RECONSTRUCTION_R0_BOOTSTRAP_PASS`;
- reserve universe: exactly 37 point-in-time reserves;
- Aave V3 round-half-up ray arithmetic;
- aToken Mint/Burn/BalanceTransfer semantics;
- variable-debt non-transferability;
- historical validation function: `scaledBalanceOf(address)`;
- exact frozen RPC set and minimum 2-provider exact-agreement quorum;
- zero tolerance for replay/RPC mismatch;
- negative scaled-balance handling unchanged;
- protected 2025/2026 firewall unchanged.

## Canonical input pinning

Canonical source census run: `35214027573`.

Required shard artifacts:
`AAVE_CENSUS_SHARD_01` through `AAVE_CENSUS_SHARD_08`.

The eight receipts must:
- each classify `SHARD_PASS`;
- match the exact canonical ranges;
- form a no-gap/no-overlap global envelope;
- expose the Borrow participant identities used for deterministic sample selection.

If any receipt is missing, expired, malformed, non-pass, range-mismatched, or produces a borrower-union count inconsistent with canonical census evidence, stop fail-closed.

## Terminal semantics

The V0.2 aggregate may emit only:
- `R1_AUDIT_PASS`
- `RECONSTRUCTION_ACQUISITION_TECHNICAL_FAILURE`
- `RECONSTRUCTION_PROVENANCE_FAILURE`
- `RECONSTRUCTION_RECONCILIATION_FAILURE`
- `RECONSTRUCTION_INSUFFICIENT_COVERAGE`

A V0.2 `R1_AUDIT_PASS` is operationally equivalent to the audit gate defined in R1 Execution Protocol V0.2 and may feed the already-frozen downstream R1 global-state/reserve reconstruction.

## Safety

Still forbidden:
- health factor;
- liquidation-overhang predictor;
- adverse-shock selection;
- future liquidation outcomes;
- market-return prices;
- returns/PnL/PF/win rate/drawdown;
- 2025/2026 access;
- live trading, orders, wallets, exchange mutation or execution webhooks;
- merge to main.

No scientific parameter or pass/fail gate is altered by this remediation.
