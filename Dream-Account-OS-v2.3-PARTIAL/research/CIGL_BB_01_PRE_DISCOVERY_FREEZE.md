# CIGL-BB-01 — PRE-DISCOVERY FREEZE

Status: FROZEN / RESEARCH ONLY / NO LIVE TRADING
Frozen before opening CIGL-BB-01 market outcomes.

## Authority
CLASSIC INDICATORS GAP LAB V0.1 — PRE-DISCOVERY PROTOCOL

## Hypothesis
Canonical Bollinger extreme mean reversion may exhibit positive pooled expectancy after frozen realistic costs.

## Universe
BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT, XRPUSDT, DOGEUSDT — Binance USD-M Futures.

## Discovery
2022-01-01 through 2023-12-31 only. 2024 remains unopened unless the frozen Discovery gate passes. 2025 protected. 2026 locked.

## Frozen rule
- Primary timeframe: 1H completed bars.
- Bollinger basis: 20-period SMA of completed 1H closes.
- Dispersion: 20-period population standard deviation (ddof=0).
- Upper band = SMA20 + 2*SD20.
- Lower band = SMA20 - 2*SD20.
- LONG signal when completed close is strictly below lower band.
- SHORT signal when completed close is strictly above upper band.
- Entry: next available 1H bar open.
- Exit: open exactly 4 completed bars after entry.
- One position per asset at a time; signals while a position is active are ignored.
- No stop, TP, trailing, pyramiding, trend filter, volume filter, ATR filter, VWAP filter, ADX filter, or parameter perturbation.
- Base roundtrip cost: 10 bps. Stress: 14 bps.
- Any data gap invalidates windows crossing the gap; rolling state must restart after discontinuity.

## Discovery gate
Pooled equal-weight six-asset 1H trade set must satisfy ALL:
1. N >= 300 completed trades.
2. NET10 mean > 0 bps.
3. Profit Factor > 1.00.

If any condition fails: CIGL-BB-01 closes at Discovery and 2024 MUST NOT be accessed.
If all pass: 2024 may open once with unchanged rule as internal OOS.

## Governance
No post-outcome tuning. No asset selection. No subgroup rescue. No use of 4H to rescue failed 1H. No 2025/2026 access. No live orders, exchange mutation, merge to main, or deployment.