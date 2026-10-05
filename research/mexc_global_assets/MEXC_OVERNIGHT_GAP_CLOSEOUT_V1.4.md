# MEXC OVERNIGHT GAP CATCH-UP V1.4 — CLOSEOUT

Run: 37265900559
Date: 2026-10-05

Frozen rule:
- previous-session anchor 20:00 UTC
- current signal/entry 13:29 UTC
- external overnight return from mean(Binance+Bitget)
- require abs(external overnight return) >=100 bps
- require same-sign external-minus-MEXC lag gap >=25 bps
- FOLLOW_EXTERNAL_CONSENSUS
- exit 13:59 UTC
- 30m horizon
- all 35 source-pass assets eligible
- daily equal-weight basket is the scientific unit

Results:
- total triggered trades: 2
- triggered days: 2
- mean daily gross: -24.7063 bps
- median daily gross: -24.7063 bps
- winning days: 0/2
- chronological halves: -23.1767 / -26.2358 bps
- exact one-sided binomial p=1.0
- mean net after 16 bps: -40.7063 bps
- median net after 16 bps: -40.7063 bps

Triggered observations:
- 2026-09-14 CATSTOCK_USDT: -23.1767 bps
- 2026-10-01 RKLBSTOCK_USDT: -26.2358 bps

Verdict:
`OVERNIGHT_GAP_UNDERPOWERED_AT_FROZEN_V14_GATE`

No threshold rescue, direction flip, horizon change, asset selection, private endpoints, account reads, orders, wallets, exchange mutation or live trading.
