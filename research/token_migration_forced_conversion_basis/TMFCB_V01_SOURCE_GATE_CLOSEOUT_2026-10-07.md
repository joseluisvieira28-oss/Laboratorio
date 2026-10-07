# TOKEN-MIGRATION-FORCED-CONVERSION-BASIS-001 — SOURCE GATE CENSUS / CLOSEOUT V0.1

Date: 2026-10-07
Branch: token-migration-forced-conversion-basis-001-v0.1-source-2026-10-07
Parent freeze commit: 5cc8367326740217aed08252c139486f8a84fbe5
Outcome access: NONE
2026 market outcomes: CLOSED

## Verdict

SOURCE_BLOCKED

This is a source/provenance verdict, not an economic verdict. No market price outcomes, returns, spreads, or basis values were opened.

## Why SOURCE_BLOCKED rather than INSUFFICIENT_SAMPLE

The broad 2022–2025 census produced well over 12 migration/rebrand/swap leads, so the existence of nominal "token migrations" is not the problem.

The block is that the hard V0.1 inclusion standard requires, for >=12 independent project programmes, a defensible immutable chain linking:
- OLD identity;
- NEW identity;
- deterministic ratio/formula;
- migration/redemption mechanism;
- identifiable on-chain contract or immutable equivalent;
- activation transaction/block;
- demonstrated OLD retirement/deprecation/economic consequence;
- immutable temporal/economic boundary;
- public historical OLD + NEW price-source feasibility with frozen venue/quote mapping before outcome access.

Public project/exchange announcements frequently prove ratio and service cutover, but many do NOT by themselves prove the required on-chain activation transaction/block and immutable project-level boundary. Several otherwise attractive migrations are explicitly open-ended, reversible for a period, permanent, optional, or leave the legacy network/token functional.

Because complete provenance sufficient to adjudicate >=12 programmes could not be established without weakening the frozen standard, the correct fail-closed verdict is SOURCE_BLOCKED.

## Census register

### A. Strong mechanism evidence, but still not fully source-admissible under V0.1

1. Merit Circle MC -> BEAM (2023)
   - Ratio: 1 MC = 100 BEAM.
   - Public migration contract evidence exists; published contract address: 0x8fb4223b7751243ae14987d6fc9e71d06aaf6ddf (Ethereum; same address reported for BNB Smart Chain).
   - Migration opened 2023-10-26; public sources describe a finite migration window.
   - Strongest candidate found.
   - Remaining hard requirement before inclusion: independently pin activation transaction/block + immutable closure boundary from first-party/on-chain evidence and freeze price-source schema without reading values.

2. GALA v1 -> GALA v2 (2023)
   - 1:1 snapshot/drop on 2023-05-15.
   - First-party documentation states GALA v1 would no longer be supported or have ecosystem functionality.
   - Strong economic-deprecation evidence.
   - Block: V0.1 requires contract/immutable mechanism + activation block/boundary evidence; the first-party material located is announcement/snapshot oriented rather than a complete on-chain provenance chain.

3. Polygon MATIC -> POL (2024)
   - PIP-17 / PIP-46 define 1:1 migration contract architecture and Polygon PoS activation.
   - Strong canonical governance/contract documentation.
   - Block: migration on Ethereum is open-ended and historically reversible/unmigration-capable; legacy MATIC existence is not cleanly terminated by a single immutable deadline. Needs stricter adjudication against "economically binding" criterion.

4. Render RNDR -> RENDER (2024)
   - First-party upgrade portal; 1:1 RNDR ERC-20 -> RENDER SPL.
   - RNDR Polygon explicitly deprecated; Foundation focus moved to RENDER.
   - Multiple CEX cutovers.
   - Block: no clean immutable project-level deadline located; upgrade path is open-ended. Activation contract/transaction provenance still needs immutable pinning.

5. Galxe GAL -> G (2024)
   - CEX migrations documented at 1:60 with legacy trading/deposit suspension.
   - Block: first-party migration contract + activation tx/block + immutable programme boundary not established in this pass.

