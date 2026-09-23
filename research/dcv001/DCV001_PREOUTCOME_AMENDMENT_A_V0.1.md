# DCV-001 — PRE-OUTCOME AMENDMENT A V0.1

Date: 2026-09-23
State when frozen: SOURCE_GATE_V0.1 passed; no funding/OI/price values, returns, regression coefficients, PnL or protected-period outcomes had been opened.

This amendment resolves implementation semantics that were not fully explicit in the parent authority. It changes no observed economic result because none has been opened.

## 1. Calendar-year attribution

For the Discovery stability gate, each eligible row belongs to the calendar year of its information day D.

## 2. Missing metrics

A missing daily metrics archive is never interpolated. The corresponding information day cannot be model-eligible. Source census may pass only within the already-frozen >=99% archive-day coverage requirement.

## 3. Funding

Funding_D is the sum of all valid official funding observations timestamped inside day D. No forward fill or synthetic funding event is allowed. A source gap >12 hours is a full-source census failure as already frozen.

## 4. Exact 7-day realized-volatility window

RV7_D requires a continuous hourly mark-price chain from 00:00 UTC on D-6 through 23:00 UTC on D, plus the immediately preceding 23:00 UTC mark close needed to form the first hourly log return.

Therefore each eligible RV7_D contains exactly 168 one-hour log returns. Any missing hour in that required chain makes D ineligible. A multi-hour price move must never be treated as a one-hour return.

## 5. Daily mark close

mark_close_D is the 23:00 UTC 1h mark-price candle close for D. If that exact hourly candle is absent, D is not model-eligible. Do not substitute an earlier hour.

## 6. OI daily point

OI_D is the last valid metrics row by create_time whose timestamp lies inside D. If multiple rows share that final create_time, the source census fails as duplicate/ambiguous. No average or alternative intraday point is allowed.

## 7. Ninety-day normalization

"previous 90 valid information days" means the immediately preceding 90 dates for which all three raw predictors (funding_D, oi_change_D and RV7_D) are defined before causal z-scoring. The current day D never contributes to its own normalization mean/std.

## 8. Moving-block bootstrap

Blocks are drawn from the chronological eligible-row sequence, length 7, without circular wraparound. Random block starts are sampled with replacement until at least N observations are accumulated; the sample is truncated to N.

The complete row (outcome and all frozen predictors/interactions) is resampled as one unit.

Singular bootstrap design matrices are discarded and counted. Parent minimum 4,750 valid / 5,000 remains binding.

## 9. 2024 source firewall

Full 2024 archive acquisition and economic parsing is forbidden unless every 2021-2023 Discovery gate passes. The four fixed 2024 objects already accessed by SOURCE_GATE_V0.1 were source-only schema/timestamp/checksum probes and opened no economic values.

## 10. Raw-cache boundary

The full-source census may download verified raw ZIP bytes locally in the ephemeral GitHub runner, but before SOURCE_CENSUS_PASS it may parse only filenames, schemas, timestamps, row counts, ZIP integrity and checksums. Funding/OI/price numeric values may be parsed only after the full census passes.

No raw market corpus is committed to GitHub.
