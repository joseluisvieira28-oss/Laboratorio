# MEXC GLOBAL-ASSET CASH-OPEN BASIS FADE — PRE-OUTCOME FREEZE V0.7

Date: 2026-10-05
Status: FROZEN BEFORE CASH-OPEN OUTCOMES

Source authority:
- run 37263208615
- artifact SHA256 `8aeb2c5c0f6cc34846c2dcf9142fbdf1965d36bb10778e82011d679f7760f995`
- 35/35 candidates passed MEXC + Binance + Bitget source transport at 13:20–14:05 UTC.
- source date 2026-09-30 is burned.

This is an independent cross-asset transfer of the NVIDIA V0.2 cash-open basis-fade arm that showed the largest gross magnitude at 30 minutes.

Frozen sample:
- weekdays 2026-09-09 through 2026-10-02
- exclude 2026-09-30

Frozen rule:
- signal at exact closed-candle timestamp 13:29 UTC
- external price = mean(Binance + Bitget) at 13:29
- basis = 10000*(MEXC/external - 1)
- side = -sign(basis)
- no basis threshold
- entry = MEXC 13:29 close
- exit = MEXC 13:59 close
- horizon = 30 minutes

Scientific PASS per asset:
- N>=15
- mean gross >0
- median gross >0
- win rate >50%
- both chronological halves mean >0
- exact one-sided binomial p survives Holm-Bonferroni FWER 0.05 across ALL 35 assets.

Operational classifications:
- fee-floor survivor: scientific PASS and mean net after 12 bps >0
- robust API-fee survivor: scientific PASS and mean net after 16 bps >0

No asset-specific tuning, threshold search, horizon search, retrospective rescue, private endpoints, account reads, orders, wallets, exchange mutation or live trading.
