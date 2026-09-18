# STETH-REDEMPTION-BASIS-002 — PARALLEL RETRY CANONICAL PRECEDENCE V0.1

Date: 2026-09-18
Status: FROZEN BEFORE ANY RETRY OUTCOME IS AVAILABLE

## Situation

Two transport-remediated Discovery retries exist concurrently:

1. Earlier retry:
   - workflow: STETH Redemption Basis 002 — Discovery V0.1.1 Transport Retry
   - run: 35393537717
   - head: b4c4802cd7a99d27d4eee59956d6976a3a0817dd
   - preflight: PASS
   - discovery: IN_PROGRESS at freeze time

2. Later retry:
   - workflow: STETH Redemption Basis 002 — Discovery V0.1A Retry
   - run: 35394498416
   - head: aef4f4f69a0c33cf493baa474d71716d434ca428
   - preflight: PASS
   - discovery: IN_PROGRESS at freeze time

Neither had a final artifact or scientific classification when this precedence rule was frozen.

## Canonical authority

The earlier legitimate transport-only retry, run 35393537717, is the canonical retry for scientific adjudication.

Run 35394498416 is redundant/superseded for scientific outcome selection.

It may be used only as a transport diagnostic if needed to explain infrastructure behavior.

## Anti-cherry-pick rule

Do not choose between the two runs based on:
- edge magnitude;
- PnL;
- sample count;
- pass/fail classification;
- any economic result.

If run 35393537717 reaches a scientifically valid terminal classification, that classification is authoritative.

If run 35393537717 terminates with TECHNICAL_OR_PROVENANCE_FAILURE, run 35394498416 may not automatically replace it as a scientific result. Its output may only diagnose whether the technical failure is transport-specific. A separate prospective authority would be required before using any later retry as the canonical scientific adjudication.

## Science unchanged

No economic rule, parameter, sample gate, period, venue, notional, cost, horizon or promotion rule is changed by this document.
