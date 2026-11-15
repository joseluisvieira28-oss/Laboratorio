# LICP-001 — ELIGIBLE FORWARD BASELINE V0.1

Date: 2026-10-08

## State

**FORWARD_INSUFFICIENT**

A deep audit of historical GitHub Actions found one canonical forward observation run that is
eligible under the economic freeze and must be part of the frozen first-20 sequence.

### Canonical run

- run: `37311668666`
- job: `111768312870`
- artifact: `11364886047`
- artifact SHA256: `dbf6cc1cf8a8f22d556d7adf7cf475ed14f58747d1ac45b83bc67a5280ad8f39`
- observation duration: **20,700 s**
- run start: `1791204294773`
- economic-freeze cutoff: `1791204237000`

The run began after the canonical freeze and is eligible.

## Forward records

- total records: **8**
- BTC_CONFIRMED: **6**
- ALT_SECOND_WAVE: **2**
- BTC_CONFIRMED with complete BTC_USDT 60s primary outcome: **6/6**
- distinct UTC dates: **1**

Descriptive primary metrics for the six BTC_CONFIRMED events:

- mean gross: **+3.1487 bps**
- median gross: **+2.0622 bps**
- mean net after 16 bps: **-12.8513 bps**
- median net after 16 bps: **-13.9378 bps**
- mean stress net after 32 bps: **-28.8513 bps**
- positive base-net events: **1/6**

These numbers are descriptive only.

The frozen evidence gate requires at least 20 independent primary episodes across at least
3 UTC dates with >=90% primary coverage. Therefore neither NO_EDGE nor SURVIVES is authorized.

## Integrity correction

This eligible run predates the later addition of the explicit `episode_id` field. It cannot be
discarded because of a later schema improvement. The durable ledger reconstructs the same
deterministic identifier mechanically from:

`config_version | ignition_venue_ts | pressure`

using the exact SHA-256 formula subsequently embedded in the observer.

No outcome is used in that reconstruction.

## Next state

Continue canonical forward collection under the unchanged frozen trigger and outcome contract.
No threshold, target, horizon, fee or direction may be altered.
