# MEXC EVENT FUTURES LAB — PUBLIC INDEX SOURCE GATE V0.12.1

Date: 2026-10-03
Status: SOURCE-ONLY / READ-ONLY / PRE-V0.13

## Why this gate exists

V0.11.6 proved exact current Event Futures payout fields.
V0.12 validated a forward-only exact-product collector.

Before any Event-Conditioned Edge evaluation, the lab needs a defensible public price source for prospective direction labels.

MEXC's Event Futures guide states that Up/Down is determined by the underlying index price and settlement is based on the price index at expiry.

The live Event Futures web bundle independently shows that the Event Futures page itself sends:

- `sub.event.contract`
- `sub.index.price` with the current Event Futures symbol

and listens to:

- `push.index.price`

The same bundle maps `push.index.price` through `formatIndexPriceData` into the Event Futures store field `eventContractIndexPrice`.

MEXC's public Futures websocket documentation documents `sub.index.price` / `push.index.price` as a public read-only index-price stream.

## Mission

Prove that a fresh unauthenticated client can obtain timestamped public index-price updates for the currently ONLINE Event Futures crypto symbols without any private/account access.

Frozen symbols for this gate:

- BTC_USDT
- ETH_USDT

Frozen websocket endpoint:

`wss://futures.mexc.com/edge`

Frozen subscription messages:

`{"method":"sub.index.price","param":{"symbol":"BTC_USDT"}}`

`{"method":"sub.index.price","param":{"symbol":"ETH_USDT"}}`

A passive/read-only `sub.event.contract` subscription may also be sent because the normal public Event Futures page sends it automatically. It is source reconnaissance only and is not required for PASS.

## Hard safety boundary

- no login;
- no API key or secret;
- no Authorization header;
- no private websocket channels;
- no account/position/order channels;
- no HTTP POST;
- no order placement;
- no live trading;
- no exchange/account mutation;
- no wallet action;
- no merge to main;
- no holdout opening.

Websocket subscription/unsubscription messages to public market-data channels are read-only transport operations and are permitted.

## Required evidence

For each frozen symbol:

- channel exactly `push.index.price`;
- symbol;
- numeric positive index price;
- exchange/server timestamp if supplied;
- local receive timestamp;
- raw-message SHA-256.

## Verdicts

`PUBLIC_INDEX_STREAM_PASS`
: both BTC_USDT and ETH_USDT produce at least one valid `push.index.price` record.

`PARTIAL_INDEX_STREAM`
: exactly one frozen symbol produces a valid record.

`INDEX_STREAM_BLOCKED`
: no valid frozen-symbol index record is obtained.

No trading-edge verdict is permitted.

## Scientific limitation preserved

Even if this gate passes, a public index tick observed at research decision time is a **shadow decision index**, not a proven exact order `openPrice`.

Static Event Futures order code sends `symbol, amount, side, payRate, cycleAmount, cycleType`; it does not send `openPrice`, implying the server assigns the real order entry price.

Without placing an order or reading a private position receipt, V0.13 must not label a shadow decision index as the exact executed Event Futures entry price.
