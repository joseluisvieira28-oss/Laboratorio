# LIQUIDATION-PRESSURE-002-FORWARD — SOURCE CALIBRATION IMPLEMENTATION V0.1

Date: 2026-09-23
Status: PRE-OUTCOME SOURCE-ONLY IMPLEMENTATION FREEZE
Authority: ECONOMIC_MVE_FREEZE_V0.1

## Purpose

Persist the already-frozen Bybit liquidation calibration population across multiple read-only capture sessions until the scientific source minimum is reached.

This document changes no scientific rule.

## Frozen scientific rules preserved

- Venue: Bybit USDT linear perpetuals.
- Symbols: BTCUSDT, ETHUSDT, SOLUSDT, XRPUSDT, DOGEUSDT, BNBUSDT.
- Source variable: public allLiquidation messages only.
- 5-second non-overlapping calibration windows.
- Minimum before canonical q95 freeze: >=24 UTC hours from first to last raw liquidation record AND >=500 raw liquidation records.
- Per-symbol eligibility: >=30 non-empty 5-second windows.
- Primary threshold: nearest-rank per-symbol q95.
- q90/q99 descriptive only.
- No markouts, price-response outcomes, economic returns, PnL or promotion credit during calibration.

## Transport

A dedicated public WebSocket collector subscribes only to:
allLiquidation.<symbol>

Each liquidation item is persisted once using an exact source-record identity tuple:
(symbol, exchange event timestamp T, side S, volume v, bankruptcy/record price p).

Repeated delivery of the exact same source item is deduplicated. No candidate is selected or excluded by later market outcome.

The persistent JSONL remains compatible with calibrate_source_thresholds_v0_1.py.

## Operational cadence

Capture sessions may repeat as needed to approach continuous coverage. Session frequency, reconnects and transport retries create no scientific credit by themselves.

A canonical threshold file may be emitted only by the already-frozen calibrator when both source minima are met.

## Safety

- authenticated endpoint: false
- orders: false
- wallet mutation: false
- exchange mutation: false
- markouts opened: false
- PnL computed: false
- main merge: false
- post-outcome tuning: false
