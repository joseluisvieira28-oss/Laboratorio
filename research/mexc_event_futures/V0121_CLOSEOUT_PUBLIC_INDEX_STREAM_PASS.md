# MEXC EVENT FUTURES LAB — PUBLIC INDEX SOURCE V0.12.1 CLOSEOUT

Date: 2026-10-03
Status: SOURCE GATE PASSED
Verdict: `PUBLIC_INDEX_STREAM_PASS`

## Authoritative run

- Workflow: `MEXC Event Futures Public Index Source V0.12.1`
- Run: `37071859766`
- Job: `111052911829`
- Head: `5f15d043f4a60701ac18a7d50e14f772ee5918a9`
- Artifact: `mexc-event-futures-index-source-v0121`
- Artifact id: `11254349695`
- Artifact digest: `sha256:1db66fa8f6b16eba6a4a77ddd889cb8598d8aa8c13091fc9ae0ae2eea01e4c8c`

## Result

A fresh unauthenticated client connected to:

`wss://futures.mexc.com/edge`

using only public read-only subscriptions.

Both frozen Event Futures crypto symbols returned valid `push.index.price` records.

Observed source evidence included:

- BTC_USDT: 84534.0 at server ts 1790979573620
- ETH_USDT: 2661.86 at server ts 1790979573909
- ETH_USDT: 2661.76 at server ts 1790979574762
- BTC_USDT: 84532.8 at server ts 1790979575026

Four exact public index records were captured, each with local receive timestamp and raw-message SHA-256.

The public `sub.event.contract` request also received acknowledgement channel:

`rs.sub.event.contract`

No product-change push was required for this source gate.

## Safety

- NO_AUTH = PASS
- NO_PRIVATE = PASS
- NO_ORDERS = PASS
- NO_MUTATION = PASS

Only public market-data subscribe/unsubscribe messages were transmitted.

## Source binding

This gate closes the public index-source dependency for research:

1. MEXC Event Futures documentation defines settlement using the underlying index price.
2. The live Event Futures web bundle subscribes to `sub.index.price` and consumes `push.index.price` into the Event Futures index-price state.
3. The official public Futures websocket documents the same public channel.
4. V0.12.1 independently obtained live timestamped records from that channel without authentication.

## Limitation that remains

The public index stream is now defensible for shadow research, but it is NOT the same thing as a real order receipt.

The live Event Futures order builder sends:

- symbol
- amount
- side
- payRate
- cycleAmount
- cycleType

It does not send `openPrice`; the actual position `openPrice` is server-assigned and only appears in position records/position-change data.

Therefore:

- a shadow decision index can be recorded exactly;
- a shadow expiry index can be recorded exactly;
- a shadow Up/Down outcome can be resolved;
- but the lab must NOT claim that the shadow decision index equals the exact executed order openPrice.

No order or private-position access is authorized or required for V0.13 research.

## Next legitimate gate

V0.13 may now be preregistered as a forward-only Event-Conditioned Edge study using:

- exact observed payout from V0.12;
- exact public shadow decision index from V0.12.1;
- exact public shadow expiry index captured after the frozen horizon;
- externally defined/frozen event conditions.

Every result must be called a **shadow Event Futures result** unless exact executed openPrice evidence exists.
