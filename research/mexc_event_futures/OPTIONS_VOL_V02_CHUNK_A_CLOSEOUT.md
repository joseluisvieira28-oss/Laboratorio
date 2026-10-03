# OPTIONS-VOL-FWD-001 V0.2 — SOURCE CALIBRATION CHUNK A CLOSEOUT

Date: 2026-10-03
Status: `SOURCE_CALIBRATION_INCOMPLETE`
Scientific outcome opened: 0
MEXC data accessed: false

## Authoritative run

- Workflow run: `37127908110`
- Job: `111216908196`
- Head: `7b19fbeedc33cdade76314635133351ea91d3ae4`
- Artifact: `v013-options-v02-sourcecal-a`
- Artifact id: `11279821837`
- Artifact digest: `sha256:53f52b82e7d4016a1915724db0c5592cd896ba0d2055a8113f6fb97215e06b66`
- Ledger: `source_calibration_rows.jsonl`
- Ledger SHA256: `0fddc5f67acb46a287fc449dbe685eae7687639da578cb6a936f80c2b9fc4fc7`

## Frozen calibration boundary

Original V0.2 calibration boundary:
`1791035711000` ms UTC.

Chunk A first minute:
`1791035820000`.

Chunk A last minute:
`1791046560000`.

No row precedes the frozen calibration boundary.

## Chunk A counts

### BTC
- observed UTC minutes: 180
- valid matched-pair minutes: 166
- missing/invalid: 14
- valid rate: 92.2222%
- source-only preview P95 |skew|: 0.93 pp
- minimum skew observed: -0.96 pp
- maximum skew observed: +0.22 pp
- maximum absolute skew: 0.96 pp

### ETH
- observed UTC minutes: 180
- valid matched-pair minutes: 172
- missing/invalid: 8
- valid rate: 95.5556%
- source-only preview P95 |skew|: 0.79 pp
- minimum skew observed: -0.85 pp
- maximum skew observed: +0.45 pp
- maximum absolute skew: 0.85 pp

The preview P95 values are descriptive only.
They are NOT activation thresholds and MUST NOT be frozen or used for outcomes yet.

## Integrity

Receipt confirms:
- source errors: 0
- threshold_committed: false
- statistics_run: false
- MEXC data accessed: false
- Event Futures outcomes opened: 0
- research outcomes opened: 0

## Gate state

Required before numeric activation freeze, per symbol:
- >=1440 unique observed UTC minutes;
- >=1200 valid matched-pair minutes.

Chunk A therefore remains:
`SOURCE_CALIBRATION_INCOMPLETE`.

The next legitimate action is a NEW non-overlapping bounded source-only chunk.
