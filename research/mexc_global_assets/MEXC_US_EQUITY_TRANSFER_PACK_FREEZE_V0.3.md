# MEXC U.S. EQUITY TRANSFER PACK — PRE-OUTCOME FREEZE V0.3

Date: 2026-10-04
Status: FROZEN BEFORE META / AMZN / MSFT OUTCOMES

The exact 5/3/1m FOLLOW cell has already survived:
- NVIDIA discovery under Holm correction
- TESLA transfer at alpha 0.025
- APPLE transfer at alpha 0.0125
- PLTR transfer at alpha 0.00625

This pack evaluates ALL remaining source-pass candidates from the pre-frozen high-beta census, regardless of earlier results.

Frozen assets and sequential alpha:
- META: MEXC `METASTOCK_USDT`, external `METAUSDT`, alpha 0.003125
- AMZN: MEXC `AMZNSTOCK_USDT`, external `AMZNUSDT`, alpha 0.0015625
- MSFT: MEXC `MSFTSTOCK_USDT`, external `MSFTUSDT`, alpha 0.00078125

Sample:
- weekdays 2026-09-09 through 2026-10-02
- exclude source day 2026-09-30
- signal window 14:31–18:44 UTC

Exact rule for every asset:
- external return = mean(Binance 1m return, Bitget 1m return)
- lag gap = external return - MEXC 1m return
- abs(external) >= 5 bps
- sign(lag gap) == sign(external)
- abs(lag gap) >= 3 bps
- FOLLOW_EXTERNAL_CONSENSUS
- horizon 1 minute
- cooldown 1 minute

For an asset to PASS:
- N>=50
- >=12 distinct signal sessions
- mean gross >0
- median gross >0
- win rate >50%
- all three chronological thirds mean >0
- exact one-sided binomial p < that asset's frozen alpha

No asset is skipped because another passes/fails.
No grid search.
No tuning.
No private endpoints, account reads, wallets, orders, exchange mutation or live trading.
