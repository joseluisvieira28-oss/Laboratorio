# TV DIAMOND HUNTER V0.1 — BTC VOLATILITY CORRELATION / EXLUX
Date: 2026-10-14 UTC
Status: USER_CSV_HISTORICAL_RECONCILED / COST_BASE_NEGATIVE / SOURCE_POINT_IN_TIME_UNPROVEN / NO_LIVE_GO.
Research-only. No orders, API keys, accounts, venue mutation, Render, main merge, paid resources, or opening protected Crypto Lab 2026 holdout.

## Operator evidence and custody
- Supplied formatted Pine v5 source with MPL 2.0 header © exlux and two TradingView screenshot settings (Inputs, Properties). Full exact original .pine byte source NOT obtained, hence no source SHA256 or independent compiler confirmation; do not republish third-party source in this public repo.
- Operator-exported TradingView CSV: Crypto_Volatility_Bitcoin_Correlation_Strategy_BINANCE_BTCUSDT_2026-10-14_76e19.csv; SHA256 `0ad68c94c28e4068a77f7043fc7a23d358ee8eb39ce65abe84bcec9f28f9dea6`.
- Screenshots: BINANCE:BTCUSDT trading chart named in export, source inputs COINBASE:BTCUSD (close and low), BITMEX:BVOL7D external historical BTC volatility index, VIXFix window 22, EMA 50. Initial virtual capital 1,000,000 USDT, fixed order size 1 BTC (quantity), pyramiding 1; 0% commission, 0 ticks slippage, margin long/short Infinity, orders next available tick, default four-tick broker emulator. Chart timeframe not directly pictured; 335/335 elapsed hours equal duration bars, strongly consistent with **1h**, needs screenshot confirmation.
- CSV 670 rows = 335 matched entry / exit pairs; **no open-position row in the supplied export** (does not prove real account flat). Do NOT double-count entry rows as trades, and do not use exit `Tamanho (valor)` as exit transactional notional: that column repeats the entry value.
- First entry 2024-01-03 08:00; last exit 2026-09-20 09:00 in exported time display; timezone not attested.

## Exact independent arithmetic over 335 exit rows
- ALL trades LONG, 100 winners, 235 losers, 0 zeros, 29.8507% win fraction.
- Sum of winning net PnL +217,797.15 USDT, losing -173,037.09 USDT, total **+44,760.06 USDT**, which exactly equals last cumulative PnL; 4.4760% of 1m initial virtual capital. Gross PF 1.258673.
- 2024: 122 exits, +41,619.88 USDT, PF 1.7282; 2025: 114 exits, -89.98 USDT, PF 0.99883; 2026 through September 20: 99 exits, +3,230.16 USDT, PF 1.08291. These spans are neither comparable full years nor independent 2026 holdout.
- Median closed hold 12 hourly bars, mean 25.30h, max 220h; largest recorded adverse excursion -6.65% of individual position. Closed-only marked-equity-path approximate drawdown -2.171%, ignoring within-position equity variation (not trustworthy MTM DD).
- Largest three winners: trade #104 +19,955.74 (2024-11-14), #210 +13,597.28 (2025-10-07), #325 +12,650.05 (2026-08-23). Sum **+46,203.07**, greater than overall +44,760.06. Static removal = -1,443.01 USDT, NOT causal rerun. Original profitability critically relies on right tail.
- Exact entry notional sum (1 BTC × every entry price): 26,702,325.39 USDT. Actual exit notional sum (1 BTC × every exit price): 26,747,085.45 USDT. Two-sided turnover: **53,449,410.84 USDT**.

## Frozen-ledger economic sensitivities (NO cost-inclusive portfolio simulation)
- BASE: 8bps commission per side + 2bps adverse slippage per side = 10bps/side; 53,449.41 USDT friction; +44,760.06 - 53,449.41 = **-8,689.35 USDT**, -0.869% of initial virtual equity.
- STRESS: 8bps commission/side +5bps adverse slippage/side = 13bps/side; 69,484.23 friction; net **-24,724.17 USDT**, -2.472%.
- At 8bps commission and zero slippage, net only **+2,000.53 USDT** pre-funding/spread. Illustrative 2bps fee +2bps slip/side -> +23,380.30 USDT; 2bps fee +5bps slip/side -> +7,345.47 USDT. These fee tiers are HYPOTHETICAL and have not been authenticated for user/venue.
- Static break-even **8.374285bps combined commission+slippage PER SIDE** with original frozen trades and sizes, excluding funding, actual spreads, market impact and execution/venue mismatches.
- By exit-year the BASE original unchanged ledger: 2024 +25,572.62, 2025 -23,201.31, 2026 to Sept -11,060.66 USDT. This points to major regime dependence.
- Zero fee/slip TradingView orders were based on Binance BTCUSDT, but source signals use Coinbase BTCUSD and BitMEX BVOL7D. No historical venue-executable fills or financing proven. Cost analysis is a STATIC accounting test, not an independent causal backtest or valid future PnL proof.

