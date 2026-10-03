# OPTIONS-RR-TERM-FWD-001 — PRE-OUTCOME ACTIVATION SHELL FREEZE V0.1

Date: 2026-10-03
Status: `NOT_ACTIVE_PENDING_NUMERIC_SOURCE_CALIBRATION`

This document freezes every nonnumeric activation choice BEFORE any outcome.
It does NOT authorize opening an outcome because the symbol thresholds are not yet known.

## Authority

Source gate:
- run `37137352304`
- artifact `11279410408`
- digest `sha256:0472b41436195f91085fcf88fc8bedbf5ccd0388c876d6054f5373dc62b8c706`
- verdict `SOURCE_GATE_PASS`

Calibration freeze:
`OPTIONS_RR_TERM_SOURCE_CALIBRATION_FREEZE_V01.md`

## Frozen identity

Family:
`OPTIONS-RR-TERM-FWD-001`

Future family version:
`0.1`

Symbols:
- BTC -> BTC_USDT
- ETH -> ETH_USDT

Feature:
`rr_term_pp = short_25d_put_minus_call_IV - medium_25d_put_minus_call_IV`

Expiry buckets:
- SHORT nearest active expiry DTE [7,21] days
- MEDIUM nearest active expiry DTE [35,70] days

Direction policy:
`FOLLOW_NEAR_TERM_DOWNSIDE_STRESS`

Direction:
- rr_term_pp >= +threshold(symbol) => DOWN
- rr_term_pp <= -threshold(symbol) => UP
- otherwise NO_SIGNAL

Threshold source:
- symbol-specific nearest-rank P95 of abs(rr_term_pp)
- from the frozen forward source-only calibration only

Event Futures horizon:
- exactly 10 minutes

Signal freshness:
- source signal age <=5 seconds at decision

Overlap:
- first-only unresolved event per family/version/symbol/horizon

Minimum evidence:
- N >=100 resolved nonblocked events per symbol

Evaluation:
- 30-day batch boundary
- actual direction-specific payout q per event
- V0.13 event-specific break-even null/bootstrap/Holm unchanged
- no interim survivor verdict

## Explicit blocker

Numeric thresholds are NULL until calibration completes.

Therefore:
`OUTCOME_OPENING_AUTHORIZED = FALSE`

A later numeric activation freeze MUST commit:
- BTC threshold
- ETH threshold
- calibration artifact identities/digests
- exact calibration counts
- calibration boundary
- rule hash

before the first price/Event Futures outcome is opened.

## Governance

No threshold may be inferred from the source-gate sample.
No historical return optimization.
No post-outcome tuning.
No live trading/orders/login/private/account/wallet access.
No main merge.
