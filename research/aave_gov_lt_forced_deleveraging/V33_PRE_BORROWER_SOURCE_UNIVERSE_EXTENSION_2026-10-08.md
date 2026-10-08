# AAVE-GOV-LT-FORCED-DELEVERAGING-001 — V33 pre-borrower source-universe extension

Date: 2026-10-08 UTC
Status: SOURCE ONLY / PRE-BORROWER VALUES / HYPOTHESIS NOT TESTED / 2026 CLOSED

## Purpose

V26 froze 12 independent source candidates before borrower values. V31 added Proposal 256
from the already-running Optimism 2025 census, also before corrected borrower-state acquisition
completed. The completed Polygon 2025 census contains one additional true LT reduction not
present in the V26 set. This document freezes that source candidate before any corrected borrower
result is used.

This is not the PRE-OUTCOME ANALYSIS FREEZE.

## Additional independent shock — Governance V3 Proposal 388

Canonical proposal identity is independently documented in:

- repository: `aave-dao/aave-proposals-reports`
- pinned commit: `24086c9b04bec0d32e1fd1edaf8f41d28d187d6f`
- report: `reports/v3-388-aave-v2+v3-DPI-deprecation.md`
- title: `Proposal 388. Full Deprecation of DPI Across Aave Deployments`
- proposal creation tx:
  `0x86f73be6007454b4339164184125b686bdab684a145e726338d4acbd485dc44b`
- proposal id: `388`
- Polygon V3 payload controller:
  `0x401B5D0294E23637c18fcc38b1Bca814CDa2637C`
- Polygon V3 payload id: `132`

The same pinned report states that Proposal 388 contains three payloads: Ethereum 357,
Polygon 131, and Polygon 132. Therefore Polygon payload 132 is not treated as an orphan or as an
independent ad-hoc action; it belongs to Core Governance Proposal 388.

## Polygon V3 effect

Pinned payload source:

- repository: `aave-dao/seatbelt-gov-v3`
- commit: `a6e52bca30dff5c396f8ad7b452a9890a1f0e68e`
- report:
  `reports/payloads/137/0x401B5D0294E23637c18fcc38b1Bca814CDa2637C/132.md`

Payload 132:
- created: 2025-10-09 09:06:19 UTC
- queued: 2025-10-13 14:56:35 UTC
- queue tx:
  `0x9b2d2103331cf7f1df4631671bc7c3746e2924b83376e1136c187dc0a9231d37`
- executed: 2025-10-14 14:56:55 UTC
- effect block: `77674570`
- effect tx:
  `0xaf73caa4050d0abf0a8b9bb0cb6b37b8c9ac74e1196a352a3e71d4d7e707ccb4`

Affected Polygon V3 asset:
- DPI: `0x85955046df4668e1dd369d2de9f3aeb98dd2a369`

Exact pinned state diff:
- liquidation threshold: 45.00% (`4500`) -> 0.05% (`5`)
- LTV: set to 0
- emitted `CollateralConfigurationChanged(... ltv=0, liquidationThreshold=5, liquidationBonus=11000)`

The Polygon 2025 census was chained from the last audited 2024 state, so this is a true
decrease from an already-existing LT rather than first configuration/listing.

Under V01, Proposal 388 qualifies because an existing collateral LT decreases before effect.

## Independence

Proposal 388 is distinct from every V26/V31 proposal identifier:
- V3 V26: 2, 13, 19, 55, 71, 87, 100, 114, 173, 260
- V2 V26: 233, 288
- V31: V3 256
- V33: V3 388

Multiple payloads/reserves inside Proposal 388 remain one independent economic shock.

Pre-borrower source universe after V33:
- V26: 12
- V31: +1
- V33: +1
- total independent source candidates: 14

This count is not SOURCE_GATE_PASS. Every final accepted shock still requires the full V01
source chain and reconstructible pre-signal borrower/exposure state.

## Still closed

- corrected borrower outcomes: not used to select this shock
- signal-to-effect behavioral outcomes: unopened
- economic outcomes: 0
- Development runs: 0
- 2026 outcomes: closed
- trading/orders/wallets/private authenticated endpoints: forbidden
- main: unchanged

Next step: complete the remaining correct Base 2023-2025 census, finish exact parameter/source
proofs, reconstruct historical pre-signal exposure for the frozen source universe, and declare
SOURCE_GATE_PASS only if at least 12 independent shocks remain fully defensible.

## Versioning note

Commit `6ee46e57638698e3ca45085563971d471d0efe9e` originally wrote this extension under a V32 filename at the same time an independent V32 primary source-chain freeze already existed. This V33 file is the canonical numbering correction. No source candidate, evidence, timing, parameter, gate, or scientific rule changed.
