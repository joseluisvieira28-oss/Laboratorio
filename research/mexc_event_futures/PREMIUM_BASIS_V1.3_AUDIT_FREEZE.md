# MEXC EVENT FUTURES LAB — PREMIUM BASIS V1.3 INTEGRITY / ROBUSTNESS AUDIT FREEZE

Date: 2026-10-02
Status: POST-HOLDOUT AUDIT / NO RETUNING / FAIL-CLOSED

## Parent state frozen before this audit

Parent:
`MEXC_EVENT_FUTURES_PREMIUM_BASIS_V1.2_FINAL_HOLDOUT`

The exact five pre-frozen MUUSDT FOLLOW_PREMIUM cells all survived the September 2026 final holdout after Holm-Bonferroni FWER control.

This audit MUST NOT:
- create a new threshold;
- choose a prettier threshold;
- add an asset;
- add a horizon;
- reverse the signal;
- lower any historical statistical gate;
- use October outcomes;
- convert report-only diagnostics into a rescue rule.

The five cells are treated as one nested hypothesis family, not five independent discoveries.

## Exact frozen family

1. MUUSDT / 10m / |z_premium| >= 1.0 / FOLLOW_PREMIUM
2. MUUSDT / 10m / |z_premium| >= 1.5 / FOLLOW_PREMIUM
3. MUUSDT / 10m / |z_premium| >= 2.0 / FOLLOW_PREMIUM
4. MUUSDT / 30m / |z_premium| >= 1.5 / FOLLOW_PREMIUM
5. MUUSDT / 30m / |z_premium| >= 2.0 / FOLLOW_PREMIUM

## Source lineage

Index:
`https://contract.mexc.com/api/v1/contract/kline/index_price/MUSTOCK_USDT`

Fair:
`https://contract.mexc.com/api/v1/contract/kline/fair_price/MUSTOCK_USDT`

Raw interval:
`Min5`

Observable-time rule:
raw timestamp `s` -> close becomes observable at `s + 300 seconds`.

Feature:
`premium_bps[t] = (fair[t] - index[t]) / index[t] * 10000`

Z-score:
same trailing 24h / latest 288 Min5 observations, minimum 240, sample SD, as V1.1/V1.2.

## Audit window

Historical audit span:
2026-04-01T00:00:00Z <= entry t < 2026-10-01T00:00:00Z

Warm-up before 2026-04-01 is allowed strictly for trailing-feature initialization.

**No timestamp >= 2026-10-01T00:00:00Z may be fetched or evaluated.**

## Mechanical integrity gates

These are hard audit gates.

1. `NO_FORWARD_TIMESTAMP_USE`
   - every feature timestamp used for an entry must be <= entry timestamp;
   - z-score window must end at entry, never after it.

2. `OUTCOME_AFTER_ENTRY_ONLY`
   - target timestamp must equal entry + frozen horizon.

3. `MONOTONIC_UNIQUE_SOURCE`
   - no duplicate mapped timestamps in the canonical index/fair series;
   - mapped timestamps strictly increase after deduplication;
   - no timestamp outside the frozen source boundary.

4. `CROSS_SOURCE_ALIGNMENT`
   - each scored signal requires index[t], fair[t], index[t+H];
   - no interpolation, nearest-neighbor fill, or future carry.

5. `FROZEN_FEATURE_REPRODUCTION`
   - recompute parent five-cell Apr–Sep results from scratch;
   - September wins/losses/N/accuracy must exactly reproduce V1.2 frozen holdout receipts supplied in this freeze:
     - 10m z1.0: W901 / L603 / N1504
     - 10m z1.5: W439 / L245 / N684
     - 10m z2.0: W195 / L88 / N283
     - 30m z1.5: W149 / L76 / N225
     - 30m z2.0: W71 / L21 / N92
   - any mismatch => INTEGRITY_FAIL.

## Required report-only robustness diagnostics

These diagnostics CANNOT rescue or invalidate the historical statistical result by themselves. They expose fragility/mechanism.

For each exact cell:
- month-by-month Apr, May, Jun, Jul, Aug, Sep: N, accuracy, EV80, EV70;
- positive-premium-z signals versus negative-premium-z signals separately;
- UTC hour distribution of signals;
- weekday distribution;
- maximum count of simultaneous nested signals at the same timestamp;
- overlap audit: verify same-cell event target windows do not overlap;
- source missingness at eligible aligned entry timestamps;
- zero-change/tie rate;
- premium-bps and |z| descriptive quantiles at signal times.

## One-bar delay stress — REPORT ONLY

For each frozen cell, also calculate a deliberately adverse timing diagnostic:

- detect the signal at original frozen time `t`;
- enter one full Min5 bar later at `t+5m`;
- resolve at `t+5m+H`;
- keep the ORIGINAL signal direction; do not recompute or filter after the delay.

Report:
- delayed N;
- delayed accuracy;
- delayed EV80 / EV70;
- delayed required payout.

This stress test is not a new trade rule and cannot be used to select a threshold.

## Audit classification

- `INTEGRITY_FAIL` if any mechanical integrity gate fails or V1.2 September reproduction mismatches.
- `INTEGRITY_PASS_ROBUSTNESS_REPORTED` if all hard integrity gates pass.

No "diamond", exact profitability, or live authorization follows automatically.

## Product-level facts carried forward

Current public DOM source gate previously established:
- MUUSDT currently exposes 10m / 30m / 1H / 4H;
- exact current MUUSDT Up payout = 80%;
- exact current MUUSDT Down payout = 80%;
- this was independently observed in at least two product-matrix snapshots.

V0.6.4.2 current-display equivalence:
- 60/60 valid public Event Futures DOM-vs-public-index pairs;
- 100% within 1 bp;
- median difference 0 bp.

Still NOT proven:
- historical Event Futures payout-at-entry series;
- expiry settlement tick equivalence;
- rounding/tie semantics at expiry;
- executable Event Futures API.

## Hard boundaries

- no October outcomes;
- no authenticated exchange calls;
- no Up/Down click;
- no orders;
- no balance/account calls;
- no account mutation;
- no live trading;
- no merge to main.
