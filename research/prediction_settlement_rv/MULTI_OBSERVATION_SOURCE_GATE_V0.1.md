# PREDICTION-SETTLEMENT-RV-001 — MULTI-OBSERVATION SOURCE SCHEDULE GATE V0.1

Date: 2026-09-27
Status: FROZEN_PRE_RUN / SOURCE_ONLY / OUTCOME_BLIND
Lab: PREDICTION-SETTLEMENT-RV-001

## Objective

Stress the prospective public-source collector across repeated observations before any economic value is opened.

This gate measures collection reliability, synchronization, schema continuity and stale-detection capability only.

## Eligibility

At run start:
- use the frozen MATCHED_SETTLEMENT_BASIS_PAIR matcher;
- choose the earliest resolution with all matched pairs whose expiry is between T+15 and T+90 minutes;
- freeze the complete matched-pair population at cycle 0;
- do not add/remove strikes later in the run based on quote/depth state.

If no eligible population exists:
WAITING_ELIGIBLE_EXPIRY.

## Schedule

Exactly 5 cycles.

Target cycle offsets from the run's frozen schedule epoch:
- 0 seconds
- 60 seconds
- 120 seconds
- 180 seconds
- 240 seconds

Cycle-start lateness tolerance:
<= 10 seconds from its target.

No early cycle may be delayed deliberately after seeing source values.

## Per-pair batch

At every cycle, for every frozen matched pair:
- Polymarket YES book
- Polymarket NO book
- Kalshi public orderbook
- Coinbase Exchange USDT-USD ticker

are requested concurrently.

Frozen per-pair transport gates:
- midpoint skew <= 2.0 seconds;
- each request elapsed <= 5.0 seconds;
- all required schemas valid;
- HTTP success on all four legs.

## Coverage

Expected pair-observations:
frozen_pair_count × 5.

Successful pair-observation:
all per-pair transport gates pass.

Frozen coverage requirement:
successful_pair_observations / expected_pair_observations >= 0.99.

No missing observation may be imputed or reconstructed.

## Stale-detection capability

For every pair/leg across cycles:
- preserve raw SHA256;
- preserve request timing;
- record whether the raw hash changed from the previous cycle;
- record native/provider timestamp presence where the source exposes it.

Repeated raw hashes are a diagnostic, not automatically a failure because a legitimate book may remain unchanged.

A future economic protocol must treat an observation as invalid if the source is provably stale under a separately frozen provider-specific rule.

## Raw values

All raw payloads are preserved in the artifact.

Quote/depth/basis numerical values:
- may exist inside sealed raw files;
- must not be printed;
- must not be summarized;
- must not be ranked;
- must not be used for any economic calculation in this gate.

## PASS

SOURCE_SCHEDULE_GATE_PASS requires:
- >=1 frozen matched pair;
- all 5 cycles executed;
- every cycle starts inside the frozen lateness tolerance;
- coverage >=99%;
- zero future-nearest joins;
- zero silent imputation;
- quote-value firewall intact.

Even on PASS:
SOURCE_DATA_PASS remains false until final fee-byte provenance and stale-guard readiness are separately reconciled.

## Forbidden

No matured outcomes.
No PnL.
No complementary-package cost.
No arbitrage test.
No expected return.
No best strike/time.
No orders/authentication/capital.
No exchange mutation.
No main merge.
