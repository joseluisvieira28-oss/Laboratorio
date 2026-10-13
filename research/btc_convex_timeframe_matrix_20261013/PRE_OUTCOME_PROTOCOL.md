# BTC-CONVEX V5 — FOUR TIMEFRAME HISTORICAL MATRIX FREEZE
DATE: 2026-10-13 UTC. Source-based RETROSPECTIVE_DIAGNOSTIC_ONLY. ZERO independent OOS / economic-promotion credit.
Frozen BEFORE opening results of THIS comparison. BTC 2021–2025 Parent history known, old TV 5m/15m/4h exports known and fragile; all new historical comparisons exploratory only. Protected 2026 holdout NEVER accessed.

## Hypothesis / design
Evaluate **same recovered "Quant Trailing v5 (Payoff Invertido) - BTC" Pine strategy** on BTCUSD-M 15m, 30m, 1h, 4h with identical indicator *period counts* and identical trade lifecycle and costs. This intentionally makes 200-bar regime period last 50h / 100h / 200h / 800h respectively. It is NOT the same physical regime horizon across timeframes. No filters, threshold sweeps, retuned stops/targets or after-the-fact rescue.
Parent signal on CONFIRMED timeframe close: SMA20 and population STDEV20, Z<-2, close below SMA20-2*STD, RSI14 Wilder <30, volume>volume SMA20, score>=3 and close>SMA200. Due to overlapping Z and Bollinger tests, both can count separately, exactly as recovered Parent.
LONG-only, no overlapping slot, flat-only confirmed-bar signal, enter with 1x 20% *then current* paper equity notional at the opening of the **first 5m bar strictly after 1-second assumed signal witness** (TF candle close +5 minutes, avoiding fictitious at-close fills). Original 4% price stop from slip-adjusted entry, 12% from peak trailing but active ONLY while latest completed strategy TF close profit>=5%; nonlatched, i.e., resets to initial stop when activation becomes false. Peak highs observed since entry, stop changes only after bar CONFIRMED close; first stop applies on entry 5m and 5m gap rules apply. STOP-FIRST on OHLC ambiguity; 5m intrabar order not invented. Holding open into funding timestamp charged using historical rate and contemporaneous **5m market price as unverified mark proxy**, not 0 for missing source.

## Shared source and costs
UTC 2021-01-01 00:00 through 2025-12-31 23:55 inclusive, 2020-11/12 5m and 1h bars to warm SMA200 of the 4h version. **Official Binance USD-M monthly 5m market** bars with official publisher SHA256 CHECKSUM per archive. Aggregate contiguous 5m to 15m/30m/1h/4h OHLCV, verify every TF group complete, no gaps. Cross-check aggregated 1h OHLCV against independently downloaded official Binance monthly 1h klines; unequal => SOURCE_MISMATCH_BLOCKED, do not discard mismatching bars. 2021–2025 all monthly official Binance historical fundingRate archives with checksum, no private endpoint/orders/accounts.
BASE 8bps taker each side + adverse modeled slip 2bps each side; STRESS 8bps taker each side + adverse slip 5bps each side. Both notional exposure 20% paper equity; no leverage. Starting equity 10,000 USDT for each TF independent hypothetical account. No hardcoded price impact or live MEXC quote proof. Record actual modeled fees, funding, overlap skips and drawdowns.
For 4h, 1h and smaller times, the first signal after 2021 start may use prehistory but no economic pre-2021 outcomes and no 2026. All signals and position lifecycle must be causal and side-effect-free.

## Frozen comparisons
8 arms 4 TF x 2 cost cases. For each report: closed, wins, win%, PF, realized net return and final closed equity, marked terminal equity where open, annual realized net PnL per exit year, max realized DD and pessimistic 5m bar-low MTM DD (not liquidation/real fill), top-3 winning trades concentration, fee/funding totals, stop/time/no trade count, parent signal opportunities and overlaps. No performance ranking if source parity fails. Track no closed years. Same 2021–2025 time horizon and denominator.
Stop rules and signal logic match Parent Pine but 5m execution approximation and chosen normalized 20% risk differ from the source's historical 95% exposure/TV fill engine; do not equate account returns or infer micro-live readiness.

## Gates
- Pre-outcome source freeze and SHA256 checksum provenance, month completeness, 5m continuity and exact 1h parity.
- Synthetic tests for 15m/30m/1h/4h aggregation, timestamps, no future signals, flat-only slot, same-bar stop, gap, trailing nonlatch, costs/funding, 2025 boundary and end-censored opens.
- Regression Python tests pass before any economic claims, script in branch with SHA under immutable Actions run.
- Negative results eliminate exact experiment from active search without retuning. Positive results only justify further genuinely untouched validation, NOT execution edge.
- No main merge, live trading, orders, private API, spending, exchange mutations, wallets, protected 2026 holdout, Render or backtest optimization after outcomes.
