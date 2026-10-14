# FORWARD COLLECTOR MVE SPEC V0.1

Status: DESIGN FROZEN / NOT DEPLOYED
No orders, API trading keys, wallet signing, or private account streams.

## Goal

Capture a small, auditable forward corpus proving that cross-venue timestamps and sequence integrity can be collected without hidden clock assumptions.

## Initial streams

### Binance
- BTCUSDT spot aggTrade
- BTCUSDT spot bookTicker or selected depth stream
- BTCUSDT perpetual aggTrade
- BTCUSDT perpetual mark price
- periodic OI/basis snapshot only if the response carries source time or the local polling semantics are explicitly labelled

### Deribit
- BTC-PERPETUAL trades/ticker
- BTC option markprice.options index stream
- targeted option ticker channels for a frozen set of expiries/strikes
- DVOL stream

## Storage contract

NDJSON, append-only.

Every row contains the canonical schema in event_schema.py plus:
- collector_build
- collector_session_id
- connection_id
- reconnect_counter
- source_gap_flag
- clock_sync_sample_id
- raw payload

Raw data is never overwritten by a derived row.

## Integrity requirements

1. NTP/clock-sync evidence must be logged at collector start and periodically.
2. Reconnects create a new connection_id.
3. Any Binance depth sequence gap or Deribit change_id discontinuity marks the affected interval unusable for book-derived propagation analysis until resync.
4. No event may be reordered in storage for cosmetic reasons.
5. Derived event-time ordering must be computed from explicit timestamps after collection.
6. Cross-venue comparisons must include sensitivity bands for +/- 50ms, 100ms, 250ms, 500ms and 1s jitter before claiming sub-second lead.
7. 1s+ claims remain invalid if wall-clock skew is not bounded and recorded.

## First forward success criterion

A continuous >= 24h capture with:
- zero silent reconnects,
- explicit gap accounting,
- >= 99.9% rows with source timestamp where the source supplies one,
- deterministic raw-payload hashes,
- reproducible replay into the same normalized event sequence.

Passing this criterion means COLLECTOR_VALID, not edge.
