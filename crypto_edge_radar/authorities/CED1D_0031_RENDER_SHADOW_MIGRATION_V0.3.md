# CED1D-0031 — RENDER SHADOW MIGRATION V0.3

Status: FROZEN PROSPECTIVELY BEFORE OUTCOME COLLECTION
Date: 2026-09-22

## Parent authority

Candidate: CED1D-0031 / AVAXUSDT / A_MOMENTUM / lookback 20 valid daily observations / CONTINUATION / H1.

Preserved scientific authority:
- frozen CED-1D V0.3 hypothesis runner SHA256: `df625d0d4a05c55ba34ca51514d31fd61636ff0a823567585c2d02afa0877958`
- Tier-2 activation authority V0.2
- research notional 100 USDT
- reference costs 14 / 20 bps
- execution fee proxy 8 / 10 bps round trip
- aggTrades window 5000 ms
- bookDepth +/-1%, max age 60000 ms
- all existing Tier-1 evidence gates unchanged

## Runtime blocker resolution

GitHub-hosted execution was source-blocked on the official Binance USD-M funding endpoint.

Render Frankfurt source probe V0.2 established:
- official host: https://fapi.binance.com
- endpoint: /fapi/v1/fundingRate
- HTTP 200
- required fields symbol, fundingTime, fundingRate, markPrice
- exact schema PASS
- no authenticated API
- no exchange mutation.

Therefore the blocker is runtime-specific.

## Migration boundary

Migration freeze time:
`2026-09-22T07:25:00Z`

New first eligible signal day:
`2026-09-22`

New first eligible signal completion:
`2026-09-23T00:00:00Z`

New first eligible reference entry:
`2026-09-23T00:01:00Z`

No signal day before 2026-09-22 may be admitted by the migrated collector.
Observations missed during the GitHub blocker are not recovered.

Pre-boundary 2026 data may be accessed only as the minimum frozen 20-prior-valid-day signal warmup/path input. It may not create pre-boundary events or performance rows.

## Source migration

Funding transport is changed prospectively only from the blocked GitHub route to the exact official endpoint proven on Render:
`https://fapi.binance.com/fapi/v1/fundingRate`

The response must contain finite:
- symbol
- fundingTime
- fundingRate
- markPrice > 0

markPrice presence is validated for exact source-schema equivalence. Existing scientific funding calculations remain unchanged.

All Binance Vision archive checksum/CRC rules remain unchanged.

## Source readiness

The existing V0.2 readiness guard is preserved:
`through_signal_day <= current_UTC_date - 3 days`

No relaxation is allowed.

## Firewalls

- no retrospective 2026 performance backfill
- no parameter changes
- no source substitution beyond the frozen official endpoint
- no authenticated trading endpoints
- no orders
- no wallets
- no leverage
- no exchange mutation
- no alerts/webhooks
- no production capital
- no automatic Tier-1 promotion
- no main merge

A collector result may only accumulate research-only public-data shadow evidence.
