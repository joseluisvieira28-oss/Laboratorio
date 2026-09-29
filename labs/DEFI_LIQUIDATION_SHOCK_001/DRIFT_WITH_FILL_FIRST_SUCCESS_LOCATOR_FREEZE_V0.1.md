# DEFI-LIQUIDATION-SHOCK-001 — DRIFT WITH-FILL FIRST-SUCCESS LOCATOR FREEZE V0.1

Date: 2026-09-29
Status: FROZEN SOURCE-ONLY LOCATOR / NOT CENSUS AUTHORITY

Purpose:
find the earliest realized successful Drift liquidate_perp_with_fill instruction after the frozen Drift lower boundary, only to unblock source-semantic inspection while the full census continues.

Discriminator:
5f6f7c6956a9bb22

Window:
2022-11-04T15:17:54Z <= timestamp < 2025-01-01T00:00:00Z.

The locator may stop at the first successful committed instruction with:
- parent transaction err = null
- isCommitted = true
- instruction error = null
- exact signature + instructionAddress.

If found:
DRIFT_WITH_FILL_FIRST_SUCCESS_FOUND_PENDING_RAW_SEMANTICS.

If the stream reaches the upper boundary with none:
DRIFT_WITH_FILL_FIRST_SUCCESS_NOT_FOUND.

This locator cannot establish population prevalence or family coverage.
No price/return fields are accessed.
