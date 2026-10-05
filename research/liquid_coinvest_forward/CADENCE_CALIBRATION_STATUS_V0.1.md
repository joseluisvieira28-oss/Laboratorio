# LIQUID CO-INVEST FORWARD — CADENCE CALIBRATION STATUS V0.1

Date: 2026-10-05
Branch: liquid-coinvest-forward-v0.1-prereg-2026-10-05
Freeze commit: 2229026ef30d41d9556e8b2f6e71188b2aa12df0
Status: ACTIVE / PRE-OUTCOME / SOURCE-CADENCE CALIBRATION

## Durable observations

Two post-freeze receipts are recorded:

1. 2026-10-05T10:38:02Z
2. 2026-10-05T10:48:17Z

Universe remains exactly BTC / ETH / SOL.

## Source timestamp evidence

A source positioning version at approximately 2026-10-05T09:55:48Z was observed before/at the start of calibration.

A later source version exists at approximately 2026-10-05T10:26:59.67Z.

Observed version-to-version spacing:
- about 1,871.35 seconds
- about 31.189 minutes

Important: the new version did not become visible synchronously across all symbols in our reads.

At 10:38:02Z:
- BTC: source_created_at 10:26:59.675Z
- ETH: source_created_at 09:55:48.328Z
- SOL: source_created_at 10:26:59.677Z

At 10:48:17Z:
- BTC: still 10:26:59.675Z — duplicate proprietary snapshot
- ETH: advanced to 10:26:59.677Z
- SOL: still 10:26:59.677Z — duplicate proprietary snapshot

This demonstrates asynchronous visibility / cache propagation across symbols even when source version timestamps cluster tightly.

## Scientific consequence

We do NOT freeze a freshness acceptance threshold yet.

One observed version interval is insufficient to assert a stable refresh cadence. A minimum of additional independent source advances is required before freezing a freshness rule.

Until then:
- all captures remain cadence-calibration observations;
- duplicate proprietary snapshots are not counted as new information events;
- price/OI changes on top of an unchanged proprietary positioning snapshot do not create a new positioning event;
- no predictive outcome-conditioned analysis is allowed.

## Earliest legitimate outcome times

For the first durable observation at 10:38:02Z:
- +1h outcome earliest eligible at 11:38:02Z
- +4h outcome earliest eligible at 14:38:02Z

For the second durable observation at 10:48:17Z:
- +1h outcome earliest eligible at 11:48:17Z
- +4h outcome earliest eligible at 14:48:17Z

No outcome may be opened early.

## Current source-gate verdict

- Historical proprietary positioning backtest: BLOCKED
- Prospective source capture: PASS
- Source freshness semantics: CALIBRATING
- LIQUIDATION-FLOW-FWD-001-LIQUID-V0.1: FORWARD COLLECTING
- COHORT-DIVERGENCE-FWD-001-LIQUID-V0.1: FORWARD COLLECTING
- Edge verdict: NOT YET LEGITIMATELY AVAILABLE
