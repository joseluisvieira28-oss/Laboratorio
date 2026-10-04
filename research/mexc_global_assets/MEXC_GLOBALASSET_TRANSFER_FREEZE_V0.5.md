# MEXC GLOBAL-ASSET TRANSFER — PRE-OUTCOME FREEZE V0.5

Date: 2026-10-04
Status: FROZEN BEFORE V0.5 OUTCOMES

Source authority:
- run 37235636339
- artifact SHA256 `94f8a3865c6f6619a9cebf1ca8c546557cb538579c01fc1f82e26d7416b0b78a`
- 35/35 explicit aliases passed MEXC + Binance + Bitget source transport on the burned source date.

All 35 source-pass candidates are included. No candidate may be removed after outcomes.

Frozen sample:
- weekdays 2026-09-09 through 2026-10-02
- exclude 2026-09-30
- signal window 14:31–18:44 UTC
- 1-minute exact closed-candle timestamps

Frozen rule, unchanged from NVIDIA -> TESLA -> MUU/MVLL:
- external shock >= 5 bps
- external-minus-MEXC lag gap >= 3 bps in same sign as external move
- FOLLOW_EXTERNAL_CONSENSUS
- horizon 1 minute
- cooldown 1 minute
- external = mean(Binance + Bitget)

Scientific PASS requires N>=50, >=12 signal sessions, positive mean and median, >50% wins, all three chronological thirds positive, and exact binomial p surviving Holm-Bonferroni FWER 0.05 across ALL 35 candidates.

Operational classifications are fixed before outcomes:
- fee-floor survivor: scientific PASS and mean net after 12 bps > 0
- robust-fee survivor: scientific PASS and mean net after 16 bps > 0

A robust-fee survivor is only an execution candidate. It is NOT live authorization and still requires spread/slippage/latency/fill and forward checks.

No asset-specific tuning, retrospective rescue, private endpoints, account reads, orders, wallets, exchange mutation or live trading.
