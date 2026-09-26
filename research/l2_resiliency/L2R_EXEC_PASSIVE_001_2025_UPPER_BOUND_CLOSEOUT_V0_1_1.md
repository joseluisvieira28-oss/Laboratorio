# L2R-EXEC-PASSIVE-001 — 2025 OPTIMISTIC PASSIVE UPPER-BOUND CLOSEOUT V0.1.1

Status: **PASSIVE_STANDARD_BASE_UPPER_BOUND_FAIL — CHILD ROUTE CLOSED**  
Parent: `L2-RESILIENCY-001` remains **2025 INDEPENDENT VALIDATION PASS / MECHANISM REPLICATED**.  
Implementation: `0.1.1`  
Evidence ZIP SHA256: `ed36a1001d5c598896235257a811de98af44dc5eae4eb0a94c3c690a292590fe`  
Source manifest SHA256: `767e75594864344c75dd2669ec4fad8c738710c218322b11fd43a83077ef17c3`

## What was tested

This child used the already-open canonical 2025 corpus only. It kept all six parent causal cells and tested an intentionally optimistic passive execution upper bound:

- LONG: passive fill at bid_R, passive exit at ask_Y;
- SHORT: passive fill at ask_R, passive exit at bid_Y;
- assumed 100% fill probability;
- ignored queue delay, missed fills, cancellations, adverse selection and latency;
- no 2026, no network acquisition, no orders, no exchange mutation.

This is post-validation development evidence for a new executable identity, not independent confirmation.

## Frozen standard-base fee gate

Hyperliquid standard-base maker fee in the frozen diagnostic: **1.5 bps per fill**, or **3.0 bps round trip**.

Frozen survival gate required:
1. equal-weight six-cell net upper-bound mean > 0;
2. at least 4/6 cells positive;
3. every replenishment horizon family (R1/R5/R15) represented by at least one positive cell.

## Result

Equal-weight six-cell standard-base maker upper-bound net:
**-1.669635765191727 bps/opportunity**

Positive cells:
**0/6**

Positive by replenishment horizon:
- R1: false
- R5: false
- R15: false

All three frozen support gates fail.

| Cell | WEAK N | Mid response bps | Optimistic maker gross bps | Net @ 1.5 bps/fill |
|---|---:|---:|---:|---:|
| R1_Y5 | 2,241,028 | +0.921271 | +1.102516 | -1.897484 |
| R1_Y15 | 2,302,354 | +1.243895 | +1.421994 | -1.578006 |
| R1_Y60 | 2,307,885 | +1.344251 | +1.520861 | -1.479139 |
| R5_Y15 | 1,630,311 | +1.052318 | +1.234643 | -1.765357 |
| R5_Y60 | 1,623,754 | +1.215508 | +1.396925 | -1.603075 |
| R15_Y60 | 1,400,753 | +1.116078 | +1.305245 | -1.694755 |

## Fee-scenario diagnostic already frozen pre-run

At **0.4 bps/fill**, all six optimistic upper-bound cells remain positive.  
At **0.8 bps/fill**, all six are negative.

This does not authorize lowering costs after outcome. The standard-base child remains closed. Any account-specific lower-fee child would need a new prospective identity with the actual fee tier frozen before any further outcome use.

## Scientific adjudication

`L2R-EXEC-PASSIVE-001`:
**PASSIVE_STANDARD_BASE_UPPER_BOUND_FAIL / CLOSED**

Because the route fails even under an impossible best-case fill assumption, no queue-position/fill-probability simulation is warranted for the standard-base fee route. Realistic execution can only be worse than this upper bound.

This is **not NO_EDGE** for the parent mechanism. It is an execution-economics failure for this child implementation.

The parent remains:
**L2-RESILIENCY-001 — MECHANISM VALIDATED / DIRECT STANDARD-FEE MONETIZATION NOT DEMONSTRATED.**

## Firewalls preserved

- 2026 access: false
- network market-data acquisition: false
- live trading: false
- orders: false
- exchange mutation: false
- main merge: false
- cell selection after outcome: false

## Legitimate next paths

1. **Account-specific Hyperliquid discounted-maker path** only if an objectively available fee tier <= the pre-frozen feasible region is documented before new execution outcomes. New LAB_ID required.
2. **Cross-venue execution / lead-lag path** is materially new science and requires a new prospective LAB_ID; the Hyperliquid L2 signal may lead another lower-cost venue, but this cannot be assumed from the parent.
3. Preserve the parent mechanism as validated scientific evidence even if no standard-fee direct execution route is economical.

No fee reduction, cell selection, horizon switch, venue switch or execution-model rescue is permitted inside `L2R-EXEC-PASSIVE-001`.
