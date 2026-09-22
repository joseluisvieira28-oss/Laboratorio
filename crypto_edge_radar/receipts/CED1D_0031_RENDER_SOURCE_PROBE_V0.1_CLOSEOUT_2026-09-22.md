# CED1D-0031 — RENDER SOURCE PROBE V0.1 CLOSEOUT — 2026-09-22

Status: **RENDER_TRANSPORT_PASS / FULL FROZEN SCHEMA EQUIVALENCE NOT YET ESTABLISHED**

## Real execution

GitHub invoker run: 35698053668  
Execution surface being tested: canonical Render Frankfurt runtime  
Render service: crypto-edge-radar-v05-canary

Frozen V0.1 request:
- symbol: AVAXUSDT
- endpoint: /fapi/v1/fundingRate
- startTime: 1789948800000
- endTime: 1790035199000
- limit: 1000

Observed:
- https://fapi.binance.com — HTTP 200 — 3 rows — V0.1 subset schema PASS
- https://fapi1.binance.com — HTTP 202 — no JSON schema pass
- https://fapi2.binance.com — HTTP 202 — no JSON schema pass
- https://fapi3.binance.com — HTTP 202 — no JSON schema pass
- https://fapi4.binance.com — HTTP 202 — no JSON schema pass

Primary response SHA256:
f8b2be6eb8a35aaeb262abec74f735314f56f7a3662ec86d73a013f6eb5b02c5

## Important authority reconciliation

An earlier frozen CED funding mirror authority requires the exact fundingRate response fields:
- symbol
- fundingTime
- fundingRate
- markPrice

The V0.1 Render diagnostic validator checked only:
- symbol
- fundingTime
- fundingRate

Therefore V0.1 proves **network transport + partial schema accessibility from Render**, but MUST NOT be used to claim exact frozen source-schema equivalence or collector adoption.

Classification:
`RENDER_TRANSPORT_PASS__MARKPRICE_REVALIDATION_REQUIRED`

## Next authorized technical gate

Freeze and execute V0.2 using the same official endpoint and request window, adding mandatory finite positive `markPrice` validation before any collector migration is considered.

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
