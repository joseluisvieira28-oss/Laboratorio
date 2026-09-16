# MSEL-002 — Prior-Only Exact Metadata Duplication — Pre-Source Freeze V0.1

Status: `PRE_SOURCE_FROZEN / OUTCOMES_LOCKED`

Branch: `memecoin-metadata-duplication-v0.1`

This is a NEW experiment. It is not a rescue, retune, extension, or reinterpretation of MSEL-001 Pilot25 V14. MSEL-001 remains closed as `PILOT25_PARTIAL_GATES_FAIL` under its frozen mechanism.

## Scientific question

Does strictly point-in-time, exact reuse of a previously existing coin identity identify materially more fragile Pump.fun launches than otherwise comparable launches?

Economic thesis: a launch that exactly reuses an already-existing identity is competing against an established/original referent and may be disproportionately manufactured, low-conviction, or short-lived. The feature is knowable at creation time from prior-only metadata. No claim about fraud, intent, or common beneficial ownership is required.

## Independent prior authority

This mechanism was identified in the MSEL-001 Research Log BEFORE Pilot25 outcomes were opened as an independent `copycat / metadata-reuse fragility` attack. The 2026 CCS paper `Meme Coin Factories: Uncovering Large-Scale Manipulations on pump.fun` independently reports large-scale exact metadata duplication and materially lower graduation among duplicates than originals. Those published results motivate testing the mechanism but are NOT our trading outcome.

## Primary exposure definition — frozen concept

Primary exposure is `PRIOR_EXACT_METADATA_DUPLICATE`.

For candidate coin C at creation time t(C), exposure is TRUE only if there exists coin P with proven creation time t(P) < t(C) and all required strict identity fields match exactly under the source authority:

1. name;
2. symbol;
3. description;
4. profile-image content identity/hash.

Additional rules:

- comparison corpus is strictly prior-only;
- same-timestamp ambiguity is fail-closed unless chain ordering proves predecessor order;
- fuzzy similarity, case-insensitive similarity, edit distance, ticker-only, name-only, social-handle similarity, and semantic/image-embedding similarity are NOT primary features;
- same exact creator-address repeats are recorded separately as `SAME_CREATOR_CLONE` and are not counted as the primary cross-address exposure;
- different addresses are not asserted to be different humans/entities;
- creator-cluster relationships may be retained as a sensitivity descriptor only if funding evidence is point-in-time; they may not redefine the primary exposure after outcomes;
- mutable current HTTP content cannot establish historical identity. Image/description evidence must be content-addressed/immutable or explicitly archived/proven as-of launch.

The paper's looser name+symbol rules are excluded from the primary mechanism because they materially increase false-positive risk.

## Source Stage S0 — metadata-only audit

Before opening any dataset rows, prevalence, exposure labels, prices, trades, graduation outcomes, or future token state, perform ONLY a public-deposit inventory audit.

Authoritative public deposit identifier discovered from the authors' own publication source:

- DOI: `10.1184/R1/33420628`
- Figshare/KiltHub article id: `33420628`

S0 may inspect only:

- deposit/article metadata;
- version/revision metadata;
- license;
- file names;
- file byte sizes;
- provider checksums;
- file MIME/type metadata;
- descriptions/readme/schema text that does not contain per-coin outcomes or prevalence results.

S0 MUST NOT download or inspect record-level dataset rows.

S0 output must be an immutable inventory JSON with SHA-256.

## Source acceptance requirements before cohort freeze

After S0 inventory, but still before row-level data inspection, a separate Source Gate V0.1 must freeze the exact files and deterministic cohort rule. The source must be able to support:

- exact coin/mint identifier;
- proven creation timestamp/order;
- creator address at creation;
- all four strict identity fields or an author-provided strict-duplicate label whose exact derivation is reproducible and prior-only;
- enough provenance to ensure no post-candidate metadata leakage;
- a clearly identified random transaction sample or another outcome source if economic outcomes are later authorized.

If the public deposit omits the strict identity evidence because of redistribution restrictions, MSEL-002 becomes `FEATURE_SOURCE_BLOCKED` unless an independently reproducible immutable/PIT source is frozen BEFORE any candidate outcomes are opened. Do not silently substitute fuzzy on-chain name/symbol matching.

## Candidate period — frozen regime boundary

The intended candidate period is September–October 2025, entirely before Pump.fun Mayhem Mode was introduced. Exact cohort sampling is intentionally NOT yet frozen because it depends on identifying which deposit file is the authoritative census and which, if any, is the authors' random transaction sample. This choice must be made from S0 schema/file metadata only, never from prevalence or outcomes.

The Pump IDL authority immediately before 2025-09-01 is pinned to official `pump-fun/pump-public-docs` commit:

`7645c16c68ae9dd3a7487b543edcdc94adf7b5e0` (2025-08-29)

Pinned `idl/pump.json` Git blob SHA observed during pre-source audit:

`5ef1cbb696a0957cc7e4e191652d439d797982e9`

The June-2025 MSEL-001 IDL must NOT be silently reused.

## Outcome lock

No MSEL-002 candidate outcome may be opened during S0 or Source Gate design.

No use of MSEL-001 Pilot25 outcomes is permitted to select:

- metadata thresholds;
- candidate exclusions;
- sampling windows;
- duplicate definitions;
- creator exclusions;
- liquidity thresholds;
- future horizons.

A later economic-outcome freeze must be written before any selected MSEL-002 candidate future path is decoded.

## Governance

- research-only;
- fail-closed;
- no live trading;
- no exchange or chain mutation;
- no orders;
- no alerts/webhooks;
- no merge to main;
- no Render deployment;
- no post-outcome tuning;
- no rescue of MSEL-001;
- no candidate outcomes during source/prevalence design.
