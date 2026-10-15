# PREDICTION-ORACLE-BASIS-001 — PRE-SOURCE AUTHORITY V0.1

Date: 2026-09-27
Status: FROZEN_PRE_SOURCE / OUTCOME_BLIND / RESEARCH_ONLY
Branch: prediction-oracle-basis-v0.1

## 1. Research question
Can two BTC binary contracts that appear economically similar acquire a reproducible, executable payoff asymmetry because they settle against different reference-price/oracle definitions, and is that asymmetry measurably linked to the contemporaneously observable USDT/USD basis?

This is NOT a claim that an edge exists.

## 2. Mechanism statement
A Polymarket BTC Up/Down contract can resolve from a Binance BTC/USDT candle while a matched regulated-market contract may resolve from a USD-denominated reference index. BTC/USDT and BTC/USD need not cross their respective open/close thresholds identically because USDT/USD is not identically 1 at every instant.

The potential payer is market segmentation plus participants who price the two event contracts as if their settlement definitions were fungible. Limits to arbitrage may include fragmented collateral, venue access, fees/spreads, asynchronous execution, depth, capital lock-up and rule/settlement basis risk.

## 3. Failure mode
The hypothesis fails economically if any of the following dominates prospectively:
- matched contracts are not sufficiently equivalent apart from the predeclared oracle difference;
- synchronized executable quotes fully price the oracle basis;
- the observable basis has insufficient magnitude relative to bid/ask + fees + slippage;
- apparent wedges are caused by timestamp misalignment/stale quotes;
- capacity is negligible or one-leg execution risk dominates;
- rule changes or oracle methodology changes break comparability.

## 4. Contamination boundary
Historical periods/results already analysed in 2026 publications are THEORY/ENGINEERING ONLY.

They may be used to:
- understand market definitions;
- design source schemas;
- enumerate falsification tests;
- identify known implementation traps.

They may NOT be used as independent Crypto Lab Discovery, OOS, holdout or promotion evidence.

Primary scientific evidence for this new lab must be prospective after the final implementation freeze, unless a later authority identifies a genuinely untouched historical block and freezes the exact rule before opening it.

## 5. Current authorized phase
SOURCE/DATA FEASIBILITY ONLY.

Allowed:
- public market metadata;
- contract rules;
- settlement-source definitions;
- API/schema discovery;
- timestamp and clock semantics;
- current public bid/ask schema without evaluating strategy performance;
- availability/coverage counts;
- source hashes and receipts;
- deterministic market matching logic tested on synthetic fixtures.

Forbidden in this phase:
- PnL;
- win rate;
- return/edge optimization;
- threshold tuning;
- selecting only profitable hours;
- backfilling missed prospective opportunities;
- live orders;
- authenticated trading endpoints;
- exchange mutation;
- leverage;
- capital;
- merge to main.

## 6. Required source objects
For each candidate matched hour:
A. Polymarket
- immutable market/event identifier;
- exact rules text;
- open/close time;
- resolution source;
- YES/NO executable best bid/ask and sizes at synchronized snapshots;
- fee schedule applicable at the snapshot;
- final resolution only after the event matures.

B. Comparison venue
- immutable market/event identifier;
- exact rules text;
- open/close time;
- settlement reference/index definition;
- YES/NO executable best bid/ask and sizes at synchronized snapshots;
- fee schedule;
- final resolution only after maturity.

C. Underlying/reference
- Binance BTCUSDT reference needed by Polymarket rules;
- the exact USD reference/index specified by the comparison venue;
- USDT/USD basis source frozen before any economic test.

## 7. Equivalence classifier
Every candidate pair must be classified BEFORE economic analysis:
- EXACT_EXCEPT_ORACLE
- NON_EQUIVALENT_TIME
- NON_EQUIVALENT_THRESHOLD
- NON_EQUIVALENT_TIE_RULE
- NON_EQUIVALENT_EARLY_CLOSE
- NON_EQUIVALENT_OTHER

Only EXACT_EXCEPT_ORACLE may enter the primary future mechanism test.

No manual override after outcomes.

## 8. Timestamp integrity
All observations normalized to UTC.

Primary rule:
quotes from the two venues must be synchronized inside a prospectively frozen tolerance that is justified from feed cadence BEFORE outcomes.

A timestamp-shift placebo is mandatory later because published work shows false arbitrage can be manufactured by mistiming venues.

No nearest-future quote.
No stale last-trade substitution.
No midpoint presented as executable economics.

## 9. Source/Data Gate — PASS criteria
Before any economic outcome may be opened:
1. documented public acquisition route for both venues;
2. exact rules and settlement-source fields captured;
3. executable bid/ask + size available on both legs;
4. deterministic contract-matching routine;
5. timestamp integrity established;
6. fee schedule provenance established;
7. USDT/USD basis source provenance established;
8. >= 99% successful capture for the prospective source-observation schedule over the predeclared gate window OR a stricter later freeze;
9. zero future-nearest joins;
10. zero silent imputation;
11. source manifest + SHA256 receipts preserved.

Any failure => SOURCE_DATA_PASS=false. It is not NO_EDGE.

## 10. Later scientific test — NOT YET AUTHORIZED
If and only if SOURCE_DATA_PASS:
- freeze the exact payoff-state mapping from the two oracle definitions;
- freeze all execution assumptions;
- freeze sample minimum and inference;
- freeze friction/capacity gates;
- freeze adversarial tests;
- then collect untouched prospective evidence.

Primary future quantity should be payoff-state misclassification / executable package economics conditional on the independently observed oracle basis, not BTC directional prediction.

## 11. Mandatory adversarial falsification
Future protocol must include:
- synchronous vs intentionally shifted quote placebo;
- executable bid/ask vs midpoint diagnostic;
- shuffled USDT/USD basis sign;
- unmatched/non-equivalent contracts as negative controls;
- fee/spread stress;
- one-leg fill stress;
- exact-rule change detection;
- leave-time-block-out stability.

## 12. Promotion discipline
Any future candidate must satisfy the existing Diamond Test independently:
positive net economics, temporal stability, predeclared regime logic, untouched OOS/forward evidence, operational realism, causal fingerprint, adversarial falsification and zero post-outcome rescue.

This authority creates a mine, not a diamond.
