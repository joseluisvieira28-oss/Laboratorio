# OPTIONS-RR-TERM-FWD-001 — SOURCE GATE CLOSEOUT V0.1

Date: 2026-10-03
Verdict: `SOURCE_GATE_PASS`
Outcomes opened: 0
MEXC accessed: false

## Authoritative run

- Workflow: `MEXC V0.13 RR Term Source Gate`
- Run: `37137352304`
- Job: `111244471017`
- Head: `0ff92989ca9641079b192532ccf329c8d0c5dc87`
- Artifact: `options-rrterm-source-gate-v01`
- Artifact id: `11279410408`
- Artifact digest: `sha256:0472b41436195f91085fcf88fc8bedbf5ccd0388c876d6054f5373dc62b8c706`

## Frozen source feasibility result

All required public Deribit source rounds passed:

- BTC valid SHORT+MEDIUM dual-expiry rounds: 3/3
- ETH valid SHORT+MEDIUM dual-expiry rounds: 3/3
- source exceptions: 0
- within-expiry call/put timestamp spread: within frozen <=5000ms gate
- cross-expiry four-ticker spread: within frozen <=10000ms gate
- no price outcome accessed
- no Event Futures outcome opened

Observed source-only examples during the gate:

BTC:
- SHORT DTE ~12.64 days
- MEDIUM DTE ~54.64 days
- rr_term_pp observed around -1.52 pp

ETH:
- SHORT DTE ~12.64 days
- MEDIUM DTE ~54.64 days
- rr_term_pp observed around -0.98 pp

These values are SOURCE FEASIBILITY ONLY.
They are not thresholds and cannot be used as outcome-conditioned tuning.

## Scientific state

`SOURCE_PASS_PENDING_FORWARD_CALIBRATION`

The source gate events are excluded from calibration.

The family may now collect only the already-frozen source-only calibration required by
`OPTIONS_RR_TERM_SOURCE_CALIBRATION_FREEZE_V01.md`.

No Event Futures outcome may open until:
1. BTC and ETH calibration minima pass;
2. nearest-rank P95 thresholds are computed exactly from the frozen calibration;
3. a separate numeric activation freeze commits those thresholds and artifact hashes.
