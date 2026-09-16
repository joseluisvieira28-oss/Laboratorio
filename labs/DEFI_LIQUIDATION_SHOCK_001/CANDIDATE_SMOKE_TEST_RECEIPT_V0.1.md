# DEFI-LIQUIDATION-SHOCK-001 — BigQuery Liquidation Candidate Smoke Test Receipt V0.1

Date: 2026-09-16
Branch: `defi-liquidation-shock-v0.1`

## Classification

`CANDIDATE_SOURCE_MATCH_CONFIRMED / HISTORICAL_AUTHORITY_NOT_YET_GRANTED`

This receipt records a one-day, source-only, outcome-blind BigQuery smoke test. It is not an edge result and does not grant `SOURCE_DATA_PASS`.

## Frozen smoke-test window

`[2024-12-15T00:00:00Z, 2024-12-16T00:00:00Z)`

Query: `source/BIGQUERY_LIQUIDATION_CANDIDATE_SMOKE_TEST_V0_2.sql`

Pre-execution BigQuery estimate reported by the user: approximately 1 GB.

## Returned candidate matches

| protocol | match_name | candidate_instruction_rows | candidate_transactions | candidate_outer_rows | candidate_inner_cpi_rows | first_candidate_utc | last_candidate_utc |
|---|---|---:|---:|---:|---:|---|---|
| drift_v2 | liquidate_borrow_for_perp_pnl | 1 | 1 | 1 | 0 | 2024-12-15 04:21:43 UTC | 2024-12-15 04:21:43 UTC |
| drift_v2 | liquidate_perp | 16,753 | 16,753 | 14,367 | 2,386 | 2024-12-15 00:41:16 UTC | 2024-12-15 23:56:38 UTC |
| drift_v2 | liquidate_perp_pnl_for_deposit | 7 | 7 | 7 | 0 | 2024-12-15 07:10:03 UTC | 2024-12-15 07:44:00 UTC |
| drift_v2 | liquidate_spot | 914 | 914 | 911 | 3 | 2024-12-15 01:05:29 UTC | 2024-12-15 23:26:45 UTC |
| marginfi_v2 | lending_account_liquidate | 9 | 9 | 9 | 0 | 2024-12-15 04:56:45 UTC | 2024-12-15 23:52:19 UTC |
| save_solend | LiquidateObligationAndRedeemReserveCollateral | 26 | 26 | 1 | 25 | 2024-12-15 06:59:49 UTC | 2024-12-15 23:23:59 UTC |

No row was returned in this one-day smoke test for Kamino Lend, Save/Solend `LiquidateObligation` (0x0c), or the other pre-registered Drift liquidation-family references. Absence in this one-day window is not evidence of historical absence.

The six returned rows sum to 17,710 candidate instruction matches. This sum must not be interpreted as 17,710 unique liquidation transactions across families because transaction overlap between different match names has not yet been ruled out.

## Scientific interpretation

1. The BigQuery source contains raw instruction data that can be discriminator-matched for the frozen protocol set.
2. Candidate liquidation-family matches are non-zero for Drift v2, marginfi v2, and Save/Solend in the bounded day.
3. CPI/inner-instruction coverage is scientifically material. Drift `liquidate_perp` included 2,386 inner/CPI matches, while Save/Solend `LiquidateObligationAndRedeemReserveCollateral` was predominantly inner/CPI (25 of 26). Any census that ignores `parent_index`/inner instructions would be incomplete.
4. These are reference-discriminator candidates only. Historical program/IDL applicability and raw archival RPC reconciliation remain mandatory before an event becomes authoritative.
5. No prices, returns, PnL, market direction, future labels, or trading outcomes were opened.

## Current state

`SOURCE_COVERAGE_CONFIRMED`
`CANDIDATE_EXTRACTION_ROUTE_CONFIRMED`
`SOURCE_DATA_PASS_NOT_YET_GRANTED`
`DISCOVERY_CLOSED`

## Next valid transition

Build a bounded historical candidate census using the same frozen program IDs/discriminators, preserve outer and CPI matches, then complete historical decoder-version authority and reconcile candidate signatures against raw archival RPC/Helius evidence before freezing the final pre-discovery authority.
