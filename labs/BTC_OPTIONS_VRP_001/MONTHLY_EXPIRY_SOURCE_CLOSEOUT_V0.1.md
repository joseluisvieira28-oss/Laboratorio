# BTC-OPTIONS-VRP-001 — MONTHLY EXPIRY SOURCE CLOSEOUT V0.1

Date: 2026-09-18
Source gate: OVRP-MONTHLY-EXPIRY-SOURCE-001
Canonical corrected run: 35310337109
Head SHA: b9c71d653903b322e1da59bf980fb2163ec242a2
Aggregate artifact: BTC_OPTIONS_VRP_001_MONTHLY_EXPIRY_SOURCE_V0_1
Aggregate artifact ID: 10533316936
Aggregate artifact ZIP SHA256: 7e4ade69ccbc45214a77ee1a642d9a72901d66e8f97cc17ef46e2e8b8a0cea1f
Aggregate receipt SHA256: 3d473fc0cc2a6ceb89129e2bab0fd4a3c2835ffaf0824276efd3a72c97a02374

## FINAL CLASSIFICATION

MONTHLY_EXPIRY_SOURCE_DATA_INSUFFICIENT

## FROZEN COVERAGE

- 2021: 7 / 9 complete
- 2022: 8 / 12 complete
- 2023: 9 / 12 complete
- 2024: 10 / 12 complete
- Total complete months: 34 / 45
- Distinct years: 4 / 4

Frozen source gates:
- minimum total complete months = 36 -> FAIL (34)
- minimum per-year coverage -> PASS
- minimum distinct years = 4 -> PASS

## TRANSPORT REMEDIATION HISTORY

Initial run 35310172555 incorrectly appeared to have zero old delivery coverage because the Deribit delivery-price endpoint returned only 100 rows despite count=1000. This was corrected in V0.1.1 by deterministic pagination. No scientific gate, DTE bound or sample date changed.

## ADJUDICATION

No performance outcomes were opened. Do not lower 36, widen DTE below 25 days, add paid dates, use 2025/2026, or reinterpret 34 as a PASS under this source-gate ID.

The broader BTC Options VRP parent remains DISCOVERY_PASS_VRP_EXISTS and the Tardis paid BBO route remains PAID_SOURCE_ROUTE_FEASIBLE. This particular free first-day monthly-to-expiry route is source-insufficient under its frozen coverage requirement.

## SAFETY

- strategy PnL opened: false
- returns opened: false
- delivery price values retained: false
- paid subscription used: false
- API key used: false
- 2025/2026 accessed: false
- live trading / exchange mutation / wallet access / main merge: false
