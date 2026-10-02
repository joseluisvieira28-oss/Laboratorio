# DLS ROUTE A3 — PROTECTED 2025 SOURCE ACQUISITION FREEZE V0.1

Date: 2026-10-02
Status: FROZEN SOURCE-ONLY

Authority: Route A3 equivalence run 36969189081 / artifact 11210144684 = ROUTE_A3_GTFA_EQUIVALENCE_PASS.

Acquire only source transactions in:
2025-01-01T00:00:00Z <= blockTime < 2026-01-01T00:00:00Z.

Preserve exactly the four existing protocol classes, canonical RAW normalizer, program IDs, discriminators, instruction paths, shape rules, collateral-unit mapping, target SOL mint, and 60-second clustering rule.

Transport only:
- Helius getTransactionsForAddress
- full transaction details
- ascending order
- UTC month blockTime filter
- succeeded status
- cursor pagination to exhaustion
- fail closed on schema, pagination, duplicate, timestamp, normalization, mapping, or integrity conflict.

Materialize exactly 48 protocol-month receipts compatible with the existing V0.2 source finalizer. Shared Solend transport may produce save0c and save11 receipts from one monthly query.

Only an explicit PROTECTED_2025_SOURCE_AUTHORITY_PASS from the unchanged finalizer permits the separately frozen economic holdout to proceed.

No market price, return, PnL, 2026 outcome, parameter change, or main merge is part of this source acquisition.
