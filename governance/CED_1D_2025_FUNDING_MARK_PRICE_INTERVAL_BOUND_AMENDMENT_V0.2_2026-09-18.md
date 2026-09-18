# CED-1D-V1 — 2025 FUNDING MARK-PRICE INTERVAL BOUND AMENDMENT — V0.2 — 2026-09-18

**Status:** FROZEN BEFORE MARK-PRICE ARCHIVE ACCESS AND BEFORE 2025 STRATEGY OUTCOMES  
**Purpose:** resolve the exact-settlement markPrice provenance gap without substituting an arbitrary point estimate.

## 1. Prior source state

The frozen Confirmation formula requires funding PnL proportional to the actual Binance markPrice at each funding settlement.

The primary REST route failed in GitHub Actions with HTTP 451. A prospectively frozen probe of fapi1/fapi2/fapi3/fapi4 preserved identical query semantics but found no usable exact-schema response: each mirror returned HTTP 202 with an empty body. No strategy signal, return, PnL, p-value, or routing metric was computed during those transport probes.

The official Binance Public Data monthly fundingRate archives subsequently passed checksum/CRC/schema provenance for AVAXUSDT and SOLUSDT 2025, but those archives expose fundingTime/fundingRate/fundingIntervalHours and do not expose the settlement markPrice.

## 2. Official mark-price source

Use Binance Public Data / Data Vision USD-M monthly 1m mark-price klines:

data/futures/um/monthly/markPriceKlines/{SYMBOL}/1m/{SYMBOL}-1m-{YYYY-MM}.zip

Scope:
- AVAXUSDT
- SOLUSDT
- 2025-01 through 2025-12 only

Every archive must pass its provider .CHECKSUM, ZIP CRC, expected member/schema, timestamp ordering, duplicate checks and month bounds.

No 2026 archive may be opened.

## 3. Settlement-minute binding

For each canonical funding record:
- normalize fundingTime to milliseconds using the already-verified funding archive normalization;
- settlement_minute_open = floor(fundingTime / 60000) * 60000;
- require exactly one official 1m markPrice kline whose open time equals settlement_minute_open;
- require finite positive OHLC and LOW <= OPEN,CLOSE <= HIGH.

If the exact settlement minute is absent or duplicated, that funding record is UNBOUND and funded Confirmation is fail-closed for every event depending on it.

No nearest-neighbour candle is allowed.

## 4. Funding PnL interval

The original formula is preserved:

funding_pnl = -direction * fundingRate * (markPrice / entry_price)

The exact markPrice is not point-identified, but the official mark-price candle gives a source-supported interval:

markPrice in [mark_low, mark_high].

For each settlement define:

coefficient = -direction * fundingRate / entry_price.

If coefficient >= 0:
- funding_pnl_lower = coefficient * mark_low
- funding_pnl_upper = coefficient * mark_high

If coefficient < 0:
- funding_pnl_lower = coefficient * mark_high
- funding_pnl_upper = coefficient * mark_low

Convert each bound to bps by multiplying by 10,000 and sum all settlement bounds inside the event's frozen open interval.

This creates a mathematically valid interval containing the funding PnL implied by the frozen formula, without selecting a favorable mark price.

## 5. Robust adjudication rule

For every metric that depends on funded net returns, compute both:
- CONSERVATIVE / LOWER funded path, using each event's funding lower bound;
- OPTIMISTIC / UPPER funded path, using each event's funding upper bound.

A target may receive a strict funded Confirmation PASS only if **all frozen V0.2 gates pass under the CONSERVATIVE path**.

A target may receive a strict funded economic/statistical FAIL if a required gate still fails under the OPTIMISTIC path.

If the frozen verdict differs between lower and upper paths, classification is:
FUNDING_MARK_PRICE_INTERVAL_AMBIGUOUS / NO TIER CHANGE.

No midpoint, open, close, VWAP, interpolation, nearest-neighbour or cherry-picked mark price may control the verdict.

## 6. Multiplicity and stability

The exact frozen 8-cell Holm family remains unchanged.

Both lower and upper paths must use:
- identical events;
- identical complete signal-week eligibility;
- identical 9,999 weekly bootstrap draws and seed 20260908;
- identical Holm family;
- identical sample, temporal, concentration, neighbour and leave-one-month-out rules.

No outcome may choose which path is primary. Conservative lower is always primary for a PASS; optimistic upper is always the strongest permissible case for determining an unavoidable FAIL.

## 7. Scope boundary

This amendment changes only uncertainty treatment for the missing point-identification of settlement markPrice.

It does not change:
- signals;
- assets;
- lookbacks;
- horizons;
- direction;
- entry/exit timestamps;
- funding times/rates;
- BASE14/STRESS20 costs;
- sample floors;
- statistical thresholds;
- target population;
- neighbour family;
- 2025 interval.

Execution remains reference-price research only. No live trading, orders, exchange mutation, wallets, alerts/webhooks, 2026 access or main merge.
