# MEXC PLTR REGULAR-SESSION TRANSFER — PRE-OUTCOME FREEZE V0.2

Date: 2026-10-04
Status: FROZEN BEFORE PLTR OUTCOMES

Target:
- MEXC `PLTRSTOCK_USDT`
- Binance/Bitget `PLTRUSDT`

Source census:
- run `37229998686`
- verdict `HIGHBETA_EQUITY_SOURCE_PASS__PLTR`
- source day `2026-09-30` excluded from outcomes

Frozen sample:
- weekdays 2026-09-09 through 2026-10-02
- exclude 2026-09-30
- signal window 14:31–18:44 UTC

Exact transferred rule:
- external = mean(Binance PLTRUSDT 1m return, Bitget PLTRUSDT 1m return)
- lag gap = external return - MEXC PLTRSTOCK_USDT 1m return
- abs(external) >= 5 bps
- sign(lag gap) == sign(external)
- abs(lag gap) >= 3 bps
- direction FOLLOW_EXTERNAL_CONSENSUS
- horizon 1 minute
- cooldown 1 minute

No grid search is authorized.

Sequential cross-asset alpha:
- TESLA 0.025
- APPLE 0.0125
- PLTR 0.00625
- any next independent asset <= 0.003125

PASS requires:
- N>=50
- >=12 distinct signal sessions
- mean gross >0
- median gross >0
- win rate >50%
- all three chronological thirds mean >0
- exact one-sided binomial p<0.00625

No tuning, private endpoints, account reads, wallets, orders, exchange mutation or live trading.
