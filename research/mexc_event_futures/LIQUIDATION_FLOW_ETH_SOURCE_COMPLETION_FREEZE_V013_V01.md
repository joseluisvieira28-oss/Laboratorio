# LIQUIDATION-FLOW-FWD-001 — ETH SOURCE COMPLETION FREEZE V0.13.1

Date: 2026-10-03
Status: SOURCE-ONLY / OUTCOME-BLIND
Parent branch state includes the V0.13 freeze and the one-hour PARTIAL_SOURCE closeout.

## Purpose

Complete the original two-symbol Bybit liquidation source gate without changing source, schema, side semantics, freshness rules, direction hypothesis, horizon or any Event Futures outcome rule.

The prior one-hour run already proved three valid BTCUSDT liquidation payloads. This follow-up therefore targets the missing ETHUSDT real payload while preserving BTC transport as a contemporaneous control.

## Prior BTC anchor

Authoritative prior artifact:

- run 37075262340
- artifact 11257963990
- artifact digest `sha256:1521ef40603b46a3e76fc148c1e6df9d830faae7c00030ed720e23c45c3e1a5f`
- valid BTC raw hashes:
  - `4680e77698c7903751dcda04c1a8165ca2134cb4d6cf572a90198d414fefc302`
  - `f09a4ca383e36acf2f0e3316a2133631734f01604b6b27d978eeb1fe66b23c49`
  - `282b7fa22e79458d4b25c665d74c3eb79837d1d5fa99c428bc257436ad960455`

These remain source-gate evidence only. They cannot enter calibration bins.

## Source and transport

Use the unchanged production source:

`wss://stream.bybit.com/v5/public/linear`

Open two independent public websocket connections:

- BTC connection: `allLiquidation.BTCUSDT`
- ETH connection: `allLiquidation.ETHUSDT`

Subscribe separately with explicit request ids so each topic has an independently preserved acknowledgement.

Heartbeat: public ping every 20 seconds per connection.

No alternate venue, no pooling, no login, no API key.

## Validation

Use the exact frozen V0.13 liquidation validator:

- topic exactly matches `allLiquidation.<symbol>`;
- item symbol BTCUSDT or ETHUSDT as appropriate;
- side Buy or Sell;
- integer event timestamp T;
- integer envelope timestamp ts;
- positive finite v and p;
- receive - T in [-1000,5000] ms;
- T no more than 1000 ms after envelope ts;
- preserve raw bytes/message, receive clock and SHA256.

Bankruptcy price remains a proxy input only, not a demonstrated fill price.

## Runtime

Maximum observation window: 10800 seconds.

The run MAY stop early only after all of the following are simultaneously true:

- BTC topic subscription acknowledged successfully;
- ETH topic subscription acknowledged successfully;
- no transport/schema error has invalidated either connection;
- at least one valid real ETHUSDT liquidation payload has been preserved.

A new BTC event is welcome but not required because prior BTC real-payload evidence is explicitly anchored above.

## Verdicts

`SOURCE_GATE_PASS`
: prior BTC anchor + current independent BTC/ETH subscription acks + at least one current valid ETH payload + no invalidating transport/schema error.

`PARTIAL_SOURCE`
: subscriptions healthy but no valid ETH payload before timeout.

`SOURCE_BLOCKED`
: transport, acknowledgement or schema integrity failure.

No edge verdict is allowed.

## Calibration boundary

If and only if this gate reaches `SOURCE_GATE_PASS`, calibration may begin from a NEW timestamp strictly after the PASS receipt is finalized.

No prior BTC events and no ETH source-gate event may be reused as calibration observations.

Calibration procedure remains exactly `LIQUIDATION_FLOW_FORWARD_CALIBRATION_FREEZE_V013_V01.md`.

No Event Futures outcomes may be opened before the later numeric activation freeze.
