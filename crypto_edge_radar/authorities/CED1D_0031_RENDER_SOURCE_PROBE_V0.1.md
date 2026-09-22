# CED1D-0031 — RENDER SOURCE PROBE V0.1

Status: FROZEN TECHNICAL SOURCE-ONLY PROBE / NO SCIENTIFIC CHANGE

## Purpose

The GitHub-hosted collector is source-blocked on the official Binance USD-M funding endpoint.
This amendment tests whether the already-canonical Render Frankfurt runtime can reach the exact same official endpoint and frozen schema.

## Frozen request

Symbol: AVAXUSDT
Path: /fapi/v1/fundingRate
startTime: 1789948800000
endTime: 1790035199000
limit: 1000

Hosts:
- https://fapi.binance.com
- https://fapi1.binance.com
- https://fapi2.binance.com
- https://fapi3.binance.com
- https://fapi4.binance.com

## PASS rule

A host passes only when:
- HTTP 200;
- body is a JSON list;
- list is non-empty;
- every row contains symbol, fundingTime and fundingRate;
- symbol == AVAXUSDT;
- fundingTime remains inside the frozen probe window;
- fundingRate parses as finite numeric.

HTTP 202/451/403 or any nonconforming body is NOT a pass.

## Exposure

A read-only diagnostic HTTP endpoint may expose only:
- host;
- HTTP status;
- schema-pass boolean;
- row count;
- body SHA256;
- error class.

It must never expose arbitrary response bodies, credentials or environment variables.

## Adoption firewall

A PASS proves transport/schema feasibility from Render only.
It does NOT:
- activate the CED1D collector on Render;
- open forward outcomes;
- backfill missed observations;
- change the forward boundary;
- change funding semantics;
- establish edge;
- authorize live trading.

Any collector migration requires a separate prospective amendment after this probe closes.

authenticated_exchange_api=false
orders=false
wallets=false
exchange_mutation=false
live_capital=false
main_merge=false
