# TV SENSOR ANOMALY SENTINEL V0.1 — LIVE BASELINE RECEIPT

Observed: 2026-09-24 through 14:05 UTC
Parent lab: `TV-FOOTPRINT-CALIBRATION-001`
Sensor: `MM-V1`
Stream: `BINANCE:BTCUSDT` / 5m

## Live audit

The first 18 authentic forward receipts observed from the Render evidence stream
were audited against the frozen Sentinel invariants.

Result:

- unique receipts checked: 18
- calibration-eligible receipts: 18
- hard-invalid receipts: 0
- degraded receipts: 0
- visible 5-minute gaps: 0
- LTF incomplete bars: 0
- value-area / POC invariant failures: 0
- volume reconciliation failures: 0
- delta reconciliation failures: 0
- imbalance-row invariant failures: 0
- path-efficiency range failures: 0
- maximum observed receipt latency: 37,367 ms
- trading authority: NONE
- calibration authority: NONE

Observed contiguous bar-close sequence begins at 2026-09-24 12:40 UTC and
extends through 2026-09-24 14:05 UTC.

## Interpretation

`PASS` means the transport/sensor structure is internally coherent under the
Sentinel rules at this checkpoint. It is not a footprint calibration verdict
and does not imply edge.

Any future structural conflict, schema drift, hash failure, timestamp violation
or arithmetic inconsistency must fail closed rather than be repaired or imputed.
