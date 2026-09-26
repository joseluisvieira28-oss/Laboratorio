# RETH-NAV-DISLOCATION-001 — CLOSEOUT V0.1

Closed: 2026-09-26
Final classification: DISCOVERY_PREDICTOR_INSUFFICIENT_SAMPLE
Promotion credit: 0

## Executive result

RETH-NAV-DISLOCATION-001 is CLOSED at the predictor-sample gate.

The historical source problem was solved cleanly and the predictor calibration census passed 556/556, but the pre-registered Discovery state rule produced zero extreme-entry events across the entire frozen Discovery region.

No mechanism outcome, market return, PnL, OOS, protected holdout, or live trading result was opened.

## Source / transport

Durable historical source feasibility:
SOURCE_PASS.

Final transport hardening:
- PublicNode for canonical block number/hash/timestamp only;
- BlockMachine for historical contract state;
- Multicall3 for the frozen state reads;
- EIP-1898 exact blockHash with requireCanonical=true.

Equivalence result:
SPLIT_TRANSPORT_BLOCKHASH_EQUIVALENCE_PASS.

At blocks 20,000,000 / 22,000,000 / 24,000,000:
- PublicNode and BlockMachine block hashes matched exactly;
- direct historical return bytes matched Multicall-by-number;
- Multicall-by-number matched Multicall-by-blockHash;
- all four scientific state reads matched exactly.

## Calibration census

Frozen region:
20,000,000 through 23,996,000
step = 7,200 blocks
expected = 556

Result:
PREDICTOR_SOURCE_CENSUS_PASS

- received rows: 556
- valid rows: 556
- invalid rows: 0
- row-set SHA-256:
  e921eca64a3265533e95a87f381a23434b13490c99e643b91527972c828a2402

Predictor descriptive range:
- min ≈ -1.0691503%
- max ≈ +0.7297710%
- median ≈ -0.1497247%

## Pre-frozen state calibration

Nearest-rank tails were frozen before the completed distribution was read.

q05:
- exact source block: 21,742,400
- ppb trunc: -7,390,227
- approx: -0.7390227%

q95:
- exact source block: 20,691,200
- ppb trunc: +5,729,902
- approx: +0.5729902%

Calibration state counts:
- DISCOUNT_EXTREME: 28
- NEUTRAL: 500
- PREMIUM_EXTREME: 28

## Frozen Discovery predictor gate

Discovery grid:
24,000,000 through 24,993,600
step = 7,200 blocks
139 exact state observations
plus boundary predecessor at 23,992,800.

Source result:
- valid Discovery states: 139 / 139
- invalid states: 0
- source errors: 0
- latest fallbacks: 0

Observed Discovery predictor range:
- minimum ≈ -0.5830317%
- maximum ≈ +0.0635364%

Both remained strictly inside the frozen extreme boundaries:
- q05 ≈ -0.7390227%
- q95 ≈ +0.5729902%

Therefore:
- NEUTRAL states: 139 / 139
- DISCOUNT_EXTREME states: 0
- PREMIUM_EXTREME states: 0
- transition-entry events: 0

Final gate:
DISCOVERY_PREDICTOR_INSUFFICIENT_SAMPLE

Frozen minimum had required:
- >=30 total events;
- >=10 discount events;
- >=10 premium events.

## No-rescue enforcement

The governance decision tree was frozen before this result.

Therefore the exact lab may NOT be rescued by:
- widening q05/q95;
- switching to q10/q90;
- using q01/q99;
- changing the fee tier/pool;
- dropping a tail;
- changing the cadence;
- choosing a different Discovery region;
- redefining de-clustering;
- opening +21,600-block diagnostics;
- opening returns or PnL to search for a favorable alternative.

The correct action is closeout.

## Outcome firewall

The following remained CLOSED for the entire lab:
- future dislocation outcomes;
- market returns;
- trading direction PnL;
- execution costs;
- OOS;
- protected holdout;
- live orders;
- exchange/wallet mutation.

Mechanism Discovery was never opened because the predictor-sample gate did not pass.

## Final scientific verdict

The data/source mechanism is reconstructable and technically robust.

However, under the exact pre-registered q05/q95 extreme-state definition and frozen Discovery region, there are zero admissible extreme-entry events.

Final verdict:
DISCOVERY_PREDICTOR_INSUFFICIENT_SAMPLE — CLOSED.

This is not NO_EDGE; the predictive mechanism was never tested.
It is not SOURCE_BLOCKED; source and census passed.
It earns zero edge/promotion credit.