6. Artificial Superintelligence Alliance: AGIX + OCEAN -> FET/ASI programme (2024)
   - Fixed ratios: AGIX -> FET 0.433350; OCEAN -> FET 0.433226; later ASI ratios published.
   - First-party docs state migration contracts open and prior contracts later deprecated.
   - One programme / one independent shock by freeze.
   - Block: Phase-II timing was not fixed in initial material and the final contract-deprecation boundary was not immutably pinned pre-outcome in this pass.

7. Stratis old STRAX -> new STRAX (2024)
   - 1:10 migration, old CEX support terminated.
   - Block: project-level migration contract address + activation tx/block + immutable eligibility termination not established.

8. Kaia merger programme: KLAY + FNSA -> KAIA (2024)
   - Canonical ratios documented: KLAY:KAIA 1:1; FNSA:KAIA 148.079656:1.
   - Kaia mainnet launch fixed for 2024-08-29; FNSA burn/claim mechanism documented.
   - KLAY was automatically reflected/renamed rather than independently swapped.
   - Block: programme mixes automatic state continuity for KLAY with FNSA burn/claim; exact immutable swap-contract provenance and eligibility boundary need pinning. Count only once if ever admitted.

9. Fantom FTM -> Sonic S (2024/2025)
   - First-party migration portal; 1:1.
   - Two-way initially, then one-way FTM -> S after the initial window.
   - Block / likely exclusion: Opera continues operating and FTM->S remains one-way indefinitely; no terminal deadline. This weakens "forced/economically binding retirement" requirement.

10. Maker MKR -> SKY (2024/2025)
    - 1:24,000, one-way migration contract architecture; immutable contract evidence is publicly referenced.
    - Block / likely exclusion for this V0.1: legacy MKR was not immediately deprecated at launch and transition is extended; no clean pre-2026 terminal boundary located. Later exchange delistings are not equivalent to immutable project-level termination.

### B. Nominal migrations that fail or likely fail the frozen economic-binding test

11. BitTorrent BTTOLD -> BTT
    - 1:1000 redenomination.
    - Project states swap contracts are permanent and BTTOLD can coexist and retain prior use cases.
    - Reject: optional/permanent path with no retirement deadline; not the forced-convergence mechanism requested.

12. ANY -> MULTI (2022)
    - 1:1 CEX conversion and exchange de-support of ANY.
    - Likely rebrand/migration but project-level immutable retirement chain was not established.
    - Reject unless stronger project/on-chain evidence appears in a future source-remediation mission.

13. VIDT Datalink -> VIDT DAO (2022)
    - 1:10 CEX swap and old-token deposit de-support.
    - Insufficient project-level immutable mechanism/activation/boundary evidence located.
    - Reject under current freeze.

14. COCOS -> COMBO (2023)
    - 1:1 CEX token swap; new smart contracts published; old CEX deposits/withdrawals terminated.
    - Evidence found is primarily exchange cutover + rebrand.
    - Reject under current hard standard absent project-level immutable migration mechanism/boundary proof.

15. EOS -> Vaulta A (2025)
    - 1:1 official swap.
    - Vaulta explicitly states network continues uninterrupted with no fork/migration/reset.
    - Reject: too close to token/ticker/brand replacement for this mine; no terminal swap deadline in located first-party material.

16. STPT -> AWE (2025)
    - 1:1 on-chain swap portal.
    - A later project notice sets 2026-09-21 as final deadline.
    - Reject for 2022–2025 discovery design as frozen: the decisive terminal boundary was announced in 2026, which would contaminate a pre-outcome 2025 T_signal/T_end definition.

17. DAR -> D (2025)
    - 1:1 CEX migration/rebrand.
    - Old withdrawals de-supported, but Binance still offered old-token deposits/conversion after cutover.
    - Reject absent stronger project-level immutable retirement evidence.

