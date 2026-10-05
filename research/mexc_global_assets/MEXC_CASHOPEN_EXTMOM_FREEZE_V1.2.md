# MEXC CASH-OPEN EXTERNAL MOMENTUM BASKET — PRE-OUTCOME FREEZE V1.2

Date: 2026-10-05
Status: FROZEN BEFORE V1.2 OUTCOMES

Source authority:
- run 37263208615
- artifact SHA256 `8aeb2c5c0f6cc34846c2dcf9142fbdf1965d36bb10778e82011d679f7760f995`
- 35/35 MEXC + Binance + Bitget source-pass in the cash-open window
- 2026-09-30 burned

This is a direct cross-asset basket transfer of the NVIDIA V0.2 cash-open EXTERNAL-MOMENTUM FOLLOW arm at 30 minutes.

Frozen sample:
- weekdays 2026-09-09 through 2026-10-02
- exclude 2026-09-30

Frozen rule:
- predictor: external 5-minute momentum from exact 13:24 to 13:29 UTC
- external price = mean(Binance + Bitget)
- side = sign(external 5-minute momentum)
- no threshold
- enter MEXC at 13:29 close
- exit MEXC at 13:59 close
- horizon = 30 minutes
- all 35 assets are included whenever complete
- daily scientific observation = equal-weight mean of all included signed asset returns

Scientific PASS:
- >=15 complete basket days
- mean daily gross >0
- median daily gross >0
- winning-day rate >50%
- both chronological halves mean >0
- exact one-sided binomial p<0.05 over basket days

Operational robust survivor:
- scientific PASS
- mean daily net after 16 bps >0
- median daily net after 16 bps >0

No asset selection, threshold grid, horizon grid, retrospective rescue, private endpoints, account reads, orders, wallets, exchange mutation or live trading.
