# TOKEN-MIGRATION-FORCED-CONVERSION-BASIS-001 — V0.2 SOURCE REMEDIATION CLOSEOUT

Date: 2026-10-07
Branch: token-migration-forced-conversion-basis-001-v0.2-source-remediation-2026-10-07
Parent authority:
- V0.1 source/mechanism freeze: 5cc8367326740217aed08252c139486f8a84fbe5
- V0.1 SOURCE_BLOCKED closeout: ec7bc2aff28dc1663375ba59edcec4901e0f9d02
- V0.2 source-remediation freeze: f121b6c10d1d9e4d0e798876536fa37a73af8531

Outcome access: NONE intentionally.
2026 market outcomes: CLOSED.
Development runs: 0.
AAVE-GOV-LT-FORCED-DELEVERAGING-001: untouched.

## V0.2 verdict

SOURCE_BLOCKED

This is NOT an economic no-edge verdict.

V0.2 materially improved source coverage and established that the economic mechanism is not rare: more than twelve independent programmes can be identified that plausibly fit one of the frozen V0.2 boundary classes. However, fewer than twelve were closed to the full evidentiary standard simultaneously required by V0.1/V0.2:

1. deterministic OLD -> NEW economics;
2. project-level economic consequence;
3. immutable activation transaction/block or equivalent immutable activation boundary;
4. immutable T_end/effective boundary;
5. non-zero contemporaneous OLD/NEW public price observability;
6. pre-frozen price-source mapping that can be demonstrated without opening price outcomes.

Because >=12 plausible programmes exist but the immutable/on-chain + historical-price provenance chain could not be defensibly closed for >=12 without either using price-bearing discovery surfaces or weakening the freeze, the V0.2 stopping rule maps to SOURCE_BLOCKED, not INSUFFICIENT_SAMPLE.

## Scientific progress versus V0.1

V0.1 mostly found announcement-level candidates.

V0.2 established five allowed boundary classes before further source work:
- FIXED_DEADLINE
- SNAPSHOT_DEPRECATION
- CHAIN_HALT
- PERMANENT_CONVERTER_DISABLE
- PROTOCOL_UTILITY_CUTOVER

This legitimately rescued programmes whose economic boundary is an irreversible utility/governance/chain cutover rather than a literal final redemption date, without inspecting market outcomes.

V0.2 also froze an outcome-blind price-source hierarchy:
1. same venue + same quote;
2. pre-frozen public DEX pools with common quote;
3. two pre-frozen public venues normalized to common quote only when same-venue overlap is impossible.

## Candidate adjudication register

Statuses below are source-only. No realised price/basis values were used.

### 1. OGV -> OGN — STRONG / NOT YET FULLY CLOSED

Evidence:
- Origin first-party update states merger live.
- Fixed rate: 1 OGV = 0.09137 OGN.
- Migration window: one year from 2024-05-28.
- OGN/xOGN becomes unified governance/value-accrual system.
- OGN pre-existed the migration, making contemporaneous observability structurally plausible.

Sources:
- https://www.originprotocol.com/blog/may-2024-token-holder-update
- Origin migration/DAO documentation discovered in V0.2.

Still missing for full admission:
- authoritative migration-contract deployment/activation tx hash + block;
- immutable close/disable tx or pre-fixed closure implementation proof;
- frozen historical venue/DEX mapping demonstrated without values.

### 2. CUDOS -> FET — STRONG / NOT YET FULLY CLOSED

Evidence:
- CUDOS first-party merger material defines 118.344 CUDOS = 1 FET.
- CUDOS chain halt is an explicit migration phase.
- Native CUDOS ceases after chain halt; snapshot state is converted to FET.
- FET existed before migration, so overlap is structurally plausible.
- Qualifies conceptually as CHAIN_HALT.

Still missing:
- exact canonical halt block + timestamp in a source package suitable for reproducible ingestion;
- exact migration-contract activation tx/block;
- frozen public historical-market source mapping for CUDOS and FET.

### 3. MPL -> SYRUP — STRONG / NOT YET FULLY CLOSED

Evidence:
- Maple first-party docs state 1 MPL -> 100 SYRUP.
- Conversion programme ended and converter became permanently unavailable.
- MPL/xMPL lost governance, staking utility and value accrual.
- SYRUP/stSYRUP became sole governance tokens.
- Maple maintains a public mpl-migration contract repository.
- SYRUP existed for months before final conversion closure.
- Fits PERMANENT_CONVERTER_DISABLE + PROTOCOL_UTILITY_CUTOVER.

