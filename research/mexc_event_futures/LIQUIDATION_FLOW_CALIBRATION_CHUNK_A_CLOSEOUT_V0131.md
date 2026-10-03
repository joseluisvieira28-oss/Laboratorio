# LIQUIDATION-FLOW-FWD-001 — CALIBRATION CHUNK A CLOSEOUT V0.13.1

Date: 2026-10-03
Status: `CALIBRATION_INCOMPLETE`
Scientific outcomes opened: 0
MEXC subscriptions: 0

## Operational correction

The earlier apparent "teardown hang" was a false diagnosis.

GitHub run `37123311409` was created at:
`2026-10-03T12:34:30Z`

but the canonical latest attempt did not actually start until:
`2026-10-03T16:10:56Z`

It then completed successfully at:
`2026-10-03T19:12:09Z`

Therefore the roughly three-hour runtime matches the frozen 180-minute collection window plus setup/5s grace/teardown. No teardown code change is scientifically or operationally justified from this run.

## Authoritative evidence

- Workflow run: `37123311409`
- Run attempt: `2`
- Job: `111240266718`
- Head: `6371a003f0b554935c7d5fc736bd4929a3349be5`
- Artifact: `v0131-liquidation-calibration-chunk-a`
- Artifact id: `11282671683`
- Artifact digest: `sha256:1ba446912f5507e92f519dde3c03e00f761db621c9212cc22e9e6c91e0741cd6`
- Calibration ledger: `calibration_bins.jsonl`
- Ledger SHA256: `4b06ed7f00fd99caf6bec5afa93a45d910adb27fdada19755bd66f00d1fff23f`

## Frozen window

- first full UTC minute: `1791043920000`
- last UTC minute: `1791054660000`
- minutes requested per symbol: 180

## Counts

### BTCUSDT
- bins: 180
- healthy bins: 180
- nonzero healthy bins: 5
- source errors: 0

### ETHUSDT
- bins: 180
- healthy bins: 180
- nonzero healthy bins: 2
- source errors: 0

All 360 symbol-minute bins are healthy.

## Nonzero source-only observations

BTCUSDT had five nonzero healthy minutes.
ETHUSDT had two nonzero healthy minutes.

These observations are calibration source evidence only.
No P95 threshold is computed because the frozen minimum is not met.

## Gate state

Required per symbol before numeric activation freeze:
- >=1440 healthy bins
- >=100 nonzero healthy bins

Current cumulative canonical state after Chunk A:
- BTCUSDT: 180 healthy / 5 nonzero
- ETHUSDT: 180 healthy / 2 nonzero

Therefore:
`CALIBRATION_INCOMPLETE`

No threshold may be frozen yet.
No Event Futures outcome may be opened yet.
