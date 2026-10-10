# CED1D-0031 — EXACT BINANCE VISION SOURCE CENSUS V0.1
Date of proof: **2026-10-10 13:54:32 UTC**. Evidence: public/no-secret independent GitHub Actions [run #38057526064](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38057526064). Source-only; no trading outcomes accessed.

## Frozen source checked
Base prefix: `https://data.binance.vision/data/futures/um/daily/bookDepth/AVAXUSDT/`, exact archive filename `AVAXUSDT-bookDepth-YYYY-MM-DD.zip` and `.CHECKSUM` sibling.

| Date UTC | ZIP HEAD | Checksum GET | Status |
|---|---|---|---|
| 2026-10-04 | 200 | 200 | PRESENT_UNVALIDATED |
| 2026-10-05 | 200 | 200 | PRESENT_UNVALIDATED |
| 2026-10-06 | 200 | 200 | PRESENT_UNVALIDATED |
| 2026-10-07 | 200 | 200 | PRESENT_UNVALIDATED |
| **2026-10-08** | **404** | **404** | **SOURCE_GAP_CONFIRMED** |
| 2026-10-09 | 200 | 200 | PRESENT_UNVALIDATED |

**Finding:** Oct 08 is an isolated provider archive hole, NOT a missing date due to generic source path format or lack of Oct09 publication. The same missing exact Oct08 path appears in the canonical persisted `CED1D_RENDER_SHADOW_V03_FAILURE` on Oct10. The 200 rows prove only URL-level availability; their contents and SHA256 **not** validated by this source-only probe. Do not claim the ZIPs are valid or the missing date is permanently unrecoverable.

## Science/governance decision
- `CED1D-0031` remains **SOURCE_BLOCKED** for complete forward evaluation at Oct08; **NOT** `NO_EDGE`, **NOT** `GO`.
- **Do not** use REST depth to approximate 2026-10-08, create fabricated records, interpolate, borrow adjacent dates, ignore the frozen +/-1% bookDepth capacity test, treat partial data as complete or retrospectively tune rules.
- Runtime `retryable_latest_archive_404` currently catches only exactly latest required archive day; Oct08 while Oct09 exists is **not** such a case. This behavior is a frozen distinction; changing it requires a separate explicit SOURCE_PENDING classification contract that never credits missing observations, preserves 404 and marks the eligible day unadjudicated.
- If exact Oct08 ZIP and its checksum later become accessible, a future provider/source gate must download and verify SHA256 and ZIP/CSV schema/day coverage **before** any forward ledger persistence. Source availability alone is not scientific eligibility.
- No source substitution, spend, authenticated account endpoints, orders, capital or main change authorized.

## Next safe checks
1. On a later date perform an exact HEAD + checksum GET probe of the **same frozen Oct08** URL; do not hammer Binance.
2. If still 404, stay blocked and request publisher repair / accept that this candidate cannot be completed under the existing data agreement. Other forward families remain independently monitored.
3. Preserve all 26 historical runtime gap receipts for independent missed-window adjudication.
