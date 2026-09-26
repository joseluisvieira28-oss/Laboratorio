# MRCR V0.1 — Coinbase L2 Alternate-Host Source Probe
Status: AUTHORIZED / SOURCE-ONLY / LOCAL-OR-ALTERNATE-HOST
Date: 2026-09-24

## Trigger

The GitHub-hosted non-target probe established Coinbase market_trades schema but the connection closed abnormally before any level2 message. The same GitHub-runner hunt is closed by the anti-zombie rule.

## Independent documentation basis

Coinbase Advanced Trade documentation states that:

- the market-data WebSocket endpoint is public;
- level2 does not require authentication;
- level2 is designed to keep an order-book snapshot in sync and guarantees delivery of updates;
- level2 messages contain snapshot/update events and updates with price_level, new_quantity, event_time and side;
- new_quantity is an absolute size and zero removes the level;
- heartbeats are public and can keep subscriptions open;
- sequence gaps/out-of-order messages require explicit handling.

## Authorized alternate-host probe

A local Windows/macOS/Linux machine or separately authorized alternate host may run the supplied source-only probe.

The probe may record only:

- connection PASS/FAIL;
- subscription acknowledgement observed;
- level2 snapshot observed;
- level2 update observed;
- required-field schema PASS/FAIL;
- sequence continuity diagnostic;
- heartbeat count if enabled;
- sanitized close code/error class;
- duration and probe version.

## Forbidden

- persistence of raw payloads;
- logging price, size, quantity or notional;
- macro-event targeting;
- feature computation;
- target labels;
- PnL;
- authentication unless separately authorized;
- account endpoints;
- orders;
- exchange mutation.

## Success condition

A source PASS requires at minimum:

- public connection established;
- level2 subscription acknowledged;
- level2 snapshot observed;
- required level2 fields observed with parseable schema.

An incremental update is useful but not required for the minimum source-schema PASS if the snapshot itself establishes the documented schema.

Final boundary: **ALTERNATE-HOST CONNECTIVITY TEST ONLY.**
