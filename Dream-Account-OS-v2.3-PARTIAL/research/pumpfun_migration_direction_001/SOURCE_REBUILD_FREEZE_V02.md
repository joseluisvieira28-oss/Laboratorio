# PMD-001 — SOURCE REBUILD FREEZE V0.2

Date: 2026-09-16
Branch: `pumpfun-migration-direction-v0.2-source-rebuild`
Status: RESEARCH-ONLY / PRE-OUTCOME / FAIL-CLOSED

## Authority

V0.1 is closed as `SOURCE_ALIGNMENT_FAILURE / INSUFFICIENT_SAMPLE`. V0.2 is not permitted to reinterpret V0.1's sparse raw corpus as evidence and may not open V0.1 outcomes.

V0.2 tests the same economic hypothesis using independently reconstructed historical Solana transactions.

## Hypothesis unchanged

The frozen thesis remains:

> immediately before Pump.fun graduation/migration, broad fresh demand and accelerating genuine buyer flow relative to concentrated latent sell inventory may predict whether post-migration demand can absorb realizations by earlier holders.

No directional thesis, primary horizon, cost stress or promotion gate is changed.

## Source authority hierarchy

1. **Primary pre-migration authority:** finalized raw Solana transactions/blocks from archival RPC, preserved byte-for-byte with SHA-256 receipts.
2. **Protocol semantics authority:** Pump program IDL/version proven appropriate for the transaction date; no current-IDL backport without version proof.
3. **Migration identity/time reconciliation:** canonical PumpSwap pool plus on-chain graduation/migration evidence. Public-corpus `migrated_at` may be used as a locator but not as sole authority if on-chain evidence disagrees.
4. **Public Pumpfun corpus:** reconciliation/reference only for pre-migration trade coverage in V0.2; it is not the scientific authority for final-window flow.
5. **Post-migration price source:** remains sealed until the entire source + feature + partition gate passes.

## Historical schema lock

The source corpus covers 2026-06-05 through 2026-07-14. The official `pump-fun/pump-public-docs` repository shows no repository commits between 2026-05-18 and 2026-07-15. V0.2 must pin and hash the Pump and PumpSwap IDLs from the last official repository state preceding each sampled event and must fail closed if an on-chain instruction cannot be reconciled with that schema.

A schema may not be selected because it produces more decoded trades.

## Source-rebuild pilot population

Before any outcome is opened, create a deterministic source pilot from the existing outcome-blind, post-execution-available population.

Pilot rule:
- group the eligible migrations by UTC migration date;
- for each retained migration date, compute `SHA256("PMD001-V02-SOURCE-PILOT|" + mint)`;
- take the 3 lowest hashes for that date, or every mint if fewer than 3 exist;
- expected target is up to 60 mints across the 20 retained dates;
- no ticker, popularity, return, creator, market-cap or narrative filter is allowed.

The pilot is a **source replication test only**. It has no authority to estimate strategy performance.

## Read-only archival route

Preferred execution paths, in order:

A. Standard archival RPC using `getSignaturesForAddress`/`getTransaction` around each sampled mint and migration, when complete history can be proven.

B. Standard archival block route using `getBlocks`/`getBlock`, reusing the fail-closed receipt/hashing pattern already validated by MSEL-001.

C. `getTransactionsForAddress` only if an authorized Helius paid endpoint is already available; using it is a source optimization, not a change in evidence standard.

No transaction submission method is permitted.

## Raw evidence window

For every source-pilot mint, collect finalized raw transaction evidence covering at least:

`T0 - 10 minutes` through `T0 + 2 minutes`.

If on-chain graduation time `G*` differs from the corpus locator T0, preserve both. Do not silently shift timestamps. The final source manifest must explain the relationship between:
- last valid bonding-curve trade;
- curve completion/graduation evidence;
- migration transaction/event;
- canonical PumpSwap pool initialization.

## Participant handling

Primary buyer/seller features exclude:
- protocol/program-owned accounts;
- bonding-curve/pool/token accounts;
- known fee recipients;
- known Pump autonomous agents;
- the System Program identity;
- failed transactions.

Creator-linked flow is retained separately and is not counted as independent external demand.

## Source pilot pass criteria

The source pilot may advance only if all of the following hold:

1. raw RPC responses and request metadata are preserved with hashes;
2. every decoded Pump BUY/SELL can be traced back to a successful finalized transaction and historical schema;
3. canonical mint identity is reconciled for every retained trade;
4. migration/graduation semantics are independently reconstructed rather than copied blindly from the public corpus;
5. no post-migration return or label has been read;
6. source coverage is high enough to make a full >=1,000-event rebuild realistically possible under the already-frozen population gate.

Criterion 6 must be decided from source availability and missingness only. No economic outcome is allowed to influence it.

## Scale gate remains unchanged

The full rebuilt feature population must still satisfy:
- total eligible >= 1,000;
- Validation >= 200;
- Protected Holdout >= 200;
- >=20 migration dates.

If authoritative source reconstruction cannot reach this scale, PMD-001 closes as `SOURCE_UNAVAILABLE / INSUFFICIENT_SAMPLE`.

## Economic rules inherited unchanged

From V0.1 + pre-outcome amendment:
- canonical PumpSwap population;
- non-Mayhem primary population;
- 2026-07-03 outage excluded from the public-corpus-derived post source;
- entry not earlier than T0+15s;
- source-bound entry cap T0+90s for the existing post source;
- primary hold = 5 minutes from actual entry;
- post-source exit target tolerance <=120s;
- 3.00 percentage-point round-trip execution stress;
- chronological 60/20/20 Discovery/Validation/Holdout;
- outcomes opened in order only after feature matrix and hashes are frozen.

## Forbidden rescue

V0.2 may not:
- lower the minimum sample gate;
- use the public corpus's sparse final-window rows as zeros;
- use current wallet state to reconstruct historical holder state;
- choose a historical IDL based on decode yield;
- alter costs after results;
- add indicators/social data after results;
- open Validation/Holdout early;
- merge to main;
- place live orders or mutate an exchange.
