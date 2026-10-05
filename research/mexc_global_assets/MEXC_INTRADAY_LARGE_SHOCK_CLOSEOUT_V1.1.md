# MEXC INTRADAY LARGE-SHOCK CATCH-UP V1.1 — CLOSEOUT

Run: 37280805746
Date: 2026-10-05
Artifact: 11332920309
Artifact SHA256: 1759b5ad8889c461e16ffed145b10c450eaa3251141a8fbc82a50a0e1a38ffe8

Frozen rule:
- 35 assets
- external 1m shock >=25 bps
- same-sign MEXC lag gap >=15 bps
- FOLLOW_EXTERNAL_CONSENSUS
- 5m horizon
- 5m cooldown
- equal-weight daily basket
- no threshold/horizon/asset grid

Results:
- total trades: 465
- triggered days: 17
- winning days: 16/17 = 94.1176%
- mean daily gross: +10.8901 bps
- median daily gross: +8.6036 bps
- chronological halves: +8.0265 / +13.4355 bps
- exact one-sided binomial p=0.0001373291
- scientific PASS=true

Economic 16 bps gate:
- mean net: -5.1099 bps
- median net: -7.3964 bps
- PASS=false

Verdict:
`SCIENTIFIC_INTRADAY_SURVIVOR__FEE_BLOCKED`

Interpretation:
Large-shock conditioning materially increases the gross magnitude relative to the original 5/3/1m family and remains highly consistent across days, but it still does not clear the frozen 16 bps round-trip API cost requirement.

No post-outcome threshold rescue, horizon change, asset selection, private endpoints, account reads, orders, wallets, exchange mutation or live trading.
