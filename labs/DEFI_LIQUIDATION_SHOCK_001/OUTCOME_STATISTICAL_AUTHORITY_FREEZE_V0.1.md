# DEFI-LIQUIDATION-SHOCK-001 — OUTCOME & STATISTICAL AUTHORITY FREEZE V0.1

Date: 2026-09-27
Status: FROZEN PROSPECTIVE DESIGN / OUTCOME-BLIND
Activation: ONLY after FINAL_PRE_DISCOVERY_AUTHORITY_V0.1

## Scientific claim tested

Primary claim:

Completed on-chain liquidation cascades are followed by a larger near-term absolute market move than prospectively matched non-event control windows for the same directly mapped market.

This V0.1 does NOT claim a universal signed direction.

## Why direction is not primary

A lending liquidation transfers collateral to a liquidator but does not prove that the received collateral is immediately sold.

Drift liquidation classes do not, from the currently frozen instruction identity alone, prove a universal long/short signed market-flow direction.

Therefore:
- no negative-return assumption is made for lending;
- no long/short direction is inferred for Drift;
- no signed-return promotion gate is authorized in V0.1.

A later signed-flow experiment would require a separate pre-outcome source authority.

## Primary price target

The market target is frozen from source semantics before outcomes.

### Lending families
Target:
collateral-underlying asset.

### Drift
- liquidate_perp -> perp_market_index underlying asset
- liquidate_spot -> asset_spot_market_index
- liquidate_borrow_for_perp_pnl -> perp_market_index underlying asset
- liquidate_perp_pnl_for_deposit -> perp_market_index underlying asset

Liability/debt/secondary market identities remain descriptive or separately multiplicity-controlled.

No target may be chosen because another leg has a stronger return.

## Market mapping

Only direct historically valid market mappings are allowed.

Allowed:
- exact underlying asset;
- canonical wrapped/unwrapped identity where source equivalence is deterministic (for example native SOL / wrapped SOL);
- Drift market-index identity resolved by frozen historical market registry.

Forbidden:
- BTC/ETH proxy for an unrelated asset;
- selecting a different venue/pair after seeing the event response;
- synthetic proxy chosen from correlation to future outcomes.

Unmapped assets remain MARKET_MAPPING_UNAVAILABLE and enter the missingness gate.

## Price-bar resolution

Primary research resolution:
1-minute bars.

For cascade T0:
A = first exact UTC minute boundary >= T0.

Entry:
P0 = OPEN of the 1-minute bar at A.

For horizon h:
Ph = OPEN of the 1-minute bar at A + h.

Return:
r_h = ln(Ph / P0)

Using bar OPEN at the aligned timestamp prevents using the close of a bar partly formed after the intended observation time.

## Frozen horizons

Primary horizon:
5 minutes

Secondary/sensitivity horizons:
- 1 minute
- 30 minutes
- 240 minutes (4 hours)

No additional horizon may enter the first Discovery after outcomes are opened.

## Primary outcome

For each matched event/control pair:

event_abs_h = |r_event,h|
control_abs_h = |r_control,h|

paired difference:
D_h = event_abs_h - control_abs_h

Primary estimand at 5m:
mean(D_5m)

Primary relative uplift:
mean(event_abs_5m) / mean(control_abs_5m) - 1

## Matched control rule

Control selection is deterministic and outcome-blind.

For each eligible cluster:
1. same directly mapped asset/market;
2. same temporal split (Discovery or OOS);
3. same calendar month;
4. same UTC hour-of-day;
5. candidate aligned minute must not lie within +/- 4 hours of any 60-second primary cascade T0 for that same market;
6. candidate must have all bars required for 1m/5m/30m/240m;
7. rank admissible candidates by SHA256(cluster_id || candidate_timestamp);
8. select the first admissible candidate.

Exactly one matched control is used per primary cluster.

No return magnitude enters control selection.

## Market-data missingness gate

A source-eligible cluster may be excluded only for prospectively defined market-data reasons:
- no direct market mapping;
- missing entry/open bar;
- missing required horizon bar;
- no admissible matched control.

Before economic inference:
- aggregate eligible-pair coverage must be >= 95% of market-mappable primary clusters;
- any protocol/class subgroup claimed inferentially must have >= 90% eligible-pair coverage.

Otherwise:
MARKET_DATA_SOURCE_BLOCKED

