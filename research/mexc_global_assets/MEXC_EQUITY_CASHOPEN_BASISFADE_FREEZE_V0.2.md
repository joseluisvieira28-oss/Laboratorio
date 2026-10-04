# MEXC MULTI-EQUITY CASH-OPEN BASIS-FADE — PRE-OUTCOME FREEZE V0.2

Date: 2026-10-04
Status: FROZEN BEFORE TARGET-ASSET CASH-OPEN OUTCOMES

Hypothesis source:
NVIDIA cash-open V0.2 generated a non-promoted but economically large 30-minute basis-fade effect. That prior observation is used only to define this independent transfer hypothesis.

Targets:
TSLA / AAPL / PLTR / META / AMZN / MSFT.

Source gate:
- run 37231052066
- verdict MULTI_EQUITY_CASHOPEN_SOURCE_PASS
- source day 2026-09-30 excluded from outcomes

Sample:
- weekdays 2026-09-09 through 2026-10-02
- exclude 2026-09-30

Signal:
- exact observable time 13:29 UTC
- external price = mean(Binance, Bitget) close
- basis = 10000*(MEXC/external - 1)
- side = -sign(basis)
- no basis threshold
- horizon 30 minutes
- outcome at 13:59 UTC
- exact 1-minute alignment only

Scientific eligibility per asset:
- N>=15
- mean >0
- median >0
- win rate >50%
- both chronological halves mean >0

Exact one-sided binomial p-values for all six assets.
Holm-Bonferroni FWER 0.05 across all six.

Execution-scale gate:
- mean gross >16 bps
- median gross >12 bps

All six assets are evaluated regardless of earlier result.
No grid search, no alternate horizon, no threshold rescue, no direction switch.

No private endpoints, account reads, wallets, orders, exchange mutation or live trading.
