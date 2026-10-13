# EXPLORATORY PAYOFF SWEEP — 2R / 3R / 4R / 5R
**Frozen exploratory comparison before sweep execution:** 2026-10-13.

## Governance / purpose
Explore the user's "many small losses, a few bucket-size wins" thesis across four *different* fixed reward-to-planned-risk ratios. Comparison is **in-sample descriptive research only**, not confirmation; the historical BTC source was already studied to develop 4R. No 2026 holdout, live trading, account access, wallet, authenticated exchange, money, merge to main, or modification of the authoritative frozen PAYOFF-40-10-BTC-001 replay. Never select a winner as validated from this historical sweep.

## Exactly fixed before sweep
- **BTC-CONVEX causal LONG entries:** same exact code from parent branch `research/payoff-40-10-btc-engine-2026-10-13`, one active trade, confirmed 1h UTC signal, next-hour open entry, no intrabar foreknowledge, same re-entry rules, no other signal filtering.
- **Capital/execution:** initial equity 10,489.94 USDT, 10% of current equity initial *hypothetical isolated margin* per PAYOFF position, 2x leverage =20% initial notional; never add margin; no simultaneous positions.
- **Exit barriers anchored on initial entry FILL:** loss stop stays at net nominal -10% of initial margin under **0.08% entry+exit notional fee each side (no slippage)**, identical for all four targets. Gain target is nominal +20%, +30%, +40%, or +50% of initial margin (2R/3R/4R/5R). Formula with `f=0.0008`, `L=2`:
  `price_target/entry_fill = 1 + (target_net_on_margin / L + 2f)/(1-f)`;
  `price_stop/entry_fill = 1 + (-0.10/L + 2f)/(1-f)`.
- **Everything else unchanged**: 60 UTC calendar-day time-exit at first subsequent 1h open; stop-first for simultaneous hourly high/low touch; opening gap fill; Binance official USD-M public BTC 1h OHLC + mark bars + funding historical proxy, no fabricated bars/records; funding settlement semantics original; liquidation tier proxy unverified.
- BASE execution fee=0.08%/side, adverse slippage 2bps/side. STRESS fee=0.10%/side, adverse slippage 5bps/side. **Do not change price barriers by scenario**. Both scenarios account for funding as in parent replay.
- **Dates:** 2020-03-01 through 2025-12-31 inclusive (2020-02 warm-up); no new 2026 observations. Every ratio uses EXACT same public source manifest, same feature computations and same event replay, with only target level varied.
- **Compare** win fraction, TARGET vs STOP vs TIME_EXIT, gross/after-cost profit factor, final equity return, closed and approximate mark-to-market drawdown, funding, actual realized mean positive/negative margin payoff, yearly equity returns, capital time in market, wins/loss tails, plus Parent normalized exposure comparator. Report the complete ranking with adverse/flat results and discrepancies; do NOT optimize targets further using historical outcomes.
- **One mandatory regression anchor:** rerunning 4R in the sweep under BASE must return 111 closed, 30 positive, closed-equity return `0.283296092471792`, and under STRESS return `0.26323957585754676`; if mismatched, FAIL_CLOSED rather than rank the new ratios. Prior validated receipt: GitHub Actions run 38354594319.
- **Economic authority:** even top historical result is `EXPLORATORY_IN_SAMPLE_ZERO_PROMOTION`. Actual fees/order book, mark-liquidation, exchange min lot/notional, slippage and long-run portfolio diversification remain unknown. Forward independently frozen *after* discovery required for any economic promotion.

Keep 4R's existing code and freeze untouched. Add standalone exploratory runner and QA/workflow on this distinct branch only.
