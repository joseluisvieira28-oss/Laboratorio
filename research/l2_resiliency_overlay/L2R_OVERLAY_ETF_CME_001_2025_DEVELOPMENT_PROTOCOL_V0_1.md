# L2R-OVERLAY-ETF-CME-001 — 2025 DEVELOPMENT PROTOCOL V0.1

Date: 2026-09-26
Status: **FROZEN BEFORE COMBINED L2 × ETF-CME OUTCOME ACCESS**

## 1. Identity and purpose

LAB_ID: `L2R-OVERLAY-ETF-CME-001`

Parents:
- `L2-RESILIENCY-001` — 2025 independent mechanism validation PASS.
- `ETF-CME-INSTFLOW-001` — Tier 2 promoted candidate / fragile.

Purpose:
Test whether the already-validated Hyperliquid L2 replenishment state contains **incremental entry-timing / adverse-selection information** at the immutable ETF-CME weekly entry timestamp.

This study does **not** claim that the L2 signal can pay a standalone round trip. The standalone standard-fee taker and maker children are already closed.

This study does **not** alter the ETF-CME signal, direction, seven-day horizon, cost assumptions, position sizing or parent classification.

## 2. Evidence status

Calendar 2025 is already open for both parent evidence sets, therefore every combined 2025 result in this study is:

**POST-PARENT DEVELOPMENT EVIDENCE ONLY**

It is not independent OOS evidence for this new overlay identity and cannot promote this overlay or either parent.

Calendar 2026 remains CLOSED.

## 3. Immutable ETF-CME parent input

Use only the immutable OOS artifact:
- GitHub Actions run: `34815006815`
- artifact ID: `10335473231`
- artifact ZIP SHA256: `40bd341c300532e5b67127a098c82ecf2f41e1cc4a3ce646ac824b27529f9bd1`
- required file: `oos_2025_observations.csv`

The overlay runner must consume the parent observation ledger exactly as produced.

For every parent row:
- `T0 = entry date at 00:00:00 UTC`
- parent direction = immutable `position` (+1 / -1 / 0)
- parent exit, forward return, gross, base_net and stress_net are **not used to construct the overlay state**.

Rows with parent position 0 are reported but do not create a directional overlay observation.

Expected parent ledger: 50 evaluable weeks, first entry 2025-01-15, last entry 2025-12-24, last exit 2025-12-31.

## 4. Immutable L2 parent input

Use only the already-open canonical Hyperliquid BTC 2025 corpus:
- 8,400 official hourly objects
- 8,975,275,014 compressed bytes
- canonical manifest SHA256:
  `767e75594864344c75dd2669ec4fad8c738710c218322b11fd43a83077ef17c3`

Retain exactly:
- SOURCE_CLOCK_NORMALIZATION_AMENDMENT_V0.1B
- same sweep definition
- same top-5 PRE_DEPTH5
- same RR threshold: WEAK iff RR < 1.0
- same maximum horizon lateness: 1,100 ms
- same six cells:
  - R1 -> Y5
  - R1 -> Y15
  - R1 -> Y60
  - R5 -> Y15
  - R5 -> Y60
  - R15 -> Y60
- ASK-consumed direction = +1
- BID-consumed direction = -1

No L2 threshold, side, R, Y or cell is selected from the combined result.

## 5. Causal overlay state at T0

Evaluate each of the six cells independently.

For a given cell `R -> Y`, an L2 event is **ACTIVE_WEAK_AT_T0** only when all are true:

1. the sweep event exists in the same canonical continuous source segment;
2. its exact R target is resolved by the first accepted normalized state at/after R within 1,100 ms;
3. RR_R < 1.0;
4. the actual accepted R observation timestamp is <= T0;
5. the event's exact Y target timestamp is > T0.

Condition 5 uses the target clock only; the future Y state/value is not inspected when classifying the state.

If several ACTIVE_WEAK_AT_T0 events exist for one cell, select the event with the **latest accepted R observation timestamp**. If equal, use the later sweep event timestamp. No outcome-based tie break is allowed.

