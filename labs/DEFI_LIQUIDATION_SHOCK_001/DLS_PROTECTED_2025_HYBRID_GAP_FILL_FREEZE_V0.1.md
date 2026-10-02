# DLS PROTECTED-2025 HYBRID GAP-FILL FREEZE V0.1

Date: 2026-10-02
Status: FROZEN SOURCE-ONLY TECHNICAL RECOVERY / SCIENCE UNCHANGED
Branch: dls-field-enrichment-v01

## Proven authorities
- Route A2 four-class equivalence PASS:
  run 36900517788 / artifact 11181427969
- Route A3 gTFA equivalence PASS:
  run 36969189081 / artifact 11210144684
- Protected-2025 reusable consolidation PASS:
  run 36992035539 / artifact 11220370382
  identity d20e3b3300c0785fcf04d33c6ddb8168f651e8d68328c0340880c2a646b80820
  selected 28/48 immutable PASS partitions
- A3B run 36986263576 produced all 12 Marginfi 2025 monthly receipts as PASS before its Kamino failures.
- Kamino A3B shape conformance correction:
  code commit 8d9eb09b0f5319f155d38caae6d2c3079ed13b5c
  correction receipt commit c664f9d7c18f90c61972f0c99cf866182abd8626
  correction restores the pre-existing canonical 2025 rule only.

## Exact remaining scientific gaps
After combining the 28 consolidated PASS receipts and the 12 A3B Marginfi PASS receipts, the only missing protocol/month identities are:

- kamino: 05, 06, 07
- save0c: 01, 02, 03
- save11: 01, 05

Because save0c and save11 share the same Solend program, source transport is executed for:
- save group: 01, 02, 03, 05
- kamino group: 05, 06, 07

Exactly 7 new transport jobs may run.

## Reuse sources
Reusable receipts may be drawn only from:
- run 36740555628
- run 36733498831
- run 36986263576

A receipt is reusable only if:
- classification = PROTECTED_2025_PROTOCOL_SOURCE_PASS
- exact protocol/class/month window matches canonical V0.2
- error_count = 0
- duplicate_count = 0
- canonical scientific payload is conflict-free with any duplicate PASS receipt.

Transport metadata may differ; scientific rows and frozen semantics may not.

## Gap-fill transport
Use corrected A3B gTFA streaming only:
- exact frozen program IDs
- transactionDetails=full
- asc sort
- exact 2025 monthly blockTime filter
- status=succeeded
- pagination to terminal exhaustion
- canonical A2 RAW normalizer
- canonical frozen discriminators/shapes/unit rules
- no market data.

## Finalization
After 7 gap jobs:
1. combine all allowed reusable and gap-fill receipts;
2. deterministically select one scientific-equivalent PASS receipt for each of 48 protocol/month identities;
3. require 48/48 exactly;
4. run unchanged finalize_protected_2025_source_v0_2.py;
5. only PROTECTED_2025_SOURCE_AUTHORITY_PASS may authorize the already-frozen 2025 economic holdout.

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
