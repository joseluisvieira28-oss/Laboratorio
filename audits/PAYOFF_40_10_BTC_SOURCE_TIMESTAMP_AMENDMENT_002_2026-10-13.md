# PAYOFF BTC SOURCE AMENDMENT 002 — funding timestamp precision (2026-10-13)

Source-only failures prior to opening any historical economic replay:
- Run 38353963429: monthly mark hours missing starting 2021-07-01, corrected by exact SHA256 verified daily mark files.
- Run 38354295249: all source components loaded and month+daily mark coverage passed; `SOURCE_BLOCKED: OFFGRID_FUNDING_TIMESTAMP` with first raw offsets +1,+2,+1,+9 milliseconds vs UTC hour boundaries.

**Pre-outcome technical correction:** For each public official archive funding `calc_time`, normalize to the nearest UTC hour **only when the absolute deviation is <=1000 milliseconds**. If the deviation is larger, fail closed. Funding rate, observation count and period stay intact. On duplicate normalized timestamps, allow only byte-equal numeric rates, otherwise fail closed. Report normalization count and max deviation. No interpolation, change of settlement hour, or substitution of market values.

This matches the 1-second public funding normalization boundary used in BTC-CONVEX cross-asset source gates (read-only precision handling), not a new trading hypothesis.

All PAYOFF signal, target, stop, leverage, sizing, slippage, funding sign, entry/exit, conservative ordering, 60-day expiry and date-universe specifications are immutable. 2026 holdout unopened. Historical outputs remain diagnostic-only. No capital, live orders, account access, source retuning after PnL, or main merge.
