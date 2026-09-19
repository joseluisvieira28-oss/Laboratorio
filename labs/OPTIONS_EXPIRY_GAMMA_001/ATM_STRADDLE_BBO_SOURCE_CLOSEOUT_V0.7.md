# OPTIONS-EXPIRY-GAMMA-001 — ATM STRADDLE BBO SOURCE CLOSEOUT V0.7

Date: 2026-09-19
Source gate: OEG-ATM-STRADDLE-BBO-SOURCE-007
Canonical run: 35452239900
Canonical head SHA: 89a932641af76fa7d57516cce0bca4c078303432
Aggregate artifact: OEG_ATM_STRADDLE_BBO_SOURCE_V0_7
Artifact ID: 10587207398
Artifact ZIP SHA256: 06d61ab9ebb58d501b84f158c03bbd6204da5272d17b7a431888b26f273399b4

## FINAL CLASSIFICATION

ATM_STRADDLE_BBO_SOURCE_FEASIBLE

## OUTCOME-BLIND RESULT

All four deterministic probes passed:
- 2021-01-01
- 2022-01-01
- 2023-01-01
- 2024-01-01

Each date produced a prospectively selected ATM call+put pair with 7-14 DTE and a two-sided, non-crossed BBO with positive displayed amounts on both legs:
- first valid quote at/after 12:00 UTC within +5 minutes;
- first valid quote at/after 23:55 UTC before 24:00 UTC.

No bid/ask price values were retained. No option premium, return or PnL was computed.

## INTERPRETATION

The free Tardis Deribit OPTIONS quotes route is technically capable of supporting causal historical ATM-straddle entry/exit semantics for this family. This does not establish adequate full-corpus coverage or positive economics.

## NEXT SOURCE QUESTION

If an economic Discovery independently passes, execute a separately frozen 48-date BBO census using the same pair selection and quote-presence rules before any execution MVE.

2025/2026 access: false
Live trading: false
Exchange mutation: false
Merge to main: false
