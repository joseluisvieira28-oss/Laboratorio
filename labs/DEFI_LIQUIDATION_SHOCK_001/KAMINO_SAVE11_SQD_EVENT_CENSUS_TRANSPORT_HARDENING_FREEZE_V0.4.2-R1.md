# KAMINO + SAVE11 SQD EVENT CENSUS — TRANSPORT HARDENING FREEZE V0.4.2-R1

Lab: DEFI-LIQUIDATION-SHOCK-001

## Scope

This freeze changes transport handling only. It does not change the scientific population, source semantics, decoder, instruction identity, success/failure semantics, UTC membership, timestamp boundary rule, +16 slot transport envelope, deterministic RAW sampling rule, or any economic hypothesis.

## Frozen authority chain

The scientific day runner remains:

`source/run_sqd_event_census_partition_v0_4_2.py`

Transport R1 orchestrates that frozen runner without modifying it:

`source/run_sqd_event_census_partition_transport_r1.py`

## Trigger eligible for retry

A retry is permitted only when the frozen runner emits a day receipt with:

- classification = `SOURCE_CHUNK_BLOCKED`
- stream_complete = false
- detail = `empty_200_response`

HTTP 200 with an empty body is transport-incomplete evidence. It is not accepted as proof of a zero-event day.

## Retry rule

- Maximum attempts per UTC day: 8.
- Each attempt reruns the same frozen UTC day through the same V0.4.2 runner.
- The output directory for that attempt is cleared before the retry.
- Partial evidence from failed attempts is never merged with a later successful attempt.
- The first complete `PARTITION_COMPLETE` result for that day is preserved as the day authority receipt.
- Backoff is deterministic and bounded.
- If all 8 attempts exhaust, classification remains fail-closed / technical-source blocked.
- Any failure whose detail is not exactly `empty_200_response` is not retried by Transport R1 and remains fail-closed for diagnosis.

## Provenance hardening

Authoritative R1 workflows pin checkout to `${{ github.sha }}` so jobs in the same run cannot silently consume different branch revisions.

## Scientific invariants

Transport R1 MUST NOT alter:

- Kamino start: 2023-11-17T14:48:24Z
- Save11 start: 2024-07-19T19:30:52Z
- common end exclusive: 2025-01-01T00:00:00Z
- Kamino program/discriminator
- Save/Solend program/tag 0x11
- outer + inner/CPI preservation
- exact local UTC timestamp membership
- timestamp seed +16 slot query envelope
- instruction key = protocol + signature + instructionAddress
- success and failed-attempt ledger separation
- anomaly fail-closed semantics
- RAW sample selection and Official Solana RPC reconciliation

## Firewall

Still prohibited in this phase:

- prices
- returns
- PnL
- future direction
- economic outcomes
- protected 2025/2026 outcomes
- live trading
- orders
- wallets
- exchange mutation
- paid sources
- account creation
- merge to main

## Valid terminal states

Transport hardening validation:

- `TRANSPORT_R1_VALIDATION_PASS`
- `TECHNICAL_BLOCKED`
- `SOURCE_ANOMALY_FAIL_CLOSED`

Full census authority remains unchanged:

- intermediate: `SQD_EVENT_CENSUS_COMPLETE_PENDING_RAW_SAMPLE`
- RAW: `RAW_SAMPLE_RECONCILIATION_PASS`
- final only if both pass: `KAMINO_SAVE11_EVENT_CENSUS_SOURCE_PASS`

A transport or source blocker is never `NO_EDGE`.
