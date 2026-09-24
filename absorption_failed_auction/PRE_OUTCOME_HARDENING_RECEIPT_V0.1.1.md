# ABSORPTION-FAILED-AUCTION-001 — PRE-OUTCOME HARDENING RECEIPT

Date: 2026-09-24  
State: FROZEN_OUTCOME_BLIND  
Protocol authority: V0.1.1

## What changed before any economic outcome opening

The preliminary V0.1 design was audited while the parent
TV-FOOTPRINT-CALIBRATION-001 was still collecting and before any future-return
outcome for this lab was opened.

V0.1.1 hardens:

- rolling baseline 288 -> 2,016 prior valid forward bars;
- extreme flow q90 -> q95 of abs canonical aggressor delta percentage;
- adds q75 canonical base-volume participation requirement;
- path thresholds q30/q70 -> q25/q75;
- low displacement q30 -> q25;
- adds >=99% transport and R60 coverage requirements;
- adds internal POC/VA/imbalance structural invariants;
- adds a 60-minute event cooldown;
- requires symmetric evidence from both FAILED_AUCTION reversal and
  EFFICIENT_ACCEPTANCE continuation;
- bars before parent PASS_STRONG may seed baseline only and can never be events.

## Contamination statement

A small number of live telemetry receipts had been inspected only to verify
transport operation. No future price outcomes for this lab were opened, and no
observed receipt feature values were used to select the V0.1.1 quantiles,
baseline length, event rules, outcome horizon, sample minimums or verdict gate.

## Authority boundary

Economic outcomes remain CLOSED until the parent sensor reaches PASS_STRONG.
PASS_LIMITED cannot open this lab.

No live-trading authority is created.
