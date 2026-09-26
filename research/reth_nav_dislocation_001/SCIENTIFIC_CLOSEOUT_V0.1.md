# RETH-NAV-DISLOCATION-001 — SCIENTIFIC CLOSEOUT V0.1

Date: 2026-09-27
Exact lab: RETH-NAV-DISLOCATION-001

## Final classification

**DISCOVERY_PREDICTOR_INSUFFICIENT_SAMPLE — CLOSED**

This is a scientific closeout of the exact frozen state-transition hypothesis.
It is not SOURCE_BLOCKED and it is not NO_EDGE from an outcome test.

The mechanism hypothesis was **NOT TESTED**, because the pre-frozen predictor sample gate did not authorize opening future dislocation outcomes.

## Source / transport result

Historical source:
**SOURCE_PASS**

Final transport:
**SPLIT_TRANSPORT_BLOCKHASH_EQUIVALENCE_PASS**

Exact 556-point calibration census:
**PREDICTOR_SOURCE_CENSUS_PASS**
- valid: 556 / 556
- invalid: 0
- row-set SHA256:
  e921eca64a3265533e95a87f381a23434b13490c99e643b91527972c828a2402

The final transport used:
- PublicNode for block headers only;
- BlockMachine for historical contract state;
- Multicall3 for state-call compression;
- EIP-1898 exact blockHash + requireCanonical=true.

## Frozen calibration

Nearest-rank thresholds were computed exactly as pre-frozen:

q05:
- approximately -7,390,227 ppb
- approximately -0.7390%

q95:
- approximately +5,729,902 ppb
- approximately +0.5730%

No threshold was changed after observation.

## Discovery predictor-only gate

Frozen Discovery grid:
- start: block 24,000,000
- step: 7,200 blocks
- count: 139
- boundary predecessor: 23,992,800
- Discovery region ends below 25,000,000

Result:
- valid Discovery states: 139 / 139
- invalid: 0
- transition-entry events: 0
- discount-extreme entries: 0
- premium-extreme entries: 0
- all 139 states: NEUTRAL

Observed Discovery predictor range:
- minimum approximately -5,830,317 ppb (-0.5830%)
- maximum approximately +635,364 ppb (+0.0635%)

Therefore:
- minimum never crossed the frozen q05 threshold;
- maximum never crossed the frozen q95 threshold;
- zero qualifying transition-entry events is correct.

## Frozen sample requirement

The pre-result gate required:
- >=30 total transition-entry events;
- >=10 discount entries;
- >=10 premium entries.

Observed:
- 0 total;
- 0 discount;
- 0 premium.

Classification:
**DISCOVERY_PREDICTOR_INSUFFICIENT_SAMPLE**

## Outcome boundary

Because the predictor-only sample gate did not pass:

- mechanism Discovery outcomes were NOT opened;
- +7,200-block future dislocation outcomes were NOT tested;
- +21,600 diagnostic outcomes were NOT used;
- OOS remains CLOSED;
- protected holdout remains CLOSED;
- market returns remain CLOSED;
- PnL remains CLOSED;
- no execution economics were opened;
- no live trading or mutation was authorized.

## No-rescue enforcement

The exact lab MUST NOT be rescued by:
- widening q05/q95;
- changing quantile levels;
- changing the 7,200-block cadence;
- using level observations instead of pre-frozen transition entries;
- changing the Discovery partition;
- extending Discovery into OOS;
- using the +21,600 horizon to manufacture a test;
- selecting only the discount side;
- selecting only the premium side;
- lowering the >=30 / >=10 / >=10 sample gate;
- opening outcomes despite insufficient predictor sample.

Any future rETH/NAV research must be a scientifically distinct child hypothesis frozen independently before its protected outcomes are inspected.

## Promotion

Promotion credit: **0**

No edge, almost-diamond, diamond, trading or live-execution promotion is warranted from this lab.

PR #111 remains DRAFT / research evidence only.
No merge to main is authorized.
