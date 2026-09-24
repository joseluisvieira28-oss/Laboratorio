# BINANCE-COLLATERAL-HAIRCUT-001 — SOURCE EXTRACTION AMENDMENT V0.1C

Date: 2026-09-24
Outcome access before amendment: ZERO.

The official Binance article-detail endpoint proved identity, title, release timestamp and effective timestamp for all five 2024 clusters, but its CMS payload did not serialize the rendered collateral-ratio tables as HTML table tags. The rendered official Binance Support pages do expose the rows.

Before any market-price access, the exact 36 official rows were source-extracted and frozen in:
`BINANCE_COLLATERAL_HAIRCUT_001_EVENT_MANIFEST_V0.1C.json`.

Frozen clusters:
- 2024-06-10: 8 tightening rows
- 2024-06-28: 7 loosening rows
- 2024-07-30: 8 loosening rows
- 2024-09-03: 7 loosening rows
- 2024-11-29: 6 loosening rows

Total: 36 asset-events / 5 independent effective-time clusters.

V0.1C may validate official identity/timing against Binance article-detail and exact manifest invariants. It must not alter event rows after any outcome is opened.

Discovery protocol remains exactly as pre-frozen.
