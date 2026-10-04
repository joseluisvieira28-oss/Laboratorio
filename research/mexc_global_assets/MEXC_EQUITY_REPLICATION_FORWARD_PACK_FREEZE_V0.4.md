# MEXC MULTI-ASSET REPLICATION FORWARD PACK — PRE-OUTCOME FREEZE V0.4

Date: 2026-10-04
Status: FROZEN BEFORE 2026-10-05 OUTCOMES

Assets:
- PLTR: PLTRSTOCK_USDT / PLTRUSDT
- META: METASTOCK_USDT / METAUSDT
- AMZN: AMZNSTOCK_USDT / AMZNUSDT

Each already passed the exact transferred 5/3/1m FOLLOW rule on the frozen historical sample.

Prospective window:
- every weekday 2026-10-05 through 2026-10-30
- 20 sessions
- signal window 14:31–18:44 UTC

Exact signal:
- external return = mean(Binance 1m return, Bitget 1m return)
- lag gap = external return - MEXC 1m return
- abs(external) >= 5 bps
- sign(lag gap) == sign(external)
- abs(lag gap) >= 3 bps
- FOLLOW_EXTERNAL_CONSENSUS
- horizon 1 minute
- cooldown 1 minute

Per-asset eligibility:
- N>=100
- signals on >=15 sessions
- mean >0
- median >0
- win rate >50%
- both chronological halves mean >0

Exact one-sided binomial p-values are computed for all 3 assets.
Holm-Bonferroni controls FWER 0.05 across PLTR/META/AMZN.

No evaluation for promotion before the complete 20-session window ends.
No tuning, threshold changes, asset dropping, private endpoints, account reads, wallets, orders, exchange mutation or live trading.
