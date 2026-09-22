# CED1D-0031 — RENDER SOURCE PROBE V0.2 CLOSEOUT — 2026-09-22

Status: **OFFICIAL_ENDPOINT_EXACT_SCHEMA_PASS / COLLECTOR MIGRATION NOT YET AUTHORIZED**

## Real execution

GitHub invoker run: **35698612532**  
Execution surface being tested: canonical Render Frankfurt runtime  
Render service: `crypto-edge-radar-v05-canary`

Frozen request:
- symbol: AVAXUSDT
- endpoint: `/fapi/v1/fundingRate`
- startTime: 1789948800000
- endTime: 1790035199000
- limit: 1000

Strict required fields:
- symbol
- fundingTime
- fundingRate
- markPrice

## Observed result

Primary official host:
- `https://fapi.binance.com`
- HTTP 200
- 3 rows
- exact V0.2 schema PASS
- body SHA256: `f8b2be6eb8a35aaeb262abec74f735314f56f7a3662ec86d73a013f6eb5b02c5`

Official mirrors:
- fapi1.binance.com — HTTP 202 — schema FAIL
- fapi2.binance.com — HTTP 202 — schema FAIL
- fapi3.binance.com — HTTP 202 — schema FAIL
- fapi4.binance.com — HTTP 202 — schema FAIL

Machine classification:
`OFFICIAL_ENDPOINT_EXACT_SCHEMA_PASS`

## Adjudication

The official Binance USD-M funding endpoint is transport- and exact-schema-accessible from the canonical Render Frankfurt runtime.

This resolves the previous GitHub-hosted-runner transport blocker as a **runtime-specific** blocker. It does not retroactively make failed GitHub observations valid and does not authorize backfill.

## Next prospective action

A separate collector-migration authority may bind CED1D-0031 to the canonical Render Frankfurt runtime using:
- the same official Binance endpoint;
- the same frozen funding fields and scientific rule;
- a new prospective forward boundary set before the migrated collector opens outcomes;
- no recovery/backfill of observations missed while GitHub was blocked;
- the existing evidence backend and immutable/idempotent keys.

## Firewalls

used_as_forward_evidence=false  
collector_adoption_authorized=false  
returns_computed=false  
pnl_computed=false  
live_trading=false  
orders=false  
exchange_mutation=false  
live_capital=false  
main_merge=false
