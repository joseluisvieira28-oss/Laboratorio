# CONVEX V03B — BNB4H FULL ELIGIBLE HISTORICAL L1 SOURCE VERDICT (17 OCT 2026)

Source-only execution [GitHub Actions #39026521571](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/39026521571), BNBUSDT job 117378466712 **SUCCESS**. This is research-only and does NOT validate BNB trading profitability on any venue.

Immutable original 2023–25 V5 `BNBUSDT 4h BASE` entries from source run 38432883246, within fixed public Binance bookTicker 2023-05-16 to 2024-03-30 UTC period: EXACT 6 original entry timestamps; all included without picking by PnL. Source ZIP publisher SHA-checked when valid, two-sided event data, historical ask-side volume at original 5m entry timestamp, no lookahead. One-stop no sample rescue.

- `BOOK_QUOTE_CAUSAL_CANDIDATE` = **2/6**
- `TOP_OF_BOOK_SIZE_INSUFFICIENT` = **1/6**
- `SOURCE_BLOCKED` = **3/6** (original 2024-01-08, 2024-03-05 and 2024-03-19 probe days; see archived receipt for specific exception classes; DO NOT invent an error cause)
- Fresh quote coverage = **3/6 = 50%** (< frozen >=95% source gate).
- Original modeled trade size covered at best ask for 2/3 fresh quotes = **66.7%** (< frozen >=90% capacity gate).
- Three valid historical quotes differ from original simulated BASE entry by median **-1.6748 bps**, range [-1.9996,-1.5835] bps, but tiny conditional sample and never proof of a fill/entry after queue/impact.
- All selected original dates, including failures, retained in denominator. Original historical price indicator and 2026 protected holdout not mutated.

**SCIENTIFIC VERDICT: SOURCE_ROUTE_INSUFFICIENT_FOR_FULL_HISTORICAL_EXECUTION_GATE**. This kills the claim that this one free Binance event archive suffices to certify all original BNB V5 entry executions. It does NOT kill the BNB4H strategy or prove cross-venue execution feasibility. No LIVE GO.
