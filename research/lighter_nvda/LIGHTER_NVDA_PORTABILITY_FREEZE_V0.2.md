# LIGHTER NVDA PORTABILITY — PRE-OUTCOME FREEZE V0.2

Date: 2026-10-05
Status: FROZEN BEFORE OUTCOMES

Source authority:
- Lighter NVDA market_id 110, perp
- public API reports maker_fee=0.0000 and taker_fee=0.0000
- minimum quote amount 10 USDT
- public 1m historical candles proven
- source gate run 37238944978
- history gate run 37239002080

Burned source dates:
- 2026-09-09
- 2026-09-30
- 2026-10-02

Frozen outcome sample:
- weekdays 2026-09-10 through 2026-10-01 inclusive
- exclude 2026-09-30
- signal window 14:31–18:44 UTC

Frozen transferred mechanism:
- Binance NVDAUSDT + Bitget NVDAUSDT external consensus
- external shock >=5 bps
- same-sign external-minus-Lighter lag gap >=3 bps
- FOLLOW_EXTERNAL_CONSENSUS
- 1-minute horizon
- 1-minute cooldown
- exact closed-candle timestamps
- no forward fill/interpolation

PASS:
- N>=30
- >=10 signal sessions
- mean gross >0
- median gross >0
- win rate >50%
- both chronological halves mean >0
- exact one-sided binomial p<0.05

This is one pre-specified venue/asset/rule portability test; no parameter grid is opened.

Published Lighter market fee is frozen as 0 bps round trip, but spread/slippage/latency/fill are NOT assumed zero and must be measured separately if science passes.

No tuning, retrospective rescue, private endpoints, account reads, wallets, orders or live trading.
