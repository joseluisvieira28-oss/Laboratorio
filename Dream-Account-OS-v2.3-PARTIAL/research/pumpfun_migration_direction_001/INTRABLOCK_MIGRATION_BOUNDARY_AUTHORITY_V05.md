# PMD-001 — INTRABLOCK MIGRATION BOUNDARY AUTHORITY V0.5

Date: 2026-09-16
Status: **RESEARCH-ONLY / FAIL-CLOSED / PRE-OUTCOME / FEASIBILITY ONLY**
Branch: `pumpfun-migration-direction-v0.1`

## Why this separate source-method version exists

`TIMESTAMP_PRECISION_CUTOFF_AMENDMENT_V01.md` conservatively quarantined the entire integer second containing corpus `T0` because standard Solana `blockTime` is second-resolution while the corpus migration timestamp is microsecond-resolution.

That amendment explicitly anticipated that a future independently frozen source method could identify the exact on-chain Pump `migrate` instruction and transaction index. Cross-Date V0.4 subsequently produced mandatory rows whose visible bonding-curve signatures were confined to the quarantined T0 second. V0.4 remains failed/blocked under its own rules and is not retroactively changed by V0.5.

No economic outcome has been opened.

## Scientific question unchanged

Can information observable strictly before Pump.fun migration predict economically tradable post-migration direction?

V0.5 changes only source-time resolution at the migration boundary. It does not change:
- economic thesis;
- candidate population ceiling;
- 300-second backward source window;
- post-migration execution rules;
- 3.00 percentage-point cost stress;
- chronological split;
- minimum sample gates;
- promotion gates;
- outcome lock.

## Authoritative programs and instruction identity

Pump program:
`6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P`

PumpSwap AMM program:
`pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA`

Anchor discriminator for Pump `migrate`:
`[155,234,231,146,236,158,162,30]`
(hex `9beae792ec9ea21e`).

The official Pump IDL defines `migrate` as migration of a completed bonding curve to PumpSwap and includes the target mint, bonding-curve PDA and canonical PumpSwap pool among its accounts.

## Exact boundary definition

For a frozen candidate `(mint, canonical_pool, corpus_T0)`, V0.5 may define an exact on-chain migration boundary only if it finds exactly one successful transaction satisfying all of:

1. an outer instruction invokes the Pump program;
2. the instruction data begins with the exact `migrate` discriminator above;
3. the instruction account set contains the frozen mint;
4. the instruction account set contains the deterministically derived mint bonding-curve PDA;
5. the instruction account set contains the frozen canonical PumpSwap pool address;
6. the transaction block time is the integer second containing corpus `T0`;
7. the transaction body and containing finalized block are complete and hashable.

Zero or multiple matching boundary transactions => `BOUNDARY_UNRESOLVED` for that candidate. No nearest-transaction heuristic is allowed.

## Ordering key

The exact boundary ordering key is:

`(migration_slot, migration_transaction_index_in_finalized_block)`.

For bonding-curve transaction evidence inside `[T0-300s, T0 second]`:

- any transaction with `blockTime < floor(T0)` remains pre-migration eligible under the existing conservative rule;
- a transaction in the same integer second as `T0` is eligible only if its finalized-block ordering key `(slot, transaction_index)` is strictly less than the exact migration boundary key;
- a transaction with an ordering key equal to or after the migration boundary is forbidden from predictive features.

Where two transactions touch the same bonding-curve state, ledger order is used only as a causal ordering source; no price/outcome information is consulted.

## Corpus alignment requirement

The exact migration transaction must have `blockTime == floor(corpus_T0)`.

If the exact on-chain migrate is found in a different integer second, that candidate is `CORPUS_T0_ALIGNMENT_UNRESOLVED` and cannot be rescued with a tolerance chosen after inspection.

## Feasibility probe only

The first V0.5 execution has **no Source Gate or promotion authority**.

Frozen probe candidates:

### Previously failed boundary-precision cases
- Cross-Date V0.4 index 1: `QHhbroZxDShtSXm9X2RqjpQP9FvpxbSTUWktPMopump`
- Cross-Date V0.4 index 5: `7N3RPJC7ZxXyEnVyx8i83dcKb9QjMjV34cH2VKjypump`

### Positive source controls fixed before V0.5 results
- Cross-Date V0.4 index 0: `9af7PmWRca2QYmknQehoLH19jG5ss9ajYFpgL8dMpump`
- Cross-Date V0.4 index 10: `71HtXHfexjKgem92Y5sPLPb6qkmtqWmPUzdKAcU9pump`

These four are selected only from already-open source-integrity results; no economic outcomes exist or are consulted.

## Feasibility outputs permitted

For each frozen probe row, report only:
- migration boundary found/unresolved;
- migration signature;
- migration slot;
- migration transaction index;
- block time;
- count of same-second bonding-curve signatures;
- count/order of same-second signatures strictly before migration;
- count/order at or after migration;
- count of successful target Pump buy/sell transactions before migration;
- source completeness/integrity flags;
- hashes of raw blocks/transactions.

No post-migration price, return, direction label or PnL may be read.

## Feasibility success condition

V0.5 is only `INTRABLOCK_BOUNDARY_METHOD_FEASIBLE` if all four frozen probe candidates:
- have exactly one authoritative migration boundary;
- align to the corpus T0 integer second;
- have complete finalized-block evidence;
- can classify every same-second bonding-curve signature unambiguously as before or at/after boundary.

Failure of any one probe row => method remains `INTRABLOCK_BOUNDARY_METHOD_UNRESOLVED` and no full-population V0.5 run is authorized by this document.

A feasibility PASS still does **not** authorize outcomes. A separate pre-outcome execution freeze for the complete 1,012 population and unchanged >=1,000 / >=20-date Source Gate would be required.

## Explicit prohibitions

- V0.5 does not change or erase the V0.4 verdict.
- No replacement probe mint after results.
- No nearest timestamp heuristic.
- No inferred migration from PumpSwap price activity.
- No post-migration feature.
- No reduction of sample gates.
- No opening of `postgard_outcomes.parquet`.
- No economic outcome opening.
- No live trading or exchange mutation.
- No merge to main.