Classification relative to the immutable ETF parent direction:
- `ALIGNED`: selected L2 sweep direction == parent direction.
- `OPPOSED`: selected L2 sweep direction == -parent direction.
- `NO_ACTIVE_WEAK`: no eligible active weak event.
- `SOURCE_GATED`: T0 or required causal history is unavailable because of an immutable source gap/segment boundary.

The classification is complete before reading the selected event's Y outcome.

## 6. Development outcome

For ALIGNED or OPPOSED observations only:

- sample `MID_T0` = first accepted normalized Hyperliquid midpoint at/after exact T0, maximum lateness 1,100 ms, same segment;
- sample `MID_Y` = first accepted normalized midpoint at/after the selected event's exact Y target, maximum lateness 1,100 ms, same segment.

Parent-direction residual movement:

`RESIDUAL_BPS = parent_position * 10,000 * (MID_Y / MID_T0 - 1)`

Interpretation:
- positive RESIDUAL_BPS = price moved in the ETF parent direction after T0;
- negative = immediate adverse movement relative to parent direction.

For OPPOSED only, descriptive potential delay benefit:

`DELAY_BENEFIT_BPS = -RESIDUAL_BPS`

This is a **reference-price timing diagnostic**, not executable PnL. It does not assume a Binance fill, queue fill, market order, fee rebate or cross-venue arbitrage.

No seven-day parent return/PnL is optimized or filtered in V0.1.

## 7. Frozen development gate

This gate decides only whether a prospective overlay is worth further study.

Sample viability:
1. At least 40 parent non-zero-position T0 rows must be source-evaluable globally.
2. For every reported cell, at least 8 ALIGNED and 8 OPPOSED observations are required. A cell below this threshold is `INSUFFICIENT_CELL_SAMPLE`; it cannot count positive.

Per-cell separation:

`SEPARATION_BPS = mean(RESIDUAL_BPS | ALIGNED) - mean(RESIDUAL_BPS | OPPOSED)`

Panel diagnostics:
- equal-weight mean separation across the six frozen cells;
- positive-cell count;
- positive-by-R-family;
- equal-weight mean OPPOSED delay benefit.

Classification:

`DEVELOPMENT_OVERLAY_SIGNAL_SUPPORTED` only if all are true:
1. global source/sample viability passes;
2. equal-weight six-cell mean separation > 0;
3. at least 4/6 cell separations > 0;
4. R1, R5 and R15 each have at least one positive cell;
5. equal-weight mean OPPOSED delay benefit > 0.

Otherwise, with valid source/sample:
`DEVELOPMENT_OVERLAY_NO_SUPPORT`.

If source/sample gates fail:
`DEVELOPMENT_OVERLAY_INSUFFICIENT_SAMPLE_OR_SOURCE`.

No post-result rescue.

## 8. Required reporting

Report for all six cells:
- parent rows
- evaluable rows
- ALIGNED count
- OPPOSED count
- NO_ACTIVE_WEAK count
- SOURCE_GATED count
- aligned mean residual bps
- opposed mean residual bps
- separation bps
- opposed mean delay benefit bps

Also report:
- exact parent artifact SHA
- exact L2 manifest SHA
- all source segment/gap diagnostics
- 2026 access flag
- no-network flag for market-data acquisition during the diagnostic
- no orders / exchange mutation / live trading / main merge.

## 9. Prohibited interpretations and rescues

Do not:
- choose the best cell;
- choose a different R/Y after result;
- change RR threshold;
- change parent direction or horizon;
- skip ETF trades based on 2025 combined results;
- claim executable PnL from Hyperliquid midpoint movement;
- claim independent validation;
- use parent seven-day PnL to design the overlay after seeing combined results;
- open 2026;
- switch venue inside this LAB_ID;
- merge to main;
- deploy or place orders.

If V0.1 supports the overlay, the next step is a **new prospective execution-policy freeze** (for example exact delay/entry venue mechanics) before any forward outcome is opened.
