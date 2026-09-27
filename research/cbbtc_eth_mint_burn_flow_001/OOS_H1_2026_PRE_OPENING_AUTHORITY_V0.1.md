# CBBTC-ETH-MINT-BURN-FLOW-001 — OOS H1-2026 PRE-OPENING AUTHORITY V0.1

Frozen: 2026-09-27
Status: PREPARED / 2026 STILL CLOSED
Parent Discovery: FLOW_DISCOVERY_PASS
Parent run: #36342357118
Scope: OOS/HOLDOUT FREEZE ONLY — NO 2026 ACCESS BY THIS COMMIT

## Parent evidence

The frozen 2025 Discovery passed all required gates:
- SOURCE_PASS
- PREDICTOR_FLOW_CENSUS_PASS
- FLOW_STATE_CALIBRATION_PASS
- FLOW_PREDICTOR_SAMPLE_PASS
- FLOW_DISCOVERY_PASS

Discovery outcome sample:
- 29 eligible 24h events
- 21 NEGATIVE_EXTREME
- 8 POSITIVE_EXTREME
- pooled mean signed 24h return = 0.006504078624404028...
- NEGATIVE_EXTREME mean signed 24h return = 0.007713960811419364...
- POSITIVE_EXTREME mean signed 24h return = 0.003328137883488772...
- bootstrap 95% CI = [0.001459391995413690..., 0.011639574516276132...]

These values are evidence only and MUST NOT be used to retune any OOS rule.

## OOS calendar

Protected holdout tranche:
2026-01-01 through 2026-06-30 inclusive.

Rationale:
- natural complete calendar half-year;
- selected before any 2026 predictor or BTC outcome is opened;
- leaves 2026-07-01 onward untouched for later forward evidence if H1 survives.

No extension beyond 2026-06-30 is allowed to rescue insufficient or failed H1 evidence.

## Frozen predictor

Exactly unchanged:
f_t = (mint_t - burn_t) / prior_supply_t

Ethereum mainnet cbBTC contract:
0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf

Mint:
ERC-20 Transfer with from == zero address.

Burn:
ERC-20 Transfer with to == zero address.

No address clustering, bridge substitution, ordinary-transfer substitution, alternate network, or Coinbase-wallet heuristic.

## Frozen thresholds

Reuse the exact Discovery calibration thresholds. Do NOT recalibrate on 2026.

q10 exact rational:
- numerator = -18316281339
- denominator = 1601692985627
- ppb_trunc = -11435576
- source_day = 2025-02-07

q90 exact rational:
- numerator = 35266522085
- denominator = 1057456895899
- ppb_trunc = 33350316
- source_day = 2024-11-01

States:
- NEGATIVE_EXTREME iff f_t <= q10
- POSITIVE_EXTREME iff f_t >= q90
- NEUTRAL otherwise

## Transition rule

Unchanged transition-only de-clustering.

A holdout event occurs only when:
- current state is NEGATIVE_EXTREME and previous UTC day is not NEGATIVE_EXTREME; or
- current state is POSITIVE_EXTREME and previous UTC day is not POSITIVE_EXTREME.

For 2026-01-01, predecessor state is 2025-12-31 classified with the same frozen thresholds.

## Outcome-blind H1 sample gate

Before opening any 2026 BTC price:
- reconstruct complete predictor ledger for 2025-12-31 through 2026-06-30;
- preserve exact block provenance and supply reconciliation;
- classify 2026-01-01 through 2026-06-30;
- count transition events.

OOS_PREDICTOR_SAMPLE_PASS requires:
- all H1 calendar days present;
- valid prior supply every day;
- exact supply reconciliation;
- zero duplicate/decode/source errors;
- >=20 transition events total;
- >=6 NEGATIVE_EXTREME;
- >=6 POSITIVE_EXTREME.

If source/provenance fails:
OOS_SOURCE_BLOCKED.

If source passes but event minimum fails:
OOS_INSUFFICIENT_SAMPLE.

Neither state opens BTC price outcomes.
Do not widen tails, change de-clustering, extend beyond H1, or add another network to rescue sample size.

## Frozen OOS market outcome

Only OOS_PREDICTOR_SAMPLE_PASS may open 2026 BTC prices.

Source:
official Binance public historical BTCUSDT Spot 1d UTC archives from data.binance.vision, checksum-verified where checksum files exist.

Primary entry:
00:00 UTC of day t+1.

Primary exit:
00:00 UTC of day t+2.

Primary horizon:
24 hours.

Directional signing:
- POSITIVE_EXTREME: +raw BTC return
- NEGATIVE_EXTREME: -raw BTC return

To keep the complete primary outcome inside H1, only event days t <= 2026-06-28 are outcome-eligible.
2026-06-29 and 2026-06-30 remain predictor evidence only.

72h diagnostic may be computed only for t <= 2026-06-26 and cannot rescue the primary result.

## Frozen OOS statistical gate

Reuse the same statistical contract as Discovery:
- >=20 outcome-eligible events total;
- >=6 POSITIVE_EXTREME;
- >=6 NEGATIVE_EXTREME;
- pooled mean signed_return_24h;
- mean signed_return_24h for each tail;
- 10,000 deterministic event-row bootstrap resamples;
- bootstrap seed = 20260926;
- percentile 95% CI.

OOS_PASS requires ALL:
- pooled mean signed_return_24h > 0;
- bootstrap 95% lower bound > 0;
- POSITIVE_EXTREME mean signed return > 0;
- NEGATIVE_EXTREME mean signed return > 0.

Otherwise:
OOS_FAIL.

The 72h diagnostic cannot alter the primary verdict.

## Decision tree

- OOS_SOURCE_BLOCKED: source/provenance blocker, not NO_EDGE.
- OOS_INSUFFICIENT_SAMPLE: inconclusive H1 holdout; no cutoff extension/rescue.
- OOS_FAIL: exact CBBTC directional mechanism fails independent holdout and is not promoted.
- OOS_PASS: independent H1 holdout survives; H2-2026 remains unopened and separate promotion/forward authority is still required.

## Firewalls

This freeze authorizes NO data opening by itself.

Until a separate explicit OOS opening authorization is recorded:
- no 2026 Ethereum logs;
- no 2026 supply observations;
- no 2026 Binance price archive;
- no 2026 outcome;
- no PnL;
- no fees/slippage fitting;
- no position sizing;
- no live trading;
- no orders;
- no exchange/wallet mutation;
- no main merge.

Promotion credit from this pre-opening freeze = 0.
