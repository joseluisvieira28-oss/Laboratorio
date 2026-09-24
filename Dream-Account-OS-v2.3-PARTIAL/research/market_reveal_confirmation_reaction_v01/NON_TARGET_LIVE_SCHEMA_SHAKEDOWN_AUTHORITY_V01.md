# MRCR V0.1 — Non-Target Live Schema Shakedown Authority
Status: AUTHORIZED / SOURCE-ONLY / ECONOMIC VALUES REDACTED
Date: 2026-09-24

## Purpose

Verify that the currently documented public Binance Spot and Coinbase Advanced Spot feeds expose the fields and sequence/timestamp semantics required by the MRCR source contract.

## Scientific boundary

This is **not** a target observation.

The probe:
- runs immediately at an arbitrary non-event research time;
- does not use or check a macro calendar;
- does not classify acceptance/rejection;
- does not compute return, flow imbalance, retracement, response-per-flow or any scientific measurement;
- does not persist raw market messages;
- does not persist prices, quantities, notional or direction;
- does not compare venues economically;
- does not create labels, thresholds or PnL.

## Allowed outputs

Only:
- connection success/failure;
- message counts by expected stream/channel;
- required-field presence PASS/FAIL;
- parseability PASS/FAIL;
- sequence continuity diagnostics;
- timestamp-field presence;
- sanitized exception class/reason;
- probe duration and code revision.

## Sources

Binance Spot public WebSocket market streams:
- aggregate trade
- diff depth

Coinbase Advanced Spot public WebSocket:
- market_trades
- level2

No authentication is permitted.

## Fail-closed

Any unexpected schema, network block, sequence uncertainty or parser mismatch produces SOURCE_SHAKEDOWN_FAIL/BLOCKED, not a repaired or inferred PASS.

## Forbidden

- saving raw payloads as artifacts;
- printing economic values to logs;
- retries that switch to an economically different venue/product;
- authenticated endpoints;
- orders or account routes;
- interpreting message counts as edge evidence;
- target-event capture;
- main merge;
- Render deployment.

Final boundary: SOURCE TRANSPORT + SCHEMA ONLY.
