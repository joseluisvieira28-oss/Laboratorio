# MSEL-002 — Committed-Gate Order Fix V0.1

Date: 2026-09-20
Status: TECHNICAL BUGFIX / SCIENCE UNCHANGED

Diagnostic run 35504244944 persisted exactly one pre-adjudication failure:
- instruction `is_committed=false`
- instruction error `custom program error: 0xbc0`
- reason emitted by implementation: `PUMP_AMM_ACCOUNT_MISMATCH`.

The frozen authority already requires BOTH:
1. `isCommitted == true` and `error == null`; and
2. for a qualifying migration, exact PumpSwap continuity.

Therefore an uncommitted failed instruction is not an eligible migration event and must be discarded before continuity validation. The prior implementation applied the continuity assertion before the already-frozen committed-state predicate.

This patch changes only predicate evaluation order:
- structural program/accounts shape check;
- frozen committed/success predicate;
- frozen PumpSwap continuity predicate;
- candidate adjudication.

No cohort, source, discriminator, account mapping, horizons, matching, statistic, threshold, direction or verdict gate changed.
No price/return/PnL outcome was opened.
