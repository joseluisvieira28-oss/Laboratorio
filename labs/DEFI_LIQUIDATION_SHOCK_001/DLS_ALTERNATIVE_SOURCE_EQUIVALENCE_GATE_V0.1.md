# DLS_ALTERNATIVE_SOURCE_EQUIVALENCE_GATE_V0.1

Date: 2026-09-30
Branch: dls-field-enrichment-v01
Status: FROZEN SOURCE/TRANSPORT ONLY — SCIENCE UNCHANGED
Route A remains valid but transport-blocked. No blind SQD rerun is authorized by this gate.

## Authority and prerequisites
Read the existing archival readiness preflight, source feasibility, metadata and transaction-status receipts, sample freeze and Kamino/Save11 precedence addenda, Protected-2025 source freeze and both partition addenda before any adapter implementation.
Canonical Protected-2025 decoder authority is source/collect_protected_2025_source_v0_1.py (blob 8d59b5798770d43bbc7a7e15cd239dd355998145).
Its Kamino discriminator is b1479abce2854a37. The older SOURCE_ROUTE_FEASIBILITY reference b1479acce2854a37 is not decoder authority.
Exactly the existing marginfi, save0c, kamino and save11 classes, program IDs, ABI roles and success semantics must be preserved.

Existing frozen 23-signature authority:
- RAW_RPC_VALIDATION_RECEIPT_V0.1.md
- TRANSACTION_STATUS_RECONCILIATION_RECEIPT_V0.1.md
- DLS_RAW_SAMPLE_VERIFY_20260916_221907.zip
- ZIP SHA256 5e14c1712a97d60983b7321735615681671b76dcb1bce5f973dfdb28f3cfab7f
- CSV SHA256 b58af58b0229969d38625cc2c4e138742477b1633d3fc06f3fa6b328064d5bdc
Do not create a replacement sample after inspecting outcomes.
The 23-signature fixture has no Kamino or Save0c and is not proof of complete program history or all four classes.
Existing frozen additional source fixtures may supplement it only with explicit provenance; the 64-row Kamino/Save11 raw reconciliation is a locator, not exact CPI-tree proof.

## Credential prerequisite
Apply existing zero-RPC presence semantics to HELIUS_API_KEY or DLS_RPC_URL in the actual execution runtime. Never print, hash or persist values.
If absent: ALTERNATIVE_SOURCE_EQUIVALENCE_BLOCKED / ARCHIVAL_RPC_CREDENTIAL_DEPENDENCY.
Do not purchase a plan or substitute an unvalidated public RPC.

## Six mandatory empirical tests
1. Transaction census: on a pre-authorized frozen historical interval, compare complete SQD and RPC relevant signature sets. Record expected, observed, intersection, missing, extra relevant, duplicates and deterministic pagination termination. Selected-signature fetches alone do not prove census completeness. A page cap, nonadvancing cursor, missing blockTime or incomplete interval is BLOCKED.
2. RAW fidelity: compare signature, slot, blockTime, success/error, program IDs, ordered accounts, exact base58-decoded data, top-level and inner instructions, token metadata and loaded addresses. Preserve source bytes/hash ledger without emitting token amounts.
3. Versioned/ALT: construct ordered static keys + loaded writable + loaded readonly before resolving every programIdIndex/account index. Missing loaded address data, malformed indices or parsed/compiled ambiguity is BLOCKED.
4. CPI tree: reconstruct top-level path and child ordinals using execution order and stackHeight, then empirically compare each relevant (signature, instructionAddress) to SQD. Flat inner ordinal or outer/inner labels are not tree equivalence. Missing/ambiguous depth is BLOCKED; no invented nesting.
5. Discriminator/account roles: apply the exact canonical base58 decoder, prefixes, success rules, shape and mapping rules. BigQuery success is status = 'Success', never err IS NULL. RAW success requires explicit meta with err null; missing meta/err cannot imply success. Enhanced labels are not authority.
6. Save11: resolve accountIndex through canonical vector to pubkey, then pre/post mint and decimals. Primary accounts[8] requires exactly one pair; optional accounts[2] may be absent or exactly match. Conflicts fail closed. Exactly 15 accounts and 9/10 bytes; do not emit trailing-byte values.

## Adjudication
ALTERNATIVE_SOURCE_EQUIVALENCE_PASS requires all six empirical tests PASS with exact relevant instruction identity and no missing/extra/duplicate/conflict/ambiguity. Not run is not PASS.
Otherwise ALTERNATIVE_SOURCE_EQUIVALENCE_BLOCKED with precise diagnostics.
No thresholds may be softened after divergence. Synthetic unit tests never substitute for historical evidence.

## Downstream boundary
Only an explicit equivalence PASS permits Route A2 Protected-2025 acquisition.
Preserve 2025-01-01T00:00:00Z <= timestamp < 2026-01-01T00:00:00Z.
Require deterministic partition/checkpoint/resume, exact full coverage and real source finalization. Partial transport is never PASS.
Existing month (48 receipts) and quarter (16 receipts) routes are distinct manifests; never mix them.
Keep the scientific finalizer semantically unchanged.
Economic holdout remains closed until real PROTECTED_2025_SOURCE_AUTHORITY_PASS, unchanged strategy/cost/fee/holdout freezes, correct PASS-receipt pinning and a single launch marker.
No 2026 data/outcomes, science changes, main merge, purchases, trading, orders, wallets or exchange mutation.
