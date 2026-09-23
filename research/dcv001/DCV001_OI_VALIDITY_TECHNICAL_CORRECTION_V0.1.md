# DCV-001 — OI VALIDITY RUNNER TECHNICAL CORRECTION V0.1

Date: 2026-09-23

## State before correction

Run 35857935800:
- full 2021-2023 source census: PASS;
- official monthly+daily mark route passed frozen coverage requirements after V0.2 remediation;
- execution stopped during OI value parsing on 2021-05-22 with INVALID_OI_VALUE;
- no next-day BTC return, regression coefficient, bootstrap statistic, year result, PnL, 2024 full replication source or protected 2025/2026 data had been opened.

## Frozen authority already in force

The original pre-outcome authority states:

- sort valid metrics rows by create_time;
- take the chronologically last valid BTCUSDT row;
- OI_D = sum_open_interest;
- if required source values are missing, D is not model-eligible.

The first runner implementation was stricter than this authority: it aborted a whole day if ANY intraday metrics row was non-finite or non-positive.

## Technical correction

For each daily metrics object:

1. Exact duplicate-row normalization from Amendment B remains unchanged.
2. Evaluate BTCUSDT rows in chronological order.
3. A valid OI snapshot is one whose sum_open_interest parses to a finite number > 0.
4. Invalid intraday OI snapshots are ignored as invalid snapshots; they do not replace, interpolate or modify another observation.
5. OI_D is the value from the chronologically last valid snapshot in D.
6. If D contains no valid OI snapshot, OI_D is missing and D cannot be model-eligible.
7. No averaging, forward filling, zero substitution or alternate OI field is allowed.

## Boundary

This correction aligns code to the already-frozen rule. It does not change:
- hypothesis or expected sign;
- 90-day z-score;
- RV7;
- next-day outcome;
- bootstrap;
- Discovery gates;
- 2024 release condition;
- source thresholds;
- asset/source family.

No economic outcome informed this correction.
