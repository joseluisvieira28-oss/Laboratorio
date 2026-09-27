# PENDLE-PT-MATURITY-CONVERGENCE-001 — MECHANISM ADJUDICATION V0.1

Date: 2026-09-27  
Status: MECHANISM_DESCRIPTIVE / DISCOVERY_NOT_JUSTIFIED_AS_DEFINED  
Scientific verdict: NOT NO_EDGE / NO MARKET-OUTCOME TEST PERFORMED

## Decision

The exact question "does PT converge to its redemption anchor at maturity?" is not a suitable alpha Discovery question.

Pendle PT is contractually a principal claim. Official Pendle mechanics define PT as redeemable at maturity for the accounting asset, with the pre-maturity discount/appreciation being the fixed-yield mechanism itself.

Therefore observing raw convergence toward the maturity redemption value would primarily confirm contract mechanics, not establish a predictive market edge.

## Source result preserved

The source gate remains valuable:
- public market enumeration is available;
- immutable market identity includes chain/address/expiry/PT/accounting-asset metadata;
- historical timestamped market-state coverage is available;
- the V0.2 census found substantial Ethereum expired-market population and historical coverage;
- no convergence return, market return, price-direction rule or PnL was computed.

## Governance consequence

Do NOT open a Discovery for the exact raw-convergence question merely to demonstrate a contractual property.

Do NOT label this exact ID NO_EDGE. It was not economically falsified.

Do NOT retrofit an entry horizon, asset subset, yield threshold, fee assumption or "best maturity" after inspecting performance.

Any tradable successor requires:
1. a materially different economic question;
2. a new LAB_ID;
3. explicit treatment of variable yield, points/rewards and protocol risk;
4. point-in-time source authority;
5. a frozen independent validation path;
6. execution/friction evidence before any tradable-edge claim.

## Valid successor direction

A scientifically distinct question is whether the fixed yield embedded in PT contains a persistent premium or forecasting advantage versus the future variable-yield alternative after accounting for economically relevant rewards and risks.

That is not authorized here. It belongs under a new identity.

## Firewall

market_outcomes_opened=false  
convergence_statistic_computed=false  
pnl_computed=false  
protected_holdout_opened=false  
post_outcome_tuning=false  
live_trading=false  
orders=false  
exchange_mutation=false  
main_merge=false
