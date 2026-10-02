# DLS ROUTE A3B — KAMINO SHAPE CONFORMANCE CORRECTION V0.1

Date: 2026-10-02
Status: TECHNICAL CORRECTION / SCIENCE UNCHANGED
Branch: dls-field-enrichment-v01

## Observed failure
A3B run 36986263576 returned canonical_2025_shape_conflict:kamino in multiple 2025 partitions.

## Diagnosis
The A3A/A3B helper had accidentally strengthened the canonical 2025 Kamino shape to require:
- account[16] == SPL Token program
- account[17] == SPL Token program
- account[18] == SPL Token program
- account[19] == Instructions Sysvar

That is NOT the frozen Protected-2025 collector semantics.

Canonical frozen authority in collect_protected_2025_source_v0_1.py requires:
- account_count >= 20
- instruction data length == 32
- account[16] == SPL Token program
- account[17] non-empty
- account[18] non-empty
- account[19] == Instructions Sysvar

The already validated A2 normalizer/shape also uses the same non-empty semantics for positions 17 and 18.

## Correction
Only canonical_2025_shape(kamino) in the A3A transport helper is changed from equality-to-SPL for positions 17/18 to bool(non-empty), restoring exact frozen semantics.

Unchanged:
- discriminator
- account positions
- data length
- program ID
- source window
- event set semantics
- unit resolution
- SOL target
- clustering
- strategy/cost/timing/statistical gates
- 2025/2026 market outcome firewall

Failed A3B receipts from run 36986263576 remain immutable and are superseded for source acquisition by a clean rerun under this correction.

Trading authority: NONE.
