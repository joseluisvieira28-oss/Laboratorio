# MEXC PRE-OPEN SHOCK CATCH-UP BASKET V1.1 — CLOSEOUT

Run: 37265102523
Date: 2026-10-05

Frozen rule:
- 35 source-pass assets
- external 60m pre-open shock >= 75 bps
- same-sign MEXC lag gap >= 25 bps
- FOLLOW_EXTERNAL_CONSENSUS
- entry 13:29 UTC
- exit 13:34 UTC
- 5-minute horizon
- daily equal-weight basket as scientific unit

Result:
- total triggered trades: 2
- triggered days: 2
- mean daily gross: -23.3865 bps
- median daily gross: -23.3865 bps
- winning days: 1/2
- exact one-sided binomial p=0.75
- mean after 16 bps API cost: -39.3865 bps
- scientific PASS=false
- robust API-fee survivor=false

Triggered observations:
- 2026-09-18 VRTSTOCK_USDT: +23.8818 bps gross
- 2026-09-23 SMCISTOCK_USDT: -70.6547 bps gross

Verdict:
`PREOPEN_SHOCK_UNDERPOWERED_AT_FROZEN_V11_GATE`

No threshold reduction, horizon change, asset-specific rescue, retrospective tuning, account reads, private endpoints, orders, wallets, exchange mutation or live trading.
