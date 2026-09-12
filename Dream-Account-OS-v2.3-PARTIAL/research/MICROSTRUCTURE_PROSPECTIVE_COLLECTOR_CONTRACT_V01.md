# Microstructure Prospective Collector Contract V0.1

Status: **FROZEN PRE-COLLECTION CONTRACT / READ-ONLY / NO H02 / NO TARGET OUTCOMES**
Date: 2026-09-12
Branch: `dream-account-phase-b-signal-research-v0.1`

## Purpose

Freeze the exact prospective read-only market-data acquisition behavior before any real capture begins. This contract implements the preferred Route A from `MICROSTRUCTURE_DATA_SOURCE_AND_PROVENANCE_GATE_V01.md`.

The collector exists only to create auditable untouched microstructure data for future mechanism research. It is not a trading system and it must not inspect or optimize target outcomes.

## Authority boundary

Authorized:
- public, read-only market-data endpoints only;
- Binance Spot market-data WebSocket plus public depth snapshot REST needed to synchronize a local book;
- Coinbase Exchange public market-data WebSocket channels that do not require trading authorization;
- BTC/ETH spot pairs specified below;
- raw append-only capture;
- collector timestamps;
- source timestamps/update identifiers;
- reconnect/resync bookkeeping;
- integrity receipts and hashes;
- synthetic/offline validation of captured segments.

Forbidden:
- API keys, secrets, account/user streams, balances or positions;
- order placement/cancel/amend/test orders;
- POST/PUT/PATCH/DELETE exchange mutations;
- live or paper trade generation;
- entry/stop/TP/position sizing;
- directional signal generation;
- target-outcome analysis;
- H02 creation or freeze;
- adaptive thresholds based on captured market outcomes;
- MEXC Sep-Dec 2025;
- merge to main;
- Render deployment.

`H02_STATUS = NOT_AUTHORIZED`

## Frozen venues and symbols

### Binance Spot
- canonical venue ID: `BINANCE_SPOT`
- symbols: `BTCUSDT`, `ETHUSDT`
- stream symbol forms: `btcusdt`, `ethusdt`

Required raw public feeds:
- diff depth: `<symbol>@depth@100ms`
- best bid/ask: `<symbol>@bookTicker`
- raw trades: `<symbol>@trade`

Required public synchronization snapshot:
- Spot REST depth snapshot `GET /api/v3/depth`
- maximum documented snapshot depth may be used; snapshot response and request metadata must be captured and hashed.

Binance reconstruction semantics are frozen to the official local-order-book procedure:
- buffer diff-depth events before/while obtaining snapshot;
- use snapshot `lastUpdateId`;
- discard buffered events whose final update ID is not newer than the snapshot;
- first accepted buffered event must bridge the snapshot update ID according to documented `[U,u]` semantics;
- after synchronization, if an event indicates an update gap, invalidate the local book and resynchronize;
- quantity zero deletes a level; nonzero quantity replaces the level quantity.

### Coinbase Exchange Spot
- canonical venue ID: `COINBASE_SPOT`
- products: `BTC-USD`, `ETH-USD`

Required raw public feeds:
- `level2`
- `matches`
- `heartbeat`

Coinbase reconstruction semantics:
- initialize from the `level2` snapshot message;
- apply subsequent `level2` changes as absolute size changes at price levels according to source documentation;
- heartbeat/sequence/trade identifiers are captured for audit;
- any continuity ambiguity that prevents deterministic book state invalidates that interval until a new trusted snapshot/resubscription state is established.

The collector must not use the authenticated User channel, Full/User account data, private Direct feeds, or any trading API.

## Raw capture rule

Every source message must be persisted before transformation, except protocol-level ping/pong frames which may be counted rather than stored if the client library does not expose their original bytes.

For each message persist at minimum:
- venue;
- market/product;
- stream/channel;
- exact received payload bytes or exact UTF-8 text bytes;
- collector wall-clock timestamp in UTC Unix ns;
- collector monotonic timestamp in ns;
- connection/session ID;
- message ordinal within session;
- SHA-256 of exact stored source bytes.

