# OPTIONS-ETH-SKEW-SHOCK-001 — STAGE A CLOSEOUT V0.1

Date: 2026-10-02
Branch: `options-eth-skew-shock-v01-2026-10-02`
Workflow: `OPTIONS ETH Skew Shock Stage A V0.1`
Run: `36984112651`
Workflow head: `6c57d9eeafa6fea4ec7025da3fbba1fc99eaa398`
Artifact: `11217790806`
Artifact SHA256: `e07861f5431e17026db5e4b48b9066dd6fe63d9920ba7d4842b1d32bd012f2f0`

## Final verdict

`BACKVALIDATION_REJECTED__2025_REMAINS_LOCKED`

The prospectively frozen ETH skew-shock hypothesis did not survive the unseen 2021-2023 Stage-A back-validation.

Calendar 2025 was not opened.

## Hypothesis tested

Daily ETH options skew:

`skew_t = median(call instrument IV) - median(put instrument IV)`

Frozen shock signal:

`shock_t = skew_t - skew_(t-1 calendar day)`

Direction:
- positive shock => LONG ETH
- negative shock => SHORT ETH
- zero shock => FLAT

No threshold, z-score, magnitude filter, direction reversal, DTE retuning, moneyness retuning, weekday/quarter filtering, or post-outcome rescue was used.

## Source / provenance

Stage-A Deribit ETH option source:
- 36 calendar months: 2021-01 through 2023-12
- source rows: 8,255,044
- target rows: 8,255,044
- globally unique trade IDs: 8,255,044
- global duplicate trade IDs: 0
- within-month duplicate IDs: 0
- parse failures: 0
- invalid IV rows rejected fail-closed: 26,045
- invalid index rows: 0
- eligible rows after frozen DTE/moneyness filters: 439,505
- valid daily-skew days: 838

Outcome prices:
- Binance Vision ETHUSDT spot daily
- risk-history start: 2020-01-01
- Stage-A outcome cutoff: 2023-12-31

Calendar 2024 outcome data was not accessed by this runner.

## Stage-A economics — BASE10

- entered scaled trades: 754
- average executed notional: 0.9398213019
- LONG / SHORT: 381 / 373
- gross mean: +5.0396274704 bps/opportunity
- net mean: **-4.3585855485 bps/opportunity**
- profit factor: **0.9667263015**
- cumulative net return: **-28.0095957645%**
- max drawdown: **-65.1598597145%**
- win rate: 48.275862%

Annual BASE10 net mean:
- 2021: -4.4957417645 bps, N=157
- 2022: -6.7942399027 bps, N=284
- 2023: -2.0798016428 bps, N=313

Non-negative years: 0 / 3.

Single-year share of total positive gross PnL: 65.2394987389%, above the frozen 60% maximum.

## STRESS20 diagnostic

- net mean: -13.7567985675 bps/opportunity
- profit factor: 0.8988087620
- cumulative net return: -64.5576449953%
- max drawdown: -76.6123537334%

## Frozen gate result

PASS:
- A provenance/source/leakage
- B N >= 300
- C average executed notional >= 0.40
- I exact identity unchanged

FAIL:
- D BASE10 net mean > 0
- E BASE10 PF > 1
- F BASE10 cumulative net return > 0
- G at least 2 of 3 years non-negative
- H concentration <= 60%

High-risk fragility flag: TRUE because BASE10 max drawdown was worse than -50%.

## Protected windows / governance

- 2024 used for promotion: false
- 2025 accessed: false
- 2026 accessed: false
- live trading authorized: false
- exchange mutation: false
- main merge: false
- post-outcome rescue: false

## Scientific interpretation

The observed gross directional effect (+5.04 bps/opportunity) was insufficient to overcome the frozen 10 bps full-notional cost model after causal risk scaling.

The failure is broad, not a single-gate technicality:
- all three tested years were negative after BASE10 costs;
- PF was below 1;
- cumulative return was negative;
- concentration exceeded the frozen cap;
- drawdown was severe.

Therefore this exact `skew_t - skew_(t-1)` identity is closed and must not be rescued by opening 2025, lowering gates, changing direction, adding thresholds, or selecting subperiods.

2025 remains untouched for a genuinely different prospectively frozen ETH hypothesis, if one is later proposed.
