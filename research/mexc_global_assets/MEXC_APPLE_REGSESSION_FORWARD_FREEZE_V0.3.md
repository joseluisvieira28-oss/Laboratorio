# MEXC APPLE REGULAR-SESSION FORWARD — PRE-OUTCOME FREEZE V0.3

Date: 2026-10-04
Status: FROZEN BEFORE 2026-10-05 OUTCOMES

Prior authority:
- exact NVIDIA rule transferred to APPLE
- N=154
- wins=104
- win rate=67.5325%
- mean gross=+2.840377 bps
- median gross=+2.660010 bps
- p=8.070222e-6
- thirds all positive
- frozen transfer alpha=0.0125

Prospective window:
- every weekday 2026-10-05 through 2026-10-30
- 20 sessions
- signal window 14:31–18:44 UTC

Frozen cell:
- shock >= 5 bps
- lag gap >= 3 bps
- horizon 1m
- FOLLOW_EXTERNAL_CONSENSUS
- external = mean(Binance AAPLUSDT, Bitget AAPLUSDT) 1m returns
- MEXC = AAPLSTOCK_USDT
- 1m cooldown

PASS requires:
- N>=70
- >=15 distinct signal sessions
- mean >0
- median >0
- win rate >50%
- both chronological half means >0
- exact one-sided binomial p<0.05

No interim promotion. Evaluate only after full window.
No tuning, private endpoints, account reads, wallets, orders, exchange mutation or live trading.
