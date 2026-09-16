# TFG-PBR01-4H-XVENUE-BINANCE-001 — Source Remediation V0.1

Date: 2026-09-16

## State before remediation

- Frozen authority commit: `6703e683f59d5d5c322f119895d6d3e89a88857f`.
- First run: `35124332645`.
- Source gate classification: `SOURCE_OR_DATA_BLOCKED`.
- Accepted archives: 132/138.
- All six rejected archives were March 2023 and failed on the same Binance Spot timestamp, open time `1679661000000` (2023-03-24 12:30 UTC).
- The open time is a valid 15-minute UTC boundary. The source validator rejected the row because its raw `close_time` did not equal `open_time + 15m - 1ms`.
- No signal, forward outcome, trade PnL, expectancy, profit factor, bootstrap or cross-venue classification was computed. The workflow skipped all outcome steps.

## External source context

Binance publicly documented a Spot matching-engine incident on 2023-03-24: Spot trading was disabled at 11:27 UTC and resumed at 14:00 UTC after maintenance. This independently explains why a nominal 15-minute archive row inside that interval can have non-standard candle-close metadata.

## Frozen rule controlling the remediation

The prospective authority already states:

- `require_exact_contiguous_15m_spacing = true`;
- `require_all_16_closed_candles = true`;
- `open_or_incomplete_candles_allowed = false`;
- `incomplete_or_gapped_bucket = DROP_BUCKET_AND_SPLIT_CONTIGUITY`;
- `synthetic_missing_candles_allowed = false`.

Therefore the correct implementation is not to fail the entire monthly archive and not to repair/fill the candle. A row whose open time is aligned but whose close time is not the exact completed-15m close is ineligible as a completed 15m candle. It must be dropped. The resulting 4h bucket is incomplete and must be dropped; the 4h series must split continuity around the gap.

## Authorized technical correction

1. Keep SHA-256 archive verification unchanged.
2. Keep open-time UTC alignment mandatory; an unaligned open time remains a source failure.
3. Count rows with non-standard 15m `close_time` as `ineligible_incomplete_15m_rows` rather than rejecting the entire archive.
4. Exclude those rows from the evaluation loader.
5. Do not interpolate, synthesize, forward-fill or alter OHLCV.
6. Preserve every frozen trading parameter, cost, symbol, date window, bootstrap setting and adjudication gate unchanged.
7. Preserve 2025 and 2026 as unopened.
8. Re-run from source gate. This retry is permitted solely because the first run never reached outcome evaluation.

This remediation is technical/source-semantic only and is frozen before any Binance cross-venue outcome inspection.
