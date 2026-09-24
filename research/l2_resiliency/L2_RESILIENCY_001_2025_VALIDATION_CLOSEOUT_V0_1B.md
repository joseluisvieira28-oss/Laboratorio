# L2-RESILIENCY-001 — 2025 INDEPENDENT VALIDATION CLOSEOUT V0.1B

Status: **VALIDATION_PASS — IMMUTABLE 2025 HOLDOUT RESULT**  
Protocol: `INDEPENDENT_2025_VALIDATION_HOLDOUT_PROTOCOL_V0.1`  
Source-clock amendment: `SOURCE_CLOCK_NORMALIZATION_AMENDMENT_V0.1B`  
Evidence bundle SHA256: `e191a0f02031f8f84d264b365aeeaf4b16929dee3e4d507f034d0c3bbff06c22`  
Canonical RAW manifest SHA256: `767e75594864344c75dd2669ec4fad8c738710c218322b11fd43a83077ef17c3`

## Source / schema

- 8,400 present hourly BTC l2Book objects of 8,760 expected.
- Source coverage: **95.89041095890411%**.
- Records audited: **53,647,758**.
- Accepted states: **53,647,518**.
- Segments: **3**.
- Stale late payload rows: **240**.
- Equal payload timestamp rows: **13,949**.
- Future payload clock-skew rows: **109**.
- Source/schema classification: **SOURCE_SCHEMA_NORMALIZED_PASS**.
- 2026 access: **false**.

## Frozen 2025 primary result

- Classification: **VALIDATION_PASS**.
- Eligible days: **351**.
- Global weak-minus-strong contrast: **+0.8873531352251535 bps**.
- Bootstrap 95% CI: **[+0.859990240973238, +0.9157540345723161] bps**.
- Positive cells: **6/6**.
- Positive replenishment horizons: **1000 ms, 5000 ms, 15000 ms — all true**.

| Cell | Days | Contrast bps | CI95 low | CI95 high |
|---|---:|---:|---:|---:|
| R1_Y5 | 351 | +0.5984582215583941 | +0.5743511480802143 | +0.6240240238946501 |
| R1_Y15 | 351 | +0.7578359967283747 | +0.7325934489353628 | +0.7849401170658692 |
| R1_Y60 | 351 | +0.7951769275463941 | +0.7681823274062399 | +0.8234995515567638 |
| R5_Y15 | 351 | +0.9427075785523383 | +0.9105086220275008 | +0.9763383411150006 |
| R5_Y60 | 351 | +1.063525204679606 | +1.0282190095672652 | +1.0996946640728165 |
| R15_Y60 | 351 | +1.166414882285814 | +1.1339715573048768 | +1.200238651334403 |

## Temporal / side diagnostics

All 12 calendar months represented in the eligible sample have positive global mean contrast and **100% positive eligible days** inside each represented month.  
ASK/BID side diagnostics preserve the weak-vs-strong separation across all six cells.

## Firewalls preserved

The frozen receipt records:
- no 2026 access;
- no PnL;
- no trading-cost computation;
- no Sharpe;
- no leverage computation;
- no live trading;
- no exchange mutation;
- no deployment;
- no main merge.

The post-outcome rule remains: **NO RESCUE / NO RETUNING. Exact V0.1 validation verdict is immutable.**

## Scientific adjudication

The pre-specified L2 replenishment mechanism that was supported in 2024 **replicated independently in the frozen 2025 holdout**. This closes the 2025 replication question as **VALIDATION_PASS**, not BLOCKED, INSUFFICIENT_SAMPLE, or NO_EDGE.

This closeout does **not** by itself promote L2-RESILIENCY-001 to Promotion Policy V3 Tier 2 / Quase Diamante. The 2025 validation tested a mechanism-response contrast and deliberately did not compute trading costs, Profit Factor, PnL or an executable market implementation. V3 universal eligibility still requires frozen realistic economics and execution feasibility before a Tier-2 adjudication.

## Next legitimate action

Create a **prospective execution/economics translation freeze** that preserves the validated mechanism and defines, before any new outcomes:
- exact signal formation from the validated replenishment state;
- side/direction;
- entry clock and order type;
- exit/horizon;
- fees, spread, slippage and latency assumptions;
- notional/capacity envelope;
- source/execution preflight;
- shadow evidence requirements and stop conditions.

No 2026 market outcomes, live orders, exchange mutation, post-outcome parameter rescue or production capital are authorized by this closeout.
