# ETF-CME-INSTFLOW-001 — SOURCE RECONNAISSANCE V0.1

STATUS: SOURCE ROUTE VIABLE / PRE-DISCOVERY NOT YET FROZEN

## Objective

Outcome-blind feasibility check only. No predictive outcomes, no PnL, no parameter tuning.

## Primary source candidate

CFTC Commitments of Traders (COT), CME Bitcoin futures, contract code `133741`.

Official evidence:
- CME Bitcoin futures launched for trade date 2017-12-18.
- CFTC Legacy Futures Only report exposes weekly CME Bitcoin positioning for code `133741`, including non-commercial long/short/spreading, commercial long/short, total and nonreportable positions, plus open interest.
- CFTC states COT reflects Tuesday open interest and publishes historical weekly reports plus annual compressed historical files.
- CFTC Public Reporting Environment supports filtered/API downloads and states it uses the same source data as traditional COT reports.

## Sample feasibility

A pre-2025 discovery sample is feasible in principle from late-2017 through 2024, giving multiple years of weekly institutional-positioning observations without opening 2025 or 2026.

## ETF overlay

US spot-Bitcoin ETF flows should NOT be the primary long-history discovery source because the sample only begins in 2024. They may be considered later as a 2024 overlay/diagnostic after the primary weekly CFTC/CME protocol is frozen, if governance permits.

## Candidate information family

Institutional positioning state / changes in regulated CME Bitcoin futures, measured from CFTC weekly positioning. Candidate fields for later protocol design include only source-native quantities such as non-commercial net positioning, commercial net positioning, spreading, open interest, and week-over-week changes. No field is yet selected as the frozen signal.

## Current gate

SOURCE_ROUTE_VIABLE.

Next authorized scientific action: design one minimal, outcome-blind pre-discovery protocol using the CFTC/CME weekly source, freeze source/signal/timing/outcome/costs/sample/MVE criteria BEFORE looking at predictive outcomes, then run a source/data gate. 2025 and 2026 remain locked.
