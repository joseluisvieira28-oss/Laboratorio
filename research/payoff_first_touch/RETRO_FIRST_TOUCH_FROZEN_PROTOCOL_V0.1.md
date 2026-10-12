# PAYOFF-FIRST-TOUCH-RETRO-001 — Descriptive protocol freeze, V0.1

Date: 2026-10-12. Research-only, no account/exchange authenticated read, no orders, no execution, no 2026 holdout opening.

## Authority and interpretation

Parent source = PR #166 commit `98454c4516b69fae54526ed37600895f0b6063a9`. This experiment **does not test an independently pre-registered trading strategy**. BTC-CONVEX seed entry times and results were known when this protocol was written. Therefore, all outputs are **RETROSPECTIVE_DIAGNOSTIC_ONLY** and award **ZERO_PROMOTION_CREDIT**, regardless of sign.

Question: For already published BTC 1h seed entries, was a synthetic *price barrier* equivalent to +40% of initial margin at 2× touched before a barrier equivalent to -10% of initial margin? Stop-first vs target-first is chronological; the original strategy's trailing rule is not being modified or retested.

## Frozen units and barrier math

Set initial margin M > 0, initial notional N = 2M, constant quantity q, price change x, synthetic assumed taker fee f=0.0008 both entry and exit; fee on actual respective entry/exit notionals, no funding/slippage in price-barrier diagnostic.

`netPnL/M = 2 * ((1-f)*x-2*f)`.

`x_target=(0.40/2+2*f)/(1-f) = 0.20176140912730184`.
`x_stop=(-0.10/2+2*f)/(1-f) = -0.04843875100080064`.

Fees f represent an **illustrative observed MEXC schedule**, not the historic Pine ledger's 0.1% per side; the source/bar is Binance BTCUSDT USD-M perpetual **proxy**, not evidence of fillable MEXC quotes.

## Frozen data universe and first-touch rules

- Source ledger: pinned `research/margin_payoff_audit/evidence/btc-convex-trend-capture-001-v0.1/labs/btc-convex-trend-capture-001/evidence/SEED_TRADE_LEDGER_1H_V0.1.csv.gz.b64`; SHA256 decoded CSV `ca6903faf7d4f42a40d0b76d4e7d106edec36007075d2da4600c4800b08583fa`.
- Universe: already-open **closed** BTC 1h seed trades with entry and original exit strictly before `2026-01-01T00:00:00Z`. No 2026 candle download, no future periods.
- Source: Binance's public official USD-M futures 1h **monthly klines** and monthly CHECKSUM files, `https://data.binance.vision/data/futures/um/monthly/klines/BTCUSDT/1h/BTCUSDT-1h-YYYY-MM.zip`. SHA256 verify each downloaded ZIP against corresponding official CHECKSUM and preserve per-month manifests. If missing, return SOURCE_BLOCKED; do not fabricate candles.
- UTC 1h timestamps; no gap filling. For each *original* position's `entry_dt` through (not including) its `exit_dt`, evaluate barrier hits against only then-open bars. Exclude end timestamp bar. If exact source entry-fill timestamp semantics are uncertain, report BOTH (A) entry-hour inclusive and (B) from following full hour. Do not select whichever looks better.
- Trade entry price must be explicitly present in the supplied ledger; otherwise classify SOURCE_ENTRY_PRICE_MISSING (not silently substitute candle price). Divergences or venue mismatch prevent promotion.
- Crossing stop and target on same hourly OHLC => AMBIGUOUS_SAME_BAR. Gap across barrier at bar open => GAP_FIRST (not guaranteed fill). Missing bar => MISSING_PATH. Path without barrier before original exit => NEITHER_WITHIN_ORIGINAL_HOLD / CENSORED. Never convert this into a losing exit or assume trades can remain held past the original exit.
- No position chaining, portfolio compounding, liquidation claims, wallet or account economics. Original entries are **not re-generated** after hypothetical changes of exits: original trade sequence is endogenous, hence a counterfactual entry-path classification **cannot** equal strategy PnL.
- The 2026 original open trade and already open 2026 seed exits are excluded. No new forward results or 2025 Donchian holdout opened.

## Frozen decision rule

Three classes of reporting:
- `DATA_SOURCE_BLOCKED`: archive/checksums/ledger timestamp cannot be reconstructed.
- `RETRO_FIRST_TOUCH_DESCRIPTIVE_READY`: valid complete and timestamp-aligned entry paths for supported subset. Report exact counts, ambiguities, censoring, unknown fills and note selection bias.
- `TARGET_40_10_NOT_ESTABLISHED`: irrespective of retrospective first-touch results, absent fully independent forward/OOS with full cost and execution receipts, the user's proposed **economic strategy** is not established. This is **not NO_EDGE** for parent BTC-CONVEX.

**No scientific GO is possible from this retrospective dataset**, no post-outcome tuning, no leverage sweep, no new strategy signal/exit/target adaptation. Publish full results including unfavorable runs. Leave PR draft and main untouched.
