# DLS PROTECTED-2025 — ORDER-INSENSITIVE CANONICALIZATION ADDENDUM V0.2A

Date: 2026-10-03
Status: FROZEN TECHNICAL CORRECTION / SOURCE ONLY / OUTCOMES CLOSED

## Trigger
Finalizer-only run 37134211494 reached HYBRID_PARTITION_BLOCKED before the canonical source finalizer.
Five duplicate PASS partition identities were reported with different canonical payload hashes:
- kamino 2025-06
- save11 2025-01
- save11 2025-02
- save11 2025-03
- save11 2025-05

No price, return, PnL, funding or 2026 outcome was opened.

## Empirical source-only adjudication
For every one of the five pairs, independent artifact comparison established:
- identical classification = PROTECTED_2025_PROTOCOL_SOURCE_PASS;
- identical window_start/window_end;
- identical successful_instruction_count;
- identical sol_collateral_event_count;
- identical duplicate_count = 0;
- identical error_count = 0;
- identical firewall values;
- identical row identity set by (signature, instructionAddress);
- zero rows present in only one route;
- zero semantic field differences across common rows for:
  protocol, instruction_class, signature, instructionAddress, slot, timestamp,
  account_count, data_length, collateral_mint, collateral_decimals,
  collateral_token_mint, unit_resolution.

Observed counts:
- kamino 2025-06: 1095 vs 1095 rows
- save11 2025-01: 1141 vs 1141
- save11 2025-02: 5016 vs 5016
- save11 2025-03: 1771 vs 1771
- save11 2025-05: 392 vs 392

The first sequence-order mismatch appears at different indices, proving the V0.1 conflict was caused solely by transport row ordering.

## Technical correction
Create materializer V0.2 from V0.1 with exactly one semantic-neutral change:
before hashing canonical payload, sort the already-normalized row dictionaries deterministically by their compact sort-key JSON.

The row contents are not changed.
No row is added, removed, filtered or deduplicated.
Selection rules remain unchanged.
Any true row-set/field divergence still produces different canonical hashes and remains BLOCKED.

The selected underlying receipt is preserved unchanged for the canonical finalizer.

## Firewall
protected_2025_market_outcomes_opened=false
protected_2026_outcomes_opened=false
science_changed=false
post_outcome_tuning=false
trading_authority=NONE
