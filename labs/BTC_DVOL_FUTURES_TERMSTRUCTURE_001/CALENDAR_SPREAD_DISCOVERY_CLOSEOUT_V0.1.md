# BTC-DVOL-FUTURES-TERMSTRUCTURE-001 — CALENDAR SPREAD DISCOVERY CLOSEOUT V0.1

Date: 2026-09-18
Discovery ID: DVOL-TS-CALENDAR-SPREAD-DISCOVERY-001
Canonical run: 35280406507
Canonical head SHA: 1514a66f5e7490eb29f5acf0c021c5c87b48a13e

## FINAL CLASSIFICATION

CALENDAR_SPREAD_DISCOVERY_NO_ROBUST_EDGE

## FROZEN RESULT

- pair clusters with scores: 17
- adjacent common-day scores: 59
- equal-weight mean pair score/day: +0.5924673203
- median pair score/day: +0.6400000000
- positive pair share: 70.5882%
- pooled hit rate: 59.3220%
- nonnegative near-expiration quarters: 6/7
- cluster bootstrap 95% CI: [-0.0055906863, +1.1833357843]

All frozen sample gates passed. Four of five statistical gates passed. The sole failing gate was bootstrap lower 95% > 0.

Quarter means:
- 2023-Q2 +0.3300
- 2023-Q3 +0.3633
- 2023-Q4 +1.1033
- 2024-Q1 +1.3713
- 2024-Q2 +1.0375
- 2024-Q3 +0.4622
- 2024-Q4 -1.5222

## ADJUDICATION

No promotion. The exact equal-unit near/far implementation is closed. The small negative bootstrap lower bound may not be rescued by deleting 2024-Q4, selecting only positive pairs, lowering the bootstrap gate, changing the hedge ratio, changing the anchor or adding a basis threshold under this Discovery ID.

The parent DVOL basis-convergence Discovery remains independently recorded as PASS, but this calendar-spread translation did not achieve robust statistical evidence.

## NEW-HYPOTHESIS FIREWALL

Any materially different calendar-spread signal designed after this result must treat 2023-2024 as contaminated development history. It may not use those outcomes as confirmation evidence. A new rule may only be adjudicated on a genuinely disjoint block under a new source gate and frozen authority.

2026 remains locked.
Transaction costs/PnL: unopened under this Discovery.
Live trading/exchange mutation/wallet access/main merge: false.
