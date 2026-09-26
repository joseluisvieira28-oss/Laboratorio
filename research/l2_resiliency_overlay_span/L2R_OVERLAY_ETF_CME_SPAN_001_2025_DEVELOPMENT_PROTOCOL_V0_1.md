# L2R-OVERLAY-ETF-CME-SPAN-001 — 2025 DEVELOPMENT PROTOCOL V0.1

Date: 2026-09-27
Status: **FROZEN BEFORE ANY SPAN DIRECTIONAL OUTCOME ACCESS**

## 1. Identity

LAB_ID: `L2R-OVERLAY-ETF-CME-SPAN-001`

This is a materially new successor to the closed:
`L2R-OVERLAY-ETF-CME-001`.

The predecessor closed as:
`DEVELOPMENT_OVERLAY_INSUFFICIENT_SAMPLE_OR_SOURCE`.

No ALIGNED/OPPOSED residual outcome was observed in the predecessor because its exact-T0 reference-price gate produced zero source-evaluable rows.

This successor therefore changes only the reference-price construction, under a new LAB_ID, before any span-directional outcome is opened.

## 2. Scientific question

At an immutable ETF-CME weekly entry T0, does a pre-existing Hyperliquid weak-replenishment event that is still causally active across T0 carry directionally compatible information with the ETF-CME parent direction?

This is a **cross-T0 state/response compatibility diagnostic**.

It is NOT:
- an executable ETF fill model;
- a standalone L2 strategy;
- a claim that Hyperliquid midpoint equals Binance/MEXC execution;
- independent OOS for the new identity;
- promotion evidence by itself.

## 3. Parent identities remain immutable

ETF-CME parent:
- exact immutable 2025 OOS artifact SHA256:
  `40bd341c300532e5b67127a098c82ecf2f41e1cc4a3ce646ac824b27529f9bd1`
- 50 rows expected
- immutable parent direction from `position`
- no modification of signal, threshold, entry calendar, seven-day horizon, cost model or parent classification

L2 parent:
- canonical 2025 manifest SHA256:
  `767e75594864344c75dd2669ec4fad8c738710c218322b11fd43a83077ef17c3`
- 8,400 official hourly objects
- same V0.1B source-clock normalization
- same sweep definition
- same RR threshold: WEAK iff RR < 1.0
- same six causal cells
- same 1,100 ms max lateness for R/Y sampling
- same ASK=+1 / BID=-1 direction convention

2026 remains CLOSED.

## 4. Frozen active-state selection

For each ETF parent non-zero-position row:
- `T0 = parent entry date 00:00:00 UTC`.

For each of the six cells `R -> Y`, an event is `ACTIVE_WEAK_AT_T0` iff all are true:

1. sweep exists in the same canonical contiguous source segment;
2. R resolves at first accepted normalized state at/after exact R target within 1,100 ms;
3. RR_R < 1.0;
4. accepted R observation timestamp <= T0;
5. exact Y target timestamp > T0.

Condition 5 uses only the target clock; future Y value is not read for selection.

If multiple events qualify:
- choose latest accepted R observation timestamp;
- tie break by later sweep event timestamp;
- no outcome-based tie break.

Classification:
- `ALIGNED` if selected L2 sweep direction == ETF parent direction;
- `OPPOSED` if selected L2 sweep direction == -ETF parent direction;
- `NO_ACTIVE_WEAK` if none;
- `SOURCE_GATED` only for immutable source-gap / unresolved R/Y timing failures.

## 5. New successor baseline

The predecessor's exact-T0 midpoint requirement is NOT reused.

For a selected event:
- baseline = the already-frozen accepted midpoint at that event's R observation;
- endpoint = the already-frozen accepted midpoint at its Y observation.

No new timestamp is interpolated or fitted.

Define:

`PARENT_SPAN_BPS = parent_position * 10,000 * (MID_Y / MID_R - 1)`

Interpretation:
- positive = R->Y movement was in ETF parent direction;
- negative = R->Y movement was against ETF parent direction.

This span may begin before T0 and end after T0. Therefore it is not described as post-entry PnL or executable timing improvement.

## 6. Source/sample feasibility known before directional outcomes

The closed predecessor exposed only source/sample routing, not directional residuals.

For 49 non-zero ETF rows, source-present selected-event counts inferable without any span return sign are:

- R1_Y5: 6
- R1_Y15: 22
- R1_Y60: 38
- R5_Y15: 10
- R5_Y60: 34
- R15_Y60: 26

This pre-outcome sample inventory is allowed only to freeze adequacy rules; it provides zero directional credit.

## 7. Frozen sample gate

A cell is `SAMPLE_VIABLE` only if:
- selected ALIGNED + OPPOSED observations >= 10;
- ALIGNED >= 3;
- OPPOSED >= 3.

Global sample viability requires:
1. at least 40 ETF non-zero rows with source-present T0 windows;
2. at least 4/6 SAMPLE_VIABLE cells;
3. each replenishment family R1, R5, R15 has at least one SAMPLE_VIABLE cell.

Cells failing sample viability are reported and receive no positive scientific credit.

No minimum is changed after outcome.

## 8. Frozen directional development gate

For each sample-viable cell:

`SEPARATION_BPS = mean(PARENT_SPAN_BPS | ALIGNED) - mean(PARENT_SPAN_BPS | OPPOSED)`

Panel statistics are equal-weight across SAMPLE_VIABLE cells.

`DEVELOPMENT_SPAN_SIGNAL_SUPPORTED` only if all are true:

1. global sample viability passes;
2. equal-weight mean separation > 0;
3. at least 4 cell separations > 0;
4. R1, R5 and R15 each have at least one positive viable cell;
5. equal-weight ALIGNED mean PARENT_SPAN_BPS > 0;
6. equal-weight OPPOSED mean PARENT_SPAN_BPS < 0.

Otherwise, with valid global sample:
`DEVELOPMENT_SPAN_NO_SUPPORT`.

If global sample/source viability fails:
`DEVELOPMENT_SPAN_INSUFFICIENT_SAMPLE_OR_SOURCE`.

No post-result rescue.

## 9. Required reporting

All six cells:
- parent non-zero rows;
- source-present rows;
- ALIGNED n;
- OPPOSED n;
- NO_ACTIVE_WEAK n;
- SOURCE_GATED n;
- aligned mean span bps;
- opposed mean span bps;
- separation bps;
- sample viability.

Panel:
- viable cell count;
- equal-weight separation;
- positive cell count;
- positive-by-R;
- equal-weight aligned mean;
- equal-weight opposed mean.

Also:
- exact parent artifact hashes;
- raw object/state traversal;
- source gaps;
- 2026=false;
- orders/live/exchange/main=false.

## 10. Prohibited interpretations/rescues

Do not:
- widen or modify 1,100ms R/Y lateness;
- choose the best cell;
- drop R1_Y5 because it is sample-thin and then pretend the remaining panel was always the original hypothesis;
- change >=10 / >=3+3 sample rules after result;
- change RR threshold;
- change parent direction/horizon;
- use parent seven-day PnL to design the overlay;
- reinterpret R->Y span as executable entry PnL;
- open 2026;
- merge to main;
- place orders or mutate an exchange.

## 11. Routing

If SUPPORTED:
freeze a new prospective execution-policy / forward-shadow specification before any protected outcome.

If NO_SUPPORT:
close this exact span identity; no cell rescue.

If INSUFFICIENT:
close or park as sample/source constrained; do not call NO_EDGE.
