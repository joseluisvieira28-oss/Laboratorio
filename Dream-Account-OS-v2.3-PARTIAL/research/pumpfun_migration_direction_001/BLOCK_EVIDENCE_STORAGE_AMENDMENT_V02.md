# PMD-001 — BLOCK EVIDENCE STORAGE AMENDMENT V0.2

Status: RESEARCH-ONLY / FAIL-CLOSED / PRE-OUTCOME
Branch: `pumpfun-migration-direction-v0.1`
Date: 2026-09-16

## Purpose

This amendment resolves one storage-only inconsistency discovered before economic outcomes were opened.

`BLOCK_FIRST_REBUILD_METHOD_FREEZE_V01.md` required preservation of the full returned block payload for every relevant slot. That requirement is retained for the bounded deterministic 20-date cross-date audit, where full block persistence remains practical and desirable as forensic evidence.

For the full 1,012-candidate reconstruction, persisting every entire block would materially increase artifact/storage volume while adding no new information to the frozen candidate/signature selection rule. This amendment therefore changes **only the persistence format** for the full-population stage.

It does not change the RPC data requested, the provider semantics, the window, sample, mint selection, transaction matching, feature-source eligibility, Source Gate thresholds, economic hypothesis, cost stress, split, or any outcome rule.

No economic outcome has been opened.

## 1. Cross-date audit storage remains unchanged

For the deterministic 20-date cross-date V0.2 audit, every requested full block payload MUST be persisted together with:
- source/provider name;
- mint;
- slot;
- blockTime where returned;
- UTC retrieval timestamp;
- canonical SHA-256 of the returned block payload;
- source error state, if any.

The cross-date audit therefore retains full forensic block evidence.

## 2. Full 1,012-population storage amendment

For the full-population block-first reconstruction, every required slot MUST still be fetched using canonical full `getBlock` transaction data. The source method is unchanged.

However, persistent storage of the entire block payload is not mandatory for all 1,012 candidates provided that the following evidence is preserved before the in-memory block object is discarded:

### Per fetched block
- source/provider name;
- mint;
- slot;
- blockTime where returned;
- UTC retrieval timestamp;
- canonical SHA-256 of the exact returned full block object;
- RPC/source error state;
- indicator stating whether the full block payload was additionally persisted.

### Per relevant signature
- mint;
- bonding-curve PDA;
- signature;
- declared slot;
- signature blockTime;
- transaction success/error metadata;
- exact full matched transaction body obtained from that block;
- canonical SHA-256 of the matched transaction response;
- canonical SHA-256 of the source block;
- source-block UTC retrieval timestamp.

This transaction-level evidence is the data actually available to the future feature builder and remains sufficient to audit that each included transaction came from a specific fetched canonical block response.

## 3. What is NOT changed

This amendment does not authorize any of the following:
- using `getTransaction` as the final transaction-body authority;
- skipping a required slot because the block is large;
- interpreting provider failure as zero activity;
- replacing a failed mint;
- shortening the 300-second window;
- including the integer second containing T0;
- changing `source_complete` or `feature_source_eligible` definitions;
- reducing the >=1,000 minimum viable Source Gate;
- reducing the >=20 distinct-date requirement;
- opening post-migration price values, returns, PnL or direction labels.

## 4. Reproducibility rule

A full-population block whose entire payload is not persisted remains reproducible only through the frozen tuple:
`(source/provider class, slot, retrieval timestamp, canonical block SHA-256)`.

If a later audit re-fetches a block and obtains a different canonical payload/hash, that difference is a source-integrity event and may not be silently reconciled.

The original matched transaction body and original block hash remain the scientific evidence used by this run.

## 5. Supersession scope

This amendment supersedes only the full-population persistence requirement in `BLOCK_FIRST_REBUILD_METHOD_FREEZE_V01.md` that every entire returned block payload must be stored.

It does **not** supersede the requirement that every relevant slot be fetched with full `getBlock`, nor any source-completeness, identity, ordering, hashing or leakage requirement.

For the 20-date cross-date audit, the original full-block persistence requirement remains binding.

## 6. Governance

- research-only;
- fail-closed;
- no economic outcomes opened;
- no exchange mutation;
- no live orders;
- no main merge;
- no post-outcome tuning;
- no cherry-picking;
- no threshold rescue.
