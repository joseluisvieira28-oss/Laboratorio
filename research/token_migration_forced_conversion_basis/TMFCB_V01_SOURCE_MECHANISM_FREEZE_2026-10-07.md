# TOKEN-MIGRATION-FORCED-CONVERSION-BASIS-001 — V0.1 SOURCE / MECHANISM FREEZE

Date: 2026-10-07
Branch: token-migration-forced-conversion-basis-001-v0.1-source-2026-10-07
Authority: operator instruction in ChatGPT conversation.
Scope: 2022-01-01 through 2025-12-31 only. 2026 is CLOSED.

## Scientific question

In token migrations / redenominations that are mandatory or economically binding, with a known OLD -> NEW conversion ratio, does the conversion-adjusted legacy/new basis converge predictably toward zero between the first immutable public signal and the frozen migration end/effective boundary?

Primary mechanism is NOT absolute token direction. It is conversion-adjusted OLD/NEW basis convergence.

## Hard governance

- Research only; fail closed.
- Do not alter or merge main.
- No trading, orders, wallets, account reads, private/authenticated endpoints, exchange mutation, or spending.
- No post-outcome tuning.
- Do not use this family to rescue any result from another mine.
- AAVE-GOV-LT-FORCED-DELEVERAGING-001 is separate and MUST NOT be modified, reinterpreted, or used here.
- During SOURCE GATE, market outcome values MUST NOT be opened.
- 2026 remains sealed for possible later confirmation.

## Unit of independence

One project / migration programme = one independent shock, even if:
- multiple chains are involved;
- multiple exchanges support the conversion;
- multiple legacy tokens merge into one new token.

## Inclusion requirements — ALL must be defensible before outcome access

An event is source-eligible only if the pre-outcome source record can establish:

1. OLD token identity.
2. NEW token identity.
3. Fixed conversion ratio or deterministic conversion formula.
4. Public migration / redemption mechanism.
5. An identifiable migration/redemption contract OR an equivalently immutable on-chain mechanism.
6. Activation transaction/block or another immutable activation boundary.
7. Economic retirement, deprecation, redemption consequence, or termination of OLD that makes the conversion economically binding rather than a cosmetic rename.
8. A deadline, termination boundary, irreversible phase transition, or another immutable temporal/economic boundary.
9. A public source trail sufficient to establish points 1–8 without inspecting post-event market returns.
10. Public historical-price source feasibility for BOTH OLD and NEW over a contemporaneous interval, preferably same venue and quote currency, with venue selected before outcomes.

## Exclusions

Reject before outcome access:
- simple rebrands;
- ticker-only changes;
- chain bridges where the economic asset remains the same;
- optional swaps with no demonstrated economic consequence for OLD;
- exchange-only bookkeeping where no project-level migration mechanism is evidenced;
- migrations whose ratio/formula cannot be frozen from pre-outcome evidence;
- programmes where OLD/NEW identity is ambiguous;
- events selected because of later price behaviour.

## Census gate

- Complete defensible universe scan across 2022–2025.
- Minimum fully defensible independent programmes required: >= 12.
- If complete universe proves < 12: verdict = INSUFFICIENT_SAMPLE.
- If provenance / source coverage cannot be demonstrated sufficiently to adjudicate the universe: verdict = SOURCE_BLOCKED.
- No outcome access before this gate is adjudicated.

## Price-source feasibility gate (schema/provenance only)

For each otherwise eligible programme, prove BEFORE opening values:
- historical OLD market-data endpoint/archive exists;
- historical NEW market-data endpoint/archive exists;
- date range can cover a contemporaneous window between T_signal and T_end/effective boundary;
- same venue + quote is preferred;
- venue/quote mapping is frozen before values are fetched;
- endpoint schema, timestamp semantics, symbol identity, and provenance are recorded;
- no venue substitution after outcome inspection.

Permitted at SOURCE GATE:
- endpoint existence checks;
- metadata / symbol listings;
- archive filenames / manifest checks;
- HTTP status / schema checks;
- timestamps and coverage boundaries;
- contract/code/event source inspection.

Forbidden at SOURCE GATE:
- OHLC/open/high/low/close values;
- trade prices;
- calculated returns;
- calculated basis;
- any ranking by realised market behaviour.

## Candidate-discovery register (NOT YET INCLUDED)

Candidates may be listed here only as leads. Presence is not inclusion.

Known leads to source-adjudicate without market outcomes:
- BTTOLD -> BTT (2022 redenomination)
- ANY -> MULTI (2022)
- VIDT old -> VIDT DAO (2022)
- COCOS -> COMBO (2023)
- MC -> BEAM (2023)
- GALA v1 -> GALA v2 (2023)
- STG v1 -> STG v2 (2023)
- MATIC -> POL (2024)
- RNDR -> RENDER (2024)
- GAL -> G (2024)
- AGIX -> FET / ASI programme (2024)
- OCEAN -> FET / ASI programme (same programme as AGIX; count once)
- KLAY + FNSA -> KAIA programme (2024)
- STRAX -> new STRAX (2024)
- FTM -> S (2024/2025)
- EOS -> A / Vaulta (2025)
- MKR -> SKY (2025)
- LOKA -> A2Z (2025)
- STPT -> AWE (2025)
- DAR -> D (2025)

Each lead must still pass ALL hard inclusion requirements. Cosmetic rebrands and non-binding optional swaps must be rejected.

## Frozen downstream rule if SOURCE_GATE_PASS

A separate PRE-OUTCOME ANALYSIS FREEZE MUST be created and committed before any market outcome is opened. It must freeze:
- exact T_signal definition;
- exact T_end definition;
- exact conversion-adjusted basis formula;
- primary horizon;
- treatment/control logic;
- liquidity minimums;
- event clustering;
- fees/slippage;
- missingness;
- minimum sample;
- leave-one-out rule;
- calendar/project concentration;
- exact decision gates.

Only after that freeze may Development be run ONCE.

Allowed verdict taxonomy:
- SOURCE_BLOCKED
- INSUFFICIENT_SAMPLE
- NO_EDGE_DISCOVERY
- SURVIVES_CONVERSION_DISCOVERY

If the primary test fails: close with NO_EDGE_DISCOVERY. No rescue subsets, alternate horizons, alternate venues, or secondary resurrection.

If Development survives: STOP. Do not call it a diamond and do not open 2026 or trading. A new confirmatory freeze requires explicit operator authority.