Sources:
- https://github.com/maple-labs/maple-docs/blob/master/maple-for-token-holders/mpl-token/faqs.md
- https://github.com/maple-labs/mpl-migration
- https://github.com/maple-labs/syrup-utils

Still missing:
- canonical deployed migrator address tied to deployment tx/block;
- exact disable/closure tx hash + block;
- outcome-blind frozen OLD/NEW market mapping.

### 4. LBR v1 -> LBR v2 — STRONG / NOT YET FULLY CLOSED

Evidence:
- Lybra first-party launch set a finite migration window ending 2023-09-30.
- V1 emissions cease and old token is intended to be burned/retired.
- Operational evidence establishes 1:1 conversion.
- First-party material indicates V1 liquidity and V2 liquidity existed during the migration period, supporting possible contemporaneous DEX observation.

Known token identities recorded:
- old LBR: 0xf1182229b71e79e504b1d2bf076c15a277311e05
- v2 LBR: 0xed1167b6Dc64E8a366DB86F2E952A482D0981ebd

Still missing:
- canonical migration contract + activation tx/block;
- final close/burn tx/block;
- pre-frozen DEX pools and quote mapping.

### 5. RAINI -> RST — STRONG MECHANISM / NOT YET FULLY CLOSED

First-party evidence:
- ratio: 1 RAINI = 1 RST;
- RAINI->RST bridge: 0x569997a49a01C6762909BEeA5FAfD0cA69cdf8E4;
- RST Beam contract: 0xe338aA35D844D5C1a4E052380DBFA939e0cce13F;
- deadline: 2024-03-01;
- later first-party historical update says bridge closed and RAINI no longer supported;
- RST could be purchased while migration was open, supporting structural contemporaneous observability.

Sources:
- https://rainicoin.medium.com/raininomics-the-next-evolution-47608a4077c9
- https://rainicoin.medium.com/as-we-pro-ceed-to-give-you-rst-28f1b0da9324
- https://rainicoin.medium.com/embracing-change-the-new-rst-tokenomics-v2-at-raini-studios-72cc4821f4c8

Still missing:
- bridge deployment/activation tx hash + block;
- closure/disable tx hash + block;
- exact pre-frozen OLD/NEW pool mapping.

### 6. PLA -> PDA — STRONG MECHANISM / PRICE-PROVENANCE OPEN

Evidence:
- PlayDapp first-party post-hack recovery defines snapshot/cutover.
- 1:1 migration.
- PDA contract publicly specified: 0x0D3CbED3f69EE050668ADF3D9Ea57241cBa33A2B.
- PLA loses ecosystem utility after migration.
- Migration portal remained open for a finite support period.
- Fits SNAPSHOT_DEPRECATION / PROTOCOL_UTILITY_CUTOVER.

Still missing:
- immutable activation transaction/block package beyond published snapshot/cutover statement;
- defensible non-zero contemporaneous OLD/NEW market source mapping.

### 7. MATIC -> POL — STRONG CONTRACT PROVENANCE / BOUNDARY NEEDS CLOSURE

Evidence:
- Polygon PIP-17 defines 1:1 MATIC/POL migration architecture and migration/unmigration contract logic.
- PIP-46 defines Polygon PoS POL activation.
- POL canonical Ethereum token identity is public in Polygon deployment repositories.
- Later PoS utility/staking/gas moves to POL, which may satisfy PROTOCOL_UTILITY_CUTOVER even while Ethereum conversion remains open.

Sources:
- Polygon Improvement Proposals PIP-17, PIP-41, PIP-46.
- Polygon official deployment repositories.

Still missing:
- one exact pre-outcome T_end/effective-boundary block suitable for the basis test;
- frozen contemporaneous market mapping;
- complete activation receipt package committed locally.

### 8. RNDR -> RENDER — ECONOMIC CUTOVER PLAUSIBLE / IMMUTABLE BOUNDARY OPEN

Evidence:
- Render first-party portal defines 1:1 RNDR ERC-20 -> RENDER SPL.
- Polygon RNDR explicitly deprecated.
- Governance/project support moves to RENDER.
- Migration portal remained available.

Issue:
- open-ended conversion weakens FIXED_DEADLINE.
- Can qualify only if an exact PROTOCOL_UTILITY_CUTOVER is pinned immutably.

Still missing:
- immutable utility-cutover block/transaction;
- deterministic migration activation transaction;
- frozen OLD/NEW market mapping.

