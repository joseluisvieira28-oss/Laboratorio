# DLS ROUTE A3B — STREAMING PROGRAM-HISTORY TRANSPORT ADDENDUM V0.1

Date: 2026-10-02
Status: FROZEN TECHNICAL TRANSPORT / SCIENCE UNCHANGED / PROTECTED OUTCOMES CLOSED
Branch: dls-field-enrichment-v01

## Parent authority
Inherit without modification:
- DLS_ROUTE_A3_GTFA_EQUIVALENCE_FREEZE_V0.1.md
- ROUTE_A3_GTFA_EQUIVALENCE_PASS run 36969189081 / artifact 11210144684
- DLS_ROUTE_A3_PROTECTED_2025_ACQUISITION_FREEZE_V0.1.md
- all canonical decoder/source/unit/clustering rules frozen before protected outcomes.

## Reason for transport implementation
The A3A adaptive implementation performs signatures-only probes before refetching full payloads.
On dense program histories this duplicates archival traversal and is operationally wasteful.

A3B implements the parent A3 freeze literally:
cursor pagination of FULL gTFA pages to terminal exhaustion for one exact protocol-program/month,
processing each page immediately instead of retaining a full month in memory.

No scientific rule changes.

## Exact transport
For each frozen program/month:
- method = getTransactionsForAddress
- address = exact frozen protocol program ID
- transactionDetails = full
- sortOrder = asc
- limit = 1000
- filters.blockTime = [month_start, next_month_start)
- filters.status = succeeded
- follow paginationToken until terminal absence
- no scientific page ceiling
- no sample, truncation or event prefilter.

Each page:
- must be a valid result object with data[];
- every full transaction is normalized by the A2/A3-validated canonical RAW normalizer;
- explicit success is required;
- timestamp must remain inside the exact month;
- duplicate signature with unequal payload => BLOCKED;
- nonadvancing/repeated pagination token => BLOCKED;
- empty page with a continuation token => BLOCKED;
- transport/capability exhaustion => BLOCKED.

The same 2025 canonical shapes and unit-resolution rules frozen for A3/A3A remain unchanged.

## Solend shared transport
One Solend program traversal emits both save0c and save11 month receipts from their exact frozen
discriminators. They remain separate scientific receipts.

## Output and final gate
Exactly 48 finalizer-compatible receipts are required across 2025.
The unchanged finalizer:
source/finalize_protected_2025_source_v0_2.py
must return PROTECTED_2025_SOURCE_AUTHORITY_PASS before market access.

## Operational supersession
If A3B smoke begins, any still-running A3A smoke/full acquisition may be cancelled through the
shared source-transport concurrency group. This is compute/transport supersession only.
No A3A source receipt is used unless terminally complete and independently PASS.

## Firewall
prices_2025_opened=false
returns_2025_opened=false
pnl_2025_opened=false
prices_2026_opened=false
returns_2026_opened=false
post_outcome_tuning=false
purchases=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
trading_authority=NONE
