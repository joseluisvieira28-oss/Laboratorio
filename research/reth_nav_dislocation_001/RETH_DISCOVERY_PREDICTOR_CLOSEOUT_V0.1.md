# RETH-NAV-DISLOCATION-001 — DISCOVERY PREDICTOR CLOSEOUT V0.1

Date: 2026-09-26
Status: **CLOSED — DISCOVERY_PREDICTOR_INSUFFICIENT_SAMPLE**

## Final gate path

1. Historical source gate: **SOURCE_PASS**
2. Split transport + EIP-1898 blockHash equivalence: **PASS**
3. Frozen predictor census 20,000,000 → <24,000,000: **PASS**
   - expected: 556
   - valid: 556
   - invalid: 0
   - row-set SHA256: e921eca64a3265533e95a87f381a23434b13490c99e643b91527972c828a2402
4. Pre-frozen nearest-rank state calibration: **PASS**
   - q05: approximately -7.390227e-3 dislocation
   - q95: approximately +5.729902e-3 dislocation
   - calibration state counts: 28 DISCOUNT_EXTREME / 500 NEUTRAL / 28 PREMIUM_EXTREME
5. Frozen Discovery predictor grid 24,000,000 → <25,000,000: **139/139 valid**
6. Frozen transition-entry event census:
   - total entries: 0
   - discount entries: 0
   - premium entries: 0
7. Required sample:
   - >=30 total
   - >=10 discount
   - >=10 premium

Final classification:
**DISCOVERY_PREDICTOR_INSUFFICIENT_SAMPLE**

## Scientific meaning

The exact frozen predictor state definition did not occur in the Discovery region at the required sampling grid.

This is not:
- a source failure;
- an RPC failure;
- missing historical state;
- a mechanism FAIL;
- evidence of no mechanism;
- evidence of an edge.

The mechanism hypothesis was **NOT TESTED** because the pre-registered predictor sample gate did not open.

## No-rescue enforcement

Per the decision tree frozen before Discovery values were observed:

Do NOT:
- widen q05/q95;
- select different quantiles;
- change the 7,200-block predictor grid;
- use within-state observations instead of transition entries;
- alter de-clustering;
- change the Discovery boundary;
- open +7,200 future dislocation outcomes;
- use the +21,600 diagnostic;
- open OOS;
- open protected holdout;
- open market-return/PnL outcomes.

The exact lab is closed.

## Preserved reusable infrastructure

The following remains scientifically useful with zero edge credit:
- public/keyless archive source proof;
- PublicNode header + BlockMachine archive split transport;
- Multicall3 state compression;
- EIP-1898 exact blockHash / requireCanonical binding;
- 556-point predictor census;
- source and transport receipts.

A future child hypothesis must be economically/scientifically distinct and frozen independently before seeing its outcomes. It must not be a rescue of this exact failed sample gate.

## Promotion

Promotion credit: **0**
Edge status: **NOT TESTED**
OOS: **CLOSED**
Protected holdout: **CLOSED**
PnL: **CLOSED**
Live execution: **PROHIBITED**
Main merge: **NOT AUTHORIZED**