### 9. GAL -> G — STRONG RATIO / BOUNDARY NOT EXACTLY CLOSED

Evidence:
- Galxe first-party source defines 1 GAL = 60 G.
- G contract: 0x9C7BEBa8F6eF6643aBd725e45a4E8387eF260649.
- Migration burns self-custodied GAL and releases G.
- Utilities transition from GAL to G.

Issue:
- public wording found says portal remains live "at least one year", not an exact immutable final deadline.
- Must qualify under utility cutover, not a fabricated fixed deadline.

Still missing:
- exact utility cutover tx/block;
- migration contract activation receipt;
- frozen overlap source.

### 10. MFT -> HIFI — STRONG CONTRACT DESIGN / MARKET OVERLAP OPEN

Evidence:
- Hifi governance defines fixed 100 MFT = 1 HIFI.
- HIFI is the successor governance token.
- Hifi public contract documentation includes token swap functionality.
- Public GitHub organisation contains swap/governance contracts.

Issue:
- major CEX cutovers show OLD halted before NEW opened on the same CEX.
- Must prove pre-frozen DEX or cross-venue contemporaneous overlap before admission.

Still missing:
- canonical activation tx/block package;
- exact utility-cutover boundary;
- outcome-blind overlap mapping.

### 11. KEEP + NU -> T — STRONG MECHANISM / ONE PROGRAMME

Evidence:
- Threshold describes an on-chain merger of Keep + NuCypher.
- T contract, vending machines, staking contracts are public.
- Legacy KEEP rewards ceased unless upgraded to Threshold-compatible staking.
- T became the Threshold native/value/governance token.
- Final deterministic factors are approximately:
  - 1 NU -> ~3.26 T
  - 1 KEEP -> ~4.78 T
- Count ONCE as one independent programme.

Sources:
- https://www.threshold.network/blog/decentralized-merger
- https://www.threshold.network/blog/keep-legacy-stake-upgrade
- https://www.threshold.network/blog/stake-migration-pre-nodes
- https://github.com/threshold-network/solidity-contracts

Still missing:
- canonical vending-machine deployment transaction/block for both legacy inputs;
- one immutable T_end/effective utility-cutover definition frozen for the programme;
- frozen market-source mapping across NU/KEEP/T without outcome values.

### 12. tBTC v1 -> tBTC v2 — STRONG SUNSET MECHANISM / TIMING PACKAGE INCOMPLETE

Evidence:
- Threshold first-party proposal/roadmap documents explicit v1 sunsetting.
- VendingMachineV2 exchanges v1 -> v2 at 1:1.
- Contract exposes an Exchanged event.
- Old v1 bridge was intentionally sunset and later ceased normal BTC redemption functionality.
- Qualifies conceptually as PROTOCOL_UTILITY_CUTOVER / bridge sunset, not a cosmetic rename.

Sources:
- https://www.threshold.network/blog/v1-to-v2-migration-roadmap
- https://docs.threshold.network/app-development/tbtc-contracts-api/tbtc-v2-api/vendingmachinev2

Still missing:
- exact canonical v1 sunset boundary tx/block from the historical period;
- deployment/activation receipt for VendingMachineV2;
- proof of non-zero OLD/NEW price-observation overlap under a pre-frozen source map.

### 13. BIT -> MNT — CANDIDATE / RATIO PROVENANCE CONFLICT

Evidence:
- Mantle/BitDAO governance created MNT as successor ecosystem token.
- MNT assumes Mantle governance/gas roles.
- A conversion contract exists operationally.

Block:
- early proposal material and later operational conversion material found in discovery disagree about the intended/final ratio.
- Until the final ratified canonical ratio + contract implementation is reconciled from first-party governance/on-chain evidence, exclude.

### 14. ASI programme: AGIX + OCEAN -> FET — MECHANISM VALID / DEADLINE WEAK

Evidence:
- first-party alliance sources define deterministic ratios:
  - AGIX -> FET 0.433350
  - OCEAN -> FET 0.433226
- FET remains active target market.
- one programme / one shock.

Block:
- first-party material explicitly allowed migration years later.
- Can only qualify if a separate immutable protocol-utility cutover for AGIX/OCEAN is proven.
- Not closed in V0.2.

### 15. CQT -> CXT — MECHANISM STRONG / BASIS FEASIBILITY LIKELY FAIL

