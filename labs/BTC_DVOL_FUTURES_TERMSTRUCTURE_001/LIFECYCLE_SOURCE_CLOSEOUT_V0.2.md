# BTC-DVOL-FUTURES-TERMSTRUCTURE-001 — LIFECYCLE SOURCE GATE V0.2 CLOSEOUT

Date: 2026-09-17
Branch: btc-dvol-futures-lifecycle-source-v0.2
Source gate: DVOL-TS-LIFECYCLE-SOURCE-002
Canonical run: 35275287583
Canonical head SHA: 85b75014aac1c85e9b2b7cde982741e7b6cf5653
Artifact: btc-dvol-futures-lifecycle-source-v02-35275287583-1
Artifact ID: 10520437278
Artifact ZIP SHA256: d5a9fc834832c9311d1956a67768c4c34065a2e5784be67f13f9ab91295d2deb

## FINAL CLASSIFICATION

LIFECYCLE_SOURCE_DATA_PASS

This is a source/data verdict only. It is not evidence that the basis/convergence mechanism is profitable.

## CANONICAL SOURCE RESULT

- confirmed contracts: 19
- qualifying contracts: 19
- ordinary public trades: 14,012
- aggregate active contract-days: 607
- qualifying expiration quarters: 7 (2023-Q2 through 2024-Q4)
- core field coverage: 100%
- auxiliary field coverage: 100%
- exact metadata integrity: 100%
- metadata rejections: 0
- lower-boundary clipped contracts: 1

All frozen source viability checks passed.

## BOUNDARY CORRECTION

The prior DVOL-TS-LIFECYCLE-SOURCE-001 closeout remains valid and failed as frozen at metadata integrity 18/19. V0.2 is a new source-gate ID. Its only material source-definition correction is that an exact contract already alive at the lower research boundary is accepted if its listed life overlaps the research window, while trade acquisition is clipped to max(creation_timestamp, 2023-03-27T00:00:00Z).

This admitted BTCDVOL_USDC-26APR23 without opening pre-boundary market outcomes. No source viability threshold was lowered.

## FIREWALL

- basis opened: false
- convergence opened: false
- returns opened: false
- strategy PnL opened: false
- 2025 accessed: false
- 2026 accessed: false
- live trading: false
- exchange mutation: false
- merge to main: false

## RELEASE

This PASS authorizes only a separately frozen pre-Discovery authority. No economic outcome may be opened until that authority fixes the mechanism statistic, sampling rule, source route, statistical gates and stop/no-rescue rules.
