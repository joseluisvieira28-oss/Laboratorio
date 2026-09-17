# DEFI-LIQUIDATION-SHOCK-001 — BOUNDED CENSUS PLAN V0.1

Date: 2026-09-17  
Branch: `defi-liquidation-shock-v0.1`  
Posture: `RESEARCH_ONLY / SOURCE_ONLY / OUTCOME_BLIND / FAIL_CLOSED`

## Purpose

Design the historical candidate census after the transaction-status semantics gate passed, without opening market outcomes and without running an unbounded 2021-2024 JavaScript-Base58 scan.

This plan does NOT authorize prices, returns, PnL, future direction, tuning, live trading, exchange mutation, wallets, alerts/webhooks, or merge to main.

## Frozen transaction execution rule

Canonical successful-transaction predicate:

```sql
status = 'Success'
```

Fail-closed consistency check:

```sql
status = 'Success' AND COALESCE(err, '') = ''
```

Rows whose `status` and `err` disagree are `SOURCE_ANOMALY_FAIL_CLOSED` and cannot enter realized forced flow.

Failed discriminator/tag matches are retained separately as `LIQUIDATION_ATTEMPT_FAILED_NOT_REALIZED`.

## Query implementation

Use:

`source/BIGQUERY_BOUNDED_CANDIDATE_CENSUS_V0_2.sql`

Properties:

- exactly one frozen program ID per run;
- explicit UTC chunk bounds;
- hard SQL assertion that a chunk cannot exceed 7 days;
- `Instructions.block_timestamp` bounded for partition pruning;
- exact `Instructions.program_id` predicate for program-ID clustering;
- `Transactions.block_timestamp` bounded for partition pruning;
- transaction signature/slot join to obtain execution state before archival Helius verification;
- outer + inner/CPI candidates retained;
- successful reference candidates and failed attempts separated;
- no historical-authority upgrade is inferred from a discriminator match or transaction success.

## Operational chunk policy

The existing one-day candidate smoke test showed that the JavaScript Base58 UDF can be runtime-heavy even when bytes scanned are modest. Therefore chunk size is an infrastructure parameter only and MUST NOT be selected using market outcomes or candidate profitability.

Initial execution policy:

1. Drift v2: start at **1 UTC day per chunk**.
2. Save/Solend, marginfi v2, Kamino Lend: start at **1 UTC day per chunk** as the conservative baseline.
3. A protocol may be expanded prospectively to 2-7 day chunks only after source-only runtime/bytes measurements show the smaller chunk is comfortably below operational limits.
4. Never exceed 7 days in this V0.1 plan.
5. Before every execution, inspect estimated bytes.
6. If estimate is **>100 GB**, DO NOT RUN; split the chunk.
7. Runtime/bytes-based splitting is infrastructure remediation, not scientific tuning, because it never uses prices, returns, direction or PnL.

## Historical authority firewall

Candidate enumeration is allowed while historical version mapping remains incomplete, but candidate rows must remain reference-only until the protocol/date interval is authoritative.

Current boundaries remain those in `HISTORICAL_DECODER_AUTHORITY_MATRIX_V0.1.md`:

- Save `0x0c`: source-code support from 2021-12-08; chain activation boundary still matters.
- Save `0x11`: no back-application to 2021-2023/early 2024; exact activation boundary pending.
- marginfi v2: historical version map pending.
- Kamino Lend: public repository decoder support from 2024-09-26; earlier interval pending.
- Drift v2: historical version map pending.

No `SOURCE_DATA_PASS` may be issued until historical decoder authority is completed for every interval used in the authoritative realized-event population.

## Helius policy

Do NOT send every BigQuery row to Helius.

The order is:

1. BigQuery protocol/date bounded candidate detection.
2. BigQuery transaction execution-state classification.
3. Exclude failed transactions from the realized-event verification queue, while retaining them in the attempt ledger.
4. Deduplicate successful candidate transactions by signature for RPC work.
5. Helius RAW verification only for classes/intervals requiring archival reconciliation under the source authority.
6. Preserve exact RPC receipts/hashes and fail closed on any mismatch.

This prevents failed transactions from consuming expensive archival verification intended for realized flow, while preserving failed-attempt evidence separately.

## Census outputs

Each chunk must produce or support two logically separate ledgers:

### A. Successful reference candidates

`SUCCESSFUL_REFERENCE_CANDIDATE_PENDING_HISTORICAL_AUTHORITY_AND_RAW_CLASS_VALIDATION`

These are NOT yet economic events and are NOT automatically authoritative liquidations.

### B. Failed attempts

`LIQUIDATION_ATTEMPT_FAILED_NOT_REALIZED`

These must never enter realized forced-flow event counts.

Any inconsistent transaction metadata is:

`SOURCE_ANOMALY_FAIL_CLOSED`

and blocks that row from promotion.

## Stop conditions before Discovery

Do not open any market outcome until all of the following are true:

1. bounded source census complete for the frozen window/protocol scope;
2. chunk completeness audited;
3. historical decoder authority completed for authoritative intervals;
4. successful transaction rule applied consistently;
5. required absent-class validation completed when Kamino / Save 0x0c first appear;
6. Helius RAW validation/class reconciliation complete where required;
7. numerical sample gate frozen prospectively;
8. final pre-Discovery authority written.

Until then the lab remains `SOURCE GATE ACTIVE`.
