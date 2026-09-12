# Macro Shock Mechanism Review V1

Status: **CLOSED REVIEW — NO NEW DIRECTIONAL HYPOTHESIS AUTHORIZED**

## Scope

This review synthesizes only already-observed internal results plus independent external literature. It does **not** retune MSM_H01, does not reinterpret descriptive subgroups as edges, and does not authorize another test on the same 2026 holdout.

Internal evidence considered:

- FOMC V0 diagnostic study.
- CPI/NFP V0.2 robust-control replication.
- Macro Shock Microstructure Lab V0.1 prospective 2026 holdout.
- Existing News Shock provenance and raw-surprise work.

## 1. What replicated consistently

Across internal studies, scheduled U.S. macro announcements consistently produced a strong abnormal market-activity regime:

- FOMC V0 showed large event/control volume and trade-count ratios for BTC and ETH, plus strong short-horizon taker-flow persistence.
- CPI/NFP V0.2 replicated sharp activity expansion, with CPI especially strong, and high 5→15 minute taker-flow persistence.
- Independent 2026 literature reports that crypto volatility, trading volume and bid-ask spreads rise sharply at macro announcement times and remain elevated for roughly the first 30 minutes; order flow is implicated in price discovery.

**Mechanism conclusion A:** `MACRO_ANNOUNCEMENT -> ABNORMAL_ACTIVITY_LIQUIDITY_PRICE_DISCOVERY_REGIME` is strongly supported.

## 2. What did not replicate as a directional edge

The prospective MSM_H01 asked a stricter question: whether same-sign taker-flow persistence across 0–5 and 5–15 minutes predicts same-direction 15–30 minute continuation better than matched non-event controls.

Frozen 2026 result:

- classification: `INSUFFICIENT_SAMPLE`
- resolved cases: 28 vs frozen minimum 30
- distinct event dates: 20 vs frozen minimum 20
- continuation-rate difference: **-0.09208972845336488**
- cluster-bootstrap 95% CI: **[-0.30315789473684207, 0.10963066853669945]**
- 5,000 bootstrap repetitions

The point estimate is negative and the confidence interval crosses zero. Therefore there is no scientific basis to rescue or extend the original continuation hypothesis.

**Mechanism conclusion B:** `PERSISTENT_TAKER_FLOW -> SUBSEQUENT_15_30M_SAME_DIRECTION_CONTINUATION` is **not established**.

## 3. Descriptive subgroup audit — non-authoritative

These are reported only to prevent future accidental cherry-picking. They are not hypothesis tests and cannot authorize a new edge.

Approximate paired descriptive continuation-rate differences from the 28 resolved cases:

- CPI: **-23.70 pp**
- FOMC: **-22.14 pp**
- NFP: **+7.24 pp**
- BTCUSDT: **-2.72 pp**
- ETHUSDT: **-17.38 pp**

The NFP subgroup is the only family with a positive descriptive point estimate, but selecting NFP now would be post-outcome subgroup selection and is explicitly forbidden as a rescue path.

## 4. External evidence and what it actually supports

Independent 2026 work supports a robust event-risk mechanism rather than a simple continuation rule:

- Kroner, Mohammed and Vega (Federal Reserve Board / SSRN, 2026) find sharply elevated volatility, volume and spreads around U.S. monetary-policy, inflation and labor announcements, with effects lasting up to about 30 minutes and order flow playing a role in price discovery.
- A 2026 Finance Research Letters FOMC event study reports large post-statement increases in BTC/ETH absolute returns and trading volume using matched controls.
- 2026 high-frequency crypto research also emphasizes rapid algorithmic price discovery and heterogeneous reactions across macro categories and sentiment states.

These findings support modeling **state changes in volatility, liquidity and price-discovery intensity**. They do not independently justify the exact MSM_H01 15–30 minute continuation mapping.

## 5. H02 decision

Decision: **DO NOT FREEZE A NEW DIRECTIONAL H02 NOW.**

Reason:

1. The strongest replicated evidence concerns event-regime intensity, not future directional continuation.
2. The prospective continuation test did not produce supportive evidence.
3. The only apparently favorable subgroup would require post-outcome selection.
4. Any immediate directional H02 would therefore risk being a disguised rescue of MSM_H01.

## 6. Highest-priority next research direction

The next justified research program is **not another direction signal**. It is a prospective microstructure-state study designed to answer whether macro-event regimes create an exploitable change in execution conditions or risk, for example:

- spread widening and recovery,
- realized volatility expansion and decay,
- depth/liquidity depletion and refill,
- cross-venue price-discovery lead/lag,
- event-specific slippage and adverse-selection risk.

This should require genuinely richer market-microstructure data than the existing 1-minute outcome framework. No threshold, venue, symbol, event family or execution rule should be frozen until its data provenance and ex-ante rationale are established.

A future trading hypothesis may be created only if that mechanism study yields an independently justified, prospectively testable relationship on untouched data.

## 7. Governance

- No retest of MSM_H01 on the same 2026 holdout.
- No lowering 30 resolved cases to 28.
- No CPI/NFP/FOMC cherry-pick.
- No BTC/ETH cherry-pick.
- No window or threshold optimization using 2026 outcomes.
- No live trading authorization.
- No exchange mutation.
- No merge to main.
- No Render deployment.

Final decision: **MSM_H01 CLOSED. MECHANISM RETAINED. DIRECTIONAL EDGE NOT ESTABLISHED. H02 NOT AUTHORIZED.**
