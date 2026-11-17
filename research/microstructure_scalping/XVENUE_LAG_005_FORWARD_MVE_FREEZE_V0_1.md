# XVENUE-LAG-005 — BINANCE→MEXC FORWARD MVE FREEZE V0.1

Date: 2026-09-26
Status: PRE-RUN FORWARD MVE
Scope: PUBLIC MARKET DATA ONLY

## Hypothesis
A rapid Binance USD-M BTCUSDT BBO move may lead MEXC BTC_USDT BBO adjustment on the same local observer clock.

## Capture
Duration: 180 seconds.

Leader:
- Binance BTCUSDT bookTicker.

Follower:
- MEXC BTC_USDT reconstructed order book.

Both are captured concurrently in one GitHub Actions runner.

Primary time axis:
- local Unix receive timestamp in nanoseconds.

Exchange timestamps are diagnostic only.

## MEXC book reconstruction
1. Open and subscribe to MEXC incremental depth.
2. Buffer deltas continuously.
3. Fetch REST depth snapshot while subscription remains active.
4. Discard buffered deltas with version <= snapshot version.
5. First applied delta MUST equal snapshot version + 1.
6. Every subsequent delta MUST increment version by exactly 1.
7. Any gap = fail closed.
8. Quantity zero deletes a price level.
9. Nonzero quantity replaces the level quantity.
10. Reconstructed best bid must remain < best ask.

Retry snapshot synchronization up to 5 times before BLOCKED.

## Leader shock families
Trailing leader windows:
- 250 ms
- 500 ms
- 1,000 ms

Absolute Binance mid-return thresholds:
- 2 bps
- 5 bps
- 10 bps

Direction = sign of the Binance trailing return.

Each window × threshold pair has a 1,000 ms cooldown after a selected event.

These are generic predeclared thresholds, not calibrated on outcomes.

## Follower labels
At event t use latest reconstructed MEXC BBO at/before t.
Require its receive age <= 500 ms.

Future states use latest reconstructed MEXC BBO at/before:
- t + 100 ms
- t + 250 ms
- t + 500 ms
- t + 1s
- t + 2s
- t + 5s

Require future state's receive age <= 500 ms.

Report:
- directional MEXC mid return
- MEXC executable taker gross
- MEXC taker fee-only net using 16 bps round trip
- 50% catch-up delay when observed within 5s

## Interpretation
This 180-second run is a FORWARD MVE, not enough for scientific promotion.

Possible states:
- FORWARD_PLUMBING_PASS_NO_ECONOMIC_SIGNAL
- FORWARD_ECONOMIC_SIGNAL_SAMPLE
- BLOCKED

FORWARD_ECONOMIC_SIGNAL_SAMPLE requires for at least one frozen variant/horizon:
- n >= 5
- mean MEXC taker fee-only net > 0

Even if observed, it requires longer forward replication before any capital use.
