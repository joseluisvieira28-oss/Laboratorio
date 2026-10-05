# MEXC CASH-OPEN EXTERNAL MOMENTUM BASKET V1.2 — CLOSEOUT

Run: 37265438959
Date: 2026-10-05

Frozen rule:
- external 5m momentum 13:24 -> 13:29 UTC
- FOLLOW_EXTERNAL_MOMENTUM
- enter MEXC 13:29
- exit MEXC 13:59
- 30m horizon
- all 35 source-pass assets included
- daily equal-weight basket is scientific unit
- no threshold, no asset selection, no grid

Results:
- basket days: 17
- mean assets/day: 34.706
- minimum assets/day: 34
- mean daily gross: +5.6249 bps
- median daily gross: +6.0209 bps
- winning days: 11/17 = 64.71%
- chronological halves: +1.1815 / +9.5746 bps
- exact one-sided binomial p=0.166153
- mean net after 12 bps: -6.3751 bps
- mean net after 16 bps: -10.3751 bps
- median net after 16 bps: -9.9791 bps

Verdict:
`NO_CASHOPEN_EXTMOM_BASKET_SURVIVOR_AT_FROZEN_V12_GATE`

No post-outcome rescue, asset selection, parameter tuning, private endpoints, account reads, orders, wallets, exchange mutation or live trading.
