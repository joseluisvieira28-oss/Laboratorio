# DEFI-LIQUIDATION-SHOCK-001 — SAVE11 SQD INNER/CPI CALIBRATION FREEZE V0.3.1

Date: 2026-09-23
Status: TECHNICAL SUPERSESSION ONLY / SOURCE-ONLY / OUTCOME-BLIND / FAIL-CLOSED

Parent calibration V0.3:
- Kamino exact `programId + d8` control: PASS.
- Save/Solend 0x11 exact `programId + d1` selector: no row returned in the known first-success window.
- The known Save11 first-success call is an inner/CPI instruction under canonical RAW authority.

This V0.3.1 changes only the Save candidate transport filter:
- same program;
- same slot window `[278496094,278496110]`;
- same expected RAW signature/slot/time;
- SQD selector uses programId only;
- every returned Save program instruction is locally base58-decoded;
- only decoded first byte `0x11` is retained.

No date, program, tag, success predicate or expected boundary changes.

PASS requires recovery of:
- signature `WdTyQhEUhG2HjQ5LHApW8DU4aLRiKGQ5s8PZYBeoCJ8Acm6tkzqAdL4iasRYnSVnkHTVHTXu7zdgsSmDH8WmQ4L`;
- slot `278496102`;
- timestamp `2024-07-19T19:30:52Z`;
- program `So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo`;
- decoded first byte `11`;
- `transaction.err == null`;
- `instruction.isCommitted == true`;
- `instruction.error == null`;
- non-empty instructionAddress.

Classification:
- `SAVE11_SQD_INNER_CPI_CALIBRATION_PASS`
- `SAVE11_SQD_INNER_CPI_CALIBRATION_BLOCKED`
- `SOURCE_ANOMALY_FAIL_CLOSED`

If PASS, Save11 full census must use program-only SQD server filtering plus local exact `0x11` decoding, because this preserves inner/CPI coverage demonstrated by the RAW boundary.

Firewall unchanged; no economic outcomes.
