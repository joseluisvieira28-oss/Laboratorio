# HV SPIKE — BTC/USDT — FIRST OPERATOR CSV + PINE AUDIT
Date: 2026-10-14 UTC
Status: ORIGINAL_HISTORICAL_FAIL / BRACKET_LIFECYCLE_CRITICAL / NO_LIVE_GO
Research-only, PR #221. No main merge, real execution, wallet, trading, protected holdout opening.

## Operator material and provenance
The operator submitted a formatted full Pine v6 script, three screenshots (Inputs, Properties and Style), and a TradingView BTCUSDT CSV export. Exact raw Pine-script bytes and script compiler run have NOT been supplied, so no exact Pine SHA-256 is claimed; do not publish the external Pine source in this public repository pending license verification.

Export CSV SHA-256: fd3eaa634b02cb02045ea4019ed866332e18fc4c112d5d882e90fa4dcb8cddac.
CSV 376 data rows = 188 trade exit + 188 duplicate trade entry accounting rows; only count EXIT for PnL.
Screenshot properties: initial virtual equity 100,000 USDT, default trade 10% equity, pyramiding=1, long/short margin 1x, commission 0%, slippage 0 ticks, close-of-bar calculation, default four emulator ticks per candle, 1-tick order-fill delay. Inputs length30, HVP lookback252, threshold50%, ATR14, stop1xATR, target2xATR, HV Spike mode.
Exact chart timeframe not shown; first 121-bar trade lasts exactly 121 hours, compatible with 1h but not independently verified.

## Exact reported economic audit
- TradingView displayed cumulative terminal net PnL: -5,688.27 USDT (-5.69%). Sum of 188 separately rounded trade PnL: -5,688.31 (0.04 USDT rounding difference).
- Win: 60 (gross +20,419.47 USDT); loss: 74 (gross -26,107.78 USDT); zero PnL: 54. Profit factor 0.7821. 61/188 trades duration zero bars (including 54 zero PnL).
- 2024 calendar exit year 61 trades +3,626.23 USDT PF1.4885; 2025 72 trades -6,154.53 PF0.4673; 2026 through Oct 13 55 trades -3,160.01 PF0.5569. These are not independent held-out segments.
- Long exits 97 -1,289.47 USDT; short exits 91 -4,398.84.
- Exit labeled "Exit Long": 68, +6,956.74; labeled "Exit Short": 54, +6,243.20; exit labeled "Long" on opposite order: 37, -10,642.04; "Short" on opposite order: 29, -8,246.21. Reversal-driven exit subset net -18,888.25. These labels are evidence of simulator route, not complete order-fill trace.
- Exit-only closed-equity observed peak-to-trough from initial capital ~-11.50%, ignoring intra-trade open drawdown.
- All exported commission cells zero. Thus **the original implementation loses money before any trading friction**.
- Entry traded notional across 188 10%-size exposures = 1,863,527.45 USDT; real quantity x exit price sum = 1,866,636.85. Static counterfactual 8bps fee/side ~2,984.13 USDT, BASE 2bps slippage/side ~746.03, STRESS 5bps/side ~1,865.08. Freeze rows/sizes: implied BASE terminal ~-9,418.43 USDT (-9.42% vs initial); STRESS ~-10,537.48 (-10.54%). Not independent replay and no actual venue fee/fill authentication. Raw CSV not published.

## Causal code findings
1. CRITICAL: Computes entryPrice from strategy.position_avg_price before calling strategy.entry, then sends strategy.exit with stop and limit derived from that variable **only within the new-entry signal branch**. On flat signal calculation, position_avg_price is na, because new order fills only afterward under default broker simulation. Therefore valid bracket prices are NOT reliably established for the newly opened position; source has no recalculation or unconditional next-bar exit-order path. When already in a trade, a new opposite signal may use the OLD position's average price to calculate the NEXT position's bracket. Exact fills need TradingView emulator trace; never assume working protective stop. Official documentation: https://www.tradingview.com/pine-script-docs/faq/strategies/ .
2. HIGH: New HVP activation resets tradeTaken false even when position is open, then opposite strategy.entry can auto-reverse position. CSV shows 66 exit rows with opposite entry labels. 54 zero-PnL exits and 61 zero-bar exits warrant a targeted state-machine test, rather than a causality claim about every individual trade.
3. HIGH: extendBars=10 controls line drawing only, not trigger expiry. Once set, spike range and trigger prices persist until a new activation. A trade may use an old regime level.
4. MEDIUM: '50%' reversal price guards are automatically satisfied once close has re-entered the original spikeHigh/spikeLow interval: close>spikeLow-0.5*range and close<spikeHigh+0.5*range. They are redundant, not impossible.
5. MEDIUM: HV annualization sqrt(365/per), where per=1 for ALL intraday TF, underannualizes e.g. hourly sample-vol; **ranking is invariant under constant positive scaling on one TF**, so not enough to condemn percentile crossing itself. Current HV is included in its own percentile window; early history requires proper warmup.
6. MEDIUM: hour/minute used by session mode originate in exchange timezone; simple integer hour offset cannot establish universal UTC/DST correctness. User default uses HV Spike, not sessions.
7. CRITICAL economics: no commission, no slippage and broker emulator 4-tick bars; missing actual historical bid/ask, funding, real fill/slippage, stop recoverability, order min and margin. No evidence of executable net edge.
8. No request.security apparent in supplied source; absence of this obvious lookahead mechanism does not prove full non-repainting causality.

## Scientific disposition and next steps
Original exact script under exported settings = historical economic failure + unreliable stop bracket => **REJECT current variant for forward/live allocation / NO MICRO-LIVE GO**. Do NOT rescue by adjusting threshold or ATR on the already observed 2024-2026 outcomes, then call it independent OOS. The user's exported CSV already exposes 2026 performance of THIS script: it cannot be treated as untouched independent 2026 for this family; unrelated Crypto Lab protected 2026 holdout is kept closed.

Next assistance: get raw downloadable .pine/.txt (exact source SHA + license), a chart screenshot showing symbol/timeframe + report overall performance/open trades. Build standalone synthetic cases (flat entry, new protective bracket, opposite signal with existing position, same-bar exit, stale trigger >10 bars, cross into range), and separately freeze HV-SPIKE-STOP-FIX-V0.1 as a DIFFERENT strategy before unobserved prospective trials. Do not generate new market outcomes without a valid protocol.
