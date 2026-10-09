# V0.3 timestamp-granularity source amendment — 2026-10-09

Attempt 37896763252 successfully passed source/identity and original cost-layer checks but failed with `OPEN_TRADES_AT_PERIOD_BOUNDARY` in the event sorter; original 1h parent bar-model can OPEN and STOP inside the same 1-hour bar and timestamps both at the bar's opening time (`entry_t == exit_t`). This is a timestamp-granularity distinction, NOT a new market rule.

Technical source-preserving repair:
1. Preserve original PnL, fees, funding, trade list, symbol, 1h entry/exit timestamps, and fixed low-risk capital budgets.
2. At a shared timestamp, process CLOSEs of positions opened in earlier bars first; process new bar-OPEN entries next; process same-bar entry-and-stop closes last. `same_bar_stop_exit` has event priority 2 vs normal exit 0 and new entry 1. This follows the simulation's source code: pending entry executes at 1h OPEN, then stop can hit at 1h LOW.
3. Track and report same-bar 1h stop counts per layer and asset. Without intrahour tick/quote timestamps, this is a deterministic **bar-model** assumption, NOT proof of executable stop/fill or order-of-operations across symbols.
4. All research verdicts retain HISTORICAL_SCIENCE_SCOPE_LIMITED locally and GENERALIZATION_FAIL globally, whatever this sizing study returns. No drawdown estimate from closed-only equity is promoted as marked drawdown.

No post-outcome threshold changes, modified scientific costs, filters, traded orders, or hidden duplicate/zero-pnl observations.
