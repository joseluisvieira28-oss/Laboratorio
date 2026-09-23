# DEFI-LIQUIDATION-SHOCK-001 — SQD EVENT CENSUS RUN FREEZE V0.5

Date: 2026-09-23
Status: FROZEN PRE-EXECUTION / SOURCE-ONLY / OUTCOME-BLIND / FAIL-CLOSED

Authority:
- KAMINO_SAVE11_SQD_EVENT_CENSUS_EXECUTION_FREEZE_V0.4.md
- KAMINO_SAVE11_SQD_EVENT_CENSUS_AUTHORITY_ADDENDUM_V0.4.1.md

Both calibration prerequisites are satisfied.

This run performs the complete frozen 2023/2024 Kamino + 2024 Save11 source census through the public SQD finalized Solana archive.

## Execution architecture

To make progress durable under GitHub Actions limits, the census is split into fixed calendar batches of 31 UTC days. Batch boundaries are purely calendar-derived and frozen before candidate counts are opened.

For each protocol, batch 0 starts on its authoritative first-success UTC date. Batch N starts 31 calendar days after batch N-1. The final batch is truncated at 2025-01-01 exclusive.

Each batch:
- processes every UTC day in order;
- resolves UTC midnight boundaries through SQD's timestamp-to-block endpoint;
- follows stream continuation to the day's end slot;
- writes one receipt per day, including zero-candidate days;
- writes instruction-level and successful-signature ledgers;
- never requests accounts, balances, token balances, fees, amounts, prices or market outcomes.

A batch may be retried idempotently. Dedup keys remain those frozen in V0.4.

## Protocol query rules

Kamino:
- program exact;
- server-side d8 discriminator exact;
- transaction=true;
- local base58 discriminator revalidation.

Save11:
- program exact only on server;
- transaction=true;
- local base58 first-byte == 0x11;
- outer and inner/CPI instructions retained.

## Batch completion

A batch is PASS only if:
- every required day has a receipt;
- each day reaches its frozen end slot or receives an explicit terminal 204;
- no source anomaly;
- no unresolved transport error;
- local prefix validation is exact;
- first batch recovers the already RAW-verified first-success signature.

Classification:
- `SQD_EVENT_CENSUS_BATCH_PASS`
- `SQD_EVENT_CENSUS_BATCH_BLOCKED`
- `SOURCE_ANOMALY_FAIL_CLOSED`

No economic interpretation is authorized.
