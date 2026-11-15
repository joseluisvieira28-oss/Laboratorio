# Liquidation Exhaustion V1 — independent byte-level archived receipt check
Date: 2026-11-04. Source-only forensic. Not a historical economic backtest.

## Source custody
Original genuine GitHub Actions PR #279 full-day public Tardis source run #40896404712; artifact ID **12907307779**.
Downloaded ZIP name: github-actions-artifact-12907307779.zip.
ZIP SHA256 (recomputed on downloaded bytes): **736a010b7afe39887fde2269ccddb7b89f6de9b75ce4c18aafe4d5fc3d5e32ea**. This equals the original reported digest, so the ZIP contents match that immutable released artifact.
One entry: whole_day_receipt.json (uncompressed **456661 bytes**).
Inner whole_day_receipt.json SHA256: **bc73109b711d3d5f247b3e4e51d45d8aab4e814972c5f8c68471700a30f449fa**.

## Independently recomputed from JSON receipt (not inferred from PR prose)
- Exactly **1440** 1-minute receipt records; contiguous offsets 0..1439, original 2026-04-01 UTC.
- Sum of per-minute liquidation nested-child counts: **BTCUSDT 1318, ETHUSDT 1013**.
- Both sums equal the JSON's own declared raw_liquidations and frozen_normalized_counts fields. This is intra-artifact parity, not a full independent normalized CSV reparse.
- Positive-event minutes: **261** out of 1440.
- **1173** minutes with empty raw responses.
- Exactly **6** native collector disconnect markers in offsets **480, 481, 626, 910, 934, 1222**, corresponding to **08:00, 08:01, 10:26, 15:10, 15:34, 20:22 UTC**.
- Those six marked minutes report zero liquidation child counts, but **no one may infer zero true liquidations** during the disconnections.
- Original receipt declares can_open_outcomes=false, source_census_complete_proven=false, empty_minutes_zero_liquidations_proven=false, economic_verdict=NOT_TESTED.

## Adjudication
**ARCHIVED_HISTORY_CONTINUITY_BLOCKED** for a new causally joined exhaustion / reversal PnL study using this day as if every relevant liquidation were recorded. The ZIP checksum and intra-receipt count equality do NOT establish collector continuity, as-of executable BBO, book sequence correctness or true absence of liquidations. No trading return/PnL was opened in this check.

## Next separate forward gate
Only actual positive liquidation events accompanied by contemporaneously received, independently checked book/trade/BBO custody can make an interval eligible for subsequent *future* preregistered economic study; after missing sequences, require proven reconnect and book resnapshot, not an arbitrary retrospectively chosen buffer. Record live capture run ID, raw hash and errors before reviewing outcomes.

Historical LICP-001 PR #107 original **NO_EDGE** remains unchanged. No orders, accounts, paid sources, merge to main or 2026-09 protected holdout.
