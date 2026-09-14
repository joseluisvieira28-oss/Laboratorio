# OPTIONS-SPOTPERP-002 — CONFIRMATION TECHNICAL CORRECTION V0.1

Status: TECHNICAL_FAILURE CORRECTED PROSPECTIVELY / SCIENTIFIC SPECIFICATION UNCHANGED

Failed run: 34842929987
Failure class: TECHNICAL_FAILURE during source-only Binance timestamp decoding.
Observed error: year 57053 is out of range.

## Correction scope

The frozen Confirmation scientific specification is unchanged.

Unchanged:
- candidate regime: UP_LOW only
- OOS window: 2025 only
- 2026: locked
- base cost: 10 bps
- stress cost: 20 bps diagnostic only
- minimum entered trades: 80
- beta sign gate
- base net expectancy gate
- base profit-factor gate
- quarterly stability gate
- quarterly concentration gate
- no tuning / no cherry-picking / no parameter rescue
- no live trading / no exchange mutation / no merge to main

Correction only:
- normalize Binance public-data open timestamps that may be encoded as milliseconds or microseconds;
- fail closed for unsupported timestamp magnitudes;
- normalize to milliseconds for source receipts;
- use the same normalization when decoding BTC daily bars in the OOS runner.

## Isolation proof

Base scientific implementation commit before compatibility correction:
337317d2c43f09e898c20864d3f45375090da6bf

Compatibility implementation head after correction:
8c389ea63622f0a1ff5e2b243240473ece8aaab3

Git compare between those commits contains only three newly added technical compatibility files:
- binance_timestamp_normalizer_v01.py
- confirmation_source_acquire_2025_compat_v01.py
- confirmation_runner_2025_compat_v01.py

The frozen original files confirmation_source_acquire_2025_v01.py and confirmation_runner_2025_v01.py were not modified.

## Scientific classification rule

The failed run 34842929987 remains TECHNICAL_FAILURE and is not NO_EDGE, OOS_FAILED, INSUFFICIENT_SAMPLE, or any other scientific outcome.

A retry is authorized only with the exact same frozen scientific gates and the compatibility layer above. The retry may produce a scientific classification only after source-only acquisition and source firewalls pass.
