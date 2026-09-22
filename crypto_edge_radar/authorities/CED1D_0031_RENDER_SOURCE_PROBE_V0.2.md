# CED1D-0031 — RENDER SOURCE PROBE V0.2

Status: FROZEN BEFORE EXECUTION / STRICTER SOURCE-SCHEMA REVALIDATION

## Parent evidence

V0.1 established that the canonical Render Frankfurt runtime can reach:
`https://fapi.binance.com/fapi/v1/fundingRate`
for the frozen AVAXUSDT probe window.

V0.1 is transport evidence only because its validator did not enforce `markPrice`.

## Frozen V0.2 request

Identical to V0.1:
- symbol: AVAXUSDT
- path: /fapi/v1/fundingRate
- startTime: 1789948800000
- endTime: 1790035199000
- limit: 1000
- hosts: fapi.binance.com and official fapi1-fapi4 mirrors.

## Strict PASS rule

A host passes only if:
- HTTP 200;
- body is a non-empty JSON list;
- every row contains symbol, fundingTime, fundingRate and markPrice;
- symbol == AVAXUSDT;
- fundingTime is inside the frozen window;
- fundingRate is finite numeric;
- markPrice is finite numeric and > 0.

No fallback reconstruction of markPrice is allowed.
No alternate endpoint or venue is allowed.

## Meaning

`OFFICIAL_ENDPOINT_EXACT_SCHEMA_PASS` proves transport + exact frozen response-field feasibility from Render only.

It does NOT authorize collector migration, forward backfill, outcome opening, changed boundary, signal calculation, trading, orders or capital.

Any collector migration requires a separate prospective authority after V0.2 closeout.

## Firewalls

used_as_forward_evidence=false
collector_adoption_authorized=false
returns_computed=false
pnl_computed=false
authenticated_exchange_api=false
orders=false
exchange_mutation=false
live_capital=false
main_merge=false
