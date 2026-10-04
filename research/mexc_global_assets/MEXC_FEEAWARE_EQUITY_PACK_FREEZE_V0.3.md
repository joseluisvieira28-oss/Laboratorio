# MEXC FEE-AWARE EQUITY PACK — PRE-OUTCOME FREEZE V0.3

Date: 2026-10-04
Status: FROZEN BEFORE NFLX / BABA / GOOGL / ORCL OUTCOMES

AMD V0.2 was underpowered at the identical fee-aware rule:
- shock >= 20 bps
- lag gap >= 10 bps
- horizon 1 minute
- FOLLOW_EXTERNAL_CONSENSUS
- N=5, 5/5 wins
- mean gross +14.798598 bps
- median +12.027951 bps

No AMD threshold is changed.

The remaining source-pass assets were predeclared before AMD outcomes:
- NFLX: MEXC NFLXSTOCK_USDT / external NFLXUSDT
- BABA: MEXC BABASTOCK_USDT / external BABAUSDT
- GOOGL: MEXC GOOGLSTOCK_USDT / external GOOGLUSDT
- ORCL: MEXC ORCLSTOCK_USDT / external ORCLUSDT

Frozen sample:
- weekdays 2026-09-09 through 2026-10-02
- exclude source-verification day 2026-09-30
- signal window 14:31–18:44 UTC
- exact 1m observable alignment
- no forward fill/interpolation

Exact rule for every asset:
- external return = mean(Binance 1m return, Bitget 1m return)
- lag gap = external return - MEXC 1m return
- abs(external) >= 20 bps
- sign(lag gap) == sign(external)
- abs(lag gap) >= 10 bps
- FOLLOW_EXTERNAL_CONSENSUS
- horizon 1 minute
- cooldown 1 minute

Scientific eligibility per asset:
- N>=20
- >=8 distinct signal sessions
- mean gross >0
- median gross >0
- win rate >50%
- all chronological thirds mean >0

Exact one-sided binomial p-values are computed for all four assets.
Holm-Bonferroni controls FWER 0.05 across all four assets.

A scientific survivor is an asset that is both eligible and Holm-rejected.

Execution-scale gate is separate:
- mean gross >16 bps
- median gross >12 bps

Only a scientific survivor that also passes execution scale may be classified:
`FEEAWARE_MULTI_ASSET_EXECUTION_SCALE_CANDIDATE__FORWARD_VALIDATION_REQUIRED`

All four assets are evaluated regardless of earlier outcomes.
No grid search.
No threshold/horizon/direction changes.
No private endpoints, account reads, wallets, orders, exchange mutation or live trading.
