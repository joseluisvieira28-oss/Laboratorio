# Triple Fishing V0.3 — operator manual MEXC zero-exposure checkpoint

Date of operator declaration: **2026-10-08** (Europe/Zurich).
Status: **OPERATOR_MANUAL_ZERO_EXPOSURE_REPORTED — NOT INDEPENDENTLY RECONCILED**.

## Manual snapshot declared by operator

- MEXC Futures open positions: **0**.
- MEXC Futures open orders: **0**.
- MEXC Futures pending TP/SL orders: **0**.

This information was supplied by the operator in the Crypto Lab audit conversation. It has **not** been independently checked by an authenticated read-only MEXC client, matched to immutable order/position identifiers, or timestamp-bound to an exchange API receipt. Do **not** treat it as ongoing safety guarantee, authorization to trade, or proof that local receipt/slot state is reconciled. Recheck immediately before any future controlled maintenance that might start, stop, arm or otherwise change a position-managing supervisor.

## Current technical status and authority

- Isolated repair branch: `fix/triple-v03-launcher-observability-2026-10-08`.
- Draft PR: https://github.com/joseluisvieira28-oss/Laboratorio/pull/165.
- Patch scope: sanitized launcher diagnostics, fail-closed supervisor-fatal receipt, read-only Windows inspector, SHA256 full-package verification, inert synthetic offline regression tests, CI windows build rules.
- CI release audit for latest observed head `233e249d0b400632907d5daeeece8f8cd2eaf5a8`: run `37738777615`, **queued** at last read. No verified new Windows artifact or passed offline test has been independently observed in this audit checkpoint.
- Installed PC version provenance mismatch remains verified: user HOTFIX2 source SHA `47ec9997dbd9d68afe2316c9693fcbc4f15f0579` is not the newer production release SHA `e581823ae82c6c14ab9ae9d984430ba6e248a9ea`.
- Historical task exit code 1 remains unproven causally. **Do not claim that the patch repaired that historical failure.**
- No account API calls, trading, exchange mutation, arming, Windows task restart, credential reads, or merge to main were performed in this phase.

## Remaining release prerequisites

1. GitHub offline CI including inert launcher tests and fatal supervisor unit tests **must PASS**.
2. Branch-scoped Windows workflow must produce a newly validated complete artifact (not the expired Sept 30 one), with BUILD_INFO SHA and all local SHA256 hashes verified without executing any binaries.
3. Independently reconcile read-only MEXC current positions, open orders, TP/SL and local receipt/slot/active-owner states just before any maintenance that may start a supervisor.
4. Under separate operator instruction, perform *controlled maintenance only* with all entry markers unarmed and monitor heartbeats. The existing installer automatically starts a supervisor, so never use it as a diagnostic.
5. Actual trading authority remains a separate explicit decision after risk/position review. Never auto-arm, delete slot/receipts, bypass a fail-closed gate or infer exchange flatness solely from missing local slot markers.
