# L2R-EXEC-PASSIVE-001 — 2025 OPTIMISTIC UPPER-BOUND CLOSEOUT V0.1

Date: 2026-09-26  
Status: **PASSIVE_STANDARD_BASE_UPPER_BOUND_FAIL — STANDARD-BASE PASSIVE CHILD CLOSED**  
Parent: `L2-RESILIENCY-001` remains **VALIDATION_PASS**.

## Evidence identity

Uploaded evidence bundle:
- file: `L2R_EXEC_PASSIVE_001_2025_UPPER_BOUND_EVIDENCE_V0_1.zip`
- SHA256: `ed36a1001d5c598896235257a811de98af44dc5eae4eb0a94c3c690a292590fe`
- size: 3,175 bytes
- implementation: V0.1.1
- source: already-open canonical 2025 corpus only
- 2026 access: false
- network: false
- orders/exchange mutation/live trading/main merge: false

## Frozen standard-base result

Hyperliquid base maker fee frozen pre-run: **1.5 bps per fill**.

The diagnostic deliberately assumed an unrealistically favorable passive execution upper bound:
- 100% passive fill probability;
- perfect touch fill on both entry and exit;
- no queue delay;
- no missed fills;
- no adverse selection;
- no extra latency;
- no market impact.

Even under that upper bound:

- equal-weight six-cell mean net = **-1.6696357652 bps/opportunity**;
- positive cells = **0/6**;
- positive R families = **0/3**;
- all three frozen support gates failed.

| Cell | WEAK N | Mid response bps | Optimistic maker gross bps | Net @ 1.5 bps/fill |
|---|---:|---:|---:|---:|
| R1_Y5 | 2,241,028 | +0.921271 | +1.102516 | -1.897484 |
| R1_Y15 | 2,302,354 | +1.243895 | +1.421994 | -1.578006 |
| R1_Y60 | 2,307,885 | +1.344251 | +1.520861 | -1.479139 |
| R5_Y15 | 1,630,311 | +1.052318 | +1.234643 | -1.765357 |
| R5_Y60 | 1,623,754 | +1.215508 | +1.396925 | -1.603075 |
| R15_Y60 | 1,400,753 | +1.116078 | +1.305245 | -1.694755 |

## Scientific / economic interpretation

This is an **execution-path failure**, not a failure of the parent microstructure mechanism.

The parent claim remains:
`L2-RESILIENCY-001 = 2025 INDEPENDENT VALIDATION PASS`.

The child claim is:
`L2R-EXEC-PASSIVE-001 STANDARD-BASE DIRECT MONETIZATION = CLOSED`.

Because the standard-base route fails even before queue/fill/adverse-selection realism, no standard-base queue/fill simulation is justified. Adding realism can only worsen this upper bound.

No post-outcome cell selection, horizon rescue, fee reduction, direction change, venue switch or threshold change is allowed under this exact child.

## Pre-frozen fee sensitivity

The implementation froze maker scenarios before the diagnostic: 0.0 / 0.4 / 0.8 / 1.2 / 1.5 bps per fill.

Equal-weight six-cell optimistic upper-bound results:

| Maker fee / fill | Mean net bps | Positive cells |
|---:|---:|---:|
| 0.0 | +1.330364 | 6/6 |
| 0.4 | +0.530364 | 6/6 |
| 0.8 | -0.269636 | 0/6 |
| 1.2 | -1.069636 | 0/6 |
| 1.5 | -1.669636 | 0/6 |

Descriptive break-even only:
- panel mean break-even maker fee ≈ **0.665182 bps/fill**;
- fee required to keep all six cells above zero ≈ **0.551258 bps/fill**.

These break-even values are descriptive diagnostics, not a new admissible fee target.

## Legitimate reopening trigger

The only pre-frozen discrete fee scenario below the all-cell break-even that was specified before this outcome is **0.4 bps/fill**.

A separate fee-tier child may be opened only if an account/venue execution route can prove **effective maker fee <= 0.4 bps/fill before any new forward outcome is accessed**.

That route would still need a separately frozen queue/fill/adverse-selection study. The 2025 0.4-bps result is development evidence only, not independent confirmation.

## Final routing

- standard-base Hyperliquid taker: CLOSED by fee-floor;
- standard-base Hyperliquid passive maker: CLOSED by optimistic upper-bound failure;
- parent L2 mechanism: VALIDATED, scientifically preserved;
- low-fee maker route: DORMANT / objective reopen trigger <=0.4 bps/fill;
- cross-venue or execution-overlay uses: materially new identities, prospective freeze required.
