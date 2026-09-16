# PMD-001 — V0.7 OFFLINE BOUNDARY RE-ADJUDICATION FREEZE

Status: SOURCE-ONLY / OUTCOME-BLIND / DIAGNOSTIC
Date: 2026-09-16

Purpose: determine whether the 10 unresolved Chain-Exact Cross-Date V0.6 rows were caused by the V0.6 parser recognizing only legacy `migrate` rather than both `migrate` and `migrate_v2`.

Evidence authority is frozen to the 20 full-block artifacts already produced by GitHub Actions run `35132853202` (`PMD-001 Chain-Exact Cross-Date V06`). No new RPC call is permitted in this diagnostic.

For each of the same 20 artifact rows, scan only the persisted finalized block payloads and apply `MIGRATE_V2_PARSER_AMENDMENT_V07.md` exactly. A boundary is resolved only when exactly one successful supported Pump `migrate` or `migrate_v2` outer instruction for the frozen mint + bonding-curve PDA + canonical pool actually invokes PumpSwap `CreatePool` and does not log `Bonding curve already migrated`.

This diagnostic may classify parser coverage only. It cannot authorize the full 1,012-row ceiling or any economic outcome because V0.6 failure rows did not necessarily persist every block needed for the re-anchored 300-second feature window.

PASS for parser coverage requires 20/20 unique boundaries from the frozen V0.6 block evidence. Anything less remains unresolved.

No prices, returns, PnL, direction labels, outcome files or economic results may be opened.
