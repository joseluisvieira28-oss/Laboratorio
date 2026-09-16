# PMD-001 — FULL SOURCE PREREQUISITE AMENDMENT V0.7.1

Date: 2026-09-16
Status: PRE-OUTCOME / FAIL-CLOSED

This document amends only the cross-date prerequisite named in `FULL_CHAIN_EXACT_SOURCE_EXECUTION_AMENDMENT_V07.md`.

The 1,012-row V0.7 ceiling is authorized if, and only if, one of these scientifically equivalent frozen source reconstructions emits PASS:

1. `CHAIN_EXACT_CROSSDATE_V07_PASS` from the direct V0.7 refetch route; or
2. `CHAIN_EXACT_CROSSDATE_V071_REUSE_PASS` from `CROSSDATE_EVIDENCE_REUSE_TRANSPORT_AMENDMENT_V071.md`.

The V0.7.1 route is equivalent only because it uses the exact same 20 mandatory rows, the same finalized Solana ledger, the same V0.7 migration parser, the same T* boundary, the same 300-second source window, exact transaction ordering, and the same 20/20 eligibility gate. It changes only whether a required finalized block is reused from the hash-verified V0.6 artifact or fetched again from the same provider class.

No OR condition applies to partial/failing results. A FAIL/INCOMPLETE from both routes leaves the 1,012-row pipeline inert.

Everything else in the V0.7 full-source amendment remains unchanged, including the >=1,000 ceiling, 4x253 population, sequential full-block reconstruction, outcome wall and no-rescue governance.
