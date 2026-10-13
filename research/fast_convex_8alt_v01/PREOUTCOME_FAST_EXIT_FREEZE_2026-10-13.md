# FAST-CONVEX V1 — 8 ALTCOINS, FASTER CONFIRMED BARS + FORCED MAXIMUM HOLD
**UTC 2026-10-13 — frozen PRIOR to any FAST-CONVEX V1 historical performance outputs.**
RESEARCH_ONLY, diagnostic 2023–25 already studied in other long-hold families. The new fast exit hypothesis was designed *after* earlier V5 outcomes and BTC 5m scalp historical failure; **NO independent OOS, NO promotional trading authority** can be earned by this historical backtest. Do not touch 2026 protected holdout, live trade, orders, account, private API, wallets, spend, Render, merge main or post-outcome rule tuning.

## Scientific goal, not just more printed trades
Falsify the following primary claim: original LONG-only V5 RSI/BB/SMA200 pullback signals on faster 5m/15m/30m/1h bars, **plus a fixed time-bounded exit**, can generate more independent net profitable trades per week than the previously long-hold V5 while still winning after realistic costs. Having a short HOLD does NOT imply a high SIGNAL arrival rate. No forced entries or lowering V5 signal gates to inflate opportunities.

## Frozen assets and full common dates
ETHUSDT BNBUSDT SOLUSDT XRPUSDT DOGEUSDT ADAUSDT LINKUSDT AVAXUSDT, exactly eight, no dynamic substitution, selection or post-outcome addition. All same official Binance USD-M FUTURES BTC-Lab canonical official 5m market+independent 1h source for discrepancy census, publisher SHA256 ZIP CHECKSUM, historical fundingRate archive 2023-01-01..2025-12-31, market warmup 2022-11-01..2022-12-31. 333216 5m, 27768 1h, 3288 funding observations each, ZERO bar gaps allowed. API historical protected 2026 never used. Full 38 source market and 36 funding months per asset; one missing item = SOURCE_BLOCKED without backfilling or short sample.

## Exactly predefined experiment arms: 8 x 4 x 2 x 2 = 128
Timeframes 5m, 15m, 30m, 1h, all source reconstructed only from same official continuous 5m series. Fixed ORIGINAL recovered Parent V5 LONG entry score on CONFIRMED candle (SMA200 trend, BB20 z <-2, Wilder RSI14, volume>SMA20, score>=3). No RSI tweak, regime retune, alternate symbols or extra filters.
- **PRIMARY FAST-8H:** fixed +1.2% price take-profit, -0.6% initial price stop, exit at earliest first 5m candle OPEN timestamp >=8h from entry (adverse slippage on exit), one position at a time.
- **SENSITIVITY FAST-24H:** SAME +1.2% target/-0.6% stop, exit at earliest 5m OPEN >=24h from entry. These two horizons are independent preregistered alternatives; historical ranking alone does not select a winner or justify varying duration again.
- Entry only at FIRST 5m bar open strictly after strategy TF bar has CLOSED plus 1s witness margin = TF close+5m. Signal from 5m closed at t+5m means enter at t+10m, never price observed at signal candle close. One open position per scenario+symbol, no overlapping, no signal queue. 8H/24H exit at bar OPEN before stop/target checking on the time-expired bar. For earlier candles, gap-open stop/target applies at OPEN (if both improbable in gap, stop first), otherwise OHLC stop-before-target conservative; chosen exit includes negative slipped exit price. Always exclude open terminal trade from *closed trade* stats and record remaining marked liability/funding as of cutoff.
- Paper account initial 10000 USDT for each independent asset/TF/horizon/fees. Long 1x NOT leveraged, entry notional = 20% of available CASH equity before entry. 8 bps taker fee each side, assume adverse slippage BASE 2bps EACH SIDE vs STRESS 5bps EACH SIDE. Funding event timestamps from official original archive, applied LONG debit/credit with 5m market open price proxy (NOT actual settlement mark, not MEXC funding). No default maker fill. Stop may gap worse than -0.6. Apply fees/funding to cash and full net portfolio. Count closed-outcome years 2023/2024/2025 and *positive annual net*, not just cumulative result.
- 128 complete rows required; include 0-trade outcomes. For source fully complete, 8 independent GitHub matrix jobs; full 128-cell aggregation with exact manifest SHA/symbol/timeframe/horizon/cost identities; every complete trade ledger CSV and original model Git commit.

## Predeclared decision gates (not predictive if reached on old years)
A historical arm only receives FAST-HISTORICAL-CANDIDATE_DESCRIPTIVE if:
(A) BOTH BASE and STRESS net marked return >0 and PF>1.15 EACH
(B) BASE at least 52 closed trades/YEAR on 3y calendar = >=156 total, with >=52 each of 2023 2024 2025, ~>=1 closed/week
(C) 2023/24/25 all positive net closed PnL years (strict)
(D) 5m-low MTM max drawdown no worse than -20%
(E) historical BASE net CAGR at least 10%/yr (from 3y terminal marked)
(F) remove the top 3 winners from original closed ledger arithmetically and remaining closed PnL still >0 (NOT portfolio rebalance proof).
If no row passes all six conditions, verdict NO FAST DIAMOND IN THIS FROZEN FAMILY. No after-outcome threshold/risk/target/stop/holding/fee/period tweaking to rescue. The above strict gates prioritize actual economic turnover and robustness rather than just trade frequency.

Report every row whether good or bad: win/PF and counts per year, notional gross pre-fees, fees, funding, BASE/STRESS 5m-low drawdown, 3y terminal marked return/CAGR, annual closed cashflow, median/max hold hours, signal count/slot skips, top3 concentration, monthly and trade dates; blocked as blocked not zero PnL. Include explain that return/volatility based on Binance 5m OHLC proxy is NOT an actionable estimate for MEXC; ask/market data can miss fills, slippage exceed models. Past BTC 5m child FAST +0.75/-0.35/4h FAILED: this new distinct ex-ante alt hypothesis is NOT to be revived if similarly loses.
- No default-branch cron or false "live forward"; any positive descriptive family would need separately preregistered truly new point-in-time read-only independent source validation before real money.
