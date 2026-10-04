# MEXC LEVERAGED STOCK TRANSFER — PRE-OUTCOME FREEZE V0.3

Date: 2026-10-04
Status: FROZEN BEFORE OUTCOMES

Source discovery run: 37235145438
Source artifact SHA256: eff1626678981ba884336bce10135bdc52542664e074cef6f87d3224db3e5a7e

The only triple-source candidates discovered without outcomes are:
- MUU_USDT / Binance MUUUSDT / Bitget MUUUSDT
- MVLL_USDT / Binance MVLLUSDT / Bitget MVLLUSDT

2026-09-30 is burned from outcomes.

Frozen sample:
- weekdays 2026-09-09 through 2026-10-02
- exclude 2026-09-30
- signal window 14:31–18:44 UTC

Exact transferred rule, unchanged from the NVIDIA/TESLA replicated mechanism:
- shock >= 5 bps
- lag gap >= 3 bps
- horizon = 1 minute
- direction = FOLLOW_EXTERNAL_CONSENSUS
- external return = mean(Binance, Bitget)
- lag gap = external return - MEXC return
- 1-minute cooldown

Scientific PASS per asset requires:
- N >= 50
- signals on >=12 distinct sessions
- mean gross > 0
- median gross > 0
- win rate > 50%
- all chronological thirds mean > 0
- exact one-sided binomial p survives Holm-Bonferroni FWER 0.05 across both assets.

Operational fee classifications are frozen separately:
- fee-floor survivor: scientific PASS and mean net after 12 bps > 0
- robust-fee survivor: scientific PASS and mean net after 16 bps > 0

A robust-fee survivor is NOT live trading approval. Spread, slippage, latency, fill probability and forward validation remain separate.

No parameter changes after outcomes.
No retrospective OOS.
No private endpoints, account reads, wallets, orders, exchange mutation or live trading.