## Pine v5 causal review (code characteristics vs hypotheses)
1. Entry on every strategy evaluation where (a) WVI/VIXFix based on Coinbase high close over 22 bars minus Coinbase low is increasing, (b) BitMEX BVOL7D close > its prior chart-aligned value, and (c) Coinbase BTCUSD close is above Coinbase EMA50. Long-only with 1 BTC fixed size. EXIT when Coinbase BTCUSD close < its EMA50; no fixed max duration/target.
2. Title 'Correlation' is not a statistical correlation calculation; no Pearson, lead-lag, cross-correlation or independent predictive coefficient in source. BVOL7D is a HISTORICAL BTC volatility index (not necessarily implied options data or independent non-price signal); must test source provenance and incremental value vs VIXFix/EMA controls.
3. All three request.security calls omit explicit lookahead; documented default is lookahead_off, so no obvious blatant historical future-leak from lookahead_on. HOWEVER point-in-time same-bar availability/publication and bar confirmation of external BitMEX BVOL, Coinbase price and Binance venue have NOT been demonstrated. Real-time unconfirmed values can change; evaluate release timestamps and whether data align from different market sources. TradingView docs: https://www.tradingview.com/pine-script-docs/concepts/repainting/ .
4. Strategy uses bar-close signals and next tick fill in default emulator. BTCUSD Coinbase feed and BTCUSDT Binance instrument can have differing prices/timestamps; order on Binance chart is not a Coinbase trade, and BitMEX feed has independent clock/publishing schedule.
5. The repeated strategy.entry call while condition is true is normally capped by pyramiding=1, but it must not be confused with fresh independent episodes. No protective stop-loss, no exchange-stop confirmation, no liquidation or funding model. Exits only when source close < EMA50; hold max 220 hours. Fixed 1 BTC on 1m virtual capital is not equivalent to 100% equity deployment, and screenshot allows infinite margin.
6. External public BVOL7D index historical feed coverage/point-in-time settlement, publication frequency, stale bars and rights for redistribution still SOURCE_UNVERIFIED. TradingView symbol identifies BVOL7D as Bitcoin Historical Volatility Index: https://in.tradingview.com/symbols/BVOL7D/ ; BitMEX indexes docs: https://docs.bitmex.com/api-explorer/get-instruments . A profitable causal strategy cannot be inferred from importing an index whose timestamps have not been validated.

## Scientific decision (original as supplied)
**HISTORICAL GROSS WIN, COST-BASE FAIL, WINNER CONCENTRATED, POINT-IN-TIME BVOL SOURCE_BLOCKED, NOT A CERTIFIED ECONOMIC EDGE, NO_LIVE_GO**.
Exact 2024–2026 outcomes already seen: stop selecting VIXFix windows, long/short, EMA, BVOL timing and entry cadence using this CSV and calling those years unseen OOS. Keep original 2026 protected Lab holdout sealed; this provided public TradingView 2026 result is already known for this *strategy*.

## Next legitimate source-first investigation
- Obtain raw author original .pine file (byte-exact license/SHA) and screenshot with chart ticker + timeframe + report full Performance/Open Trades. These are optional for descriptive closeout but required for fully pinned reproduction.
- For BVOL7D, prove a publisher-sourced, legally available, time-indexed and point-in-time archival history with explicit timestamps as available to script. FREE public BitMEX instrument/index docs only prove endpoints exist, not complete hourly 2024–26 coverage or original TradingView feed parity. Set SOURCE_BLOCKED if inaccessible.
- Before any forward test, preregister independent 1h Coinbase BTCUSD source, BitMEX BVOL7D publication/freshness, Binance/MEXC executable BBO, market-specific fees, funding/mark, entry delay, and one-slot risk protections, with ABlation comparison of EMA+VIXFix baseline to full VIXFix+BVOL. Do not retrospectively optimize.
- Immediate resource decision: prioritize affordable source-integrity check before any broad new price backtest; BASE already negative and positive past return too concentrated to warrant live engineering.

Source CSV remains in user conversation only; report records hash and summary, not third-party Pine or raw source upload.
