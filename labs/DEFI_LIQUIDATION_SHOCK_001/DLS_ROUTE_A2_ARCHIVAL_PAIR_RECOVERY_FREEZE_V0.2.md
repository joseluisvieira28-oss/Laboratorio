# DLS ROUTE A2 — ARCHIVAL FOUR-CLASS PAIR RECOVERY FREEZE V0.2

Date: 2026-10-01
Status: FROZEN SOURCE-ONLY / PROTECTED-2025 OUTCOMES CLOSED
Branch: dls-field-enrichment-v01

## Problem
The direct SQD Portal pair probe returned HTTP 403 for all four frozen decoder references.
This is transport/access failure, not evidence mismatch.

## Recovery authority
Use ONLY pre-existing, pre-Discovery SQD field-enrichment artifacts for the exact four already-frozen
reference signatures in validate_field_decoder_implementation_v0_1.py. No replacement signature,
slot, program, discriminator or event selection is permitted.

Frozen refs:
- save0c: slot 110526981 / signature 3kbwGTtWnZMi9rdTVpqS3EaJdRTp9Dyhf7A8TVfdjYP7hGkYSHBETcWyfc5qicFJ3eKQVMkCdWwi93peVNYzTD1V
- save11: slot 278496102 / signature WdTyQhEUhG2HjQ5LHApW8DU4aLRiKGQ5s8PZYBeoCJ8Acm6tkzqAdL4iasRYnSVnkHTVHTXu7zdgsSmDH8WmQ4L
- marginfi: slot 177590210 / signature 2aW2TWwxxzTTFixuYnvaA2NpentUDu6vCLxPjkvYBJWcrmB9TcRYu63uAswCrAjHJt7VXZxYUBaJsp3SGH3zNBmK
- kamino: slot 230572965 / signature 2tMYYz4YWDiqMWF4H34t1oz5PRfvMfQZbXKUM6ZpK2SocmKrik2pbbx4k734LTe2mEgi5WvqLwMAZAzUqYuBD3uv

## Pinned pre-outcome SQD artifacts
- save0c 2021-12: run 36263998920 / artifact 10925546081
- marginfi 2023-02: run 36263998920 / artifact 10913369291
- kamino 2023-11: run 36264171014 / artifact 10914381181
- save11 V0.4 2024-07: run 36313729668 / artifact 10930811495
- save11 unit V0.4 2024-07: run 36313729668 / artifact 10930621736

RAW authority:
- run 36897600425 / artifact 11179957023
- exact same four frozen signatures, Helius archival RAW.

## Exact pair test
For each frozen reference:
1. SQD artifact must contain exactly one row with exact signature + slot.
2. Use current canonical RAW normalizer and decoder config.
3. Relevant instruction path must exactly match the SQD instructionAddress.
4. Program ID, ordered accounts and instruction data must be byte/string exact.
5. Canonical frozen shape() must PASS.
6. RAW transaction success must be explicit.
7. For Save11, canonical unit() must equal the pre-outcome V0.4 unit artifact and RAW token-balance
   mint/decimals for primary account; optional crosscheck may be absent or exact-match.
8. Target top-level instructions ([3], [0], [7]) are path-unambiguous by definition. Unrelated child
   stackHeight ambiguity may be recorded but cannot alter the top-level target path.
9. The Save11 inner target [4,0] must have no target-depth ambiguity.

No economic fields, prices, returns or 2025 source population may be opened.

## Final equivalence adjudication
A new V0.3 equivalence receipt may classify PASS only if:
- V0.2 current run 36898066100 tests 1,2,3,4,6 are PASS;
- archival pair V0.2 is 4/4 PASS;
- V0.2 frozen-semantics evidence for marginfi/kamino/save11 remains PASS;
- archival pair adds canonical Save0c shape PASS;
- combined semantic coverage is exactly all four canonical classes;
- no errors/conflicts.

This is evidence completion only. It does not alter scientific rules or authorize market outcomes.

Trading authority: NONE.
