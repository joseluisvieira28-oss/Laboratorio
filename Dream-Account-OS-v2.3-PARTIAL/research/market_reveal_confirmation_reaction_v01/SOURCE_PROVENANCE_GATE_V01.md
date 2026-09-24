# MRCR V0.1 — Public Source + Semantic Provenance Gate
Status: PASS_FOR_SYNTHETIC_ADAPTER_IMPLEMENTATION / TARGET_CAPTURE_NOT_AUTHORIZED
As of: 2026-09-24

## Scope

This gate selects public/read-only source semantics for implementation and synthetic verification only. It does not authorize prospective target capture, historical outcome inspection, a directional H02, or trading.

## Binance Spot

Canonical public components:

1. Aggregate Trade stream: `<symbol>@aggTrade`
   - real-time
   - fields include event time `E`, aggregate trade ID `a`, price `p`, quantity `q`, trade time `T`, and `m` = buyer is market maker.
   - canonical aggressor mapping:
     - `m = true` => buyer is maker => taker/aggressor is SELL
     - `m = false` => buyer is taker => aggressor is BUY

2. Diff depth stream: `<symbol>@depth@100ms`
   - fields include event time `E`, first update ID `U`, final update ID `u`, bid updates `b`, ask updates `a`.
   - local order book must be synchronized from a REST depth snapshot and sequence gaps must fail closed/reinitialize.
   - quantities are absolute replacement quantities at each level; zero removes the level.

3. Individual bookTicker is not the canonical MRCR clock source.
   - it provides BBO price/quantity and update ID but the documented payload does not provide exchange event time.
   - it may be retained only as a diagnostic cross-check, never as the sole timestamp authority for MRCR state vectors.

Timestamp policy:
- trade-time semantics use `T`;
- market-data emission diagnostics may retain `E`;
- collector wall clock and monotonic clock must also be recorded;
- no future observation may fill an earlier decision timestamp.

## Coinbase Advanced Trade Spot

Canonical public components:

1. `market_trades` channel
   - public market data;
   - update batches can contain one or more trades;
   - each trade exposes `trade_id`, `product_id`, `price`, `size`, maker-side `side`, and trade `time`.
   - Coinbase documents `side` as the maker side.
   - canonical aggressor mapping:
     - maker side BUY => taker/aggressor SELL
     - maker side SELL => taker/aggressor BUY

2. `level2` channel
   - public;
   - Coinbase documents it as guaranteeing delivery of all updates and suitable for maintaining an in-sync order book;
   - update objects contain `side`, `event_time`, `price_level`, and `new_quantity`;
   - `event_time` is recorded by the trading engine;
   - `new_quantity` is an absolute size, not a delta; zero removes the level.

3. Feed sequence handling
   - feed messages expose `sequence_num`;
   - gaps or out-of-order sequences must be detected;
   - MRCR must fail closed or resynchronize rather than silently continue with an uncertain state.

## Cross-venue normalization boundary

- Binance scope: BTCUSDT / ETHUSDT spot.
- Coinbase scope: BTC-USD / ETH-USD spot.
- No synthetic USD/USDT conversion is authorized.
- Price levels are not merged across venues.
- MRCR state vectors are computed within venue/symbol first.
- Cross-venue comparison, if ever authorized, must use separately frozen normalized descriptors rather than pretending USD and USDT prices are identical.

## Canonical semantic fields

Trade:
- venue
- native_symbol
- trade_id
- trade_time
- source_event_time where available
- price
- base_quantity
- quote_notional
- aggressor_side
- collector_wall_time
- collector_monotonic_time
- raw_hash

Book update:
- venue
- native_symbol
- source_event_time
- sequence/update identifiers
- side
- price_level
- absolute_quantity
- collector_wall_time
- collector_monotonic_time
- raw_hash

## Fail-closed rules

A record is invalid for state-vector construction when:
- required numeric fields are non-finite or non-positive where positivity is required;
- aggressor semantics are ambiguous;
- symbol does not match the frozen native symbol;
- depth sequence integrity is broken and not resynchronized;
- book is crossed/invalid;
- event time is later than the frozen decision boundary;
- raw provenance hash is absent in a target-authorized future collector.

## Current decision

BINANCE_SPOT_SOURCE_SEMANTICS = PASS_FOR_SYNTHETIC_IMPLEMENTATION
COINBASE_SPOT_SOURCE_SEMANTICS = PASS_FOR_SYNTHETIC_IMPLEMENTATION
TARGET_CAPTURE = NOT_AUTHORIZED
H02 = NOT_AUTHORIZED

Next allowed step: implement deterministic parsers and synthetic fixtures for these exact semantics.