18. EOS/A, LOKA/A2Z, STPT/AWE and similar 2025 CEX migration lists
    - Useful census leads only.
    - Exchange operational cutovers are not sufficient substitutes for the required project-level immutable mechanism + activation provenance.

19. Simple chain migrations where token economic identity remains unchanged
    - Reject by freeze (bridge/chain move only).

20. Ticker-only / cosmetic renames
    - Reject by freeze.

## Price-source feasibility finding (NO VALUES OPENED)

The basis study requires OLD and NEW historical prices with a pre-frozen mapping. CEX migration mechanics frequently create a structural data problem:
- OLD spot pair is halted/delisted before NEW trading opens;
- therefore the same venue/quote often has no contemporaneous OLD/NEW overlap;
- using another venue or DEX only after discovering that gap would violate the no-post-outcome venue-substitution rule unless frozen in advance;
- DEX/on-chain price reconstruction additionally requires pre-specified pool identities, token decimals, block/timestamp mapping, and historical archive availability.

This pass did not establish a public/free, outcome-blind historical-price provenance stack for >=12 programmes that also passed the mechanism gate.

No OHLC/trade price values were fetched.

## Source classes searched

- first-party project documentation / governance specifications;
- first-party migration portals / migration FAQs;
- canonical governance proposal repositories where available;
- major exchange migration announcements as secondary operational evidence;
- public smart-contract/source-code references;
- public migration/support indexes used only as census discovery surfaces.

## Representative evidence captured

- Polygon PIP-17 / PIP-46: canonical 1:1 MATIC/POL migration architecture.
- Render Network Upgrade Portal: 1:1 RNDR -> RENDER and deprecation of RNDR(POL).
- Gala first-party GALA v2 upgrade: 1:1 drop and v1 loss of ecosystem functionality.
- ASI Alliance first-party docs: AGIX/OCEAN/FET ratios and migration-contract phases.
- Sonic first-party docs: 1:1 FTM/S and two-way -> one-way transition.
- Kaia first-party docs/whitepaper: KLAY/FNSA -> KAIA ratios and launch transition.
- Beam migration documentation / public contract evidence: 1:100 and finite migration window.
- Stratis CEX/project-linked migration evidence: 1:10.
- BTTC first-party redenomination: 1:1000, but permanent BTTOLD swap/coexistence => exclusion.
- Vaulta first-party EOS/A: 1:1, but uninterrupted network/no reset and no clean terminal deadline => exclusion.
- AWE first-party STPT/AWE: 1:1; final deadline announced in 2026 => unusable for frozen 2022–2025 pre-outcome design.

## Gate accounting

Nominal leads screened: >=20
Strong mechanism candidates requiring further immutable provenance remediation: approximately 10
Fully defensible programmes meeting ALL frozen V0.1 hard requirements with price-source feasibility proven outcome-blind: <12
Market outcomes opened: 0
Development runs: 0
2026 opened: 0

Because the source/provenance chain is incomplete for the minimum sample, V0.1 MUST stop here.

## Scientific meaning

SOURCE_BLOCKED does NOT mean:
- the convergence mechanism is false;
- the migration basis has no edge;
- there are fewer than 12 nominal migrations in crypto;
- any candidate should be promoted.

It means the requested study cannot currently be executed to the frozen evidentiary standard without either:
1. weakening the on-chain/immutable provenance requirements;
2. accepting mutable exchange announcements as substitutes for project-level proof;
3. allowing outcome-driven venue substitutions;
4. using post-2025 information to define 2022–2025 boundaries.

All four are forbidden.

## Closeout

- Do not create PRE-OUTCOME ANALYSIS FREEZE.
- Do not open market outcomes.
- Do not run Development.
- Do not touch 2026.
- Do not rescue using subsets or other mines.
- AAVE-GOV-LT-FORCED-DELEVERAGING-001 remains untouched.

A future source-remediation mission may reopen ONLY the source/provenance question, preserving this freeze, and may attempt to pin contract addresses, deployment/activation tx hashes, block timestamps, immutable closure conditions, and an outcome-blind public historical price stack for >=12 programmes.