Evidence:
- fixed 1:1 snapshot migration.
- snapshot block 20279064 publicly identified by Covalent.
- CQT loses staking/governance/security utility and becomes deprecated.
- CXT contract publicly identified.

Block:
- NEW issuance occurs at/after the cutover snapshot.
- V0.2 requires a non-zero contemporaneous interval after T_signal and before T_end where BOTH OLD and NEW have public price observability.
- This overlap has not been proven and appears structurally doubtful.
- Do not admit absent proof.

## Mandatory contamination exclusions

### MC -> BEAM

V0.1 had MC->BEAM as the strongest candidate.

During V0.2 source remediation, direct inspection of the migration-contract explorer page exposed the current market price of MC alongside contract metadata.

The V0.2 contamination rule is explicit: if source discovery exposes realised market prices for a candidate before PRE-OUTCOME ANALYSIS FREEZE, that candidate is excluded from the V0.2 Development sample.

Therefore:
- MC -> BEAM = EXCLUDED_CONTAMINATED_V0.2
- It may remain useful as a future independently frozen confirmatory/example dataset, but may not enter V0.2 Development.

Previously frozen contamination exclusions remain:
- RBN -> AEVO
- BNX old -> BNX new
- OMI if encountered with contaminated discovery surface.

## Metadata-only market-source probe

A metadata-only CoinGecko ID resolver exists at:
research/token_migration_forced_conversion_basis/tools/tmfcb_v02_metadata_probe.py

Workflow:
.github/workflows/tmfcb-v02-source-metadata-probe.yml

The probe:
- requests only /api/v3/coins/list;
- outputs id/symbol/name metadata;
- does NOT request market_data;
- does NOT request OHLC;
- does NOT request historical prices;
- does NOT request returns or basis.

V0.2 expanded this probe to cover OGV/OGN, CUDOS/FET, MPL/SYRUP, RAINI/RST, MFT/HIFI, BIT/MNT, GAL/G, PLA/PDA, CQT/CXT, MATIC/POL, RNDR/RENDER, KEEP/NU/T and tBTC identities.

This improves symbol-identity feasibility but does NOT prove historical contemporaneous coverage by itself.

## Why V0.2 stops at SOURCE_BLOCKED

There are now >=12 plausible mechanism programmes.

However, at least one of these remains unresolved for too many programmes:
- exact activation transaction hash;
- exact activation block/timestamp;
- exact immutable effective/closure boundary;
- converter disable transaction;
- historic DEX pool identity;
- same/cross-venue overlap existence;
- archive/schema provenance that can be inspected without opening values.

Direct explorer pages are unsafe for this phase because modern explorers commonly render live token prices automatically. The MC contamination proves this is a real failure mode, not a theoretical concern.

A source gate cannot be passed by silently accepting announcement dates in place of activation blocks or by browsing price-bearing explorer UI until twelve events look usable.

## Exact next remediation needed

A future V0.3 may reopen SOURCE ONLY, preserving all V0.1/V0.2 rules, and use a machine-readable metadata-only acquisition path:

1. contract/deployment manifests from first-party GitHub repositories;
2. raw JSON-RPC calls limited to:
   - eth_getCode
   - eth_getTransactionReceipt for pre-identified tx hashes
   - eth_getBlockByNumber for timestamps
   - eth_getLogs for migration/disable events only;
3. no token-price APIs;
4. no explorer HTML pages;
5. exchange symbol/listing archives queried only for symbol + listing/delisting timestamps, never OHLC/trade values;
6. DEX factory/event logs used only to prove pool creation/token identities/fee tier, never swap amounts or implied prices;
7. freeze exact venue/pool mapping before any price endpoint becomes callable.

If this closes >=12 programmes, V0.3 can issue SOURCE_GATE_PASS and create the separate PRE-OUTCOME ANALYSIS FREEZE.

If an exhaustive machine-readable remediation leaves <12 fully admissible programmes, close INSUFFICIENT_SAMPLE.

## Final V0.2 accounting

Plausible independent mechanism programmes after remediation: >=14
Fully closed to ALL immutable + outcome-blind price-provenance requirements: <12
Contaminated candidates newly excluded: MC -> BEAM
Market price endpoints intentionally queried: 0
OHLC values intentionally opened: 0
Returns calculated: 0
Basis calculated: 0
Development runs: 0
2026 outcomes opened: 0
Trading/account/private endpoints: 0

Verdict: SOURCE_BLOCKED

No PRE-OUTCOME ANALYSIS FREEZE may be created from V0.2.
