# BACKES-DIAMANTE-004 — Cross-venue and chronological pseudo-OOS audit
Frozen on 2026-11-24, BEFORE evaluating the 004 result. NO TRADING.

## Prior work and necessary caution
BACKES-002's spot BTC/ETH rotation rule is a **Crypto Lab original** inspired by public themes discussed by Augusto Backes; this research cannot be attributed to his proprietary system or personal trading. BACKES-003/PR#388 found that one 10-week ETH period in 2025 accounts for practically all historic excess relative to BTC.

All 2018–2026 data are known to the researcher: all evaluations here, including time-ordered folds, are **RETROSPECTIVE / PSEUDO-OOS**; not genuinely future-unseen.

## Pre-registered questions
1. Does frozen BACKES-002 model performance repeat on Kraken and Coinbase independent BTC/ETH spot orderbooks?
2. Does a simple ETHBTC relative momentum MOM4, MOM8 or MOM12 outperform the original more complex pivot+momentum model?
3. Does 104-week rolling training selection followed by next 26 weeks holdout outperform BTC, ETH and 50/50, after costs?
4. What happens after realistic cost stresses and in separate 2018–22, 2023–24 and 2025–26 regimes?

## Authentic sources / no substitution
- Binance Spot: BTCUSDT, ETHUSDT, ETHBTC official ZIP daily candles from 2018-01-01 through 2026-11-22, original SHA-256 archive digest 735fff332994ce546f56258a01787d7f250203efa701586fa24eefd553f1ecaf.
- Coinbase Exchange: GET /products/{BTC-USD,ETH-USD,ETH-BTC}/candles?granularity=86400, unauthed free public reads, request windows of <=200 daily candles, daily completeness and timestamp deduplication.
- Kraken Spot: GET /0/public/OHLC?pair={XBTUSD,ETHUSD,ETHXBT}&interval=10080&since=..., max 720 candles; all three trade pairs must be available as Monday-anchored whole-week prices. Drop current unfinished candle. Other anchors or incomplete historical coverage => SOURCE_BLOCKED_KRAKEN.
- All venue-specific weekly datasets must cover exactly 464 Monday–Sunday UTC weeks 2018-01-01..2026-11-22; no gap fill; positive valid OHLC; timestamp and cross quote sanity gates. Require DIRECT traded ETH/BTC pair; cannot use ratio of asynchronous USD high/low to synthesize pivots. Compare each venue in its native USD or USDT quote (do not confuse these numeraires).
- Archive every API GET receipt with URL, timestamp, bytes and SHA256, weekly parsed price series, source errors and reproducible results. Failed source should not veto other valid source results.

## Frozen signals and portfolios
- Baselines: BTC buy+hold, ETH buy+hold, 50/50 BTC/ETH weekly rebalance, and cash in USD/USDT at zero interest (not risk-free actual yield).
- FROZEN002: EXACT same ETHBTC 3-left/3-right swing low confirmation and 4-week ETHBTC momentum rule, no changes. Signal as of Sunday closed week t used on Monday open t+1.
- MOM4 / MOM8 / MOM12: ETH if Sunday close ETHBTC(t)>ETHBTC(t-k), else BTC; act next Monday open. These are **lab-created baselines**, not the influencer's strategies.
- Primary cost: 10 bps all-in hypothetical commission+slippage per traded unit portfolio, initial buy charged. Stress 5/10/20/35 bps, and two-leg via USD swap stress 35 bps. No real fees/fills/spread reconstructions; terminal liquidation omitted as in BACKES002.
- For each 2018–22, 2023–24, 2025–26 and full-period calculate return, max drawdown, exposures, switch count and rank vs benchmarks; 8-week block bootstrap of active 2025–26 arithmetic weekly excess with fixed random seed, 2000 replicates.
- Rolling chronological diagnostic: from week index 104, each 26-week test fold chooses among FROZEN002, MOM4, MOM8, MOM12 based only on preceding 104 weeks NET cumulative wealth at 10bps; tie-break lexicographic; apply choice for following 26 weeks, charge change costs, concatenate test rows. This is pseudo-OOS ONLY because all data already known to researcher; no statistical proof of undiscovered economic edge.

## Interpretative gates
SOURCE_BLOCKED for unavailable pair/history or invalid data, no alternative-price imputation.
NO-GO ECONOMIC if complex strategy is dominated by simple benchmark in two regimes, extreme DD, or one episode dominance.
INCONCLUSIVE if sources/independent tests insufficient.
CANDIDATE FOR PROSPECTIVE SHADOW ONLY after cross-venue robust positive benchmark relative after costs, period stability, no single-episode dependency and reasonable drawdown.
NEVER LIVE GO from historic retrospective analysis. No orders/trades, private APIs, credentials, purchases, subscriptions, transfers, paid sources, deployments or strategy re-optimisation after viewing outputs.


## Pre-result cost addendum: verified public taker schedules (2026-11-24)
Before any successful 004 historical economic result was obtained, fee verification revealed that Coinbase Exchange's 30-day volume tier USD 0–10k charges 60bps TAKer and Kraken Pro Spot's initial tier charges 80bps TAKer; these do not include slippage. Official sources:
- https://help.coinbase.com/en/exchange/trading-and-funding/exchange-fees
- https://www.kraken.com/pro/fees
Therefore additional fixed *sensitivity-only* scenarios **60, 80, 100 bps per direct trading leg** are pre-registered alongside 5,10,20,35bps. 100bps is not a calibrated upper bound for adverse execution. For two-hop USD routing, pay two legs on swaps; initial acquisition is one leg. Applied identically to all venues for comparability, with first-tier relevant comparison: Coinbase 60bps and Kraken 80bps. Actual fee tiers, historic changes, bid/ask and liquidity remain not reconstructed. A 10bps result must **not** be advertised as realistic net trading profitability for a low-volume account.
