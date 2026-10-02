# DLS PROTECTED-2025 MARGINFI — STREAM-PAGED TRANSPORT ADDENDUM V0.3A

Date: 2026-10-02
Status: FROZEN TECHNICAL TRANSPORT / SOURCE ONLY / MARKET OUTCOMES CLOSED

Purpose:
Reduce transport overhead for the already-frozen Marginfi programId-only Protected-2025 source route.

Scientific semantics remain exactly those of:
- PROTECTED_2025_SOURCE_AUTHORITY_FREEZE_V0.1.md
- DLS_MARGINFI_PROGRAM_ONLY_SQD_TRANSPORT_ADDENDUM_V0.3.md
- DLS_MARGINFI_PROGRAM_ONLY_IMPLEMENTATION_BINDING_V0.3.md

The only additional transport change:
- replace fixed 10,000-slot request_to chunks with request_to = exact month end slot;
- after each SQD NDJSON response, advance deterministically to last observed block + 1;
- continue until the exact end-slot boundary.

This transport pattern is inherited from the pre-outcome Marginfi field-enrichment route that exact-joined
the canonical 2023-2024 source population.

Unchanged:
program ID, local d6a997d5fba756db prefix, success predicate, account roles, asset_bank mapping,
bank dataSlice, event identity, timestamp bounds, output schema, duplicate/error rules and firewalls.

No price/return/PnL/funding/2026/trading data.
No scientific threshold or event definition changes.
Trading authority: NONE.
