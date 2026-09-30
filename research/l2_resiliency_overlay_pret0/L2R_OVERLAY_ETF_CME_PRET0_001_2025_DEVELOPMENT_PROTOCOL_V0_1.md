# L2R-OVERLAY-ETF-CME-PRET0-001 — 2025 DEVELOPMENT PROTOCOL V0.1

Date: 2026-09-30
Status: **FROZEN BEFORE ANY COMBINED DIRECTIONAL OUTCOME ACCESS UNDER THIS LAB_ID**

## 1. Identity and purpose

LAB_ID: `L2R-OVERLAY-ETF-CME-PRET0-001`

Parents:
- `L2-RESILIENCY-001` — independent 2025 mechanism validation PASS.
- `ETF-CME-INSTFLOW-001` — existing Tier-2 / fragile parent.

Predecessor:
- `L2R-OVERLAY-ETF-CME-001` — closed as `DEVELOPMENT_OVERLAY_INSUFFICIENT_SAMPLE_OR_SOURCE`.
- The predecessor produced **0 directional residual observations** because its first-at/after-T0 midpoint gate failed before directional outcome adjudication.
- This successor is a materially new identity, not a rescue rerun of the predecessor.

Purpose:
Test whether the already-validated Hyperliquid L2 replenishment state contains incremental entry-timing / adverse-selection information at the immutable ETF-CME weekly entry timestamp using a strictly causal **pre-T0 reference state**.

This study does not claim standalone L2 monetization. Standard-fee taker and maker children remain closed.

## 2. Evidence status and boundary

Calendar 2025 is already open for both parents. Every combined 2025 result here is:
**POST-PARENT DEVELOPMENT EVIDENCE ONLY**.

It cannot independently validate or promote this overlay or either parent.

Calendar 2026 remains CLOSED.

No 2026 market data, outcome, return or PnL may be accessed by this LAB_ID.

## 3. Immutable parent identities

ETF-CME parent:
- GitHub Actions run: `34815006815`
- artifact ID: `10335473231`
- artifact ZIP SHA256: `40bd341c300532e5b67127a098c82ecf2f41e1cc4a3ce646ac824b27529f9bd1`
- required member: `oos_2025_observations.csv`
- expected rows: 50
- immutable T0: parent entry date 00:00:00 UTC
- immutable parent direction: `position` (+1 / -1 / 0)

L2 parent:
- canonical 2025 BTC Hyperliquid corpus objects: 8,400
- canonical compressed bytes: 8,975,275,014
- canonical manifest SHA256: `767e75594864344c75dd2669ec4fad8c738710c218322b11fd43a83077ef17c3`
- preserve SOURCE_CLOCK_NORMALIZATION_AMENDMENT_V0.1B
- preserve sweep definition and top-5 PRE_DEPTH5
- preserve WEAK threshold: RR < 1.0
- preserve six cells:
  - R1 -> Y5
  - R1 -> Y15
  - R1 -> Y60
  - R5 -> Y15
  - R5 -> Y60
  - R15 -> Y60
- ASK-consumed direction = +1
- BID-consumed direction = -1

No cell, side, horizon or threshold may be selected using this successor's outcome.

## 4. Active weak state at T0

For each frozen cell, an event is `ACTIVE_WEAK_AT_T0` only if all are true:

1. event exists in the same canonical continuous source segment;
2. exact R target is resolved by first accepted normalized state at/after R within the unchanged 1,100 ms horizon-lateness rule;
3. RR_R < 1.0;
4. accepted R observation timestamp <= T0;
5. exact Y target timestamp > T0.

If several events qualify, select the event with latest accepted R observation timestamp; tie-break by later sweep event timestamp. No outcome-based tie break.

Relative to immutable ETF direction:
- `ALIGNED`: selected L2 direction == parent direction.
- `OPPOSED`: selected L2 direction == -parent direction.
- `NO_ACTIVE_WEAK`: no qualifying event.
- `SOURCE_GATED`: required causal source is unavailable.

## 5. New causal pre-T0 reference rule

For every non-zero ETF parent row:

`MID_PRET0` = midpoint from the **last accepted normalized Hyperliquid state at-or-before exact T0**, subject to all of:

- same canonical continuous source segment;
- accepted envelope timestamp <= T0;
- staleness = T0 - accepted envelope timestamp;
- staleness <= **1,100 ms**;
- no interpolation;
- no future/after-T0 state;
- no fallback to selected event R state;
- no widening after outcomes.

The 1,100 ms tolerance is intentionally unchanged from the predecessor's pre-frozen timing tolerance. Only the causal orientation changes from first-at/after to last-at-or-before.

Exact equality at T0 is allowed and has staleness 0.

If no qualifying state exists, that row is source-gated.

## 6. Development outcome

For ALIGNED or OPPOSED observations only:

- `MID_PRET0` = frozen causal reference above.
- `MID_Y` = first accepted normalized midpoint at/after selected event's exact Y target, within unchanged 1,100 ms lateness and same segment.

Parent-direction residual:

`RESIDUAL_BPS = parent_position * 10,000 * (MID_Y / MID_PRET0 - 1)`

For OPPOSED only:

`DELAY_BENEFIT_BPS = -RESIDUAL_BPS`

This is a reference-price timing diagnostic, not executable fill/PnL.

ETF seven-day parent PnL is not used to construct, filter or select the overlay.

## 7. Frozen development gate

Source/sample viability:
1. at least 40 non-zero parent T0 rows source-evaluable globally;
2. each reported cell requires >=8 ALIGNED and >=8 OPPOSED observations.

Per cell:
`SEPARATION_BPS = mean(RESIDUAL_BPS | ALIGNED) - mean(RESIDUAL_BPS | OPPOSED)`

Panel diagnostics:
- equal-weight mean separation across all six frozen cells;
- positive-cell count;
- positive-by-R-family;
- equal-weight mean OPPOSED delay benefit.

`DEVELOPMENT_OVERLAY_SIGNAL_SUPPORTED` only if all are true:
1. global source/sample viability passes;
2. six-cell equal-weight mean separation > 0;
3. >=4/6 cell separations > 0;
4. R1, R5 and R15 each have >=1 positive cell;
5. equal-weight mean OPPOSED delay benefit > 0.

With valid source/sample but failed support gates:
`DEVELOPMENT_OVERLAY_NO_SUPPORT`.

If source/sample fails:
`DEVELOPMENT_OVERLAY_INSUFFICIENT_SAMPLE_OR_SOURCE`.

No post-result rescue under this LAB_ID.

## 8. Implementation and execution authority

Before any real 2025 combined directional outcome is opened under this LAB_ID:
- runner bytes must be committed;
- synthetic/network-free QA must PASS;
- exact Git blob/SHA256 identities must be frozen in an implementation lock;
- the eventual one-shot must verify the immutable parent artifact and L2 manifest identities before outcome evaluation.

The QA stage may use only synthetic states. It must not access the 2025 raw corpus, ETF outcome artifact, network market data, or 2026.

## 9. Firewalls

Prohibited:
- 2026 access;
- widening the 1,100 ms pre-T0 staleness rule;
- switching from pre-T0 to after-T0 inside this LAB_ID;
- using event R as fallback reference;
- selecting a best cell;
- changing RR threshold;
- changing parent direction or horizon;
- using ETF weekly PnL to design/filter the overlay;
- venue switch;
- live trading;
- orders;
- wallet access;
- exchange mutation;
- leverage deployment;
- merge to main;
- post-outcome tuning/rescue.

A valid terminal 2025 result remains development-only. Any independent confirmation requires a separately frozen future prospective boundary.
