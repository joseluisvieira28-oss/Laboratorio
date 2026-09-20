# MSEL-002 — ECONOMIC OUTCOME FREEZE V0.1

Date: 2026-09-20
Branch: `memecoin-metadata-duplication-v0.1`
Status: **ECONOMIC OUTCOME DESIGN FROZEN / OUTCOMES STILL LOCKED UNTIL COHORT FREEZE PASS**

## Upstream source authority

This freeze is downstream only of the official MSEL-002 source/prevalence result:

- workflow run: `35449436752`
- aggregate artifact: `10592246992`
- artifact digest: `sha256:659e2b03e95fbaa867f0ef20df1c44eb5a34f579aebae3b918b11b5d8c45a64f`
- `candidate_identity_features_v05.jsonl` SHA-256:
  `59cda61a7d7284d233bd1ad93424d87db35229ac1e8876d80174591a85d36e0a`
- source/prevalence result: **PASS**
- candidate CREATEs: 3,278
- immutable-URI candidates: 2,595
- primary cross-creator exposed: 51
- unique primary identity groups: 47
- unique primary candidate creators: 33

No post-launch economic outcome was used to create this freeze.

## Frozen exposure

Primary exposure remains unchanged:

`PRIOR_EXACT_IMMUTABLE_IDENTITY_REUSE_6H`

No fuzzy matching, case-folding, URI relaxation, same-creator inclusion, time-window widening, second source window, or outcome-driven feature edit is permitted.

## Frozen matched cohort

All 51 primary exposed candidates enter the economic cohort.

For each exposed candidate, exactly 10 unique unexposed controls are chosen from the already-open source/prevalence rows.

Control eligibility:

1. `candidate == true`;
2. `immutable_uri_eligible == true`;
3. `prior_exact_immutable_identity_reuse_6h == false`;
4. `same_creator_clone_6h == false`;
5. control origin creator differs from the exposed origin creator;
6. control identity key differs from the exposed identity key;
7. absolute candidate launch-time difference is <= 300 seconds.

Exposures are processed in ascending `(block_time, slot, mint)` order.

Eligible controls are ranked by:

1. absolute launch-time difference;
2. `SHA256("MSEL-002-ECONOMIC-OUTCOME-CONTROLS-V1|2026-09-20" | exposure_mint | control_mint)`;
3. slot;
4. mint.

The first 10 unused controls are selected. Controls are globally unique across exposed sets.

Expected frozen cohort:

- 51 exposed;
- 510 controls;
- 561 total candidates;
- 51 matched sets.

Any count mismatch, duplicate control, source-file hash mismatch, or inability to assign 10 controls to every exposure is `COHORT_FREEZE_FAILURE`. Do not change the matching window or reuse controls as rescue.

## Point-in-time protocol authority

Official Pump documentation is pinned to:

`pump-fun/pump-public-docs@7645c16c68ae9dd3a7487b543edcdc94adf7b5e0`

Pump program:
`6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P`

Frozen Pump `migrate` discriminator:
`[155,234,231,146,236,158,162,30]`
hex:
`9beae792ec9ea21e`

PumpSwap / Pump AMM program:
`pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA`

The official pinned docs state that `migrate(user, mint)` migrates a completed Pump bonding curve to PumpSwap and that canonical migrated PumpSwap pools use index 0.

## Frozen Discovery question

Does prior exact cross-creator immutable-identity reuse identify candidates that are materially less likely to complete Pump -> PumpSwap migration than otherwise comparable immutable-URI launches created at essentially the same time?

This is a fragility/mechanism Discovery test. It is **not** yet a trading strategy test.

## Frozen outcomes

### Primary outcome — MIGRATE_24H

TRUE iff a successful Solana transaction (`meta.err == null`) contains the exact Pump program `migrate` instruction for the candidate mint within:

`candidate_block_time < migrate_block_time <= candidate_block_time + 86,400 seconds`

The Pump program ID, discriminator and mint account mapping must match the pinned official IDL exactly.

### Secondary outcome — MIGRATE_72H

Same exact definition over:

`candidate_block_time < migrate_block_time <= candidate_block_time + 259,200 seconds`

### PumpSwap continuity audit

If migration is detected, the outcome collector must preserve enough raw evidence to verify the canonical PumpSwap program/account continuity. Absence of a PumpSwap continuity proof cannot be silently treated as a clean non-migration observation.

No price, return, market-cap, PnL, winner/catastrophe, liquidity-PnL or trading execution outcome is authorized in V0.1.

## Frozen source-completeness gate

Because the scientific outcome includes absence of migration, the source must prove the full candidate-specific 72-hour observation interval.

Every one of the 561 frozen candidates must end in exactly one state:

- `MIGRATED_24H`;
- `MIGRATED_72H_ONLY`;
- `NO_MIGRATION_72H_SOURCE_COMPLETE`;
- `SOURCE_UNRESOLVED`.

Primary scientific adjudication is forbidden if any candidate is `SOURCE_UNRESOLVED`.

No candidate may be dropped after outcome acquisition.

## Frozen statistic

For matched set i:

`d24_i = exposed_migrate24_i - mean(control_migrate24_i[1..10])`

Primary effect:

`D24 = mean(d24_i)`

Negative is the predicted direction.

Secondary effect `D72` is defined identically using MIGRATE_72H.

Uncertainty:

- matched-set bootstrap;
- 100,000 resamples of the 51 matched sets with replacement;
- frozen seed `MSEL-002-MIGRATION-BOOTSTRAP-V1|2026-09-20`;
- percentile 95% confidence interval.

## Frozen verdict gates

`DISCOVERY_SIGNAL` only if ALL are true:

1. cohort/source integrity PASS;
2. all 561 outcomes source-resolved;
3. `D24 <= -0.10`;
4. upper bound of the 95% matched-set bootstrap CI for D24 is < 0;
5. `D72 < 0`.

If source integrity fails: `SOURCE_DATA_FAILURE`.

If D24 does not meet both the -10 percentage-point effect gate and CI gate, or D72 is non-negative: `DISCOVERY_NO_EDGE_FOR_FROZEN_MIGRATION_MECHANISM`.

No rescue by changing 24h/72h horizons, matching window, control count, exposure definition, identity rules, creator rules, effect threshold, bootstrap method, or source population.

A Discovery signal does NOT authorize prices, returns, PnL, live trading, capital, alerts/webhooks, wallets, exchange mutation, main merge, or automatic Tier promotion. Any later market-price/execution test requires a new prospectively frozen authority.

## Immediate execution boundary

The next allowed action is **source-only cohort freeze reproduction** from the exact upstream artifact.

Post-launch migration outcomes remain locked until that cohort reproduction returns `ECONOMIC_COHORT_FREEZE_PASS`.
