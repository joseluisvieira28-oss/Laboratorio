# MEXC-WTI-EVENT-SHOCK-001 — V1.4 CLOSEOUT

Date: 2026-10-04
Run: 37201654642
Artifact SHA256: `46865887820a83d52613db5a73b13639a79cf179b38ab57105532baa8279d8ce`
Rule SHA256: `a65eaa67fbf931ede07c56cd01dad37120b4d70233e1bb98e096fa7a7ced905f`

## Coverage

Min5 resolved the V1.3 retention blocker:
- 35 / 35 EIA event windows usable;
- 30 / 30 Discovery;
- 5 / 5 September coverage;
- zero bad events.

## Frozen price-shock family result

Cells:
- thresholds 0 / 10 / 20 / 40 bps;
- CONTINUATION / REVERSAL;
- horizons 5 / 15 / 30 / 60m;
- next-Min5-open entry.

Result:
- pre-Holm eligible cells: 0;
- Holm-selected cells: 0;
- September OOS scored: NO;
- survivors: 0.

Verdict:
`NO_WTI_EIA_EVENT_SHOCK_OOS_SURVIVOR_AT_FROZEN_V14_GATE`

## Descriptive observations — NOT candidates

All-event continuation at 60m:
- N=29
- wins=16
- win rate=55.17%
- mean gross=+11.3042 bps
- one-sided binomial p=0.3555
- failed the frozen eligibility gate.

Rare shock >=40 bps / continuation / 60m:
- N=2
- wins=2
- mean gross=+80.6561 bps
- p=0.25
- anecdotal only.

No post-outcome threshold or mode rescue is allowed.

## Holdout contamination note

Although September OOS performance was not scored because no Discovery cell passed Holm, V1.4 did retrieve the five September raw WTI event windows for source coverage.

Therefore a new economically distinct WTI hypothesis must NOT present September as a pristine holdout.

A new fundamental EIA-data hypothesis may use February-August only as exploratory Discovery, but any confirmatory validation must be future-forward from a new pre-event freeze.

No live trading, account reads, credentials, wallets, private endpoints, orders, mutation, or main merge.
