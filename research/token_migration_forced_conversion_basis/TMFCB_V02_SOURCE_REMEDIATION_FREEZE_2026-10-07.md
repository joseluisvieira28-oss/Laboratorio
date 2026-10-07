# TOKEN-MIGRATION-FORCED-CONVERSION-BASIS-001 — V0.2 SOURCE REMEDIATION FREEZE

Date: 2026-10-07
Branch: token-migration-forced-conversion-basis-001-v0.2-source-remediation-2026-10-07
Parent: V0.1 SOURCE_BLOCKED closeout at ec7bc2aff28dc1663375ba59edcec4901e0f9d02

## Purpose

Attempt to remediate SOURCE_BLOCKED by improving immutable provenance collection WITHOUT changing the economic hypothesis, opening market outcomes, lowering the minimum sample, or using post-outcome performance to select events.

V0.1 remains authoritative and unchanged.

## Operationalization of the V0.1 immutable temporal/economic boundary

A candidate may satisfy the frozen "deadline on-chain or other immutable temporal condition" only through one of these source-defined classes, adjudicated before market outcome access:

A. FIXED_DEADLINE
- A finite conversion/migration deadline published by a first-party/governance source.
- After the deadline, conversion is disabled or materially penalized by a rule fixed before outcome access.

B. SNAPSHOT_DEPRECATION
- A deterministic snapshot/cutover block or timestamp creates NEW at a fixed ratio/formula.
- After that boundary, OLD loses project/ecosystem utility or is explicitly deprecated/defunct.
- Mere exchange delisting is insufficient.

C. CHAIN_HALT
- OLD is native to a chain that stops producing blocks / is sunset at an identifiable block or upgrade boundary.
- Balances are deterministically converted or redeemable into NEW.

D. PERMANENT_CONVERTER_DISABLE
- A conversion contract is permanently disabled at an identifiable on-chain transaction/block after a previously public finite window.

E. PROTOCOL_UTILITY_CUTOVER
- Governance/protocol rights, emissions, staking rewards, or required network utility are immutably moved to NEW at a specified boundary and OLD ceases those rights.
- Indefinite convertibility alone does not qualify; the economic consequence must be objectively demonstrated.

Excluded:
- cosmetic rebrand/ticker-only changes;
- bridge-only chain moves with unchanged economic asset;
- indefinite optional swaps where OLD retains material project utility;
- exchange-only bookkeeping without project-level mechanism;
- any event needing market-return evidence to justify inclusion.

## Contemporaneous-price feasibility rule

To study conversion-adjusted basis, BOTH assets must be publicly price-observable for a non-zero contemporaneous interval after T_signal and before T_end/effective boundary.

Acceptable outcome-blind source stacks may be:
1. same venue + same quote;
2. pre-frozen public DEX pools for both tokens with a common quote;
3. two pre-frozen public venues normalized to a common quote, only if same-venue overlap is impossible and the mapping is frozen before any price is fetched.

A project fails the SOURCE GATE if NEW is not transferable/tradeable until after the migration window closes, because no contemporaneous OLD/NEW basis can exist.

## Contamination rule

If a source-discovery result accidentally exposes realized market prices, realised returns, or realised conversion-basis values for a candidate before PRE-OUTCOME ANALYSIS FREEZE, that candidate is EXCLUDED from this V0.2 Development sample. It cannot be rescued.

Known V0.2 contamination exclusions:
- RBN -> AEVO: a broad discovery result surfaced realised RBN/AEVO price/spread commentary. EXCLUDE.
- BNX old -> BNX new: broad discovery results surfaced realised price commentary. EXCLUDE.
- OMI migration: a discovery surface exposed post-event price-change fields. EXCLUDE if encountered as a candidate.

Pre-announced conversion ratios, tokenomics, target/vesting formulas, contract parameters, and deadlines are source/mechanism evidence, not realised market outcomes.

## Minimum sample and stopping rule

- Need >=12 independent programmes meeting ALL V0.1 + V0.2 requirements.
- One project/programme = one shock.
- If exhaustive remediation establishes fewer than 12 admissible programmes: INSUFFICIENT_SAMPLE.
- If >=12 appear eligible but immutable provenance or public historical-price provenance cannot be closed defensibly: SOURCE_BLOCKED.
- If >=12 are fully source-admissible: SOURCE_GATE_PASS, then create a separate PRE-OUTCOME ANALYSIS FREEZE before any price values are fetched.

## 2026

2026 market outcomes remain CLOSED.
Sources published in 2026 may not be used to retrospectively define a 2022–2025 T_signal/T_end unless they merely reproduce an already immutable historical on-chain fact and no earlier source is reasonably available. Any such use must be flagged.
