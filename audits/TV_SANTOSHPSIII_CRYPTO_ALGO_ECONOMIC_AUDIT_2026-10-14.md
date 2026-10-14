# TradingView Hunter — Crypto Algo BTCUSDT forensic audit
Date 2026-10-14. SCIENCE ONLY / BASE AFTER-COST FAIL / NO LIVE GO. PR #221. No main merge.

## Evidence custody
Operator supplied formatted Pine v5, three screenshots and CSV @santoshpsiii_Crypto_Algo_BINANCE_BTCUSDT_2026-10-14_b764e.csv.
CSV SHA256: e171292614e2306c576c4c82c11063e403a8fbb6aabda4762496f76df7dd4abb.
682 rows = 341 paired entry/exit-like rows, but trade #341 shows Abertura (OPEN, not realized exit). Exactly 340 closed plus 1 currently open LONG. No exact Pine source bytes or license proved; no third-party script republished.
Screenshot properties: 1000 USDT initial, 100% equity order sizing, pyramiding=1, 0 commission, 0 ticks slippage, margin long/short Infinity, default broker four ticks/bar. Pine input SuperTrend 10/3, Bollinger bands 20/2, width moving-average 20. Timestamp gaps for every one of the 340 closed trades match duration bars as WHOLE HOURS, consistent with 1h chart; raw chart identity not yet confirmed.

## Measured original zero-cost ledger
First entry 2024-01-03, latest closed exit 2026-10-09; currently open LONG entry 2026-10-13.
340 closed: 122 winners, 218 losers, zero exactly flat; gross winning +4567.76, gross losses -4220.71 USDT; PF 1.08223; win rate 35.88%.
Sum of 2-decimal per-trade rounded closed PnL +347.05 USDT; native TradingView cumulative closed PnL +346.99 USDT (+34.70% on 1000 initial), 0.06 difference due cumulative vs per-trade rounding. Remaining OPEN LONG unrealized +3.70 USDT, marked total +350.69 (+35.07%); DO NOT treat that trade as closed profit.
Exit-year PnL: 2024 117 trades +312.95 PF1.201; 2025 129 -163.83 PF0.904; 2026-to-Oct09 94 +197.93 PF1.206. Not independent OOS, 2026 already exposed for this particular script.
LONG 165 closed +516.98; SHORT 175 -169.93. Selecting the positive direction after observing results is post-hoc selection, not a new OOS pass.
97 SHORT exits labeled Open Long (automatic opposite entry reversal) sum -292.83, while 78 normal Close Short exits +122.90.
Median hold 30.5 completed 1h bars, max 205; reported worst adverse excursion -6.65% of trade notional. PnL price difference x contract qty reconciles within 0.005 per trade.

## Static executed-leg fee sensitivity — not a dynamic backtest
Total ENTRY quantity x price 423344.4048437 USDT. Total actual closed EXIT quantity x price 424031.3154731 USDT. Combined leg notional 847375.7203168.
BASE (8 basis points fees + 2 basis points adverse slippage EACH SIDE): fixed-trade cost 847.38; net from individually rounded trades +347.05 - 847.38 = -500.33 USDT, or -500.39 using native TradingView cumulative.
STRESS (8 fee +5 slip EACH SIDE): fixed-trade cost 1101.59, net -754.54 USDT (native cumulative -754.60).
Illustrative optimistic 2 fee +2 slip each side: cost 338.95, net +8.10, excluding funding, real spread/impact. 0 fee +2 slip each side => +177.57; zero fee +5 slip each side => -76.64. Static break-even total fee+slippage combined = 4.0956 basis points PER SIDE with same position sizes and timestamps. User actual venue fee tier not authenticated.
ALL sensitivities freeze the original positions/timing. They are accounting, not causal portfolio replays or actual broker fills. Original report is WITHOUT ANY fees or slip, funding absent.

## Pine implementation and concerns
1. Trades ONLY on local chart SuperTrend direction flip when Bollinger BAND WIDTH exceeds its own 20-period SMA. Exits occur on opposite SuperTrend flip even when BB width filter is false. No evidence of a new cross-timeframe information edge.
2. SuperTrend 5m, 15m, 1h and 4h returned by request.security lookahead_off are used only for dashboard table: they are NOT present in entry/exit logical conditions. Dashboard may fluctuate on still unconfirmed HTF realtime bars, but it does NOT control this version's trading orders.
3. NO stop-loss, no take-profit, no max hold and no standing order protection. strategy.close issues market exit after directional flip. Original max completed 205h hold. These are material risks for automated futures.
4. Opposite SuperTrend flip can send both entry and exit alerts in same bar, and strategy.entry auto-reverses contrary positions. Sending alerts independently to a real execution bot risks duplicate or out-of-order instructions absent position reconciliation.
5. Chart defaults 100% virtual equity exposure and Infinity margin, not a tested executable Futures broker margin policy. Four pseudo-tick broker emulator, 0 fees, 0 slippage, no bid/ask or exact funding historical source.
6. Neither actual observed liquidation path nor MEXC/other venue fees, order lot, funding, protections, gaps, restarts nor broker fills have been verified. TradingView Pine documented: https://www.tradingview.com/pine-script-docs/concepts/strategies/ ; https://www.tradingview.com/pine-script-docs/concepts/other-timeframes-and-data/ .

## Freeze/verdict
Original source under screenshot settings: HISTORICAL GROSS POSITIVE, CONSERVATIVE COST MODEL NEGATIVE, NO VERIFIED NET EDGE, NO LIVE AUTHORITY. 2024-2026 original outcomes were opened by the supplied operator CSV: do not select LONG-only, new ATR/BBW, timeframe, stops or 2026 subsection post-outcome and then mislabel as independent OOS. Other protected Crypto Lab 2026 holdout is still closed.
Next input: raw complete .pine file (hash/licensing) plus TradingView ticker and chart 1h confirmation, optional broker real fee evidence at later stage without secrets. Any new safer executable STOP policy or candidate must be frozen as a distinct child before FUTURE outcomes, with source and unit accounting then read-only forward. No trading or main merge.