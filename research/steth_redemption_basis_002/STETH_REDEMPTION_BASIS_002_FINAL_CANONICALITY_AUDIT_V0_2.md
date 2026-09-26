# STETH-REDEMPTION-BASIS-002 — FINAL CANONICALITY AUDIT V0.2

Date: 2026-09-26  
Branch: `steth-redemption-basis-002-final-audit-v0.2`  
Parent closeout: `steth-redemption-basis-002-discovery-closeout-v0.1`

## FINAL SCIENTIFIC VERDICT

**DISCOVERY_INSUFFICIENT_SAMPLE / NO_PROMOTION / V0.1 CLOSED**

This audit does not rerun economic outcomes and does not alter any frozen scientific rule.

## WHY THIS AUDIT WAS REQUIRED

The frozen document `STETH_REDEMPTION_BASIS_002_PARALLEL_RETRY_CANONICAL_PRECEDENCE_V0_1.md` prospectively assigned canonical precedence to run **35393537717** (V0.1.1 transport retry), provided that run reached a scientifically valid terminal classification.

The later closeout document cited run **35398364376** as the canonical Discovery execution.

That lineage mismatch required adjudication before treating the closeout as fully clean.

## CANONICAL PRECEDENCE CHECK

### Run 35393537717 — prospectively preferred run

Workflow: `STETH Redemption Basis 002 — Discovery V0.1.1 Transport Retry`  
Head: `b4c4802cd7a99d27d4eee59956d6976a3a0817dd`  
Conclusion: **success**  
Artifact: `10569640734`  
Artifact digest: `sha256:5cf5d34a40089cc01c289dc37ea3c7f86087cd1e8732206fdcb9761fd574fc10`

Scientific result printed by the completed workflow:
- classification: **DISCOVERY_INSUFFICIENT_SAMPLE**
- signals: **2**
- completed redemptions: **2**
- operational wait failures: **0**
- right-censored positions: **0**
- mean base net ETH: **0.000173072406161847**
- median base net ETH: **0.000173072406161847**
- positive rate: **0.5**
- bootstrap lower statistic: **0.00017307240616184702**
- stress mean net ETH: **-0.02709919710712846**

The workflow explicitly verified:
- exact source receipt binding;
- frozen protocol blob identity;
- frozen implementation-freeze blob identity;
- transport-only remediation identity;
- no 2025/2026 access;
- no live trading;
- no wallet access;
- no orders;
- no exchange mutation;
- no leverage deployment;
- no main merge;
- no market-direction return test.

Therefore run **35393537717 reached a scientifically valid terminal classification** and, by the prospectively frozen precedence rule, is the authoritative canonical Discovery run.

## CORROBORATING RUNS

Run **35394498416** (V0.1A) completed successfully and independently printed the same scientific summary:
- 2 signals;
- 2 completed redemptions;
- classification `DISCOVERY_INSUFFICIENT_SAMPLE`;
- identical base/stress diagnostics.

Run **35398364376** (later V0.1 workflow) also completed successfully and printed the same scientific summary:
- 2 signals;
- 2 completed redemptions;
- classification `DISCOVERY_INSUFFICIENT_SAMPLE`;
- identical base/stress diagnostics.

These later runs are corroborating executions. They are not needed to select the scientific result and do not change the prospectively frozen precedence.

## SAMPLE GATE

Frozen requirement:
- at least **30 completed non-overlapping hypothetical redemptions**.

Canonical observed result:
- **2 completed redemptions**.

Mechanical sample-gate result:

**2 < 30**

Therefore expectancy, bootstrap, year breadth, concentration and stress diagnostics cannot promote the MVE even where individually positive.

In particular, the tiny positive base mean and median are diagnostics only. The stress mean is negative, but because the sample gate fails first, V0.1 remains classified `DISCOVERY_INSUFFICIENT_SAMPLE`, not `DISCOVERY_NO_REDEMPTION_EDGE`.

## LINEAGE CORRECTION

The scientific conclusion in `STETH_REDEMPTION_BASIS_002_DISCOVERY_CLOSEOUT_V0_1.md` remains correct.

The only correction made by this audit is canonical-run attribution:

- authoritative Discovery run: **35393537717**
- authoritative artifact: **10569640734**
- authoritative artifact digest: **sha256:5cf5d34a40089cc01c289dc37ea3c7f86087cd1e8732206fdcb9761fd574fc10**

Run 35398364376 remains corroborating evidence, not the precedence-selected canonical run.

## FINAL DISPOSITION

For `STETH-REDEMPTION-BASIS-002 / V0.1`:

- SOURCE_DATA_PASS: YES
- DISCOVERY_INSUFFICIENT_SAMPLE: YES
- DISCOVERY_NO_REDEMPTION_EDGE: NOT ADJUDICATED
- DISCOVERY PASS: NO
- REPLICATION ELIGIBLE: NO
- PROMOTION: NO
- SHADOW: NO
- MICRO-LIVE: NO
- 2025/2026: LOCKED
- RESCUE OF V0.1: FORBIDDEN
- EXACT V0.1 LINEAGE: CLOSED

Any successor that changes snapshot frequency, threshold, notional, venue, LST, queue horizon, period, cost model or signal construction must be a new prospectively frozen LAB_ID and may not be described as a rescue of STETH-002 V0.1.
