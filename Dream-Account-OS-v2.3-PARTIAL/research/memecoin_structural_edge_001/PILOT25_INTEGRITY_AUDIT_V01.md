# MSEL-001 — PILOT25 INTEGRITY AUDIT V0.1

Status: **SOURCE-SELECTION INTEGRITY PASS / OUTCOMES LOCKED**

Branch: `memecoin-structural-edge-v0.1`

Frozen cohort source: first 25 successful Pump CREATE instructions with `blockTime > 2025-06-13T12:22:13Z` in canonical block transaction order.

## Hash verification

The user-supplied pilot outputs were independently re-hashed before any outcome inspection.

- `cohort_25.jsonl` SHA-256: `7e107b82cc80afe1a9ea3ef4ac321d3ac35bbb89a317af84bc6cf317fd617aa9`
- `rpc_receipts.json` SHA-256: `2a69709f14eb602bfaa49e965d2d30fd6270b0d6e1ec1416aca9cde84cd969da`
- `source_manifest.json` SHA-256: `f6990bd8728a092cbab28aa57026bfd72080460c9a3a191ce42e567be4f10414`

The cohort and RPC-receipt hashes exactly match the values recorded in the manifest. Cohort size is 25 and `outcomes_opened=false`.

## Structural integrity checks

PASS:

- cohort ranks are exactly 1..25;
- 25 unique mints;
- 25 unique CREATE signatures;
- 25 unique bonding-curve addresses;
- canonical `(slot, transaction_index)` ordering is monotonic;
- first launch block time: `2025-06-13T12:22:16Z`;
- last launch block time: `2025-06-13T12:23:43Z`;
- complete frozen cohort spans only 87 seconds;
- all 25 CREATE instructions are outer Pump instructions;
- all 25 decoded CREATE payloads have zero unexplained trailing bytes.

RPC receipt ledger:

- 796 sequential request IDs, exactly 1..796;
- 218 `getBlock` reads retained as raw response files;
- 543 `getBlockTime` reads;
- 31 `getBlocksWithLimit` reads;
- 2 `getBlocks` reads;
- 1 `getFirstAvailableBlock` read;
- 1 `getSlot` read;
- all 796 response hashes are distinct.

## Pre-outcome cohort observations

These observations describe only launch-time structure and MUST NOT be interpreted as alpha or outcome separation.

- `origin_creator == tx_user` in 25/25 launches.
- `origin_creator == fee_payer` in 25/25 launches.
- 22 unique creator identities across 25 launches.
- One creator emitted 2 launches inside the 87-second cohort.
- Another creator emitted 3 launches inside the 87-second cohort.
- 24/25 launches contain a Pump BUY in the same transaction as CREATE.
- 1/25 does not contain a same-transaction Pump BUY.
- 24/25 CREATE URIs use `ipfs.io`; 1/25 uses `cloudflare-ipfs.com`.
- No exact URI is duplicated inside the 25-launch cohort.
- Exact `rooroo` name/symbol reuse occurs three times and all three are from the same creator, with later occurrences strictly after the first. This is admissible prior-only metadata reuse evidence for later cohort members, but is not an outcome signal.

## Interpretation firewall

The following conclusions are NOT authorized from this audit:

- no rug/winner label;
- no graduation claim;
- no future return claim;
- no trading-edge claim;
- no creator-quality claim;
- no causal claim from same-transaction seed buying;
- no final Organicity Ratio;
- no hidden economic concentration until transfer closure and point-in-time entity reconstruction are complete.

## Next authorized step

Reconstruct the full on-chain state observable through T+1/T+3/T+5 for the exact frozen cohort, using archival blocks only:

1. reconcile all 25 frozen CREATE signatures in the new scan;
2. decode Pump BUY/SELL activity for each target mint through T+300s;
3. reconstruct target-mint token-account pre/post balances from transaction metadata;
4. capture direct SPL-token balance changes even when no Pump trade occurs;
5. derive raw holder concentration excluding the bonding-curve owner from external-holder metrics;
6. freeze T+1/T+3/T+5 source snapshots;
7. keep economic clustering and final Organicity Ratio unavailable until a separate PIT funding/entity pass;
8. keep all outcomes locked.

## Verdict

`SOURCE_SELECTION_INTEGRITY_PASS`

This is a data-integrity success only. It is not `SURVIVES_MVE`, not a trading signal, and not evidence of a diamond.
