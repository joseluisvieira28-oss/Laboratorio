# DIGUI-011 — LIQUIDITY & STRUCTURE (frozen before first historical backtest)
Date: 2026-11-17. RESEARCH / READ-ONLY. NOT A BOT OR PRODUCTION TRADING SYSTEM.

## Question
Do mechanical, observable 1h and 4h price/volume market-structure patterns in BTC, ETH and SOL USD-M perpetuals generate an out-of-sample positive NET return against simple baselines under realistic costs? Do not label this as the creator's exact method. Adaptations are hypotheses only. Earlier Convex SOL4h PR #266 had no independently verified net edge and insufficient effective trade count; avoid passing on tiny samples.

## Sources
Public monthly Binance Vision USD-M perpetual OHLCV 1h, BTCUSDT, ETHUSDT, SOLUSDT from 2023-06-01 to 2026-10-31 inclusive (period subject to availability). Immutable monthly source archives SHA-256. Actual Binance historical settled funding BTC/ETH/SOL from CARRY-001 verified source artifact, SHA256 extended_funding_events.csv `a7fdd25b7155ca1a81db7aba0d9e6d7d4ee43c070d4cc15de98114a80c935ce0`. Only source-present horizons count.

Fundamental limitations: 1h OHLCV DOES NOT reveal traded volume at each price. The rolling "POC" in this study is a **typical-price volume bucket approximation**, NOT genuine volume profile POC and NOT a replication of specific influencer signals. Every decision at close of bar t uses bars <= t; positions enter at next bar open t+1. Intrabar stop and target in same bar -> STOP FIRST. If missing contiguous hourly bars, no bridged positions and mark absent/censor. Historical candle open is NOT a guaranteed executable quote; NO LIVE GO from OHLCV alone.

## Frozen signal rules
For 1h and 4h, use 1h source bars, aggregate 4h into completed UTC blocks and discard incomplete 4h blocks.
- rolling levels: previous 72 completed 1h bars or previous 42 completed 4h bars (excluding current), previous high and low.
- ATR = prior 14 completed bars (exclude bar t), mean true range.
- BREAKOUT trend: close_t >= previous range high+0.15 ATR, previous close below/equal range high, volume_t>=1.1x median previous 20 bars, vice versa short.
- SWEEP/false-break: high_t>=previous range high+0.10 ATR AND close_t<previous high-0.05 ATR -> short; opposite at prior range low -> long, with candle close inside prior range.
- POC-retest proxy: divide previous 72 or 42 bars into 20 fixed price buckets based on their typical prices (H+L+C)/3, weighted by quote-volume; choose maximum-volume bin center. Long if prior close was >POC+0.30 ATR, current low revisits POC and close above POC+0.10ATR. Reverse for short. The zero-cost benchmark is not an exact POC and POC is never built with current/future bars.
- Baseline simple trend, direction of close vs rolling prior 20-bar simple average, only on first cross. No exotic state or extra tune.

## Trade and fee accounting
One position at a time per (coin,timeframe,strategy); no overlapping same-strategy positions.
At next bar OPEN apply adverse slippage 0.02% (also test 0.05%) on both entry and exit; Binance taker fee 0.05% per side, charged on changing notional; funding cashflows paid/received at historical settled intervals if position open at that event. No leverage, borrow or liquidation claims. Stop 1.0 ATR from entry, target 1.5 ATR from entry, maximum 8 completed bars (1h or 4h), stop-first if both touched same bar; gap through stop executes next open (adverse), never "fills at stop despite a gap".
Measure trades, avg/median net expectancy after costs, aggregate PnL per 1 unit of fixed notional (NO compounding claims), annual trades, net profit per 1000 exposure, % wins, max drawdown in accumulated trade-return units, payoff concentration; assess random-direction negative control on identical signal timestamps.
Slippage tests: 0.02% and 0.05% each side; fees fixed 0.05% taker/side. In real operation cost may be higher; bars have no book depth, financing/taxes/borrowing/infrastructure and order rejection unverified.
Baseline buy-and-hold perps not equivalent with trade-based risk, hence no assertion of superiority from incompatible position time; include momentum and random-direction controls.

## Chronological boundaries, never optimize on test
Train/descriptive: 2023-06 through 2024-12.
Validation: 2025-01 through 2025-06.
Final untouched test: 2025-07 through 2026-10.
No parameter fitting/selection allowed using test results. These 4 families × 3 coins × 2 frames are a prespecified *multiple testing family*, so a lone positive result does NOT earn GO. A credible candidate needs stable results on validation and TEST across multiple months, stable 5bps adverse slippage, enough events (prefer >=100 final-test trades) and economically meaningful net expectancy. No selection based on hindsight highest-ranked strategy.

## Safety & decision
NO trading, no sign/send orders, no exchange API credentials, no production workflow or Telegram changes, no GitHub main merge. Research draft PR only. No GO if source missing/incomplete/funding missing, realized net returns <=0, too few trades, unstable concentration, cost sensitivity, or no executable bid/ask independent evidence. GO only for LIMITED FOLLOWUP PAPER RESEARCH if a statistically robust positive candidate survives; still no capital without independent prospective execution evidence.
