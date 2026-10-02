# DLS MARGINFI PROGRAM-ONLY COLLECTOR — IMPLEMENTATION BINDING V0.3

Date: 2026-10-02
Status: FROZEN BEFORE PROTECTED-2025 SOURCE ACQUISITION

Authority addendum commit:
82004a2c236198c284c33a12d62f8bf21a9b8b40

Canonical collector:
- path: labs/DEFI_LIQUIDATION_SHOCK_001/source/collect_protected_2025_source_v0_1.py
- Git blob: 8d59b5798770d43bbc7a7e15cd239dd355998145

Derived collector:
- path: labs/DEFI_LIQUIDATION_SHOCK_001/source/collect_protected_2025_marginfi_program_only_v0_3.py
- Git blob: e136e109d7d3dd08fb4f208eaafd2ae41f9f7d55
- creation commit: 8fc6beabd413fd905a52c40f9a77326312a94e3b

Authorized differences only:
1. SQD request omits the server-side d8 discriminator and queries Marginfi programId-only.
2. Runtime refuses any protocol other than marginfi.

Unchanged:
- exact local d6a997d5fba756db prefix filter;
- explicit successful transaction predicate;
- account shape;
- event identity;
- timestamp/month boundary semantics;
- asset_bank mapping account;
- finalized bank dataSlice offset 8 length 33;
- mint/decimals resolution;
- duplicate/error handling;
- output schema;
- source-only firewalls.

No prices, returns, PnL, funding, 2026 data or trading authority.
Trading authority: NONE.
