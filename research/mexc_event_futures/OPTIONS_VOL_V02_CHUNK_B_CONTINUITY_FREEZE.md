# OPTIONS-VOL-FWD-001 V0.2 — CHUNK B CONTINUITY FREEZE

Date: 2026-10-03
Status: PRE-COLLECTION / TECHNICAL CONTINUITY ONLY

Scientific rule remains exactly:
`OPTIONS_VOL_SOURCE_CALIBRATION_FREEZE_V02.md`.

Chunk A is canonically anchored by:
`OPTIONS_VOL_V02_CHUNK_A_CANONICAL_STATE.json`.

## Non-overlap requirement

Chunk A final observed minute:
`1791046560000`.

Chunk B MUST choose its first UTC minute strictly greater than:
`1791046560000`.

Any equality or earlier minute => FAIL CLOSED.

A gap between chunks is allowed and remains unobserved/missing time.
No gap may be backfilled.

Chunk B remains:
- Deribit public source-only;
- one source round per UTC minute;
- no same-minute retry;
- no MEXC;
- no outcome;
- no threshold commitment.

The original calibration boundary remains unchanged.
