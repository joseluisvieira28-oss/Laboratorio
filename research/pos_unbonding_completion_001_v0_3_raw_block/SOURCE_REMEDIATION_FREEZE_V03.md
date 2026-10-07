# POS-UNBONDING-COMPLETION-SUPPLY-RELEASE-001 — V0.3

SOURCE REMEDIATION + MATERIALITY FREEZE — 2026-10-07

Parent V0.2 branch: `pos-unbonding-completion-001-source-remediation-v0.2-2026-10-06`
Parent V0.2 verdict: `SOURCE_HISTORICAL_COVERAGE_BLOCKED`
Parent main baseline: `f263c6c6f3a57f26666a7aee28e782f2cbd08418`
Outcomes opened before this freeze: NO

## Scope and firewall

V0.3 exists only to remove the V0.2 `tx_search` dependency by reconstructing the staking lifecycle from canonical historical raw blocks and block results, and to freeze source-only materiality before any event census/count is inspected.

Frozen study completion interval remains 2023-01-01 through 2024-12-31 UTC. Earlier initiation blocks may be read only when required to reconstruct a completion inside that interval. 2025 remains unopened. 2026 chain observations and all market outcomes remain forbidden.

No market prices, returns, PnL, market-volume values, wallets, account reads, authenticated/private endpoints, orders, exchange mutation, spending, main merge/update or post-outcome tuning.

## Comparable mechanism

Eligible chains must use production Cosmos SDK native `x/staking` undelegation semantics (or a chain-pinned fork proven behaviorally equivalent for the fields below).

Required lifecycle:
1. successful `/cosmos.staking.v1beta1.MsgUndelegate`;
2. committed chain-native completion schedule/entry;
3. explicit handling of `MsgCancelUnbondingDelegation` including partial cancellation;
4. slash-adjusted remaining principal;
5. validator/ICS/module hold or unbonding-counter effects;
6. actual canonical staking completion where the same remaining voluntary principal exits unbonding state;
7. final released native amount and canonical block timestamp.

Nominal unbonding duration, expected maturity or transaction index is never a substitute for actual completion.

## Raw-block reconstruction protocol

`tx_search` is not required.

For every bounded historical block:
- fetch `/block?height=H` and persist response digest;
- decode every base64 transaction as Cosmos `TxRaw -> TxBody -> Any`;
- retain staking messages needed for the cohort ledger, at minimum `MsgUndelegate` and `MsgCancelUnbondingDelegation`;
- parse transaction execution only from the corresponding `txs_results` at the same block, and retain only successful messages/transactions;
- NEVER align a later `complete_unbonding` lifecycle event to the initiation by transaction index.

For each canonical `/block_results?height=H`:
- inspect `end_block_events` on legacy Tendermint/Cosmos versions and `finalize_block_events` on ABCI++/CometBFT versions;
- detect staking `complete_unbonding` events and record final amount, validator, delegator and block time;
- preserve source/version schema and response hash.

Cohort matching must use delegator + validator + creation context + committed completion entry and remaining principal, not merely day, amount or array position.

## Independent evidence

Each selected chain requires two independently operated historical evidence paths, or one canonical archive plus an independently reconstructed verifiable path that does not merely proxy the same operator.

Provider agreement must reconcile:
- canonical block IDs/timestamps;
- initiation cohort principal and committed completion schedule;
- cancellations/partials;
- slash/hold adjustments or explicit absence;
- actual completion block;
- final released amount;
- bounded coverage/pagination completeness.

Agreement on isolated sample blocks is not enough to claim full census completeness.

## Predeclared V0.3 primary chain set

The primary source-remediation set is the first five comparable chains for which two independent archive paths can be proven without private/authenticated access:

1. Cosmos Hub / ATOM
2. Osmosis / OSMO
3. Kava / KAVA
4. Celestia / TIA
5. dYdX Chain / DYDX

The deterministic registry universe remains authoritative for exclusions and audit. These five do not permit outcome-based replacement. A chain that fails comparability or independent historical coverage causes the >=5-chain gate to fail unless another registry-eligible chain was prospectively proven comparable before any market outcome is opened.

## Material chain-day definition — frozen before census

Primary source unit: UTC `chain-day`.

For each eligible chain-day d:
- `R_d` = sum of final native principal actually released by qualifying voluntary `complete_unbonding` cohorts whose canonical T_completion lies in UTC day d, after cancellation, partial cancellation, slash and hold reconciliation.
- `B_d` = canonical historical bonded native tokens from staking pool state at the last available block strictly before 00:00:00 UTC of day d (or the first canonical block of the day if the chain began that day). No current-state substitution.
- `M_d = R_d / B_d`.

A chain-day is **MATERIAL** iff:

`M_d >= 0.001`  (10 basis points = 0.10% of historical bonded stake)

Rationale frozen ex ante: a one-day release of at least 10 bps of bonded stake is a clearly non-trivial liquidity transition; if repeated daily it corresponds to 36.5% of bonded stake per year. The threshold is intentionally conservative and is not chosen from observed counts or market outcomes.

All eligible completion days are retained in census evidence, including sub-threshold days. The threshold cannot be lowered, changed to circulating supply, changed to ADV, or chain-tuned after counts are observed.

## Hard source gates

G1. >=5 comparable production chains with pinned staking lifecycle semantics.
G2. two independent historical evidence paths per selected chain with bounded 2023-2024 coverage.
G3. raw-block initiation reconstruction + actual completion reconstruction works without `tx_search`.
G4. cancellations, slash effects, forced transitions and holds are explicitly resolved or fail-closed.
G5. >=40 MATERIAL chain-days TOTAL across >=5 chains under the frozen 10 bp rule. This is total, not per-chain.
G6. >=12 consecutive months of pre-2026 liquid-market source capability/provenance for every final selected instrument, without opening outcomes before this source gate passes.
G7. reproducible receipts/digests and no prohibited access.

Allowed source verdicts:
- `SOURCE_GATE_PASS`
- `SOURCE_HISTORICAL_COVERAGE_BLOCKED`
- `INSUFFICIENT_INDEPENDENT_SAMPLE`
- `MECHANISM_NOT_COMPARABLE`
- `SOURCE_PROVENANCE_INCOMPLETE`
- `TECHNICAL_FAILURE`

No economic `NO_EDGE` verdict is possible in this version.

## Next step only after PASS

If and only if all G1-G7 pass, create a separate PRE-OUTCOME ANALYSIS FREEZE before reading any market outcome. It must preserve the paired same-cohort `T_signal` versus actual `T_completion` design required by V0.1.1 and freeze exact outcome windows, controls, anticipation handling, costs, clustering, leave-one-out/concentration gates and decision rule before one Development execution.
