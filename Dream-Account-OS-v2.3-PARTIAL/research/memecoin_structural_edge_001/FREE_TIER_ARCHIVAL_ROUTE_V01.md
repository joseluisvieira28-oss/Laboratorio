# MSEL-001 — FREE-TIER ARCHIVAL ROUTE V0.1

Status: RESEARCH-ONLY / FAIL-CLOSED / OUTCOMES LOCKED
Date: 2026-09-15
Branch: memecoin-structural-edge-v0.1

## Key correction

The frozen 25-launch pilot does **not** require the paid Helius `getTransactionsForAddress` method.

Helius currently documents two distinct facts:

1. `getTransactionsForAddress` (gTFA) is Helius-only and available on paid plans; it is the fast path.
2. Standard Solana archival methods such as `getBlock`, `getTransaction`, `getBlocks`, `getBlockTime`, and related archival RPC reads are backed by Helius archival infrastructure and archival access is available on all plans, including Free.

Therefore MSEL-001 can attempt the 25-launch cohort on a free Helius project/API key using a block-first archival scan. No paid subscription is scientifically required for the pilot.

## Primary free-route design

Frozen timestamp: `2025-06-13T12:22:13Z` / Unix `1749817333`.

Frozen population rule remains unchanged:

> first 25 successful Pump CREATE instructions with `blockTime > 1749817333`, in canonical blockchain order.

Route:

1. Use `getFirstAvailableBlock` and `getSlot(finalized)` to obtain provider bounds.
2. Locate the timestamp boundary using `getBlockTime` with skipped-slot handling through `getBlocksWithLimit`.
3. Refine the boundary over a local confirmed-block window; fail if block-time ordering is inconsistent or the local window cannot prove a before/after boundary.
4. Starting from the first confirmed block strictly after the frozen timestamp, call `getBlock` with `transactionDetails=full`, `encoding=json`, `rewards=false`, `maxSupportedTransactionVersion=0`.
5. Preserve the exact transaction-array order returned by the block. Array position is the canonical transaction index for the pilot.
6. Parse successful transactions only (`meta.err == null`).
7. Resolve Pump program instructions, including inner instructions.
8. Decode only the historically frozen CREATE discriminator `[24,30,200,40,5,28,7,119]` using the official Pump IDL commit `e2b66e4fce2fc130955912315167dc41e56956ad`.
9. Stop only after the first 25 CREATE events have been observed in canonical block / transaction / instruction order.
10. Hash and retain raw JSON-RPC responses before derived cohort files are produced.

## Why blockscan is scientifically attractive

The paid gTFA route is faster, but blockscan has one important audit advantage for a tiny pilot: the complete block contains the transaction array in canonical block order. This removes any dependence on provider-specific address-index ordering when deciding which CREATE is #1 ... #25.

For MSEL-001, speed is secondary to cohort identity.

## Expected cost

Free Helius currently advertises 1M monthly credits and archival access. A 25-launch Pump.fun pilot should require only a small fraction of that budget if the launch-rate window is narrow. The exact request count is recorded in the evidence manifest and is not assumed in advance.

No paid upgrade is authorized merely for convenience. Upgrade only if the free route fails for an explicit technical reason and that failure is documented.

## Two-route reconciliation

If a paid Helius key later becomes available, run both:

- Route A: standard archival blockscan (canonical selection authority)
- Route B: gTFA fast address scan (independent Helius index cross-check)

Required match for all 25:

- mint
- signature
- slot
- blockTime
- transaction ordering
- origin creator
- transaction user / payer

Any mismatch => `SOURCE_CONFLICT`, not edge/no-edge.

## Raw-evidence correction

The first gTFA collector canonicalized `result` before writing page files. That is useful for deterministic hashing but is not byte-for-byte preservation of the HTTP JSON-RPC response envelope.

For the blockscan route, preserve both:

- exact HTTP response bytes + SHA-256;
- normalized/canonical derived records + SHA-256.

Do not call a normalized result “raw HTTP”.

## Transaction-version rule

The June-2025 pilot is frozen to historical transactions from that period, for which transaction version `0`/legacy coverage is sufficient. Current Solana/Agave guidance in 2026 now requires clients indexing present-day v1 transactions to use `maxSupportedTransactionVersion=1`, but that protocol change must not be retroactively mixed into this 2025 pilot without evidence that a selected 2025 transaction requires it.

If any selected historical block returns a transaction-version error under version 0, stop and classify `SCHEMA_VERSION_BLOCKED` before changing the rule.

## STOP conditions

Fail closed if any occurs:

- provider cannot return historical June-2025 blocks;
- boundary around frozen timestamp cannot be proven deterministically;
- blockTime is missing in the boundary/selected window;
- full transaction data is missing;
- historical CREATE data does not decode exactly under the frozen IDL;
- CREATE account layout does not match the historical schema;
- selected CREATE event ordering is ambiguous;
- duplicate CREATE identity or duplicate mint appears inside the selected 25 without an explainable protocol event;
- provider/raw response hashes are not preserved;
- any future-price, migration, survival, or post-T+5 field is introduced before feature freeze.

## Current verdict

`PAID_HELIUS_REQUIRED` => **REJECTED**.

`ARCHIVAL_API_KEY_REQUIRED` => **YES**, but a free Helius key should be sufficient for the blockscan route.

`PILOT_EXECUTABLE_WITHOUT_OUTCOME_OPENING` => **YES once an archival RPC key/URL is supplied to the collector environment**.

Governance unchanged: no live trading, no chain mutation, no exchange mutation, no merge to main, no protected outcome opening, no post-outcome tuning.