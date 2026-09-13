# Macro Shock Microstructure State Lab V0.1 — Independent Pre-Data Measurement Design Review

Status: **CLOSED PRE-DATA REVIEW — MEASUREMENT LAYER JUSTIFIED, DIRECTIONAL H02 NOT AUTHORIZED**

## Scope

This review asks one narrow question before any target-outcome access:

> Are the proposed microstructure measurements independently justified as state/price-discovery measurements, without relying on favorable realized BTC/ETH outcomes?

It does **not** ask whether any measurement predicts direction, produces positive expectancy, or supports a trading strategy.

## Inputs reviewed

- the prior Macro Shock Mechanism Review V1;
- the Microstructure State Lab V0.1 pre-data charter;
- the V0.2 public read-only provenance PASS;
- the frozen schema/alignment specification;
- the pre-data measurement catalog;
- synthetic-only implementation/tests and the green research-safety CI.

No target outcomes were inspected for this review.

## Review findings

### Spread / quoted liquidity

**JUSTIFIED AS A MEASUREMENT.**

Quoted spread is a direct contemporaneous liquidity-state variable. It is mechanically measurable from synchronized BBO state and does not require a directional assumption.

What is *not* justified here: a spread threshold, a recovery horizon, or any rule that predicts future price direction.

### Book depth / depletion / refill

**JUSTIFIED AS A MEASUREMENT, PARAMETERIZATION NOT YET FROZEN.**

Depth and refill/depletion are direct order-book-state descriptors. However, level count, price-distance band, aggregation method, and comparison horizon are research parameters and cannot be selected after viewing target outcomes.

### Trade and signed-flow intensity

**JUSTIFIED AS A MEASUREMENT WHERE SOURCE SEMANTICS ARE UNAMBIGUOUS.**

Trade count/notional intensity and source-supported aggressor-side flow are legitimate descriptors of market activity and order-flow state. The earlier Macro Shock work supports activity/price-discovery mechanisms, but it did not establish that any signed-flow state predicts later continuation.

Therefore no flow threshold, persistence rule, or directional mapping is authorized.

### Realized-volatility state

**JUSTIFIED AS A MEASUREMENT, WINDOW NOT YET FROZEN.**

Realized volatility is a non-directional descriptor of state change. Sampling cadence, window length, annualization/scaling, and event-relative interval remain prospective design choices and may not be optimized on target outcomes.

### Cross-venue alignment / price-discovery state

**JUSTIFIED AS A MEASUREMENT PRIMITIVE, LEADER/FOLLOWER CLAIM NOT AUTHORIZED.**

Backward as-of alignment is technically justified for non-look-ahead cross-venue comparison. Relative mid-price differences, clock skew, and missingness can be measured without declaring a venue leader.

No lead/lag horizon, venue priority, or predictive direction is justified by this pre-data review.

### Read-only execution-condition proxies

**JUSTIFIED AS DESCRIPTIVE MEASUREMENTS ONLY.**

Quoted spread, available depth and hypothetical slippage/adverse-selection calculations can describe execution conditions without placing orders, provided notional and horizons are fixed independently of target outcomes.

They are not authorization for paper/live execution.

## Data and implementation sufficiency

The bounded V0.2 shakedown established that the selected public read-only Binance Spot market-data-only and Coinbase Advanced Spot paths can be captured and reconstructed with zero parse failures in the tested run, synchronized BTC/ETH books, valid Coinbase connection sequencing, preserved raw hashes, and no authenticated/mutating access.

The schema implementation then added deterministic identity validation, timestamp/provenance preservation, strictly backward as-of alignment, missingness preservation, stable tie-breaking and fail-closed conflict handling. Synthetic tests passed under the global Phase B research-safety workflow.

This is sufficient to support further **pre-data measurement-contract design**. It is not evidence of edge.

## H02 decision

**DO NOT FREEZE A DIRECTIONAL H02.**

Reason:

- the measurement layer is independently justified;
- the earlier directional continuation mapping was not established;
- no new independent mechanism currently specifies a directional sign, numeric threshold, window or venue/event-family mapping without target-outcome dependence.

A future prospective hypothesis may only be considered after its exact parameters and directional logic are independently justified before target data are inspected.

`H02_STATUS = NOT_AUTHORIZED`

## Authorized next action

The only justified next step is to draft a **non-directional prospective measurement contract** that freezes how macro-event microstructure state will be measured, including any required windows, sampling cadence, depth definition, skew tolerance and missing-data rules, using independent mechanism/operational justification rather than target outcomes.

That contract, by itself, must not contain a trading rule or directional edge claim.

## Final boundary

- target outcomes: **LOCKED**
- directional H02: **NOT AUTHORIZED**
- live trading: **FORBIDDEN**
- exchange mutation: **FORBIDDEN**
- MEXC Sep–Dec 2025: **LOCKED**
- main merge: **FORBIDDEN**
- Render deployment: **FORBIDDEN**

Final decision: **MEASUREMENT LAYER RETAINED. EDGE NOT ESTABLISHED. STOP BEFORE TARGET OUTCOMES OR H02 FREEZE.**
