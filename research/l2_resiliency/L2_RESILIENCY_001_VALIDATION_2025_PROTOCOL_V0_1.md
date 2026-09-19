# L2-RESILIENCY-001 — INDEPENDENT 2025 VALIDATION / HOLDOUT PROTOCOL V0.1

Status: FROZEN BEFORE ANY 2025 SOURCE OR OUTCOME ACCESS

## Purpose
Independently validate the exact L2 replenishment/resilience mechanism that survived the frozen 2024 Discovery. No rule, threshold, horizon, side definition, normalization rule or inference method may be retuned from 2024.

## Holdout period
- 2025-01-01 00:00:00 UTC through 2025-12-31 23:59:59.999... UTC only.
- Full calendar-year holdout; no subperiod selection.
- 2026 remains FORBIDDEN.

## Canonical source
- Hyperliquid official requester-pays historical archive only.
- Bucket/key family: hyperliquid-archive / market_data/YYYYMMDD/H/l2Book/BTC.lz4.
- BTC only.
- Exact raw .lz4 bytes preserved locally with SHA256 + MD5/ETag binding.
- Missing official hours are immutable gaps; no interpolation, reconstruction, alternate vendor or source substitution.

## Source viability gate
- Expected 2025 hourly key universe: 365 * 24 = 8,760 keys.
- At least 95.0% of expected hourly keys must be PRESENT.
- Every PRESENT object must pass byte binding and the frozen corrected source/schema rules.
- If hourly coverage <95.0%, classification is VALIDATION_BLOCKED_SOURCE_COVERAGE, not a scientific failure.
- Present-source continuity is segmented at every missing-hour boundary.

## Frozen normalization
- top-level envelope time = archive availability/order clock.
- raw.data.time = payload snapshot clock.
- payload later than envelope = fail closed.
- envelope time must be non-decreasing inside each contiguous PRESENT segment.
- payload rewind below last accepted payload time = STALE_LATE_PAYLOAD, preserved but quarantined from state continuity.
- equal payload timestamps preserved in envelope order.

## Frozen sweep rule
- ASK consumed: post best ask > pre best ask; prior-best ask absent post-snapshot; bid not simultaneously adverse.
- BID consumed: post best bid < pre best bid; prior-best bid absent post-snapshot; ask not simultaneously adverse.
- both sides adverse = AMBIGUOUS_BOTH_SIDES and excluded.
- event anchor = post-transition envelope time.

## Frozen timing rule
- Horizons: +1s, +5s, +15s, +60s.
- For each horizon select first accepted normalized state at or after anchor+horizon.
- Maximum lateness 1,100 ms.
- No interpolation.
- No cross-segment lookup.

## Frozen replenishment
- PRE_DEPTH5 = immediately pre-sweep same-side displayed top-5 depth.
- RR_R = same-side top-5 depth at R / PRE_DEPTH5.
- WEAK = RR < 1.0.
- STRONG = RR >= 1.0.
- PRE_DEPTH5 <=0 => undefined and excluded.

## Frozen causal cells
- R1 -> Y5
- R1 -> Y15
- R1 -> Y60
- R5 -> Y15
- R5 -> Y60
- R15 -> Y60

## Frozen response
- ASK-consumed direction = +1; BID-consumed direction = -1.
- DIRECTIONAL_RESPONSE_BPS = direction * 10,000 * (MID_Y / MID_R - 1).
- Positive means continuation after the replenishment observation; negative means reversal.

## Frozen inference
- UTC-day clustered daily contrasts.
- For each day/cell: mean(response | WEAK) - mean(response | STRONG).
- Cell point estimate = unweighted mean of eligible daily contrasts.
- Global daily contrast = unweighted mean of available six cell daily contrasts.
- Global effect = unweighted mean of eligible global daily contrasts.
- 95% percentile bootstrap on UTC days, 10,000 resamples, deterministic seed 20260919.

## Holdout sample viability
- At least 300 eligible UTC days are required for the global statistic.
- Each of the six causal cells must have at least 300 eligible UTC days with both WEAK and STRONG observations.
- If this is not met after a source-valid year, classification is VALIDATION_INSUFFICIENT_SAMPLE, not a mechanism failure.

## Frozen validation PASS gate
VALIDATION_PASS requires ALL:
1. GLOBAL_EFFECT > 0;
2. global bootstrap 95% CI lower bound > 0;
3. at least 4 of 6 cell point estimates > 0;
4. each replenishment horizon R={1s,5s,15s} has at least one positive causal-cell point estimate;
5. source viability and holdout sample viability gates pass.

Failure of items 1-4 with valid source/sample => VALIDATION_FAIL_NO_PROMOTION.
No side/month/subperiod rescue, threshold changes, winsorization, RR clipping, timing widening or alternative inference is allowed after outcome access.

## Interpretation
- VALIDATION_PASS establishes independent temporal replication of the information-transmission mechanism.
- It does NOT establish economically tradable edge.
- PnL, fees, slippage, latency/fill simulation, Sharpe, leverage and position sizing remain prohibited in this holdout.

## Next routing
Only after VALIDATION_PASS may a separate prospectively frozen economic/execution feasibility gate be designed. 2026 remains forbidden.