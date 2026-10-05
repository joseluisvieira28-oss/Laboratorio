# MEXC SESSION-WIDE SHOCK CLUSTER — NEW ASSETS PRE-OUTCOME FREEZE V1.5

Date: 2026-10-05
Status: FROZEN BEFORE V1.5 OUTCOMES

Candidate selection:
- include every V1.4 candidate that passes MEXC + Binance + Bitget source transport
- no candidate may be removed or added after outcomes
- ambiguous-identity contracts excluded in V1.4 remain excluded

Outcome period:
- weekdays 2026-09-09 through 2026-10-02
- exclude source date 2026-09-30

Rule transferred unchanged from source-blocked V1.3:
- 5-minute external return = mean(Binance, Bitget)
- abs external 5m move >=50 bps
- lag gap = external 5m return - MEXC 5m return
- same-sign lag gap
- abs lag gap >=25 bps
- FOLLOW_EXTERNAL_CONSENSUS
- 5-minute horizon

Scientific unit:
- equal-weight timestamp cluster across all triggering candidates
- global 5-minute cooldown
- no overlapping cluster outcomes

Scientific PASS:
- >=20 clusters
- >=8 triggered dates
- positive mean and median gross cluster return
- >50% winning clusters
- both chronological half means positive
- exact one-sided binomial p<0.05

Operational PASS:
- scientific PASS
- mean and median after 16 bps round-trip remain >0

No tuning, threshold grid, horizon grid, asset-specific rescue, private endpoints, account reads, orders, wallets, exchange mutation or live trading.
