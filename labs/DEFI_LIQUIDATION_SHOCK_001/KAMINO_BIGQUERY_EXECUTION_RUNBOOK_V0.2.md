# DEFI-LIQUIDATION-SHOCK-001 — KAMINO BIGQUERY EXECUTION RUNBOOK V0.2

Date: 2026-09-18
Branch: defi-liquidation-shock-v0.1
Posture: SOURCE_ONLY / OUTCOME_BLIND / FAIL_CLOSED

## Exact next action

Execute only:
labs/DEFI_LIQUIDATION_SHOCK_001/source/BIGQUERY_KAMINO_CORRECTED_SMOKE_TEST_V0_2.sql

Do not edit the date window, program ID, discriminator, success predicate, selected columns or classification logic.

Correct discriminator: b1479abce2854a37
Retired wrong discriminator: b1479acce2854a37

## BigQuery safety

1. Paste the SQL unchanged.
2. Inspect estimated bytes before execution.
3. If estimated bytes >100 GB: STOP and do not run.
4. If <=100 GB: execute once.
5. Export the result unchanged as CSV.
6. Do not sort/filter/delete/edit rows in the CSV.

Recommended evidence filename: DLS_KAMINO_CORRECTED_SMOKE_V02.csv

## Local adjudication

PowerShell:
python labs/DEFI_LIQUIDATION_SHOCK_001/source/adjudicate_kamino_corrected_smoke_v0_2.py --input DLS_KAMINO_CORRECTED_SMOKE_V02.csv --output DLS_KAMINO_CORRECTED_SMOKE_V02_ADJ

The adjudicator creates all source rows, successful reference candidates, failed attempts, source anomalies and a machine-readable receipt.

## If successful reference candidates exist

Use KAMINO_SUCCESSFUL_REFERENCE_CANDIDATES_RAW_VERIFY_INPUT_V0.2.csv directly with:

python labs/DEFI_LIQUIDATION_SHOCK_001/source/verify_bigquery_candidates_v0_1.py --input DLS_KAMINO_CORRECTED_SMOKE_V02_ADJ/KAMINO_SUCCESSFUL_REFERENCE_CANDIDATES_RAW_VERIFY_INPUT_V0.2.csv --out-dir DLS_KAMINO_RAW_VERIFY_V02

The RPC URL/API key must remain local and must not be pasted into chat or committed.

## Interpretation rules

Successful candidates found: KAMINO_CORRECTED_SMOKE_CANDIDATES_FOUND_RAW_VALIDATION_REQUIRED. This is not SOURCE_DATA_PASS and not an economic result.

Failed attempts only: KAMINO_CORRECTED_SMOKE_FAILED_ATTEMPTS_ONLY_NO_REALIZED_EVENT_IN_SMOKE_DAY. Failed attempts remain source evidence but do not count as realized forced flow.

Zero candidates: KAMINO_CORRECTED_SMOKE_ZERO_CANDIDATES. This means only that the exact smoke day has no corrected reference candidate. It is not evidence that Kamino lacks historical liquidations.

Any anomaly: KAMINO_CORRECTED_SMOKE_SOURCE_ANOMALY_FAIL_CLOSED. Stop. Do not promote rows.

## Outcome firewall

Forbidden: price data, future returns, PnL, market direction, threshold selection, protocol selection by outcomes, live trading, orders, wallets, exchange mutation, alerts/webhooks and main merge.

## Current authority

- corrected source QA run 35349082272 — SUCCESS
- implementation freeze commit 3056331bfc33f80ac26f2c81eecc944096c10aa6
- V0.1 preflight is historical/manual-only and superseded for future execution.
