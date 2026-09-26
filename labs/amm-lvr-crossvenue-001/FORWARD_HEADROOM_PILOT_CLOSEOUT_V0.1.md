# AMM-LVR-CROSSVENUE-001 — FORWARD HEADROOM PILOT CLOSEOUT V0.1

**Date:** 2026-09-23  
**Scientific status:** NOT ADJUDICATED  
**Lifecycle:** PROSPECTIVE ENGINEERING / FORWARD EVIDENCE ACTIVE  
**Controlling protocol:** FORWARD_ECONOMIC_PROTOCOL_V0.1  
**Headroom freeze:** HEADROOM_EVALUATOR_FREEZE_V0.1  
**Canonical pilot run:** 35823661252  
**Artifact:** 10734341315  
**Artifact SHA-256:** be277e8fe0d81a78d7d16a777b9fd6c1e807761c5a7a370ef6029e681611df2a

## 1. Raw prospective capture

The protocol-compliant capture completed successfully before the headroom evaluator opened outcomes.

- 60 real DEX transaction events
- 62 swap logs
- 43 unique end-of-block × pool states in the evaluator
- 29 frozen pools available in the source implementation
  - 23 Uniswap V3
  - 6 Uniswap V2
- 60/60 recent transaction traces PASS
- 4 captured events with positive direct fee-recipient transfer
- Binance depth coverage:
  - T0: 111/111
  - +250 ms: 111/111
  - +1000 ms: 111/111
  - +3000 ms: 111/111
- source/runtime errors: 0

No capital, order, wallet or authenticated CEX endpoint was used.

## 2. Interim pre-inclusion headroom result

The evaluator used exactly the frozen notionals:
- 500 USDT
- 1,000 USDT
- 5,000 USDT

For each unique block×pool state it evaluated both directions at T0, froze the direction with the higher gross executable convergence value, and held that direction through the frozen latency buckets.

PRE_INCLUSION_HEADROOM deducts:
- exact DEX economics / fee;
- Binance Spot depth and 10 bps taker fee per actual hedge leg;
- frozen 300,000-gas Ethereum base-fee burn.

It does **not** set priority fee, direct/private builder payment or failed-inclusion probability to zero. Those layers remain UNBOUND.

### 500 USDT

| Latency | Evaluable | Positive headroom | Max USDT | Median USDT | Mean USDT |
|---|---:|---:|---:|---:|---:|
| T0 | 43 | 0 | -1.4589 | -2.0727 | -2.1241 |
| +250ms | 43 | 0 | -1.4589 | -2.0546 | -2.1236 |
| +1000ms | 43 | 0 | -1.4589 | -2.0294 | -2.1211 |
| +3000ms | 43 | 0 | -1.4553 | -2.0294 | -2.1216 |

### 1,000 USDT

| Latency | Evaluable | Positive headroom | Max USDT | Median USDT | Mean USDT |
|---|---:|---:|---:|---:|---:|
| T0 | 43 | 0 | -2.0014 | -3.0280 | -3.2388 |
| +250ms | 43 | 0 | -2.0014 | -3.0280 | -3.2374 |
| +1000ms | 43 | 0 | -2.0014 | -3.0116 | -3.2324 |
| +3000ms | 43 | 0 | -1.9942 | -2.9902 | -3.2337 |

### 5,000 USDT

| Latency | Evaluable | Positive headroom | Max USDT | Median USDT | Mean USDT |
|---|---:|---:|---:|---:|---:|
| T0 | 43 | 0 | -7.4621 | -11.2334 | -15.4019 |
| +250ms | 43 | 0 | -7.4621 | -11.2334 | -15.3920 |
| +1000ms | 43 | 0 | -7.4621 | -11.1276 | -15.3614 |
| +3000ms | 43 | 0 | -7.4621 | -11.1276 | -15.3781 |

Evaluator errors: 0.

## 3. Interpretation

This pilot is a strong negative engineering diagnostic for **ordinary post-block states** under the frozen headroom model.

All 43 observed states had negative PRE_INCLUSION_HEADROOM at every frozen notional and latency. Under this exact diagnostic, adding the still-missing non-negative competitive inclusion costs cannot turn any of those observed states positive.

This does **not** establish NO_EDGE for AMM-LVR-CROSSVENUE-001 because the controlling protocol prospectively froze:
- >=500 eligible events; AND
- >=14 UTC calendar days
before an economic verdict.

The pilot also evaluates end-of-block state rather than transaction-index intermediate state. Therefore a rare intrablock or event-shock dislocation can still exist without contradicting this result.

No token, pair, direction, notional, latency or cost rule may be changed because of this negative pilot.

## 4. Missing accessibility layer

The following remain unbound for a hypothetical independent searcher:
- priority fee required for inclusion;
- direct/private builder payment required for inclusion;
- failed-inclusion probability / opportunity cost.

Observed historical/current searcher transactions show that transaction-local priority and direct fee-recipient transfers can be measured when a transaction is included. Public relay probes did not provide a complete outsider view of private bundle economics or failed submissions.

Therefore:
- FULL_COST_PNL = NOT COMPUTED
- ACCESSIBILITY = UNPROVEN
- DISCOVERY_EVENT_CREDIT = 0
- QUASE DIAMANTE = NOT CLAIMED
- TIER 2 = NOT CLAIMED
- NO_EDGE = NOT CLAIMED

## 5. Next frozen action

Continue prospective collection without changing science until the controlling protocol's evidence horizon is satisfied.

Every future run must preserve:
- same six pair families;
- same notionals 500 / 1,000 / 5,000;
- same T0 / +250 / +1000 / +3000 ms latency buckets;
- same cost rules;
- no post-outcome tuning;
- no synthetic quote-grid promotion credit.

At >=500 eligible events and >=14 UTC calendar days, adjudication remains blocked unless every required full-cost layer is bound or conservatively bounded under an authority frozen before those outcomes are used.

No live trading, wallet mutation, exchange trading credential, paid-data purchase or main merge is authorized.
