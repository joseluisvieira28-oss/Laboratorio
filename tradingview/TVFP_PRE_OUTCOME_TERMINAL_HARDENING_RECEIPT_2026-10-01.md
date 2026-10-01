# TV-FOOTPRINT-CALIBRATION-001 — PRE-OUTCOME TERMINAL HARDENING RECEIPT

Date: 2026-10-01
State at hardening: first 2,016 TradingView receipts reached; Binance comparison metrics NOT YET OPENED.

## Prospective operational correction

Before accessing Binance comparison outcomes, the calibration utility was hardened so that:

- the terminal TradingView sample is exactly the first 2,016 unique consecutive forward receipts;
- the terminal interval is fixed by those receipts and bars outside it cannot alter any denominator;
- Binance source completeness is measured separately from matched-bar coverage;
- the full Binance day containing the terminal boundary cannot inflate the denominator;
- TradingView CSV timestamps without an explicit timezone are rejected instead of silently assumed UTC.

This correction does not change any frozen PASS_STRONG, PASS_LIMITED or FAIL_SENSOR threshold.
It does not change symbol, venue, timeframe, footprint parameters, side semantics, metric definitions or sample minimum.

## Frozen terminal TV sample

- first bar close: 2026-09-24 12:40:00 UTC
- final / #2,016 bar close: 2026-10-01 12:35:00 UTC
- terminal receipts: 2,016
- gaps: 0
- conflicting duplicate evidence keys: 0
- sample storage: two immutable CSV parts of 1,008 receipts each under tradingview/terminal/
- post-terminal receipts: excluded from terminal verdict

## Authority

Research instrument calibration only.
No edge authority.
No trading authority.
No main merge.
