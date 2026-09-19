# MSEL-002 — Sharded Source/Prevalence Transport Remediation V0.4 Freeze

Status: **FROZEN / DORMANT UNTIL UNIBLOCK_TRANSPORT_QUALIFICATION_PASS / ECONOMIC OUTCOMES LOCKED**
Date: 2026-09-19
Branch: `memecoin-metadata-duplication-v0.1`

## Activation condition

This remediation is dormant unless exact qualification run `35438540272` emits
`UNIBLOCK_TRANSPORT_QUALIFICATION_PASS`, proving:
- identical frozen source-start/source-end boundaries versus official Solana mainnet-beta;
- exactly 9,564 successful Token Mint Authority signatures;
- identical deterministic signature-set SHA256 across both providers.

No substitute qualification run may be used without a new prospective amendment.

## Scientific invariants

Unchanged from `MSEL_002_ONCHAIN_IMMUTABLE_IDENTITY_SOURCE_FREEZE_V01.md`:
- exact deterministic 12h source window;
- 6h warmup + 6h candidate window;
- 6h prior-only lookback;
- exact name + exact symbol + exact immutable IPFS/Arweave URI;
- different origin_creator for primary exposure;
- same-creator clone descriptive only;
- fixed Pump program, Token Mint Authority, IDL commit/blob and CREATE discriminator;
- fixed source/prevalence gates;
- all economic outcomes remain locked.

## Transport-only sharding

The qualified 9,564 signature rows are sorted by `(slot, signature)`.
Use exactly 8 deterministic shards. Signature at zero-based sorted index `i` belongs to shard `i mod 8`.

Each shard:
- uses only the qualified Uniblock read-only JSON-RPC route;
- fetches `getTransaction` for its exact signature subset;
- preserves raw JSON-RPC batch responses and SHA256 receipts;
- decodes Pump CREATE with the frozen V0.1 implementation;
- fails on any missing transaction result or schema ambiguity;
- emits no prevalence verdict by itself.

The canonical aggregate:
- verifies 8/8 shard receipts;
- verifies exact signature union, no duplicates/omissions, and upstream signature-set SHA256;
- combines CREATE rows and sorts by the original frozen point-in-time ordering;
- applies the unchanged `build_features` and `source_gates` logic from V0.1;
- is the only stage allowed to emit `SOURCE_PREVALENCE_PASS` or the frozen failure classification.

## Forbidden

- changing provider after qualification;
- moving or widening the time window;
- changing the 6h lookback;
- fuzzy/case-insensitive matching;
- relaxing any sample gate;
- dropping failed/missing signatures;
- opening migration, graduation, prices, returns, future transaction paths, winner/catastrophe labels or MSEL-001 outcomes;
- live trading, wallet/chain mutation, main merge.

This is a throughput remediation only.
