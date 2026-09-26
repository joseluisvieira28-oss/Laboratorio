# BTC-ALT-LL-004B — SOL EXECUTABLE BBO VALIDATION
## PRE-RUN FREEZE V0.1

Date: 2026-09-26
Status: PRE-OUTCOME FREEZE
Phase: DISCOVERY VALIDATION — NOT OOS

## Why this candidate exists
The already-frozen BTC-ALT-LL-004 informational ceiling produced one alternative-venue-feasible candidate after applying current published venue fee hurdles:

Follower: SOLUSDT
Signal: W5000_P99
Horizon: 60,000 ms
Flow gate: NONE
Lag gate: NONE

Original pooled trade-price informational result:
- n: 142
- gross: +6.5398597970 bps
- MEXC maker fee-only net: -5.4601402030 bps
- Bybit VIP0 maker fee-only overlay: +2.5398597970 bps
- date means: +10.2935610274 / -1.8554962392 / +4.0294589611 bps

This overlay is NOT an edge claim because follower trade prices ignore spread and executable BBO.

## Candidate frozen exactly
BTC source:
- BTCUSDT Bybit linear L2

Shock window:
- 5,000 ms

Absolute BTC shock threshold:
- 7.002526745067178 bps

This numeric threshold is frozen from the prior 2024-05-01 feature-only p99 calibration.

Direction:
- sign of BTC 5-second prior mid return

Follower:
- SOLUSDT Bybit linear L2

Exit horizon:
- 60,000 ms

No flow gate.
No follower lag gate.
No cooldown added.
No threshold changes.

## Fresh validation dates
Deterministic rule:
first Wednesday of each of the next three months after the last date used by BTC-ALT-LL-004.

- 2024-08-07
- 2024-09-04
- 2024-10-02

All remain inside 2023–2024 Discovery.
These are fresh to this candidate.

2025 OOS = LOCKED.
2026 protected holdout = LOCKED.

## Source
For each date:
- BTCUSDT historical L2, first 250,000 messages
- SOLUSDT historical L2, first 250,000 messages

Before any outcomes, all six URLs must return HTTP 200 and positive Content-Length.

## Clock / executable alignment
BTC:
- 1-second anchors
- cts preferred; fallback ts only if cts absent

SOL entry:
- latest reconstructed SOL BBO at or before BTC anchor
- staleness <= 250 ms

SOL future:
- first reconstructed SOL BBO at or after anchor + 60s
- label delay <= 250 ms

Otherwise event is excluded.

## Economics

### Perfect maker/maker executable-BBO ceiling
LONG:
- entry current SOL best bid
- exit future SOL best ask

SHORT:
- entry current SOL best ask
- exit future SOL best bid

Bybit VIP0 fee hurdle: 4 bps round trip.

### Taker/taker
LONG:
- entry current ask
- exit future bid

SHORT:
- entry current bid
- exit future ask

Bybit VIP0 fee hurdle: 11 bps round trip.

No slippage or latency beyond the frozen BBO alignment allowance in this validation.

## Survival rule
EXECUTABLE_CEILING_SURVIVOR only if:
- pooled n >= 30
- pooled mean Bybit maker/maker net > 0
- at least 2 of 3 date-level maker/maker mean nets > 0

If it fails:
BTC-ALT-LL-004B = NO_EXECUTABLE_CEILING_EDGE

If it survives:
do NOT open OOS.
Next step is conservative passive fill / adverse-selection validation on additional fresh Discovery data.
