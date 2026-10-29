# EVENT FUTURES DIRECTION LAB V0.1

Status: SOURCE_GATE_REQUIRED / MODEL_NOT_FROZEN / ZERO OUTCOMES / NO LIVE.

This is an **offline, fail-closed simulator/verifier**, NOT an active MEXC collector, prediction model or trading bot. No real MEXC requests were made here. Uses read-only shadow semantics established by the V0.13 parent.

## Scope
- BTC/ETH; 10m/30m/60m; payout depends on direction and observed product/cycle.
- Rejects unregistered model+rule, unavailable product, future data, stale signal/payout join, non-positive forecast EV, overlapping same-model events and missing expiry index.
- Resolves WIN/LOSS/TIE using the first eligible captured public tick within 5s.
- Never counts a shadow hypothetical entry as an executed MEXC openPrice.
- Requires trustworthy external pre-outcome custody before any scientific outcomes may be opened.

## Tests
From repository root:
    python -m unittest discover -s research/mexc_event_direction_v01 -p 'test_*.py' -v

Only synthetic fixture tests; a PASS is not market evidence.

## Offline CLI
    python research/mexc_event_direction_v01/direction_shadow_v01.py --authority research/mexc_event_direction_v01/ACTIVATION_BLOCKED.json --decisions /path/decisions.jsonl --ticks /path/index_ticks.jsonl --output /path/shadow.json

The CLI is EXPECTED TO BLOCK by default because the included authority is SOURCE_GATE_REQUIRED, model inactive. Do not edit that file merely to make it pass: require an independently timestamp-anchored scientific freeze and source proof.

## Next work
1. Fresh read-only source and clock-health check, payouts/hash provenance and first public index tick for each asset.
2. Independent proof forecasts were recorded before expiry; no mutable post-outcome ledgers.
3. Only then design a distinct model and freeze source/features/train/probability calibration before observing targets.
4. Run a prospective shadow batch; use the existing V0.13 evaluator plus additional time-series robustness. No 2026-09 historical holdout.

**Research verdict: INSUFFICIENT_EVIDENCE, not NO_EDGE and not LIVE_GO.**
