# MSEL-002 — Official Solana Sharded Source/Prevalence Transport Remediation V0.5 Freeze

Status: **FROZEN BEFORE EXECUTION / TRANSPORT-ONLY / ECONOMIC OUTCOMES LOCKED**  
Date: **2026-09-19**  
Branch: `memecoin-metadata-duplication-v0.1`

## Why this remediation exists

The exact Uniblock qualification run `35438540272` failed as
`UNIBLOCK_TRANSPORT_QUALIFICATION_TECHNICAL_FAILURE` because Uniblock's
historical coverage starts after the already-frozen source window.

That same qualification run independently reacquired from the official Solana
mainnet-beta JSON-RPC:

- exactly **9,564** successful Token Mint Authority signatures;
- deterministic signature-set SHA256:
  `8506bd8a5fb41bdbd866c237ce11f2015bc2813b0f2fc4fe31c3c466e6cb55a1`;
- the exact pre-frozen source boundaries.

The earlier official-mainnet V0.2 source collector had already proven the same
population but was cancelled by wall-clock/rate-limit pressure during
transaction retrieval. No row-level prevalence verdict and no economic outcome
was opened.

## Scientific invariants — unchanged

Inherited unchanged from
`MSEL_002_ONCHAIN_IMMUTABLE_IDENTITY_SOURCE_FREEZE_V01.md`:

- exact deterministic 12h source window;
- 6h warmup + 6h candidate window;
- 6h prior-only lookback;
- exact UTF-8 name and symbol;
- exact immutable IPFS/Arweave URI canonicalization;
- different `origin_creator` for primary exposure;
- same-creator clone descriptive only;
- fixed Pump program, Token Mint Authority, pinned IDL and CREATE discriminator;
- exact frozen source/prevalence gates;
- all post-launch economic outcomes remain locked.

## Frozen transport remediation

Canonical upstream evidence is the official-mainnet-beta subset preserved inside
run `35438540272`, artifact
`MSEL002_UNIBLOCK_TRANSPORT_QUALIFICATION_V0_1`.

The remediation:

1. verifies the qualification receipt failed only because the alternate
   provider history starts after target;
2. loads only the preserved `official-mainnet-beta/signatures.jsonl`;
3. requires exactly 9,564 rows and the exact frozen signature-set SHA256 above;
4. sorts by `(slot, signature)`;
5. partitions into exactly **16** deterministic shards by
   `zero_based_index mod 16`;
6. uses only `https://api.mainnet-beta.solana.com`;
7. fetches `getTransaction` read-only for each exact signature;
8. preserves raw JSON-RPC responses and hashes;
9. uses the existing frozen V0.1 CREATE decoder and V0.2 429 retry semantics;
10. permits at most **2 shard jobs concurrently**.

No failed/missing signature may be dropped. Every shard must return zero missing
transaction results.

## Canonical aggregate

Only the aggregate may compute source/prevalence diagnostics.

It must prove:

- 16/16 shard receipts PASS;
- exact deterministic partition membership;
- exact upstream signature-set identity;
- no signature omissions or duplicates;
- no CREATE identity duplicates;
- the unchanged `build_features` and `source_gates` implementation from V0.1.

Permitted terminal classifications are only those already defined by the frozen
source/prevalence gate. A source/prevalence PASS authorizes only a separate
future economic-outcome freeze.

## Forbidden

- moving or widening the window;
- changing the 6h lookback;
- fuzzy/case-insensitive matching;
- changing immutable URI rules;
- changing sample thresholds;
- replacing missing signatures;
- provider substitution after this freeze;
- opening migration, graduation, prices, returns, liquidity survival,
  winner/catastrophe labels or MSEL-001 outcomes;
- live trading, wallet use, transaction submission, chain mutation;
- merge to main or Render deployment.

This is throughput engineering only. It cannot rescue a failed prevalence gate
or create an economic edge.
