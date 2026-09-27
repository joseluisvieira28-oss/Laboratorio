# POLY-COMBINATORIAL-ARB-001 — ACTIVE NEG-RISK POPULATION CENSUS V0.4

Date: 2026-09-27
Status: FROZEN_PRE_RUN / SOURCE-METADATA-ONLY / V0.3 TRANSPORT CORRECTION

## Correction
V0.3 requested limit=500 and incorrectly treated a 100-row response as terminal. The provider effectively returned 100 rows, so V0.3 did not establish complete pagination.

V0.4 changes only pagination transport:
- request limit=100;
- offset increases by the actual returned row count;
- continue until a page returns fewer than 100 rows;
- maximum 100 pages as a fail-safe;
- duplicate event IDs are detected and fail the completeness flag.

No economic variable, book, price, fee, spread, PnL or outcome is opened.

## Output
Same metadata-only population geometry as V0.3, plus unique-event integrity and pagination evidence.
