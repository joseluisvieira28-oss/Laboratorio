# AAVE-HF-CROWDING-001 — CALIBRATION TECHNICAL AMENDMENT V0.1A

Date: 2026-09-24
Reason: source-schema contract violation before any predictor value opened.

The initial calibration runner used get_reserve_holders(limit=5).
The official Aave MCP schema permits only limit=10 or limit=50.

Observed initial snapshot:
- 92 reserves;
- 92 holder-query errors;
- 0 borrower wallets;
- 0 health-factor values;
- 0 outcomes.

Scientific state therefore remained unopened.

Technical correction only:
- replace fixed holder limit 5 with the smallest schema-valid value, 10;
- preserve all-reserve enumeration, borrow side, deduplication, equal wallet weighting, HF extraction, thresholds, calibration gates and every outcome firewall;
- permit exactly one same-date retry only when the existing snapshot has 0 valid HF values and holder_query_error_count == reserve_count.

No scientific parameter is changed after seeing any predictor/outcome value because none were opened.
