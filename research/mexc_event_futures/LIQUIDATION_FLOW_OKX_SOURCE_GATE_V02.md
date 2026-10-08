# LIQUIDATION-FLOW-FWD-002 — OKX PUBLIC SOURCE GATE V0.2

Date: 2026-10-04
Status: SOURCE-ONLY / PRE-OUTCOME / RESEARCH-ONLY

## Why a new version

`LIQUIDATION-FLOW-FWD-001` remains unchanged.

Its Bybit public source produced:
- initial 10-minute gate: BTC=0, ETH=0;
- frozen 3600-second extension: BTC=3 valid real events, ETH=0;
- verdict: `PARTIAL_SOURCE`, not NO_EDGE.

No Event Futures outcome has ever been opened for the liquidation family.

V0.2 is a new source version using OKX only. It does NOT pool OKX and Bybit.

## Public source

OKX production public WebSocket:

`wss://ws.okx.com:8443/ws/v5/public`

Subscription:

`{"op":"subscribe","args":[{"channel":"liquidation-orders","instType":"SWAP"}]}`

The source gate filters only:
- `BTC-USDT-SWAP`
- `ETH-USDT-SWAP`

OKX public liquidation payload semantics expected:
- outer `instId`, `instType`, `instFamily`;
- `details[].side`: buy/sell liquidation order direction;
- `details[].posSide`: long/short position side;
- `details[].sz`: number of contracts;
- `details[].bkPx`: bankruptcy price;
- `details[].ts`: event timestamp ms.

Public instrument metadata is captured for each target so contract size/value can later be converted defensibly if calibration is activated.

## Gate duration

Exactly 600 seconds after successful subscription acknowledgement.

Heartbeat must remain healthy.

Every received raw JSON message is SHA-256 hashed and preserved.

## PASS requirements

Per target symbol require at least one real liquidation detail with ALL:

- exact target `instId`;
- `side` in {buy,sell};
- `posSide` in {long,short};
- finite positive `sz`;
- finite positive `bkPx`;
- integer `ts`;
- event age at local receipt <= 5 seconds;
- future-clock tolerance <= 1 second;
- raw message SHA-256 preserved.

Both BTC and ETH must pass for:

`OKX_LIQUIDATION_SOURCE_PASS`

If one passes and the other does not:

`PARTIAL_SOURCE`

If neither produces a valid event:

`NO_EVENTS_OBSERVED`

Transport/ack/heartbeat failure:

`SOURCE_BLOCKED`

## Outcome boundary

This gate MUST NOT access:
- MEXC Event Futures payout/product data;
- MEXC index outcomes;
- candles for outcome labels;
- future returns;
- win/loss/PnL.

Research outcomes opened must remain exactly 0.

## Future calibration — not active

A source PASS does NOT activate the family.

A separate pre-calibration freeze must define:
- healthy-minute continuity;
- contract-value conversion;
- nonzero-bin minimum;
- threshold quantile;
- direction mapping;
- future activation boundary.

No login, API keys, account reads, wallets, orders, exchange mutation, main merge or live trading.


## Execution marker — 2026-10-08

Operator authorized a fresh execution of the already-frozen V0.2 source gate. No scientific rule, threshold, duration, symbol set, source, or outcome boundary changes.
