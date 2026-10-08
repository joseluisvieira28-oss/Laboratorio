# AAVE-GOV-LT-FORCED-DELEVERAGING-001 — V26 pre-borrower source-set freeze

Date: 2026-10-08 UTC
Status: SOURCE ONLY / PRE-BORROWER VALUES / HYPOTHESIS NOT TESTED / 2026 CLOSED

This is not the PRE-OUTCOME ANALYSIS FREEZE. It fixes the minimum clean governance-linked shock set before any borrower values are opened, so later source failures or economic results cannot be used to cherry-pick replacements.

## Fixed minimum source-gate set (12 independent governance shocks)

Governance V3 proposal clusters from the pinned Seatbelt V22 mapping:
1. Proposal 2
2. Proposal 13
3. Proposal 19
4. Proposal 55
5. Proposal 71
6. Proposal 87
7. Proposal 100
8. Proposal 114
9. Proposal 173
10. Proposal 260

Governance V2:
11. AIP-233 — Stablecoin E-mode changes for V3 Avalanche, Optimism, Polygon, and Arbitrum.
12. AIP-288 — CRV LT/LTV reduction on V3 Ethereum and Polygon.

Same proposal / coordinated cross-chain payloads remain one shock. No chain execution is counted separately.

## Source basis frozen before borrower inspection

- V22 Seatbelt V3 proposal mapping: pinned repo `aave-dao/seatbelt-gov-v3` at `a6e52bca30dff5c396f8ad7b452a9890a1f0e68e`; 10 distinct V3 proposal IDs.
- Legacy V2 Seatbelt: `bgd-labs/seatbelt-for-ghosts` at `f1d1c1090ac51d01e557135c41076dab8f4b0e74`.
- AIP-233 exact eMode change: LT 97.5% -> 95%, LTV 97% -> 93%; coordinated cross-chain implementation.
- AIP-288 Polygon exact CRV change: LT 75% -> 65%, LTV 70% -> 35%; Polygon action set 53.
- V25 public historical-state capability: Optimism PASS, Avalanche PASS, Polygon PASS, Base PASS using unauthenticated public RPCs.
- Arbitrum historical-state source is not accepted for borrower reconstruction because prior public RPC probes returned missing historical state / trie-node failures. Its execution evidence remains valid for clustering, but it cannot be the sole borrower-state witness for an accepted shock.

Every selected shock has at least one non-Arbitrum candidate effect in the already mapped source universe.

## Still mandatory before SOURCE_GATE_PASS

For each of these 12 shocks:
- exact first qualifying queue/approval signal and exact effect;
- immutable payload/proposal proof and definitive old/new parameters;
- affected reserve/eMode mapping;
- complete pre-signal borrower enumeration on accepted source-capable chain members;
- historical collateral/debt balances, collateral flags, eMode, isolation semantics, reserve indices/accrual and oracle snapshot at signal-1.

No borrower values have been opened by this freeze. No economic outcomes, Development, 2026 outcomes, trading, orders, wallets, private/authenticated endpoints, or main changes are authorized.

If any one of the fixed 12 cannot pass source requirements, it is not silently replaced. Additional already-discovered shocks may only enter through a separately documented source-universe audit, never because of observed borrower/economic results.
