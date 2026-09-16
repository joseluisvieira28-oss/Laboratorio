# PMD-001 — REGIME GATE PRE-OUTCOME V0.2

Date: 2026-09-16
Status: **REGIME_DEFINITION_PASS / POPULATION_BINDING_PENDING_SOURCE_REBUILD**
Branch: `pumpfun-migration-direction-source-rebuild-v0.2`

## Purpose

This document freezes the regime interpretation before any economic outcome is opened. It does not authorize Discovery. Population binding remains subordinate to the V0.2 source rebuild gate.

## Graduation mechanism

Pump.fun's official bonding-curve documentation states that when the graduation threshold is reached, the curve closes and the liquidity pool is migrated atomically to PumpSwap; graduation is automatic and irreversible and the migrated assets form the canonical liquidity pool.

Authority: https://pump.fun/docs/bonding-curve

Therefore PMD-001 keeps the previously frozen decision boundary `T0 = authoritative canonical-pool migration timestamp`. No discretionary listing-announcement timestamp is substituted.

## Primary regime: PRE-BOOST only

The frozen public source period used by PMD-001 V0.1 runs through 2026-07-14. Reports dated 2026-07-21 and 2026-07-29 describe Pump.fun BOOST as a later mechanism that applies programmed post-migration buy pressure / buybacks during the first minutes after migration.

Authorities used only to define the external regime boundary:
- https://cryptobriefing.com/pumpfun-buyback-boost-memecoin-graduation/
- https://www.theblock.co/post/363773/pump-fun-token-graduation-rate-jumps-boost-changes-launch-incentives

Because the V0.1/V0.2 frozen source ends before 2026-07-21, the primary experiment is PRE-BOOST. POST-BOOST data is quarantined as a separate future translation/replication experiment and may not be mixed into PMD-001 V0.2.

## Mayhem quarantine

Pump.fun's official Mayhem documentation states that an autonomous agent can buy and sell eligible Mayhem coins during their first 24 hours and that Mayhem eligibility is established at coin creation. This is a direct artificial source of order flow that can contaminate the demand-vs-latent-supply mechanism.

Authority: https://pump.fun/docs/mayhem-mode

Primary PMD-001 population therefore excludes `is_mayhem_mode = true`. This exclusion was frozen before outcomes and cannot be relaxed or reversed after results.

## Fee/execution regime

Pump.fun's official fee schedule, last updated 2026-05-20, states:
- bonding-curve total trading fee: 1.25%;
- canonical PumpSwap SOL pool at 0–420 SOL market cap: 1.25% total per trade;
- canonical fees decline at higher market-cap tiers.

Authority: https://pump.fun/docs/fees

PMD-001 retains the already frozen **3.00 percentage-point round-trip execution stress**. It is intentionally not reduced to match a best-case fee tier. Network/priority/slippage/adverse-execution risk remains absorbed by the conservative stress convention. A lower-cost rescue is forbidden.

## Corpus-specific regimes retained

The following source-specific controls from `PROTOCOL_FREEZE_V01.md` remain binding:
- 2026-07-03 outage day excluded;
- post-2026-07-04 curve-depletion regime shift retained as an explicit stratification flag;
- `top10_pct_suspect` rows excluded from concentration-dependent analysis unless independently reconstructed;
- stale `wallet_stats` activity aggregates forbidden as point-in-time activity;
- synthetic migration sentinels forbidden as canonical pool identities;
- SOL-amount corruption/missingness may not be silently imputed.

These are source/regime controls, not outcome-selected filters.

## Gate status

External mechanism/regime definition: **PASS**.

Final population-level regime gate: **PENDING V0.2 SOURCE REBUILD** because the exact >=1,000 raw-source-eligible manifest must first be reconstructed and hashed.

No return, PnL, direction label, feature/outcome correlation, Validation result or Protected Holdout result has been opened by this gate.

Governance remains research-only, fail-closed, no live trading, no exchange mutation, no main merge, no post-outcome tuning, no cherry-picking.
