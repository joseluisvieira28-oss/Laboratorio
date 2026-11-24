# BACKES-DIAMANTE-004B — Kraken daily-source recovery (retrospective)
Opened 2026-11-24 AFTER original BACKES-004 data audit reported SOURCE_BLOCKED_KRAKEN: Kraken 1w weekly OHLC anchored Thursday UTC, incompatible with Binance/Coinbase Monday-week definition. Never shift Thursday OHLC price labels to Monday.

## Independent source and restricted scope
- Kraken REST public unauthenticated OHLC 1440m, max 720 recent candles, 3 direct pairs XBTUSD, ETHUSD, ETHXBT.
- Attempt exact 98 Monday–Sunday complete weeks 2025-01-06 through 2026-11-22: 686 daily rows per pair, no gaps, positive valid OHLC, price sanity.
- Archived source raw API response hashes, URLs, receipt time and normalized daily->weekly bars.
- Compare with same 98 weekly windows of Binance official public ZIP BTCUSDT ETHUSDT ETHBTC with immutable prior BACKES-002 signal.
- Use **the original Binance FROZEN002 signal as common allocations** on Kraken and Binance to test execution-price venue robustness only. This is **not** an independently derived Kraken BTC/ETH predictive strategy; insufficient Kraken daily history to derive comparable prior pivot regime over 2018–2024.
- Fixed cost scenarios 10,35,60,80,100 bps per direct leg. 80bps Kraken taker is the current published initial-volume tier, not a 2025 historical per-trade statement; spreads and real fills not reconstructed.
- Require previous BACKES-002 2025–2026 Binance return -4.0107% at 10bps within precision. Fail closed otherwise.
- Compare ratio close divergences, cumulative returns, drawdowns, and switches across USD Kraken and USDT Binance independently. Different currency numeraire, no pooling of price levels.

## Limits
004B is a post-blockage historical **source salvage addendum** and NOT prespecified out-of-sample confirmation. No unverified interpolation, no margin/derivatives, trade execution, user account access or purchases. Source errors yield SOURCE_BLOCKED. Economic verdict can never be live GO from this. Existing 004 hypotheses and results remain unchanged.
