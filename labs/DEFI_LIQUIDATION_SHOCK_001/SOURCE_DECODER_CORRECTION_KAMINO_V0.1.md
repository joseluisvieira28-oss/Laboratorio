# DEFI-LIQUIDATION-SHOCK-001 — KAMINO SOURCE DECODER CORRECTION V0.1

Date: 2026-09-17  
Branch: `defi-liquidation-shock-v0.1`  
Posture: `SOURCE_ONLY / OUTCOME_BLIND / FAIL_CLOSED`

## Classification

`DATA_FAILURE / SOURCE_DECODER_TRANSCRIPTION_ERROR` for the Kamino candidate-detection path only.

This is NOT `NO_EDGE`, NOT `NEGATIVE_EXPECTANCY`, and does not invalidate the already reconciled non-Kamino RAW sample.

## Error found

The frozen registry and early BigQuery candidate SQL used this Kamino Anchor discriminator:

`b1479acce2854a37`

That value is wrong by one nibble-pair (`cc`).

The official `Kamino-Finance/klend-sdk` historical instruction builder at commit
`fdffe6b6115e254020af2bb52fa1ed8e3b73f438` explicitly encodes identifier bytes:

`[177, 71, 154, 188, 226, 133, 74, 55]`

Those bytes are hex:

`b1479abce2854a37`

The deterministic Anchor discriminator calculation for
`global:liquidate_obligation_and_redeem_reserve_collateral` also yields:

`b1479abce2854a37`

## Scientific consequence

All previous statements of the form **"no Kamino liquidation candidate found"** that were produced by a query using `b1479acce2854a37` are invalidated for Kamino only.

They MUST NOT be interpreted as protocol absence, liquidation absence, insufficient sample, or no edge.

The 2024-12-15 candidate smoke test must be rerun for Kamino with the corrected prefix before the Kamino source class can be considered validated.

The existing 23-row RAW validation sample contains no Kamino row because the candidate registry used the wrong prefix. Therefore it remains valid evidence for the rows actually sampled, but it cannot be used as Kamino decoder validation.

## Correct frozen Kamino decoder

Program:

`KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD`

Instruction:

`liquidate_obligation_and_redeem_reserve_collateral`

Anchor 8-byte discriminator:

`b1479abce2854a37`

## Historical source boundary improvement

The official `Kamino-Finance/klend` repository contains its initial `Program code v1` commit
`57074f4599a36ab0b433a71599b206c73efe1fd7`, dated 2023-11-17.
That state already declares the frozen mainnet program ID and exposes
`liquidate_obligation_and_redeem_reserve_collateral`.

Because Anchor derives the instruction discriminator deterministically from the instruction name, this provides public source-code decoder support by 2023-11-17, substantially earlier than the previously recorded 2024-09-26 SDK boundary.

This still does NOT prove the exact on-chain activation timestamp. Chain activation remains pending a source-only first-seen successful candidate probe.

## Required remediation

1. Preserve old receipts unchanged for audit history.
2. Use only corrected SQL versions for future Kamino work.
3. Rerun a corrected Kamino candidate smoke test.
4. If candidates appear, take a deterministic Kamino RAW sample and verify bytes/program/CPI/execution state.
5. Pin first successful on-chain candidate at or after the source-supported boundary.
6. Do not issue `SOURCE_DATA_PASS` until Kamino remediation and the other historical authority boundaries are complete.

No prices, returns, PnL, future direction, trading outcomes, exchange mutation, wallets, live orders or main merge were used to discover or correct this error.
