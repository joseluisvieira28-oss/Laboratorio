# DEFI-LIQUIDATION-SHOCK-001 — SQD EVENT CENSUS EXECUTION AUTHORITY ADDENDUM V0.4.1

Date: 2026-09-23
Status: FROZEN PRE-CENSUS / SOURCE-ONLY / OUTCOME-BLIND / FAIL-CLOSED

This addendum does not alter any population, program, instruction identity, date boundary, chunk rule, success semantic, deduplication rule, RAW sample rule, or firewall in `KAMINO_SAVE11_SQD_EVENT_CENSUS_EXECUTION_FREEZE_V0.4.md`.

It corrects only the execution prerequisite after the Save/Solend 0x11 calibration learned that the authoritative first-success call is an inner CPI and therefore cannot be reliably selected by the direct `d1` server-side filter used in combined calibration V0.3.

## Superseded prerequisite wording

The V0.4 freeze stated that execution was authorized only if:

`KAMINO_SAVE11_SQD_BOUNDARY_CALIBRATION_RECEIPT_V0.3.json` == `SQD_BOUNDARY_CALIBRATION_PASS`.

That combined receipt is preserved unchanged and classified `SQD_BOUNDARY_CALIBRATION_BLOCKED` because:
- Kamino control PASSED;
- Save11 returned an empty HTTP-200 response under the direct `d1` filter.

## Replacement prerequisite

Execution is authorized only if BOTH are true:

1. Kamino control inside `KAMINO_SAVE11_SQD_BOUNDARY_CALIBRATION_RECEIPT_V0.3.json`:
   - `passed == true`;
   - exact known first-success signature recovered;
   - exact slot/program/discriminator recovered;
   - transaction `err == null`;
   - instruction committed;
   - instructionAddress present.

2. `SAVE11_SQD_INNER_CPI_CALIBRATION_RECEIPT_V0.3.1.json`:
   - classification == `SAVE11_SQD_INNER_CPI_CALIBRATION_PASS`;
   - exact known first-success signature recovered;
   - exact slot/program/tag `0x11` recovered;
   - transaction `err == null`;
   - instruction `error == null`;
   - instruction committed;
   - instructionAddress present.

Both conditions are satisfied by the already-persisted receipts on this branch.

## Execution implications

Kamino:
- may use SQD server-side filters `programId + d8=0xb1479abce2854a37`;
- every returned row is still locally base58-decoded.

Save11:
- MUST query by exact `programId` with `transaction=true`;
- MUST locally base58-decode every returned Save/Solend instruction;
- retain only instructions whose decoded first byte is `0x11`;
- preserve outer and inner/CPI instructionAddress exactly.

No economic outcome may be opened. No `NO_EDGE`, `EDGE`, promotion, score, or quasi-diamond classification may be issued from this census.

All other V0.4 requirements remain frozen and unchanged.
