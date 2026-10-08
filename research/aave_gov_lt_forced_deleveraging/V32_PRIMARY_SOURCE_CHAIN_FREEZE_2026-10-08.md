# AAVE-GOV-LT-FORCED-DELEVERAGING-001 — V32 primary source-chain freeze

Date: 2026-10-08 UTC
Status: SOURCE ONLY / PRE-OUTCOME / HYPOTHESIS NOT TESTED / 2026 CLOSED

## Purpose

Freeze the primary historical-state witness chain for every candidate before any cross-chain
source choice can be influenced by borrower/economic results. This does not change the V01
mechanism, V26 minimum set, V31 extension, or the >=12 fully source-gated shock requirement.

Selection rule: use the already-pinned representative chain used for exact parameter semantics
where that chain passed V25 public historical protocol-state capability; use the only eligible
non-Arbitrum chain when unique. Arbitrum remains valid governance clustering evidence but is not
a borrower-state witness because V25 did not accept its public historical state.

## Frozen primary witnesses

| Shock | Primary witness | Basis |
|---|---|---|
| V3 Proposal 2 | Avalanche | V22 unique qualifying mapped effect; V30 pinned Avalanche payload; V25 archive-capable |
| V3 Proposal 13 | Avalanche | V22 unique qualifying mapped effect; V30 pinned Avalanche payload; V25 archive-capable |
| V3 Proposal 19 | Optimism | V22 unique mapped effect; V30 direct signal-1/effect proof; V25 archive-capable |
| V3 Proposal 55 | Avalanche | V30 pinned Avalanche representative; V25 archive-capable |
| V3 Proposal 71 | Optimism | V30 pinned Optimism representative; V25 archive-capable |
| V3 Proposal 87 | Optimism | V30 pinned Optimism representative; V25 archive-capable |
| V3 Proposal 100 | Optimism | V30 pinned Optimism representative; V25 archive-capable |
| V3 Proposal 114 | Optimism | only mapped qualifying representative in V22; V25 archive-capable |
| V3 Proposal 173 | Optimism | V30 pinned Optimism representative; V25 archive-capable |
| V3 Proposal 260 | Polygon | V22 unique mapped effect; V30 pinned Polygon payload; V25 archive-capable |
| V2 AIP-233 | Optimism | coordinated V2 shock; Optimism execution candidate already identified; V25 archive-capable |
| V2 AIP-288 | Polygon | exact CRV Polygon action-set evidence frozen in V26; V25 archive-capable |
| V3 Proposal 256 | Optimism | V31 pre-borrower extension; only qualifying 2025 Optimism effect; V25 archive-capable |

A multi-chain proposal remains one economic shock. Alternate chain members may be used only as
source corroboration or documented technical fallback if the primary public source becomes
unavailable; they may not be selected because borrower counts, behavior, or economic outcomes look
more favorable.

## Gate remains unchanged

Each accepted shock still requires exact queue/effect, immutable proposal/payload proof, definitive
old/new LT semantics, affected reserves/eMode mapping, complete signal-1 borrower enumeration, and
reconstructible balances/flags/eMode/isolation/indices/accrual/oracle state. Fewer than 12 fully
defensible shocks after the complete frozen source universe => INSUFFICIENT_SAMPLE. Essential
unrecoverable evidence => SOURCE_BLOCKED. No behavioral/economic outcomes or 2026 are authorized
before a separate PRE-OUTCOME ANALYSIS FREEZE.
