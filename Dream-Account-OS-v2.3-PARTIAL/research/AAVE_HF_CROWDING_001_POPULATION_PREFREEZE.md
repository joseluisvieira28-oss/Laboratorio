# AAVE-HF-CROWDING-001 — BORROWER POPULATION CENSUS — PRE-FREEZE

Date: 2026-09-24
Stage: SOURCE POPULATION ONLY
Outcome access: FORBIDDEN

## Population rule

Use the official Aave MCP read-only endpoint.

1. Enumerate **all Aave v4 markets/reserves** returned by `get_markets(version="v4")`.
2. For every returned reserveId, call `get_reserve_holders(side="borrow", version="v4")`.
3. Request the same fixed limit for every reserve: **50 borrowers**.
4. Deduplicate borrower addresses across reserves.
5. Retain only:
   - number of v4 reserves;
   - reserves queried successfully;
   - reserves with >=1 borrow holder;
   - raw holder-row count;
   - deduplicated borrower count;
   - one-way SHA256 hashes of borrower addresses for reproducibility.
6. Do NOT retain or report debt amount, collateral amount, health factor, prices, rates, balances or outcomes.

## Source population gate

PASS only if:
- >= 5 v4 reserves returned;
- >= 5 reserves successfully queried on borrow side;
- >= 25 deduplicated borrower addresses recovered;
- zero mutation/action tool calls.

PASS classification:
`AAVE_V4_BORROWER_POPULATION_SOURCE_PASS`

Otherwise:
`AAVE_V4_BORROWER_POPULATION_SOURCE_INSUFFICIENT`

A PASS authorizes only the next pre-frozen health-factor cohort definition. It does not authorize a predictive test or PnL.
