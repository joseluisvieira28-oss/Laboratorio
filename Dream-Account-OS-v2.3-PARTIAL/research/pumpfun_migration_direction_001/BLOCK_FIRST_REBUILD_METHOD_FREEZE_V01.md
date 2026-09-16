# PMD-001 — BLOCK-FIRST REBUILD METHOD FREEZE V0.1

Date: 2026-09-16
Status: **RESEARCH-ONLY / FAIL-CLOSED / PRE-OUTCOME / METHOD FROZEN**
Branch: `pumpfun-migration-direction-v0.1`

## Purpose

A deterministic public-RPC source probe showed that mint-specific bonding-curve PDA signature history was available, while direct historical `getTransaction` responses were incomplete. The already-authorized `getBlock` remediation recovered all 28 missing transaction bodies from 4/4 requested blocks without opening any economic outcome.

To avoid mixing transaction-body authorities across the final source population, PMD-001 now freezes a uniform **block-first** reconstruction method before any predictive feature or economic outcome is opened.

This is source engineering only. No economic rule, sample gate, execution convention, cost stress, split or promotion criterion changes.

## Frozen block-first algorithm

For each mint in the already-frozen 1,012-candidate manifest:

1. Derive the Pump bonding-curve PDA from `[b"bonding-curve", mint]` and Pump program ID `6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P`.
2. Use `getSignaturesForAddress` on that PDA, paginating until either:
   - at least one signature timestamp is strictly below `T0-300s`, or
   - provider history is demonstrably exhausted.
3. Keep signature metadata only for rows satisfying `T0-300s <= blockTime < T0`.
4. Collect the set of unique slots containing those in-window signatures.
5. Fetch **every** such slot with canonical full `getBlock` transaction data.
6. For every in-window signature, locate the exact transaction in its declared slot. It must appear exactly once.
7. Store the full raw block evidence separately, together with a deterministic SHA-256 receipt.
8. Derived pre-outcome transaction rows may only be built from those frozen block bodies.

Direct `getTransaction` is no longer the transaction-body authority for the block-first population. It may be used only as a non-binding reconciliation diagnostic.

## Completeness requirements per mint

A mint is `source_complete=true` only when all of the following hold:

- pagination crosses below `T0-300s` or history is provably exhausted;
- no relevant signature has null `blockTime`;
- no duplicate signature metadata conflicts;
- every unique in-window slot returns a valid full block;
- every in-window signature is located exactly once in its declared block;
- every stored block passes raw-evidence hashing;
- transaction ordering and signature identity remain internally consistent.

A provider error, missing block, absent signature body, conflicting duplicate or unproven pagination boundary fails that mint closed.

Missing history is never interpreted as zero demand.

## Provider rule

The block-first method is provider-agnostic at the JSON-RPC semantic level, but provider changes cannot silently occur inside the final source population.

- Standard public Solana RPC may be used for bounded source-access audits.
- The final 1,012-candidate collection must identify its endpoint/provider class in every receipt.
- If more than one provider is needed, deterministic overlap reconciliation must prove equivalent signature/block evidence before populations may be combined.
- Provider differences are source-integrity events, not economic observations.

## Raw evidence minimum

For each relevant slot preserve at least:

- provider/source name;
- slot;
- full returned block transaction payload;
- block time where available;
- retrieval timestamp;
- canonical SHA-256 of the stored block payload.

For each target signature preserve at least:

- mint;
- bonding-curve PDA;
- signature;
- slot;
- blockTime;
- exact matched transaction body;
- transaction success/error;
- full account keys, outer instructions, inner instructions, balances and logs available from the block response.

## Economic leakage wall

The block-first source stage MUST NOT read, project or compute:

- post-migration price values;
- `postgard_outcomes.parquet`;
- returns or PnL;
- UP/DOWN/continuation/reversal labels;
- feature/outcome correlations;
- Discovery, Validation or Protected Holdout statistics.

Only the already-authorized identity/timestamp/nullness metadata may be used to bind the 1,012-candidate source manifest.

## Cross-date access audit before full reconstruction

Before attempting the full 1,012-candidate rebuild, run exactly one deterministic source-access probe per distinct migration date in the frozen manifest:

- group the frozen manifest by UTC migration date;
- choose the earliest `(T0, mint)` candidate in each date;
- expected audit size: exactly **20 mints across 20 dates**;
- no replacement of a failed mint is allowed;
- no outcome information may influence selection.

The audit is a source-access diagnostic only. It does not reduce, redefine or satisfy the final `n>=1000` Source Gate.

## Cross-date audit classification

- `BLOCK_FIRST_CROSSDATE_ACCESS_PASS`: all 20 deterministic probes are source-complete under this method.
- `BLOCK_FIRST_CROSSDATE_ACCESS_PARTIAL`: at least one but not all deterministic probes are source-complete.
- `BLOCK_FIRST_CROSSDATE_ACCESS_FAIL`: none are source-complete or the selection/integrity contract fails.

No classification above is an economic verdict.

## Unchanged final source gate

The final source gate remains:

- eligible reconstructed population >= 1,000;
- frozen Validation count >= 200;
- frozen Protected Holdout count >= 200;
- >=20 distinct migration dates;
- no leakage/integrity failure.

Only after that gate passes may exact predictive feature formulas be frozen.

Outcomes remain locked.