Where exposed by the exchange, additionally persist:
- exchange event timestamp;
- trade timestamp;
- sequence/update IDs;
- trade ID;
- snapshot `lastUpdateId`;
- product/symbol exactly as sent.

No normalized record may replace or overwrite the raw record.

## Time policy

- collector host wall clock must be UTC-aware;
- both wall-clock and monotonic receive timestamps are recorded;
- raw exchange timestamps are preserved exactly before normalization;
- normalization to Unix ns is deterministic and venue-specific;
- collector timestamps are never substituted for missing exchange timestamps;
- no cross-venue lead/lag statistic may be computed under this contract.

A future cross-venue study requires a separately frozen maximum clock-uncertainty rule.

## Connection and reconnect policy

Every connection session has a unique `session_id` and lifecycle receipt.

Record:
- connect start/end;
- endpoint host and channel/stream subscription set;
- subscription acknowledgement where applicable;
- reconnect reason;
- clean vs abnormal close;
- ping/pong/heartbeat health counters where observable;
- number of raw messages;
- number of parsing failures;
- gap/resync counters.

On reconnect:
- never assume L2 continuity;
- Binance local books become `INVALID_UNTIL_RESYNC` and require a fresh synchronization procedure;
- Coinbase local books must be rebuilt from a new trusted level2 snapshot/subscription state;
- the gap between sessions is explicitly recorded and cannot emit L2-derived metrics.

## Segment policy

Raw data are closed into deterministic capture segments by venue, symbol/product, stream/channel and session.

Each closed segment receipt stores:
- segment ID;
- venue/product/channel;
- first/last collector timestamps;
- first/last exchange timestamps where available;
- message count;
- parsing/rejection count;
- duplicate count;
- reconnect count;
- gap/resync count;
- ordered segment SHA-256 derived from ordered per-message hashes;
- collector commit SHA;
- parent session ID.

Segments are append-only after close.

## Fail-closed conditions

Capture can continue, but an interval is invalid for future L2 metrics when any of these occurs without deterministic recovery:
- missing Binance update interval;
- invalid snapshot bridge;
- impossible or malformed price/quantity;
- crossed/locked reconstructed book under the frozen default rule;
- unproven continuity across reconnect;
- source parsing ambiguity;
- Coinbase continuity ambiguity or lost synchronization;
- collector clock anomaly that invalidates receive-time ordering.

Invalid intervals remain stored for audit but are tagged unusable for L2-derived mechanism outcomes.

## Security boundary

The collector implementation must contain:
- no exchange credentials;
- no secret loading for exchange access;
- no account endpoints;
- no order endpoints;
- no generic arbitrary-URL execution path;
- an explicit allowlist of public market-data hosts and GET/WSS usage only.

The repository safety guard must be extended narrowly for the collector only. The existing global ban on network primitives must not be weakened for unrelated research modules.

## Initial collection purpose

The first live/public capture, when implementation is authorized by CI, is a **provenance shakedown only**.

It may report:
- connection stability;
- raw message counts;
- sequence/gap/reconnect counts;
- snapshot synchronization success/failure;
- book validity fraction;
- hashing/segment integrity;
- storage volume/throughput;
- timestamp field availability.

It must NOT report:
- future returns;
- profitable direction;
- predictive hit rates;
- entries/exits;
- event-conditioned trading performance;
- any SURVIVES/NO_EDGE classification.

## Collector implementation gate

Before any real network capture, all must pass:
1. parser/unit fixtures for each venue message family;
2. Binance snapshot-bridge and gap-resync synthetic tests;
3. Coinbase snapshot/update synthetic tests;
4. malformed-message fail-closed tests;
5. append-only hashing/lineage tests;
6. security AST/domain/method allowlist tests;
7. existing Phase B inherited suite;
8. compile check;
9. explicit proof that no order/account endpoint or credential is present.

## Stop condition

After implementation and CI validation, stop before target-outcome research.

`STOP_AFTER_READ_ONLY_COLLECTOR_IMPLEMENTATION_GATE_BEFORE_PROVENANCE_SHAKEDOWN_CAPTURE`
