# Crypto Lab — ChartArt MACD + SMA200 V1.0: operator Pine v2 and six TradingView CSV forensic audit
Audit UTC: 2026-10-14. PR #221. RESEARCH ONLY / NO MAIN MERGE / NO ORDERS / NO MICRO-LIVE GO.
Decision: PINE_SOURCE_REVIEWED_WITHOUT_COMPILE / FOUR_STATIC_COST_SURVIVORS_BUT_TAIL_DEPENDENT / NO INDEPENDENT EDGE CERTIFIED.

## Evidence provenance
Operator supplied the complete *formatted* Pine Script v2 text:
\`strategy("MACD + SMA 200 Strategy (by ChartArt)", shorttitle="CA_-_MACD_SMA_strategy", overlay=true)\`.
The header declares version 1.0, idea © ChartArt, dated 2015-11-30; code does not provide a specific source redistribution license. Do not mirror verbatim third-party Pine into public repository. Source arrived pasted with formatting, NOT as byte-exact .pine file, so no original exact-source SHA256, TradingView compiler receipt, or build-source-to-CSV equivalence is claimed.
Three operator screenshots show Binance BTCUSDT 1H chart with Pine parameters: source close, SMA MACD 12/26/9, SMA200, max intraday loss 50%; properties: starting equity 100,000 USDT, default order size 1 **contract/unit BTC**, pyramiding 1, margin long/short 1x, bar-close calculation, 4 pseudo-ticks per bar, 0% commissions, 0 tick slippage and no order-fill delay selected. Six separately exported Binance BTCUSDT trade-ledger CSVs (6 intervals) supplied; actual chart TF per file inferred via matching elapsed timestamp minutes/trade duration bars. No original market OHLCV or executed venue BBO receipt; no independent replay; timestamps not authenticated for UTC.

## Operator CSV SHA256 and coverage (raw bytes; entry/exit pair validation)
| TF inferred | CSV suffix | Raw SHA256 | Closed trades | OPEN as-of-export | Earliest closed trade ENTRY to last closed EXIT |
|---|---|---|---:|---:|---|
| 5m | 297a0 | b143cbeae33fce6e917131412d2488323074f58aa6705a54ec9cca75669cf9c9 | 58 | 1 | 2026-08-03 17:00 through 2026-10-13 06:05 |
| 15m | 2ada7 | e096b70542cf571c80688b5e34e875ec95122c5b6e33cb0b14c4f409a484e812 | 65 | 1 | 2026-03-04 15:45 through 2026-10-12 19:45 |
| 30m | 83f08 | 823a8205afe0f1125565e119dd9e92766d60b3ec452e2665759aa56208cfa079 | 91 | 1 | 2025-01-06 15:30 through 2026-10-13 02:00 |
| 1H | 87bf1 | 62bfad9b0c7abe65a548bc723cda96d4eb57afdbf3e31e7284dc5d9d97ff6dd6 | 72 | 1 | 2024-01-11 22:00 through 2026-10-14 08:00 |
| 2H | 41da9 | 783331e37d3c968ef93869b6aceda87bb7ec680e99260053a1cd800498ece4d8 | 57 | 1 | 2022-01-20 02:00 through 2026-09-30 22:00 |
| 4H | 2db09 | 429de38c97c70fb73228d87e0d9de01df17f72934dc7ab5707c88a1ec372c2f6 | 58 | 1 | 2017-10-13 00:00 through 2026-08-09 04:00 |
All full SHA256 digests above were computed from exact operator CSV bytes in current session. In all exports each completed trade matches quantity×entry/exit price differential within 0.015 USDT, unit position 1 BTC, 0 commissions, paired entry+exit duplicate accounting rows. Every TF contains one additional reported OPEN line: it is **not** a realized exit. On 2H and 4H, a minority of duration/time elapsed ratios deviate from exactly 120/240m; requires exchange/archive/calendar explanation rather than assuming perfect candle continuity.

## Frozen-row static accounting — NOT new dynamic market/backtest replay
Apply to each closed trade two exchanged legs \`notional = abs(q×entry_price)+abs(q×exit_price)\`; commission/slippage excluded from the original CSV. BASE = (8bps fee +2bps adverse slip) PER LEG, STRESS = (8+5bps) PER LEG. No real authenticated fee tier, funding, liquidation, spread history, order book or fill policy; costs alter possible future path and equity if replayed causally. Original baseline virtual equity 100,000 USDT with 1 BTC contract units per trade.
| TF | Closed | Gross original USDT | BASE static USDT | STRESS static USDT | Gross PF | Breakeven cost bps/leg |
|---|---:|---:|---:|---:|---:|---:|
| 5m | 58 | +15,630.76 | +6,956.24 | +4,353.88 | 1.758 | 18.019 |
| 15m | 65 | +22,564.54 | +13,250.58 | +10,456.39 | 1.463 | 24.227 |
| 30m | 91 | **−24,069.70** | **−40,014.70** | −44,798.20 | 0.856 | −15.095 |
| 1H | 72 | **−12,765.38** | **−24,570.75** | −28,112.36 | 0.934 | −10.813 |
| 2H | 57 | +17,632.49 | +10,593.90 | +8,482.32 | 1.110 | 25.051 |
| 4H | 58 | +37,797.23 | +33,240.11 | +31,872.98 | 1.242 | 82.941 |

## Tail-dependence sensitivity (remove top 3 gross winning COMPLETED trades AND their original costs; NOT a causal re-sim)
| TF positive BASE | Best 3 gross winners USDT | Remaining closed BASE USD |
|---|---:|---:|
| 5m | +19,185.30 | **−11,762.98** |
| 15m | +33,686.62 | **−19,996.45** |
| 2H | +73,707.91 | **−62,706.66** |
| 4H | +87,542.92 | **−53,918.66** |
All positive BASE variants are dominated by few unusual winner trades. This can be intrinsic to trend-following rather than inherently falsifying, but forbids a claim of routine cashflow or broad per-event expectancy. Conditional win fractions: 5m 24/58, 15m 23/65, 2H 18/57, 4H 20/58. Results are NOT comparable as continuous strategy income due to mismatched history lengths.

### Temporal and side asymmetry (original outcomes already exposed!)
- 5m CSV only ~Aug–Oct 2026 (58 closed); 15m ~Mar–Oct 2026 (65). **These are already viewed 2026 outcomes for THIS strategy** and cannot later be called unseen 2026 holdout. Preserve unrelated Crypto Lab protected 2026 holdout.
- 2H by exit year original gross: 2022 +2,045.59; 2023 −3,466.00; 2024 +56,652.27; 2025 **−54,462.12**; 2026 +16,862.75. Very strong regime instability.
- 4H by exit year original gross: 2018 −14,967.89; 2019 +6,193.97; 2020 −4,410.21; 2021 +37,914.91; 2022 +591.23; 2023 −6,428.21; 2024 +8,667.00; 2025 **−14,462.40**; 2026 +24,698.83. Full-history average not predictive annual income.
- Direction: 5m LONG +17,723.96 gross vs SHORT −2,093.20; 15m LONG +16,328.00 vs SHORT +6,236.54; 2H LONG +29,810.11 vs SHORT −12,177.62; 4H LONG +48,573.02 vs SHORT −10,775.79. Selecting only past best directions now = post-outcome parameter selection, **not new independent evidence**.
- 4H trade worst adverse excursion reported -76.42% of trade entry value, not directly account drawdown. 2H worst -31.01%, 1H -16.53%. None has hard per-position protective stop despite max_intraday_loss(50).
- Cumulative CSV closed trade PnL equals per-trade rounded total for each of six files. All contain one open position; 4H open can show large unrealized PnL, excluded from calculations.

## Pine v2 code audit — source-derived, not market-tested hypotheses
1. \`fastMA=sma(source,12)\`, \`slowMA=sma(source,26)\`, \`signal=sma(macd,9)\`: SMA-smoothed MACD, NOT usual EMA-smoothed MACD. \`hist=macd-signal\`, bull when \`crossover(hist,0) and macd>0 and fastMA>slowMA and close[26]>veryslowMA\`; bearish mirrored. \`macd>0\` and \`fastMA>slowMA\` are identical sign checks, not two independent confirmations. \`close[26]\` refers to historical price 26 chart bars ago compared to CURRENT SMA200; not the described "current price above SMA200" trend filter; not future lookahead.
2. \`backgroundcolor\` includes \`slowMA>veryslowMA\`/inverse, but colors/background/plots are VISUAL ONLY. Real \`strategy.entry\` conditions omit the current \`slowMA>veryslowMA\` check, so changing bar colors/background does not improve entry edge.
3. CRITICAL: \`strategy.entry("MACDLE", strategy.long, stop=low)\` / \`strategy.entry("MACDSE", strategy.short, stop=high)\` are STOP-ENTRY prices, not standing risk-stop exit protection. At the signal's close, \`low<=close<=high\`: long stop=low is already below/at current market price and short stop=high above/at price, normally already marketable, fills next available emulator tick/open. This is NOT evidence of a legitimate breakout stop and not a guaranteed fill. No \`strategy.exit\`, \`strategy.close\` or \`strategy.close_all\` calls in source except implicit risk function, hence ordinary exit by future opposite \`strategy.entry\` automatic reversal. Confirm legacy v2 broker behavior with original TradingView replay if proposed.
4. \`strategy.cancel("MACDLE" / "MACDSE")\` when current slowMA crosses side of SMA200 cancels only PENDING entry orders, NOT an open position and NOT a safety stop. Cancellation is before entry creation in code and cannot be treated as an invariant protective exit.
5. \`strategy.risk.max_intraday_loss(50,strategy.percent_of_equity)\` is a portfolio/day 50% catastrophic risk lock, not a 50% per-position stop-loss. It cancels pending orders, closes open positions and inhibits further entries until the relevant intraday session boundary **only once hit**, per TradingView documentation. Source has no per-trade hard stop; unbounded drawdown and real liquidation possible earlier with leverage.
6. \`strategy.entry\` default automatic reversal means OPEN 1 BTC LONG -> order to sell roughly 2 BTC -> resulting position 1 BTC SHORT. Real automated order router must plan that transition and validate actual position state; otherwise unsafe duplicate orders/exposure.
7. 2015 Pine v2 may not be equivalent to a modern Pine v6 port or 2026 tick/quote execution; zero friction, four synthetic intrabar ticks, no venue-specific funding; isolated broker simulator != futures live route.
8. No \`security()\` or request to external unconfirmed series in the supplied code, so obvious cross-symbol lookahead route absent. This does not establish historical integrity, absence of repaint from fill modelling, or independent economic edge.

Official Pine strategy simulation reference: https://www.tradingview.com/pine-script-docs/concepts/strategies/ .

## Frozen verdict / next legitimate action
- **30m/1H EXACT ORIGINAL under given zero-friction ledger: historically losing gross and BASE. Close this exact variant on these TFs.**
- **2H/4H: retrospective positive BASE+STRESS but multi-year low-trade, severe concentration, unprotected exposure, negative regimes: DESCRIPTIVE_ONLY, not robust or deployable.**
- **5m/15m: descriptive positive BASE+STRESS even with taker static cost, but only 2026 coverage, 58/65 completed trades and dominated by 3 winners; most promising *source candidates* only, NOT pre-registered independent edge.**
- **NO LIVE GO / NO CERTIFIED ECONOMIC EDGE across all six**. No post-outcome improvement by side selection, TF switches, new stop/limit semantics, MACD EMA change or adjustment of SMA200. Any change becomes separate CHILD and must be frozen prior to FUTURE outcomes, with genuine independent source and future forward; 2026 already viewed CSV cannot be repackaged as OOS.
- Forward validation only after (a) original Pine byte-identity/compiler check (b) professional venue-quoted account fee, funding, mark-price and 1 BTC position feasibility (c) separate coherent protective-stop specification with immutable child ID (d) truly future source and execution witness, frozen before outcomes. No real orders.
