# L2R-OVERLAY-ETF-CME-001 — 2025 DEVELOPMENT CLOSEOUT V0.1

Date: 2026-09-27
Status: **DEVELOPMENT_OVERLAY_INSUFFICIENT_SAMPLE_OR_SOURCE — V0.1 CLOSED**

## Canonical identity

LAB_ID: `L2R-OVERLAY-ETF-CME-001`

Frozen protocol:
`2d12d690fe703ac6dec270cf551eeae0b85cadb0`

Implementation lock:
`81eb670ddde2bbf604f7b89a5026a48a73a04526`

One-shot authorization:
`f0fd04353eb0758d9f4f958e1f92c16f7df78e1f`

Runner SHA256:
`495129040193b01218d867bd8a29f50039e5229203d118571f38445746942b2a`

ETF-CME parent artifact SHA256:
`40bd341c300532e5b67127a098c82ecf2f41e1cc4a3ce646ac824b27529f9bd1`

L2 parent manifest SHA256:
`767e75594864344c75dd2669ec4fad8c738710c218322b11fd43a83077ef17c3`

Canonical evidence ZIP SHA256:
`a8734c72cad031e8d6f32d5836c615909e2605a0b37fe4f075a52aaeab2b09a0`

Evidence members:
- ledger SHA256: `aa10e0a70a184983032972cf9f3307e04af0cb90b9bfc722ff8b77bf8161d1a4`
- cell summary SHA256: `2c18406705d36795bf9ce9f1f9f4e2cfc4994342e09c970d551e348df902bb65`
- receipt SHA256: `eb9771ab767cc6c0c3f3dabd8ba2712038f2d6ae978c9369763ea66aa2dec56b`

## One-shot result

Frozen classification:

`DEVELOPMENT_OVERLAY_INSUFFICIENT_SAMPLE_OR_SOURCE`

Parent ETF rows: 50  
Parent non-zero-position rows: 49  
Global source-evaluable rows under the frozen T0 midpoint rule: **0**

Raw corpus traversal:
- objects verified: **8,400 / 8,400**
- accepted normalized states: **53,647,518**
- stale-late payload rows quarantined: **240**
- ambiguous sweeps: **5,384**
- 2026 access: **false**

## Six-cell reconciliation

| Cell | Parent nonzero | ALIGNED | OPPOSED | NO_ACTIVE_WEAK | SOURCE_GATED | Sample viable |
|---|---:|---:|---:|---:|---:|---|
| R1_Y5 | 49 | 0 | 0 | 40 | 9 | false |
| R1_Y15 | 49 | 0 | 0 | 24 | 25 | false |
| R1_Y60 | 49 | 0 | 0 | 8 | 41 | false |
| R5_Y15 | 49 | 0 | 0 | 36 | 13 | false |
| R5_Y60 | 49 | 0 | 0 | 12 | 37 | false |
| R15_Y60 | 49 | 0 | 0 | 20 | 29 | false |

Ledger reconciliation: **294 rows = 49 × 6**.  
Non-null residual observations: **0**.

For each cell, exactly three SOURCE_GATED rows have no selected-event timestamps, consistent with the known canonical source gaps touching ETF entry windows. The remaining SOURCE_GATED selected-event rows cannot be adjudicated because the frozen T0 reference-price requirement was not satisfied.

## Exact blocker

V0.1 required:

`MID_T0 = first accepted normalized Hyperliquid midpoint at/after exact ETF T0, maximum lateness 1,100 ms`.

The valid one-shot result contains:

`global_source_evaluable_rows = 0`.

Under the frozen runner this means that **none of the source-present non-zero ETF entry timestamps obtained an accepted T0 midpoint within the required 1,100 ms window**.

This closeout does not invent a provider explanation for that timing fact. The exact reason for the systematic T0 sampling miss was not separately measured inside V0.1.

The prior canonical source-clock work remains relevant context: archive envelope ordering is authoritative for the L2 parent, source gaps are segmented, and the downstream 1,100 ms maximum-lateness rule was frozen before this overlay outcome.

## Scientific adjudication

This is **NOT**:
- `DEVELOPMENT_OVERLAY_NO_SUPPORT`;
- `NO_EDGE`;
- a negative economic result;
- evidence that ALIGNED or OPPOSED is better/worse;
- independent validation;
- a Tier promotion or demotion of either parent.

No directional overlay response was actually adjudicable because the frozen source/timing gate failed first.

Therefore:
- exact V0.1 identity is CLOSED as source/sample constrained;
- no rerun with a wider T0 lateness window is allowed under this LAB_ID;
- no replacement of first-after-T0 with last-before-T0 is allowed under this LAB_ID;
- no cell/subgroup/horizon rescue is allowed under this LAB_ID.

## Parent states unchanged

`L2-RESILIENCY-001`:
**MECHANISM VALIDATED / DIRECT STANDARD-FEE MONETIZATION CLOSED**

`ETF-CME-INSTFLOW-001`:
its existing Tier 2 / fragile parent classification is unchanged.

## Legitimate successor research

A materially new successor may be frozen under a new LAB_ID because V0.1 exposed a source/timing feasibility failure before any directional residual outcome was observed.

A successor must choose its T0/reference-price semantics **before** accessing combined directional outcomes.

Scientifically defensible examples include:
1. a causal pre-T0 reference rule using the last accepted normalized state at-or-before T0 with a prospectively frozen staleness policy; or
2. an event-span rule using the already-frozen selected L2 R observation as the causal baseline and Y as the endpoint, without pretending it is an executable ETF fill.

Any successor remains 2025 development-only and receives no promotion credit without future independent evidence.

## Firewalls preserved

- 2026 accessed: false
- orders: false
- live trading: false
- exchange mutation: false
- wallet mutation: false
- main merge: false
- post-outcome parameter rescue: false
