# DLS — DRIFT 2022–2024 SIGNED SEMANTICS TEMPORAL AUTHORITY FREEZE V0.1

Date: 2026-09-29
Status: FROZEN BEFORE TEMPORAL SEMANTICS AUDIT
Branch: dls-signed-flow-authority-v01

## Purpose

Determine whether the source-proven signed `liquidate_perp` interpretation calibrated on January 2023
can be applied defensibly to the full frozen Drift V0.1 source interval:

`[2022-11-04T15:17:54Z, 2025-01-01T00:00:00Z)`.

This is SOURCE-ONLY. No market prices, returns, PnL or future outcomes may be read.

## Canonical population authority

The already-completed Drift field-enrichment authority is canonical:
- field enrichment finalize run: 36462724666
- artifact: dls-drift-field-unit-final-v03
- artifact ID: 10989750258
- field classification: DRIFT_FIELD_ENRICHMENT_POPULATION_PASS
- registry classification: DRIFT_MARKET_UNIT_REGISTRY_POPULATION_PASS
- total enriched events: 2,655,920
- frozen liquidate_perp candidates: 1,953,488
- partition receipts: 86 / 86 PASS
- missing / extra / duplicate / source anomaly / semantic conflict: 0
- temporal market-unit unresolved lookup count: 0

No event may be added/dropped based on direction or market outcome.

## Historical source identity

Protocol source authority is GitHub repository ID 497045217.

The legacy path `drift-labs/protocol-v2` redirects to the same repository now exposed as
`velocity-exchange/protocol-v2`.

The audit MUST use the public full Git history of that repository.

## Frozen state enumeration

Create a chronological state census for the relevant source files.

Target semantic files:
- programs/drift/src/controller/liquidation.rs
- programs/drift/src/math/orders.rs
- programs/drift/src/state/user.rs
- programs/drift/src/state/events.rs

The census includes:
1. the latest repository state at or before 2022-11-04T15:17:54Z; and
2. every subsequent commit before 2025-01-01T00:00:00Z that changes at least one target file.

A source state is not skipped because its semantics/layout are inconvenient.

## Frozen directional invariants

Every enumerated state must prove all of the following or the temporal authority FAILS CLOSED:

1. `get_position_delta_for_fill` maps:
   - PositionDirection::Long => positive base-asset delta;
   - PositionDirection::Short => negative base-asset delta.

2. Perp-position direction maps:
   - existing non-negative base position => Long;
   - existing negative base position => Short;
   - Long closes with Short;
   - Short closes with Long.

3. `liquidate_perp` builds the liquidated user's realized position delta from the direction-to-close.

4. A realized perp liquidation emits source evidence that binds the liquidated user's signed base delta
   to the liquidation/fill identity. The canonical preferred field is
   `LiquidatePerpRecord.base_asset_amount`.
   If a historical source state uses a different source-native field/path, the audit may record it
   only if its equivalence is directly proven from that state’s code. No inference from later prices is permitted.

5. Zero-transfer/early-return branches must not be reclassified as realized signed flow.

## Layout authority

The audit must enumerate every distinct historical source layout needed to decode the signed evidence.

At minimum, record normalized field order/type for:
- LiquidationRecord prefix through `liquidate_perp`;
- LiquidatePerpRecord.

Distinct layouts become immutable decoder candidates.

No deployment-date assumption is required for downstream decoding.

Instead, the future full-population decoder MUST:
- try only decoder layouts admitted by this pre-population source audit;
- require exact transaction/user/liquidator/market binding;
- accept a realized event only when all successful decodes that bind exactly agree on the same non-zero sign;
- mark ambiguous/conflicting layout interpretations fail-closed.

Thus a source deployment mapping is unnecessary only if the on-chain payload itself produces a unique,
non-contradictory signed interpretation across the admitted historical layouts.

## Temporal authority PASS

Classification:
`DRIFT_2022_2024_SIGNED_SEMANTICS_TEMPORAL_PASS`

only if:
- the state census is complete under the frozen Git history rule;
- all enumerated states satisfy the directional invariants;
- every realized signed-evidence layout is enumerated;
- no state has an opposing sign convention;
- no relevant source state is unreadable/unresolved;
- source repository identity is fixed to repository ID 497045217.

Otherwise:
`DRIFT_2022_2024_SIGNED_SEMANTICS_TEMPORAL_BLOCKED`.

PASS authorizes only a separately frozen full-population source-only signed-flow census.
It does not authorize market-return testing, 2025/2026 outcomes, or trading.

## Firewall

prices=false
returns=false
pnl=false
market_outcomes=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
paid_source=false
post_outcome_tuning=false
merge_main=false
