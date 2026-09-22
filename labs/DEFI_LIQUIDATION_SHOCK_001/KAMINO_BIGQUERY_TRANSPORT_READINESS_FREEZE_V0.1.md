# DEFI-LIQUIDATION-SHOCK-001 — KAMINO BIGQUERY TRANSPORT READINESS FREEZE V0.1

Date: 2026-09-22
Status: FROZEN PRE-EXECUTION / SOURCE-ONLY / ZERO-BILLING

Purpose: establish whether the GitHub Actions runtime can execute the already-frozen Kamino first-success BigQuery authority without exposing credentials or opening economic outcomes.

Scientific authority remains unchanged:
- queue: FIRST_SUCCESS_PROBE_QUEUE_V0.1
- queue SHA256: d701eb6ef8835429fb3fa5cfb3cfaec370be394cad99d75f6dc1b49a9ef6b3ae
- SQL: source/BIGQUERY_BOUNDED_CANDIDATE_CENSUS_V0_3.sql
- protocol: kamino_lend
- first chunk: [2023-11-17T13:25:35Z, 2023-11-24T13:25:35Z)
- program: KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD
- discriminator: b1479abce2854a37
- max chunk: 7 UTC days
- hard scientific estimate stop: 100 GB

This readiness run may:
1. test only presence of common Google/BigQuery credential secret names;
2. install the Google Cloud CLI;
3. authenticate without printing any secret or identity value;
4. instantiate only the three frozen execution variables (chunk_start, chunk_end, target_program_id) in the canonical SQL;
5. run BigQuery DRY RUN only;
6. persist estimated bytes and transport status.

This readiness run MUST NOT execute a billable query. BigQuery dry runs are non-billable. No price data, returns, PnL, direction, market outcomes, trading, wallet or exchange mutation are authorized.

Routing:
- authenticated + dry-run <=100GB => BIGQUERY_FIRST_CHUNK_READY_FOR_EXECUTION
- authenticated + dry-run >100GB => BIGQUERY_ESTIMATE_HARD_STOP
- no usable auth/project => BIGQUERY_EXECUTION_CREDENTIAL_BLOCKED
- dry-run transport/schema error => BIGQUERY_DRY_RUN_FAIL_CLOSED
