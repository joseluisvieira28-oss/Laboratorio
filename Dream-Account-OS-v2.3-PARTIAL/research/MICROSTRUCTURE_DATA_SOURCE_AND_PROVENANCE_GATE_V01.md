# Microstructure Data Source & Provenance Gate V0.1

Status: **FROZEN PRE-DATA GATE / NO H02 / NO TARGET OUTCOMES**
Branch: `dream-account-phase-b-signal-research-v0.1`
Date: 2026-09-12

## Purpose

Freeze the source, timestamp, reconstruction, integrity and retention rules required before any Macro Shock microstructure outcome study or H02 can exist.

This gate is about whether the data can be trusted. It does **not** define a trading signal, direction, entry, exit, threshold, event subgroup, or profitability test.

## Scientific boundary

Authorized now:
- read-only public market-data feasibility;
- source/provenance documentation;
- deterministic normalization rules;
- offline/synthetic order-book reconstruction tests;
- gap, duplicate, sequence and reconnect detection;
- immutable segment hashing;
- storage/retention design;
- cross-venue clock-alignment design.

Not authorized now:
- target-outcome inspection for a new hypothesis;
- H02 freeze;
- parameter selection from observed outcomes;
- live trading;
- exchange mutation;
- authenticated trading endpoints;
- MEXC Sep-Dec 2025;
- merge to main;
- Render deployment.

`H02_STATUS = NOT_AUTHORIZED`

## Route A — preferred scientific default: prospective read-only collection

### Primary venue
- Venue: Binance
- Market: Spot
- Initial symbols: `BTCUSDT`, `ETHUSDT`
- Raw families required: L2 depth snapshot + incremental depth updates, best bid/offer where available, public trades/aggTrades, exchange event/update identifiers and timestamps exposed by the feed.

### Secondary venue
- Venue: Coinbase Exchange
- Market: Spot
- Initial symbols: BTC-USD and ETH-USD equivalents
- Raw families required: Level2 snapshot + incremental updates, best bid/offer where available, public trades, exchange timestamps/sequence metadata exposed by the feed.

### Why prospective collection is preferred
It creates data that are untouched before future macro events, minimizes retrospective provider-selection bias, and permits direct audit of disconnects/reconnects and collector timing.

## Route B — historical archive, only after a separate provider audit

Candidate classes: archival L2 vendors such as Tardis or Kaiko.

No vendor dataset may be used for outcome research until a provider-specific audit freezes:
- exact venue/market/symbol coverage;
- raw feed lineage;
- snapshot policy;
- incremental update semantics;
- exchange timestamp vs collection timestamp fields;
- sequence/update-ID availability;
- documented reconnect/backfill behavior;
- known gaps/outages;
- licensing/retention constraints;
- reproducible acquisition method;
- immutable local hashing.

Provider choice may not be based on which dataset later gives a more favorable trading result.

## Normalized record contract

Every normalized record MUST contain:
- `venue`
- `market_type`
- `symbol`
- `stream_type`
- `exchange_ts_ns` or explicit `null` when the source does not expose one
- `collector_ts_ns`
- `sequence_start` or explicit `null`
- `sequence_end` or explicit `null`
- `payload`
- `source_message_hash_sha256`
- `segment_id`

Rules:
- timestamps are UTC Unix nanoseconds after normalization;
- raw source timestamps must be preserved losslessly alongside normalized values in immutable raw capture;
- collector time uses one monotonic wall-clock capture process per host and must never replace exchange time when exchange time exists;
- unknown values are explicit nulls, never invented;
- venue-specific symbol mapping is frozen in metadata and never silently rewritten.

## Order-book reconstruction contract

For any venue using snapshot + deltas:
1. obtain/identify a valid snapshot;
2. initialize bid/ask maps by price;
3. apply only updates that are valid under that venue's documented sequence/update-ID rules;
4. quantity `0` deletes a price level;
5. nonzero quantity replaces the absolute quantity at that price unless the venue explicitly documents a different semantic;
6. reject crossed books after update (`best_bid >= best_ask`) unless the raw venue documentation explicitly permits a transient state and a separate rule is frozen before data use;
7. on detected gap, ambiguous sequence, reconnect without continuity proof, or missing required snapshot, mark the book `INVALID_UNTIL_RESYNC`;
8. no spread/depth/refill metric may be produced from an invalid book interval.

## Gap / duplicate / reconnect policy

A segment is INVALID for L2-derived outcomes if any of the following occurs and continuity cannot be proven:
- missing sequence/update-ID interval;
- out-of-order update that cannot be deterministically reordered from buffered raw messages;
- duplicate update with conflicting payload;
- reconnect without a valid resynchronization snapshot/sequence bridge;
- snapshot older than the first accepted update under venue rules;
- non-monotonic exchange sequence where monotonicity is contractually required;
- impossible numeric state (negative quantity, non-positive price, non-finite value).

Exact duplicates with identical canonical payload hashes may be de-duplicated but must remain countable in an audit receipt.

## Immutable storage and hashing

Raw data are append-only.

For each closed capture segment store:
- start/end collector timestamps;
- first/last exchange timestamps when available;
- message count;
- duplicate count;
- rejected count;
- reconnect count;
- gap count;
- SHA-256 of each raw message canonical byte representation;
- SHA-256 Merkle-style or deterministic concatenation digest for the full ordered segment;
- collector software commit SHA;
- venue/symbol/stream metadata.

Any transformed dataset must include the parent raw-segment digest(s).

## Clock-alignment policy

Cross-venue analysis is forbidden until:
- each venue's timestamp semantics are documented;
- collector clock offset/health is recorded;
- exchange timestamps are preferred over collector timestamps when comparable;
- maximum tolerated clock uncertainty is prospectively frozen before analysis;
- no lag interval is chosen after observing cross-venue outcomes.

## Measurement families permitted after this gate passes

Only after provenance PASS, the lab may freeze a separate mechanism-level contract for one or more of:
- quoted spread shock/recovery;
- fixed-bps depth depletion/refill;
- realized-volatility expansion/decay;
- trade/flow intensity;
- cross-venue price-discovery timing;
- simulated execution-state proxies from contemporaneous books.

These are measurement families, not trading rules.

## PASS criteria

The gate is `PASS` only if all are true for the chosen route:
1. exact venue/market/symbols documented;
2. exact raw fields documented;
3. timestamp semantics documented;
4. snapshot + delta semantics documented for L2;
5. deterministic reconstruction implemented offline;
6. gap/duplicate/reconnect logic implemented and tested;
7. immutable hashing/lineage implemented and tested;
8. invalid intervals fail closed and cannot emit L2 metrics;
9. symbol mapping policy frozen;
10. acquisition can be reproduced without trading permissions;
11. safety tests confirm no exchange mutation/live-order path;
12. no target outcome has been used to tune any rule in this gate.

## FAIL / STOP rules

If any PASS criterion fails:
- classification: `PROVENANCE_GATE_FAIL`
- do not open H02;
- do not inspect target outcomes to compensate;
- only infrastructure/provenance defects may be corrected;
- corrections must not alter scientific rules in response to observed outcomes.

## Current decision

Preferred route: **A — prospective read-only Binance Spot + Coinbase Spot collection**.

Historical vendor route remains optional and separately gated.

Final stop condition:
`STOP_AFTER_PROVENANCE_IMPLEMENTATION_AND_SYNTHETIC_VALIDATION_BEFORE_TARGET_OUTCOME_RESEARCH_OR_H02_FREEZE`
