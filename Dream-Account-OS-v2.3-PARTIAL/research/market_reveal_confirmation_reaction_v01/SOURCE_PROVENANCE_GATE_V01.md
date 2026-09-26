# MRCR V0.1 — Public Source + Semantic Provenance Gate
Status: PASS_FOR_SYNTHETIC_ADAPTER_IMPLEMENTATION / TARGET_CAPTURE_NOT_AUTHORIZED
As of: 2026-09-24

## Scope

This gate selects public/read-only source semantics for implementation and synthetic verification only. It does not authorize prospective target capture, historical outcome inspection, a directional H02, or trading.

## Binance Spot

Canonical public components:

1. Aggregate Trade stream: `<symbol>@aggTrade`
   - real-time;
   - fields include event time `E`, aggregate trade ID `a`, price `p`, quantity `q`, trade time `T`, and `m` = buyer is market maker;
   - canonical aggressor mapping:
     - `m = true` => buyer is maker => taker/aggressor is SELL;
     - `m = false` => buyer is taker => aggressor is BUY.

2. Diff depth stream: `<symbol>@depth@100ms`
   - fields include event time `E`, first update ID `U`, final update ID `u`, bid updates `b`, ask updates `a`;
   - local order book must be synchronized from a REST depth snapshot;
   - a buffered depth event with `u <= lastUpdateId` is stale and discarded;
   - the first useful event must bridge the snapshot boundary so that `U <= lastUpdateId + 1 <= u`;
   - if `U > local_update_id + 1`, the book has a gap and must fail closed/reinitialize;
   - quantities are absolute replacement quantities at each level; zero removes the level.

3. Individual bookTicker is not the canonical MRCR clock source.
   - it provides BBO price/quantity and update ID but the documented payload does not provide exchange event time;
   - it may be retained only as a diagnostic cross-check, never as the sole timestamp authority for MRCR state vectors.

Timestamp policy:
- trade-time semantics use `T`;
- Binance event-time diagnostics may retain `E`;
- millisecond epoch timestamps are converted to integer nanoseconds without floating point;
- no future observation may fill an earlier decision timestamp.

## Coinbase Advanced Trade Spot

Canonical public components:

1. `market_trades` channel
   - public market data;
   - update batches can contain one or more trades;
   - each trade exposes `trade_id`, `product_id`, `price`, `size`, maker-side `side`, and trade `time`;
   - Coinbase documents `side` as the maker side;
   - canonical aggressor mapping:
     - maker side BUY => taker/aggressor SELL;
     - maker side SELL => taker/aggressor BUY.

2. `level2` channel
   - public;
   - Coinbase documents it as guaranteeing delivery of all updates and suitable for maintaining an in-sync order book;
   - update objects contain `side`, `event_time`, `price_level`, and `new_quantity`;
   - `event_time` is recorded by the trading engine;
   - `new_quantity` is an absolute size, not a delta; zero removes the level.

3. Snapshot timestamp semantics
   - Coinbase's documented level2 snapshot example has a real message-envelope `timestamp` while per-level snapshot `event_time` values are epoch zero;
   - MRCR therefore uses the message-envelope timestamp as the acquisition/source time for snapshot rows;
   - incremental rows retain their per-level matching-engine `event_time`.

4. Multi-update batch timing
   - one Coinbase level2 message can contain multiple price-level updates with distinct engine timestamps;
   - the post-batch book state is timestamped at the **latest** engine timestamp represented in the batch;
   - this prevents the fully updated book from being treated as available before its last constituent update.

5. Feed sequence handling
   - Coinbase documents sequence numbers as increasing integer values for each product;
   - a gap greater than one indicates a dropped message; lower values can be duplicate/out-of-order;
   - the MRCR book instance is venue-native and single-symbol, so sequence handling is evaluated within that native product;
   - gaps or out-of-order uncertainty must fail closed/resynchronize rather than silently continue.

## Exact timestamp precision

Coinbase feed examples contain fractional timestamps with up to nanosecond precision. MRCR RFC3339 parsing therefore:

- accepts 1–9 fractional digits;
- converts to integer nanoseconds without `datetime.timestamp()` floating-point arithmetic;
- preserves the ninth fractional digit;
- rejects unsupported precision beyond nanoseconds;
- applies timezone offsets before the final integer epoch-nanosecond value.

A row one nanosecond after a decision boundary is future data.

## Prospective availability boundary

Exchange/source timestamp alone is not sufficient to prove that data was available to the research process by a decision boundary.

For any future target-authorized collector, the protocol must freeze:

`availability_rule = SOURCE_AND_COLLECTOR_ARRIVAL`

A feature observation is eligible only when both:

- source/exchange timestamp <= decision timestamp; and
- collector arrival wall-clock timestamp <= decision timestamp.

Collector monotonic time must also be retained for local ordering/diagnostics, but it is not substituted for UTC wall time.

Current synthetic/offline fixtures may omit arrival provenance only because target observation is not authorized.

## Cross-venue normalization boundary

- Binance scope: BTCUSDT / ETHUSDT spot.
- Coinbase scope: BTC-USD / ETH-USD spot.
- No synthetic USD/USDT conversion is authorized.
- Price levels are not merged across venues.
- MRCR state vectors are computed within venue/symbol first.
- Cross-venue comparison, if ever authorized, must use separately frozen normalized descriptors rather than pretending USD and USDT prices are identical.

## Canonical semantic fields

Trade:
- venue;
- native_symbol;
- trade_id;
- trade_time;
- source_event_time where available;
- price;
- base_quantity;
- quote_notional;
- aggressor_side;
- collector_wall_time;
- collector_monotonic_time;
- raw_hash.

Book update:
- venue;
- native_symbol;
- source_event_time;
- sequence/update identifiers;
- side;
- price_level;
- absolute_quantity;
- collector_wall_time;
- collector_monotonic_time;
- raw_hash.

## Fail-closed rules

A record is invalid for state-vector construction when:
- required numeric fields are non-finite or non-positive where positivity is required;
- aggressor semantics are ambiguous;
- symbol does not match the frozen native symbol;
- depth sequence integrity is broken and not resynchronized;
- book is crossed/invalid;
- source time is later than the frozen decision boundary;
- in future target-authorized capture, collector arrival is absent or later than the decision boundary;
- raw provenance hash is absent in a target-authorized future collector.

## Current decision

BINANCE_SPOT_SOURCE_SEMANTICS = PASS_FOR_SYNTHETIC_IMPLEMENTATION
COINBASE_SPOT_SOURCE_SEMANTICS = PASS_FOR_SYNTHETIC_IMPLEMENTATION
TARGET_CAPTURE = NOT_AUTHORIZED
H02 = NOT_AUTHORIZED

Current implementation boundary: exact source semantics, exact chronology and synthetic verification may advance; target outcomes remain sealed.
