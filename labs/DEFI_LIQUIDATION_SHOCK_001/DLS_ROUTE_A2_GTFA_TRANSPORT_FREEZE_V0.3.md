# DLS ROUTE A2 — HELIUS gTFA TRANSPORT FREEZE V0.3

Date: 2026-10-02
Status: FROZEN SOURCE-ONLY TRANSPORT OPTIMIZATION / SCIENCE UNCHANGED
Branch: dls-field-enrichment-v01

## Problem
Route A SQD remains transport-unreliable for Protected-2025 full-year acquisition.
Route A2 archival RAW equivalence is now proven:
- run 36900517788
- artifact 11181427969
- FOUR_CLASS_ARCHIVAL_PAIRED_EVIDENCE_PASS
- ALTERNATIVE_SOURCE_EQUIVALENCE_PASS
- semantic coverage exactly kamino, marginfi, save0c, save11.

The remaining task is complete 2025 acquisition, not decoder research.

## Transport-only route
Use Helius archival RPC method getTransactionsForAddress (gTFA) for the exact frozen program IDs.
The method may be used only with:
- transactionDetails = full
- sortOrder = asc
- successful transactions only
- exact blockTime filter for one frozen calendar-month partition
- deterministic paginationToken exhaustion
- no tokenAccounts expansion

This replaces only the transport layer.
It does NOT alter:
- program IDs
- liquidation discriminators
- account roles
- instruction shape rules
- success semantics
- collateral-mint resolution
- source window
- 60-second clustering
- SOL target identity
- economic hypothesis
- strategy direction
- execution timing
- costs
- statistical gates.

## Canonical decoder authority
Frozen scientific decoder remains:
labs/DEFI_LIQUIDATION_SHOCK_001/source/collect_protected_2025_source_v0_1.py

RAW normalization semantics are additionally bound to the already-validated A2 normalizer:
labs/DEFI_LIQUIDATION_SHOCK_001/source/run_alternative_source_equivalence_v0_1.py

For every returned full transaction:
1. require explicit successful status;
2. reconstruct static + loaded writable + loaded readonly address vector;
3. inspect top-level and inner compiled instructions;
4. match only exact frozen program + discriminator;
5. apply canonical shape;
6. preserve exact signature, slot, blockTime and instruction path;
7. resolve collateral unit using the same frozen rules.

No Enhanced API labels, summaries, transaction type names or heuristic parsing are authority.

## Partition contract
Exactly the existing V0.2 monthly manifest:
4 protocols x 12 months = 48 receipts.

Existing immutable PASS receipts from prior SQD acquisition may be reused byte-for-byte.
Missing/failed partitions may be produced by this A2 gTFA route.
The finalizer may mix transport origins ONLY because both are independently bound to the identical frozen decoder semantics and each receipt retains transport provenance.
No duplicate scientific event identity may exist across partitions.

## Probe gate
Before any 2025 gTFA acquisition:
- one source-only bounded call with limit <= 2;
- no market price endpoint;
- no 2025 return/PnL field;
- record only method availability, response schema keys and pagination-token presence;
- do not persist transaction payload values in the probe receipt.

PASS:
GTFA_TRANSPORT_CAPABILITY_PASS

BLOCKED:
GTFA_TRANSPORT_CAPABILITY_BLOCKED

## Firewalls
Protected-2025 market prices/outcomes remain CLOSED.
Protected-2026 remains CLOSED.
No paid upgrade or purchase.
No main merge.
No trading, orders, wallet or exchange mutation.
Trading authority: NONE.
