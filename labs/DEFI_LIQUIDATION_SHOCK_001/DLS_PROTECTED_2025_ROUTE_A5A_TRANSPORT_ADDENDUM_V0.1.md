# DLS PROTECTED-2025 — ROUTE A5A TRANSPORT ADDENDUM V0.1

Date: 2026-10-02
Status: FROZEN TECHNICAL TRANSPORT / SCIENCE UNCHANGED / OUTCOMES CLOSED

## Preconditions

This route may execute only after immutable receipts prove:
1. ROUTE_A5A_SOL_ACCOUNT_EQUIVALENCE_PASS on the exact 9,931 canonical 2024 SOL clusters.
2. SOL_ROLE_ACCOUNT_REGISTRY_2025_PASS from the source-only creation-history census.

Until both PASS: protected-2025 acquisition is CLOSED.

## Scientific semantics inherited unchanged

- exact four protocols/classes from PROTECTED_2025_SOURCE_AUTHORITY_FREEZE_V0.1;
- exact 2025 UTC window;
- exact source success semantics;
- exact account shapes and source-role semantics;
- exact SOL collateral identity;
- exact canonical identity signature + instructionAddress;
- exact 60-second clustering;
- exact finalizer finalize_protected_2025_source_v0_2.py;
- 48 protocol-month receipts;
- zero duplicate/conflict requirement.

No event threshold, timing, market mapping, strategy, direction, cost or outcome rule changes.

## Technical transport

For each of 4 protocols x 12 calendar months:
- query every source-authoritative SOL role account in the frozen registry;
- signatures-only gTFA probe first;
- max 8 non-empty pages before deterministic midpoint split;
- recurse by exact integer Unix-second midpoint;
- minimum leaf 900 seconds;
- maximum depth 16;
- completed leaves fetch full transactions;
- full count must equal signatures probe count;
- exact interval partition, no gap/overlap;
- identical transaction copies from multiple role-account queries are transport duplicates and are deduplicated before canonical instruction identity;
- conflicting duplicate payloads fail closed.

Relevant instruction acceptance uses the already A2/A5A-equivalent RAW normalizer and frozen decoder/shape/role rules.

## Required partition schema

Each output must be named:
{protocol}-2025MM.json

and satisfy existing finalizer fields:
- protocol
- instruction_class
- classification = PROTECTED_2025_PROTOCOL_SOURCE_PASS
- exact window_start/window_end
- duplicate_count = 0
- error_count = 0
- rows[] containing signature, instructionAddress, timestamp, collateral_mint

Source-only transport diagnostics may be additional fields.

## Final source gate

Run the existing frozen:
source/finalize_protected_2025_source_v0_2.py

Only:
PROTECTED_2025_SOURCE_AUTHORITY_PASS

may authorize the already-frozen 2025 economic holdout.

## Firewall

No Binance/MEXC market payload before final source PASS.
No protected 2025 prices/returns/PnL.
No 2026 outcomes.
No post-outcome tuning.
No purchase.
No live trading/orders/wallet/exchange mutation.
No main merge.
Trading authority: NONE.
