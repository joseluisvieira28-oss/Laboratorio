# LCOD SQD SDK PARALLEL UNIVERSE V0.5A — CHUNK-15 TRANSPORT AMENDMENT

Frozen: 2026-09-25
Science change: NONE
Outcome access: CLOSED

## Trigger

V0.5 partitioned the complete Borrow-history range into 16 deterministic
contiguous transport chunks.

Chunks 0 through 14 completed PASS.
Chunk 15 (25969769..26053012) remained materially slower because it is the
most recent source range.

No market, liquidation or curve outcome has been opened. The only observed
information motivating this amendment is transport runtime.

## Technical amendment

Preserve chunks 0..14 byte-for-byte from V0.5.

Replace only transport chunk 15 with four exact contiguous subchunks:

- 15a: 25969769..25990579
- 15b: 25990580..26011390
- 15c: 26011391..26032201
- 15d: 26032202..26053012

Each subchunk uses the identical:
- SQD Portal;
- @subsquid/evm-stream@0.1.5;
- 13 official Aave V4 lending Spokes;
- Borrow topic;
- parser and pair-hash rule.

## Aggregate invariants

V0.5A PASS requires:
- V0.5 prepare artifact PASS;
- chunks 0..14 PASS;
- all four 15a..15d subchunks PASS;
- the 19 transport pieces form exact contiguous coverage from 24720899 to
  the V0.5 frozen latest block 26053012 with no gap or overlap;
- known historical Borrow fixture present in chunk 7;
- zero decode errors;
- 100% of V0.5 current-MCP pair hashes covered by the union event history.

Original chunk 15, if it later completes, is diagnostic redundancy only and is
not mixed into the V0.5A aggregate.

No borrower rule, protocol address, topic, source window or scientific gate is
changed.
