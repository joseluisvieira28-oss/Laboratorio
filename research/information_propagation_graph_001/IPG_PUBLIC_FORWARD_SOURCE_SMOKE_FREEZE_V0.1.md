# IPG-001 PUBLIC FORWARD SOURCE SMOKE FREEZE V0.1

Frozen: 2026-09-24
Stage: FORWARD SOURCE BINDING ONLY
No predictive outcome / no trading.

## Public streams

Binance:
- BTCUSDT Spot aggTrade
- BTCUSDT USD-M perpetual aggTrade

Deribit production public WebSocket:
- trades.BTC-PERPETUAL.100ms
- markprice.options.btc_usd
- deribit_volatility_index.btc_usd

The Deribit option-chain channel and DVOL channel are public market-data
sources. Raw interval is deliberately not used for public Deribit trade
subscriptions because Deribit documents raw order/trade-style intervals as
authenticated where applicable.

## Capture contract

Every persisted normalized sample retains:
- source / venue / instrument or surface;
- source event timestamp;
- source publish timestamp when separately supplied;
- local receive wall timestamp;
- local receive monotonic timestamp;
- source sequence when supplied;
- SHA-256 of the exact raw WebSocket message;
- connection id.

Raw payload contents are not persisted in the durable receipt.

## Frozen minimum smoke counts

- Binance spot aggTrade >= 10 normalized events
- Binance USD-M perp aggTrade >= 10
- Deribit BTC-PERPETUAL trades >= 5
- Deribit option mark-price packets >= 2
- Deribit DVOL packets >= 2

## PASS

FORWARD_PUBLIC_SOURCE_SMOKE_PASS only if:
- all five streams meet minimum counts;
- source timestamp completeness = 100% for normalized samples;
- receive monotonic clock never regresses within a stream;
- every absolute receive-wall minus source timestamp diagnostic <= 10 seconds;
- no stream error is unresolved.

The wall/source delta is a sanity diagnostic only and MUST NOT be interpreted
as causal exchange latency.

Passing is not COLLECTOR_VALID: the previously frozen >=24h continuous
collector gate still remains for durable forward collection.