Missingness cannot be repaired by using a correlated proxy.

## Sample gate after market mapping

SOURCE_SAMPLE_GATE_PASS is necessary but not sufficient.

After market mapping/control availability, paired clusters must still satisfy:
- Discovery >= 1,000
- OOS >= 500

Subgroup thresholds remain those in SOURCE_SAMPLE_GATE_FREEZE_V0.1.

## Dependence-aware inference

Primary inference uses calendar-day block bootstrap over matched pairs.

Frozen settings:
- bootstrap repetitions: 5,000
- block key: UTC calendar date of event cascade T0
- resample days with replacement;
- all matched pairs from a selected day travel together;
- deterministic PRNG seed derived from:
  SHA256("DEFI-LIQUIDATION-SHOCK-001" || split || horizon || "V0.1")

95% percentile confidence intervals are reported.

## Primary Discovery PASS

Discovery primary 5m test passes only if ALL hold:
1. paired Discovery N >= frozen gate;
2. mean(D_5m) > 0;
3. lower bound of 95% day-block bootstrap CI for mean(D_5m) > 0;
4. relative uplift at 5m >= 10%;
5. at least two distinct inferential protocol families have positive 5m mean paired difference;
6. at least two of the three secondary horizons have positive paired mean difference;
7. at least one secondary horizon survives the frozen secondary multiplicity gate below.

Otherwise, if source/market data are valid:
NO_EDGE_DISCOVERY

## Secondary horizon multiplicity

Family:
1m, 30m, 240m.

Use Holm-Bonferroni family-wise alpha = 0.05 on the three one-sided hypotheses:
mean(D_h) > 0

Secondary significance is supportive only and cannot replace failure of the primary 5m gate.

## OOS PASS

OOS is opened only after Discovery completes under the frozen design.

OOS passes only if ALL hold:
1. paired OOS N >= frozen gate;
2. mean(D_5m) > 0;
3. lower bound of 95% day-block bootstrap CI for mean(D_5m) > 0;
4. 5m relative uplift >= 10%;
5. at least two distinct inferential protocol families have positive 5m mean paired difference;
6. at least two secondary horizons have positive paired mean difference.

No OOS threshold may be loosened after Discovery.

## Effect-size guardrail

Statistical significance caused only by very large N is insufficient.

The 10% relative-uplift gate at the primary 5m horizon is mandatory in both Discovery and OOS.

Absolute bps effects are reported but no bps threshold is added after outcomes.

## Protocol-family guardrail

The pooled result may be cluster-weighted, but promotion cannot rest on a single protocol family.

Protocol-family means must be reported separately.

At least two inferential protocol families must show positive 5m paired mean difference in both the relevant Discovery/OOS gate.

No family is removed because it is weak.

## Sensitivity clustering

Economic sensitivity may repeat the same frozen test on:
- 15-second cascades
- 300-second cascades

Primary scientific conclusion remains the 60-second cascade result.

Sensitivity-cluster results cannot rescue a failed 60-second primary test.

If inferential p-values are reported for both sensitivity definitions, they form an additional Holm-corrected family.

## Failed liquidation attempts

Failed attempts are NOT realized forced-flow events.

They may be analyzed later only as a separately frozen negative-control family.

They do not enter primary event clusters or rescue a failed result.

## Promotion taxonomy

SOURCE_BLOCKED:
source/field/unit/market-data authority or required data coverage fails.

NO_EDGE_DISCOVERY:
valid Discovery completed but frozen primary gate fails.

SURVIVES_DISCOVERY:
all Discovery gates pass. This is not a tradability claim.

NO_EDGE_OOS:
Discovery passed, valid OOS completed, OOS gate fails.

SURVIVES_OOS:
Discovery and OOS pass under this frozen design. Still no live-trading authority.

2025/2026 remains protected after SURVIVES_OOS unless separately authorized.

## No post-outcome changes

After any market outcome is opened, do not change:
- primary target;
- control rule;
- horizons;
- cluster rule;
- sample thresholds;
- missingness thresholds;
- bootstrap design;
- uplift threshold;
- multiplicity rule;
- temporal split;
- promotion taxonomy.

## Firewall at freeze

prices_opened=false
returns_opened=false
pnl_opened=false
economic_outcomes_opened=false
protected_2025_2026_opened=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
post_outcome_tuning=false
merge_main=false
