# BTC-CONVEX-TREND-CAPTURE-001 — CAUSAL 1H REPLAY PROTOCOL V0.1

**Frozen:** 2026-09-23 before opening causal replay outcomes  
**Role:** execution-integrity diagnostic only  
**Promotion credit:** ZERO

## Purpose

Measure how the recovered V5 mechanism behaves when historical order-fill recalculation cannot access future information from the same 1h bar.

This replay is NOT an independent edge test because the BTC history has already been inspected.

## Data

Official Binance USD-M BTCUSDT 1h klines.

Warm-up data begins in February 2020.

Replay boundary:
- start: 2020-03-01 00:00 UTC;
- starting equity: 10,489.94 USDT, matching the supplied ledger after trade 6 had closed and before trade 7;
- end: 2026-06-30 23:00 UTC.

The start boundary is intentionally chosen after the long 2019-origin trade closed and while the supplied strategy was flat.

## Signal

Exact recovered source with original defaults:

- SMA20;
- STDEV20;
- zScore < -2;
- RSI14 < 30;
- close < SMA20 - 2×STDEV20;
- volume > SMA20(volume);
- score >= 3;
- close > SMA200;
- long-only while flat.

No signal parameter is changed.

## Causal order timing

1. Evaluate the entry signal only on a fully closed 1h bar.
2. If flat and the signal is true, schedule a market entry for the next bar OPEN.
3. No same-bar reentry after an intrabar exit.
4. No current-bar final close/high/volume can be used before that bar closes.

## Position sizing and fee

- 95% of current flat equity at entry;
- commission = 0.10% of entry notional;
- commission = 0.10% of exit notional;
- no slippage in this first apples-to-apples execution diagnostic;
- no funding in this first apples-to-apples execution diagnostic.

Funding/slippage belong to a later economic-cost layer and cannot rescue this diagnostic.

## Exit logic

The original non-latched V5 semantics are preserved.

Immediately after entry:
- initial protective stop = entry × 0.96;
- peak state starts at entry price.

For every bar while the trade survives:
- the stop active during that bar is the stop frozen at the previous causal decision point;
- if bar OPEN is below/equal the stop, exit at OPEN;
- else if bar LOW touches the stop, exit at the stop price;
- if no exit occurs, after the bar closes update peak with that completed bar HIGH;
- compute close-based profit using the completed bar CLOSE;
- if close profit >= 5%, next-bar stop = max(peak × 0.88, initial stop);
- otherwise next-bar stop = initial stop.

Thus the original behavior in which the trailing regime can deactivate is preserved.

## End-of-period handling

Any position still open at replay end is marked to the final close separately from realized PnL.

## Interpretation

This replay answers only:

> Does the retrospective V5 result still look economically interesting after removing historical same-bar foreknowledge?

It cannot prove edge, because the BTC period is already contaminated by observation.

No threshold tuning, parameter rescue, timeframe rescue or promotion is authorized from this output.
