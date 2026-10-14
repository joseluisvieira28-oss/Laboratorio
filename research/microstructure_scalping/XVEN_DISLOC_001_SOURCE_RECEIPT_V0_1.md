# XVEN-DISLOC-001 — SOURCE GATE RECEIPT V0.1

Date: 2026-09-26
Workflow run: 36229876510
Status: SOURCE_FEASIBLE / PASS_SAMPLE

## 60-second public forward capture
Binance BTCUSDT:
- valid BBO updates: 5,147
- crossed BBO: 0
- local clock regressions: 0

MEXC BTC_USDT:
- valid depth-derived BBO updates: 250
- crossed BBO: 0
- local clock regressions: 0

Paired:
- paired observations: 5,378
- fresh paired observations with <=1,000ms venue age: 5,378
- median fresh executable cross-venue gap: -0.0119 bps
- maximum fresh executable cross-venue gap: +0.9280 bps

## Interpretation
The public forward sources are technically feasible and can be observed concurrently with explicit stale-data handling.

The 60-second sample does NOT demonstrate an economically viable cross-venue dislocation. Its maximum observed executable gap is far below current fee hurdles.

A one-minute absence of large dislocations is not a scientific NO_EDGE verdict because the hypothesis concerns sparse transient events.

## Next step
Forward observation only:
- extend bounded public capture duration;
- persist gap episodes rather than every duplicate paired update;
- measure duration, peak gap, venue-update ordering and stale state;
- do not place orders;
- do not choose trading thresholds from outcomes.

Historical synchronized cross-venue Discovery remains BLOCKED unless a defensible source is identified.
