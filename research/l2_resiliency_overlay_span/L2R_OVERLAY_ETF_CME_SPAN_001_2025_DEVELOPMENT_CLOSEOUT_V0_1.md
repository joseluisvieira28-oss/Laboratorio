# L2R-OVERLAY-ETF-CME-SPAN-001 — 2025 DEVELOPMENT CLOSEOUT V0.1

Date: 2026-09-27
Status: **DEVELOPMENT_SPAN_NO_SUPPORT — EXACT V0.1 CLOSED / NO RESCUE**

## Canonical identity

LAB_ID: `L2R-OVERLAY-ETF-CME-SPAN-001`

Protocol freeze:
`396992a03d67a4a960445acbd9b17b7a21171994`

Source/sample preflight:
`f59d584c195b9e6f78c78f32d9cd96450d98b8cb`

Implementation lock:
`d9cc256611e3d6583af716a03b4495fc0d242bea`

One-shot authorization:
`ca747444a29e18d9dd30aea37205ce12fb8ad507`

Frozen runner SHA256:
`e3b965e3c072deb1aeeb18e7000ccb266786b484bcdeea3e5082e17cd552382a`

ETF-CME parent artifact SHA256:
`40bd341c300532e5b67127a098c82ecf2f41e1cc4a3ce646ac824b27529f9bd1`

L2 parent manifest SHA256:
`767e75594864344c75dd2669ec4fad8c738710c218322b11fd43a83077ef17c3`

Canonical evidence ZIP SHA256:
`842bafad5c4b61682ae5a2a1f95393c4331174fa5728f0eaed072048a5d0ea92`

Evidence member SHA256:
- receipt: `55394877c6c6adbf6d341f32c21b73d51cba8941479c6bb38f9b91d978fe3156`
- cell summary: `a2841f96839164a0a55bc289a756847f0875261c7762bd26dab250d5f145544f`
- ledger: `7c7612c683df28acca6bd64e65837a8fba5a11955381cf148da7647385e58fcd`

Evidence ingestion commit:
`27dbb3d188b626fb5ccaff2caae4215df69b52fa`

Independent adjudication workflow:
- run `36321383470`
- job `108625762248`
- result: `ADJUDICATION_PASS`

## Frozen one-shot result

Classification:

`DEVELOPMENT_SPAN_NO_SUPPORT`

Source-present ETF parent rows: **46**
Parent non-zero rows: **49**

Raw corpus traversal:
- objects verified: **8,400**
- accepted states: **53,647,518**
- stale-late payload rows: **240**
- ambiguous sweeps: **5,384**

Firewalls:
- 2026 accessed: **false**
- market-data network acquisition: **false**
- orders: **false**
- live trading: **false**
- exchange mutation: **false**
- main merge: **false**

## Six-cell result

| Cell | ALIGNED n | OPPOSED n | Selected n | Viable | ALIGNED mean bps | OPPOSED mean bps | Separation bps |
|---|---:|---:|---:|---|---:|---:|---:|
| R1_Y5 | 0 | 1 | 1 | no | — | -1.048761 | — |
| R1_Y15 | 6 | 7 | 13 | yes | -0.076049 | -2.721059 | **+2.645009** |
| R1_Y60 | 18 | 17 | 35 | yes | +0.288583 | -1.450030 | **+1.738613** |
| R5_Y15 | 2 | 2 | 4 | no | +1.244037 | -2.448524 | +3.692561* |
| R5_Y60 | 20 | 12 | 32 | yes | +0.518119 | +0.043765 | **+0.474354** |
| R15_Y60 | 14 | 10 | 24 | yes | +0.594556 | +0.633196 | **-0.038640** |

`*` R5_Y15 is sample-ineligible under the pre-frozen >=10 selected and >=3/side rule; its sign receives no gate credit.

Viable cells:
- R1_Y15
- R1_Y60
- R5_Y60
- R15_Y60

Viable-cell count: **4 / 6**

Positive viable-cell separations: **3 / 4**

Panel equal-weight separation:
**+1.2048343055 bps**

Panel equal-weight ALIGNED mean:
**+0.3313022563 bps**

Panel equal-weight OPPOSED mean:
**-0.8735320491 bps**

Positive by replenishment family:
- R1: **true**
- R5: **true**
- R15: **false**

## Frozen gate adjudication

| Gate | Result |
|---|---|
| global sample viability | PASS |
| panel equal-weight separation > 0 | PASS |
| >=4 positive viable cells | **FAIL** |
| each R family has >=1 positive viable cell | **FAIL** |
| panel ALIGNED mean > 0 | PASS |
| panel OPPOSED mean < 0 | PASS |

The two failed gates are decisive.

The exact frozen classification is therefore:

`DEVELOPMENT_SPAN_NO_SUPPORT`

## Scientific interpretation

The development panel contains some directional structure:
- the viable-cell equal-weight separation is positive;
- ALIGNED is positive on average;
- OPPOSED is negative on average;
- three viable cells have positive separation.

However the pre-frozen robustness requirement was deliberately stronger than a positive panel mean. The mechanism had to preserve positive separation across at least four viable cells and across every R family.

It did not.

In particular, the only viable R15 cell (`R15_Y60`) produced a slightly negative separation:
`-0.0386396917 bps`.

Therefore this exact cross-T0 SPAN identity is **not supported by the frozen 2025 development gate**.

This is not an execution/PnL verdict and does not invalidate the already-validated parent L2 replenishment mechanism. It specifically rejects this frozen ETF-CME span-overlay translation.

## No rescue

Do not:
- promote using the positive panel mean alone;
- ignore R15_Y60;
- count sample-ineligible R5_Y15 as a fourth positive cell;
- lower the >=4 positive-cell requirement;
- remove the each-R-family requirement;
- select only R1/R5;
- alter R/Y horizons or RR threshold;
- tune on ETF seven-day PnL;
- rerun this LAB_ID with modified rules.

Any materially different overlay requires a **new LAB_ID**, a new pre-outcome freeze, and independent future evidence.

## Parent states unchanged

`L2-RESILIENCY-001`:
**MECHANISM VALIDATED / DIRECT STANDARD-FEE MONETIZATION CLOSED**

`ETF-CME-INSTFLOW-001`:
existing Tier 2 / fragile classification unchanged.

## Operational closure

- exact SPAN-001 V0.1: CLOSED
- promotion credit: **none**
- Tier 2 / “quase diamante” for this overlay: **NO**
- 2026 remains CLOSED
- PR #122: NO MERGE
