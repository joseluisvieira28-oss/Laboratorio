# V05E — EXACT TWO ORIGINAL V5 EXIT DAYS — SOURCE-ONLY PRE-LOOKUP FREEZE (19 Oct 2026)

Before reading closed-trade rows, select exactly two previously fixed original Binance V5 LONG entries:
- SOLUSDT 1h BASE open_t=1685376300000 (2023-05-29 16:05:00 UTC), modeled qty 104.79202011433037 SOL.
- BNBUSDT 4h BASE open_t=1698854700000 (2023-11-01 16:05:00 UTC), modeled qty 8.822493532731512 BNB.

Look up ONLY these exact two rows in original canonical closed trade artefacts `CONVEX-8ALT-COMMON-3YEAR-SOLUSDT-RESEARCH` and `CONVEX-8ALT-COMMON-3YEAR-BNBUSDT-RESEARCH` from original successful GitHub Actions run 38432883246. Require original trade counts 84/28, exactly one matching original timestamp, quantity parity, original source status, SHA custody, no source replacement.

Disclose only frozen original closed `close_t` UTC timestamp and exit UTC **calendar date**, original `exit_reason` if present and row SHA256, NO PnL, NO optimization, NO new trades or alternative dates. A stop intrabar original `close_t` timestamp is NOT actual broker trigger time, does not prove fill, and may need the preceding 5m candle's whole window. If entry still open or source missing -> SOURCE_BLOCKED and no substitution.

Purpose: request only the two **additional official OKX historical 400-level** exit-date books from operator at user-authorized manual portal, to build a properly separate pre-outcome bid-side exit source gate in future. NOT reusing 2023 T0 buy ASK for future exit. Do not download new market books, trade, use account, merge main, change original V5, open protected 2026 holdout or claim alpha. The original observed histories have zero untouched OOS credit.
