# BITGET MAKER MICROSTRUCTURE V0.2.1 — TECHNICAL IDENTITY AMENDMENT

Date: 2026-10-05
Status: TECHNICAL CORRECTION ONLY / SCIENCE UNCHANGED

The first V0.2 run (37240975972) failed closed for HOODUSDT, COINUSDT and ARMUSDT because the microstructure runner reconstructed more parent signals than the immutable parent ledger counts.

Root cause:
- frozen parent evaluator `BINANCE_BITGET_STOCK_V0.1 score()` requires the target candle at `signal + horizon` to exist before a signal is admitted;
- the V0.2 microstructure `reconstruct_signals()` omitted that parent eligibility condition;
- this produced extra signals that never existed in the frozen parent ledger.

Frozen expected parent counts remain unchanged:
- HOODUSDT 1148
- COINUSDT 986
- ARMUSDT 923
- AAPLUSDT 86

Correction:
- require `t + horizon_min*60` to exist in Bitget target candles before admitting the parent signal.

UNCHANGED:
- candidate set;
- signal thresholds 5/3 bps;
- FOLLOW_BINANCE direction;
- 1m horizon/cooldown;
- placement latency 1s;
- post-only prices;
- queue-ahead 100%;
- no cancellation credit;
- entry/exit TTL 10s;
- forced taker exit rule;
- maker/taker fees;
- execution gates;
- Holm family;
- no candidate dropping.

The prior AAPL output is not used as a tuning input. V0.2.1 reruns all four assets under the same frozen execution model.

No private endpoints, account reads, orders, wallets, exchange mutation or live trading.
