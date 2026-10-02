# MEXC EVENT FUTURES LAB — V0.1 SOURCE CLOSEOUT / CORRECTION

Date: 2026-10-02

## Correct verdict

**V0.1 = SOURCE_BLOCKED, NOT NO_EDGE.**

The workflow completed successfully operationally, but the historical 1-minute MEXC index-price fetch returned zero usable rows for the frozen Apr-Aug 2026 windows for every asset. Because no outcome matrix was actually populated, the string `NO_PROXY_SURVIVOR_AT_FROZEN_GATE` emitted by the first script must NOT be interpreted as a scientific no-edge verdict.

The source probe did prove that the current public MEXC contract API resolves all five frozen proxy symbols and exposes current index price plus recent index K-lines.

## What is preserved

- Pre-outcome freeze remains valid.
- September 2026 holdout remained unopened.
- No order was placed.
- No authenticated exchange mutation occurred.
- No scientific thresholds were changed after outcomes.
- No outcome was available to tune against.

## V0.2 mission

Determine whether the public MEXC API can recover the required historical index-price data using alternate documented parameter forms / intervals / routes.

This is SOURCE-ONLY remediation. It may inspect row counts, timestamps, endpoint success/failure, and coverage. It must not calculate strategy returns, accuracy, EV, or select a trading rule.

If the source cannot supply historical data, the exact MEXC Event Futures backtest remains BLOCKED and the next legitimate route is a prospective collector and/or clearly labeled external-market proxy study.
