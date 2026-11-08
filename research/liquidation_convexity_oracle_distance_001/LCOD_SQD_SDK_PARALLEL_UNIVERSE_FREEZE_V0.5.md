# LCOD SQD SDK PARALLEL BORROW-UNIVERSE GATE V0.5

Frozen: 2026-09-25
Stage: SOURCE / BORROWER UNIVERSE
Outcomes: CLOSED

## Why V0.5

The official SQD SDK continuation fixture passed over 10,001 blocks:
- 13 SDK batches;
- 74 Borrow events;
- known historical truth fixture present;
- zero decode errors;
- stream began at the requested from block and ended at the requested to block.

A single full-history stream is scientifically valid but operationally slower.
V0.5 partitions only the transport workload; source semantics are unchanged.

## Snapshot/range procedure

1. Enumerate all current Ethereum Aave V4 MCP borrow-holder pairs.
2. After enumeration, read Ethereum latest block L.
3. Freeze source range:
   min official spoke deployment block 24720899 through L inclusive.
4. Partition that exact integer range into 16 deterministic contiguous chunks
   of near-equal size. No gap, overlap or omitted block is permitted.
5. Each chunk uses:
   - @subsquid/evm-stream@0.1.5;
   - same SQD Ethereum Portal;
   - all 13 official lending Spokes;
   - Borrow topic only;
   - getStream({from: chunk.from, to: chunk.to}).
6. Chunk artifacts retain only SHA256(spoke::user) pair identities, never raw
   wallets.

## Aggregate PASS

SQD_SDK_PARALLEL_BORROW_UNIVERSE_PASS requires:
- prepare/MCP enumeration has zero errors;
- all 16 chunks PASS;
- chunks exactly cover 24720899..L with no gap/overlap;
- every chunk stream reaches its requested final block;
- known BLUECHIP truth fixture transaction is present;
- zero Borrow decode errors;
- event-history pair set covers 100% of current MCP pair hashes.

This is a source-completeness gate only.
It does not classify active debt at one finalized block and does not authorize
a liquidation curve or any future outcome.
