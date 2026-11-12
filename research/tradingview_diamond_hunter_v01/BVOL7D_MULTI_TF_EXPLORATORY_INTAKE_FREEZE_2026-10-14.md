# TradingView BVOL7D — fixed multi-timeframe exploratory intake BEFORE additional operator exports
Frozen timestamp: 2026-10-14 (operator confirmed original 1H; no additional TF exports seen at this point).
Branch: research/tradingview-diamond-hunter-v01-2026-10-14 / PR #221. SCIENCE ONLY / NO MERGE / NO TRADING.

## Research question
Does the exact original exlux 'Crypto Volatility Bitcoin Correlation Strategy' show any descriptive stable net economics across other bar intervals, or is the 1H +4.476% zero-fee outcome unstable and already negative after BASE fees?
THIS IS NOT AN UNTOUCHED CONFIRMATORY OOS: BTC 2024-2026 market outcomes and the original 1H strategy have already been seen, and TF comparisons are correlated and exploratory.

## Predeclared data request and full coverage
Request exactly these four additional chart periods on BINANCE:BTCUSDT: 5m, 15m, 30m, 4h. Already received and audited: 1h benchmark. Do not add/omit a period based on which CSV looks profitable; record all four including empty trades, source errors or truncated history.
Hold author Pine script and all input defaults unchanged: Coinbase BTCUSD, BitMEX BVOL7D, VIXFix 22, EMA 50. TradingView Properties original: 1,000,000 USDT starting virtual balance, order quantity 1 BTC, pyramiding 1, 0% fees, zero tick slippage, 4 ticks/bar emulator, calculate on close, same margin settings; never change any of these for the descriptive replication. 0 fee/slip EXPORTS ONLY; realistic costs reconstructed uniformly offline. No authorization of unlimited actual margin.
Prefer identical full history 2024-01-01 through last available bar on 2026-10-14 across all TF if TradingView permits without modifying strategy. Otherwise export maximum full available period with no cherry-picking, report exact earliest/latest trade timestamps, source/chart loaded date coverage and truncation. For 5m, TradingView may limit available bars; capture that limitation and DO NOT compare truncated 5m profits to multi-year 1h profits as equivalent.
Export complete Strategy Tester > List of trades for each TF, **including both Entry and Exit** rows and any open-position row; attach screenshot of chart toolbar showing BTCUSDT ticker/timeframe and Properties/Inputs if altered by UI. Mark empty or inaccessible CSV as SOURCE_BLOCKED instead of generating data.

## Frozen accounting and reporting metrics (every TF)
1. SHA256 of exact CSV raw bytes, encoding and column mapping; validate pairs and separate OPEN vs CLOSED rows.
2. Number of realized closed trades; win/loss/zero; start/end/calendar years; trade duration median/max; LONG/SHORT distribution (source is LONG only); equity, gross profit, gross loss, PF, win rate, maximum decline as supported by report; do not infer intrabar MTM drawdown from closed rows.
3. From each EXECUTED ENTRY and closed EXIT size x actual price, calculate notional turnover. Static fee/slip sensitivities only: BASE 8bps fee +2bps adverse slip each side; STRESS 8bps +5bps slip each side; illustrative LOW 2bps +2bps separately labelled unrealistic/unverified; before funding/spread and no dynamic rebalancing.
4. Return/PF by full UTC/calendar year where possible; top 3 winning trade concentration; static delete top3 net; number of trades/week only if whole coverage window known; fee+slippage break-even bps/side; no leverage or annual-income forecasts.
5. Identify stale/nonexistent BitMEX BVOL7D chart values, unsupported historical samples, missing bars, the Coinbase/Binance cross-venue timing mismatch; CSV cannot prove point-in-time external feed availability.
6. All original candidate settings remain FIXED. No post-hoc EMA22, VIXFix variants, new stops, fees models or LONG/SHORT switching; if genuinely different hypothesis is warranted, separately define and freeze before unobserved prospective source/outcome collection.

## Gate
A visually green profit is not a pass. If BASE/STRESS net are negative, tag COST_FAIL. If positive across all, tag EXPLORATORY_HISTORICAL_ONLY and REQUIRE independent point-in-time source and FUTURE forward. Source gaps => SOURCE_BLOCKED. Any cost replays must be labeled static unless a frozen causal simulation actually runs. No 2026 independent OOS credit (already peeked); protected Crypto Lab holdout remains locked.

Operator request: four CSVs (5m, 15m, 30m, 4h). Send them without changing the author's script or properties. No access credentials or live trading.
