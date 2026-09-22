# DEFI-LIQUIDATION-SHOCK-001 — SOLARCHIVE TRANSPORT EQUIVALENCE FREEZE V0.1

Date: 2026-09-22
Status: FROZEN PRE-ACCESS / SOURCE-ONLY / OUTCOME-BLIND

## Candidate transport

SolArchive public historical Solana transaction Parquet archive.

Public documentation states:
- no API key or registration is required;
- transaction data are daily-partitioned Parquet;
- source lineage is the public Solana / Google BigQuery export;
- non-vote transactions are preserved, with vote traffic filtered.

This is evaluated strictly as a technical/source transport replacement. It is not a new hypothesis, protocol, event definition, market outcome, threshold or direction.

## Scientific authority unchanged

Lab: DEFI-LIQUIDATION-SHOCK-001
Protocol: kamino_lend
Program: KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD
Instruction: liquidate_obligation_and_redeem_reserve_collateral
Frozen discriminator: b1479abce2854a37
Frozen source-supported boundary: 2023-11-17T13:25:35Z
Frozen terminal window: [2021-01-01, 2025-01-01) UTC
Frozen chronological chunk maximum: 7 days.

## Pre-access equivalence sample

Only the already-open source-only smoke date 2024-12-15 may be used for transport equivalence.

Known BigQuery corrected smoke reference:
- 41 candidate rows;
- 16 successful unique transactions;
- 25 failed unique attempts;
- 0 source anomalies;
- all 16 successful references subsequently RAW-verified on official public Solana RPC.

The equivalence audit may inspect:
- transaction schema;
- day index/file metadata;
- signatures;
- slots;
- timestamps;
- transaction success/error state;
- account/program references;
- program logs;
- raw transaction/instruction representation if present.

Forbidden:
- prices;
- future returns;
- PnL;
- direction;
- economic outcomes;
- 2025/2026 market data;
- event-size tuning;
- protocol switching;
- candidate thresholds.

## Acceptance gate

Transport may advance only if the 2024-12-15 audit can deterministically reproduce the already-known Kamino corrected smoke population or provide a deterministic superset that can be reduced to the exact frozen event class by the same RAW discriminator verification.

At minimum:
1. all 16 frozen successful signatures must be present with exact slot and success state;
2. all 25 frozen failed-attempt signatures must be present with exact slot and failed state, if failure state is represented;
3. no known successful signature may be misclassified;
4. timestamp identity must be compatible with the frozen UTC ordering;
5. the transport must expose enough transaction identity to allow final public-RPC RAW verification of the discriminator.

If any requirement fails: SOLARCHIVE_TRANSPORT_EQUIVALENCE_FAIL_CLOSED.
If metadata/schema are insufficient: SOLARCHIVE_TRANSPORT_INSUFFICIENT.
If requirements pass: SOLARCHIVE_TRANSPORT_EQUIVALENCE_PASS and a separate prospective execution amendment must be frozen before scanning pre-smoke history.

No global SOURCE_DATA_PASS is granted by this audit.
