# MEXC INTRADAY LARGE-SHOCK CATCH-UP BASKET V1.2 — CLOSEOUT

Run: 37281575521
Date: 2026-10-05

Frozen rule:
- 35 source-complete global-asset contracts
- regular-session signals 14:35–18:39 UTC
- external 5m shock >= 30 bps
- same-sign MEXC lag gap >= 20 bps
- FOLLOW_EXTERNAL_CONSENSUS
- 5-minute horizon
- 5-minute cooldown per asset
- equal-weight daily basket as scientific unit

Result:
- total triggered trades: 361
- triggered days: 17
- winning days: 15/17
- win-day rate: 88.2353%
- mean daily gross: +9.6359 bps
- median daily gross: +10.5599 bps
- chronological half means: +8.5131 / +10.6338 bps
- exact one-sided binomial p=0.00117493
- scientific PASS=true

Execution economics:
- mean daily net after 16 bps API cost: -6.3641 bps
- median daily net after 16 bps API cost: -5.4401 bps
- robust API-fee survivor=false

Verdict:
`INTRADAY_SHOCK_SCIENTIFIC_PASS__API_FEE_BLOCKED`

Interpretation:
The event-conditioned intraday catch-up effect is materially larger and more consistent than the earlier 1-minute transfer family, but still does not clear the currently frozen standard MEXC Futures API round-trip cost floor.

No threshold reduction, horizon change, asset-specific rescue, retrospective tuning, private endpoints, account reads, orders, wallets, exchange mutation or live trading.
