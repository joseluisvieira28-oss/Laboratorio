# QUARTERLY-BASIS-CONVERGENCE-001 — FINAL SCIENTIFIC CLOSEOUT V0.2

Date: 2026-09-26  
Branch: `quarterly-basis-convergence-v02-runner-correction`  
Frozen MVE: `QBC-BINANCE-USDM-7D-001`

## FINAL CANONICAL CLASSIFICATION

**INSUFFICIENT_EVALUABLE_SAMPLE / NO_PROMOTION / EXACT_MVE_CLOSED**

This is not relabelled `DISCOVERY_NO_EDGE`.

The corrected, protocol-faithful 2021-2023 Discovery selected **0 trades from 24 qualified contract routes** because every frozen T-7d basis observation was below the pre-specified 0.7% entry threshold.

## WHY V0.1 DATA_FAILURE WAS NOT THE FINAL SCIENTIFIC ANSWER

The V0.1 runner required a completely contiguous minute-by-minute execution path before it evaluated whether a contract actually met the frozen entry threshold.

That ordering was stricter than the frozen protocol. A route that never enters has no execution path to adjudicate.

The V0.2 runner correction therefore:
1. requires the frozen snapshot bar;
2. computes the frozen signal basis;
3. returns NO_TRADE immediately when basis < 0.007;
4. requires minute-by-minute execution-path continuity only for an actually selected trade and only until its realized exit.

No economic parameter or gate was changed.

## SOURCE STATUS

The original Source Gate remains **SOURCE_DATA_PASS**:
- qualified contract routes: 32
- BTC routes: 16
- ETH routes: 16
- 2021: 8
- 2022: 8
- 2023: 8
- 2024: 8
- technical unresolved: 0
- rejected: 0

Discovery opened price fields only for 2021-2023.

2024 price fields remained locked.
2025 and 2026 remained locked.

## DISCOVERY RESULT

Qualified discovery routes: **24**  
Selected trades: **0**  
No-trade contracts below threshold: **24**

Frozen sample floors:
- resolved trades >= 12
- BTC trades >= 4
- ETH trades >= 4
- traded years >= 2

Observed:
- resolved trades: **0**
- BTC trades: **0**
- ETH trades: **0**
- traded years: **0**

Therefore the frozen breadth/sample floor fails before any expectancy, profit-factor, bootstrap, stress, concentration, or leave-one-out promotion test can be meaningfully evaluated.

## OBSERVED T-7D BASIS RANGE / REPRESENTATIVE VALUES

All 24 observed T-7d signal bases were below the frozen 0.7% threshold.

Examples:
- BTC 2021-03: 0.58799%
- ETH 2021-03: 0.61724%
- BTC 2023-03: 0.20128%
- ETH 2023-03: 0.20659%
- BTC 2023-12: 0.38645%
- ETH 2023-12: 0.27582%

The exact MVE therefore generated no eligible trade in the entire frozen Discovery period.

## BINANCE 2023-03-24 OUTAGE CONTEXT

Binance officially documented that Spot trading was temporarily disabled on 2023-03-24 at 11:27 UTC due to a matching-engine issue involving a trailing stop order, and resumed at 14:00 UTC.

That outage explains the missing Binance Spot bars that caused V0.1 to stop.

Under V0.2, it is correctly irrelevant to BTCUSDT_230331 and ETHUSDT_230331 because both frozen signals were below 0.7% and therefore neither route opened a position.

No synthetic fill or alternate execution was used.

## SCIENTIFIC INTERPRETATION

The mechanism itself — fixed-expiry basis convergence — is mechanically real, but this exact prospectively frozen trading implementation did not produce an evaluable sample.

The tested claim was not:
"does quarterly basis converge?"

It was:
"does a >=0.7% positive T-7d basis on Binance BTC/ETH quarterly USD-M futures produce a robust executable convergence edge under the frozen rules?"

During 2021-2023, the trigger occurred **0 times** across the 24 qualified routes.

Because the sample floor was prospectively frozen, the threshold must not be lowered after seeing this result.

## FINAL DISPOSITION

- SOURCE_DATA_PASS: YES
- DISCOVERY_SURVIVES: NO
- DISCOVERY_NO_EDGE: NOT ADJUDICATED
- INSUFFICIENT_EVALUABLE_SAMPLE: YES
- 2024 validation: MUST REMAIN CLOSED
- 2025/2026: CLOSED
- promotion: NO
- shadow: NO
- micro-live: NO
- live trading: NO
- exchange mutation: NO
- merge to main: NO

**ARCHIVE EXACT MVE `QBC-BINANCE-USDM-7D-001`.**

Any future test using a lower basis threshold, different lead time, different contracts, different collateral model, different costs, or another venue must be a new pre-frozen hypothesis/MVE and cannot be described as a rescue of this lineage.
