# CRYPTO LAB V2 — GOVERNANCE FREEZE
Date: 2026-10-07
Status: PRE-OUTCOME GOVERNANCE / RESEARCH-ONLY
Authority: applies to new research families only when explicitly adopted by that family.
Main branch: MUST NOT be changed by this freeze.
Trading: NO live trading, NO orders, NO wallet/exchange mutation.

## 0. Purpose
Crypto Lab V2 separates four questions that V1 sometimes collapsed:
1. Is there an economically coherent mechanism?
2. Is the mechanism accessible to this operator?
3. Can the proposed experiment detect an economically relevant effect?
4. What does the observed result actually justify?

A failed significance test is not automatically NO_EDGE.
A scientifically real effect is not automatically ACCESSIBLE.
An inaccessible edge is not the same as no edge.
A small/underpowered sample is not the same as a failed source gate.

## 1. Principles preserved from V1
The following remain mandatory:
- fail-closed;
- pre-outcome freeze;
- one primary design per scientific shot;
- no post-outcome rescue;
- no silent horizon/subset/venue switching;
- source provenance before outcomes;
- untouched holdout/forward where claimed;
- no retroactive lowering of gates;
- no live-trading authority created by research evidence.

The single-shot is spent only after the POWER GATE authorizes the experiment.

## 2. Gate order
Every new family follows this order:

IDEA
→ ECONOMIC MECHANISM & ACCESSIBILITY GATE
→ SOURCE GATE
→ POWER GATE
→ PRE-OUTCOME FREEZE
→ DEVELOPMENT
→ RESULT ADJUDICATION
→ OOS/HOLDOUT/FORWARD if authorized
→ EXECUTION FEASIBILITY
→ separate MICRO-LIVE authority, if ever granted

No later gate may repair a failed earlier gate by changing the scientific claim.

## 3. Economic Mechanism & Accessibility Gate
Before any backtest, answer all six:

P1 SERVICE — What economically valuable service are we providing?
Examples: immediacy, risk transfer, liquidity, inventory absorption, carry, intermediation.

P2 RISK — What concrete risk are we paid to carry?
Examples: inventory, tail, liquidation, counterparty, funding, regulatory, execution.

P3 PERSISTENCE — What friction or constraint prevents complete arbitrage?
Examples: capital, mandate, regulation, capacity, settlement, latency, risk appetite.

P4 BILATERAL RATIONALITY — Why can both sides rationally transact?
Do not require the counterparty to be “irrational” or to knowingly lose expectancy.

P5 COMPETITION — Why do larger/faster players not eliminate the premium completely?
“they did not notice” is not acceptable without evidence.

P6 ACCESSIBILITY — Can the operator capture the mechanism with the actual capital, venue access,
data, latency, APIs, margin, legal constraints and automation available?

Possible gate outcomes:
- MECHANISM_PASS
- MECHANISM_UNSUPPORTED
- EDGE_EXISTS_BUT_INACCESSIBLE
- ACCESSIBILITY_UNRESOLVED

An inaccessible edge may remain scientifically interesting but cannot be promoted as an operator edge.

## 4. Economic hurdle H
There is NO universal H = 2×fees and NO universal +10 bps buffer.

Each family freezes:
- the estimand (prefer NET return after modeled costs);
- cost model and uncertainty;
- minimum economically meaningful net edge;
- risk/capital charge when relevant;
- H, in the same units as the estimand;
- rationale for H.

If the estimand is gross return, the gross hurdle must explicitly include costs and required net compensation.
H must be fixed before outcomes and cannot be reduced after seeing results.

## 5. Source Gate
Source Gate asks whether the claim can be reconstructed honestly, not whether the sample is large enough.

Required:
- primary or defensible source provenance;
- timestamp semantics suitable for the hypothesis;
- enumerability rule fixed before outcomes;
- treatment/signal binding rule fixed before outcomes;
- no outcome-derived event inclusion;
- data availability documented.

Possible outcomes:
- SOURCE_PASS
- SOURCE_BLOCKED
- DESIGN_INVALID_PRE

Sample size/power failure is NOT SOURCE_BLOCKED.

## 6. Power Gate
Power is evaluated before opening outcomes.

Required freeze fields:
- primary estimand;
- directionality;
- H;
- alpha allocation;
- target power (default policy: 0.80 unless a pre-outcome justification freezes another value);
- dependence/clustering unit;
- nuisance variance source;
- N_eff estimate;
- design_alternative_theta, with design_alternative_theta strictly beyond H in the tested direction;
- power_at_design_alt;
- method.

Preferred method:
- simulation / block bootstrap using non-outcome placebo, pre-period, or otherwise outcome-blind nuisance estimates.

Power cannot be defined at the superiority boundary H itself: if H0 is theta <= H, power at theta = H is alpha by construction. Therefore each family must freeze a scientifically/economically justified design alternative theta_design beyond H. For a positive edge, theta_design > H; for a negative edge, theta_design < -H.

Analytical planning approximation for a positive superiority test:
N_eff ≈ [((z_alpha + z_beta) × sigma) / (theta_design - H)]^2
where theta_design - H is the detectable margin beyond the economic hurdle. Heavy tails, clustering and autocorrelation should be modeled where material.

There is NO universal minimum N and NO universal “100 shocks” rule.

Power outcomes:
- TEST_AUTHORIZED: power_at_design_alt >= target and prior gates PASS.
- UNDERPOWERED_PRE: do not open outcomes.
- UNDERPOWERED_BANKED: accumulate genuinely new forward data under the unchanged spec.
- DESIGN_INVALID_PRE: proposed experiment cannot answer the claim.

Power must never be recomputed from the observed effect (“observed power”).
Blind re-estimation of nuisance quantities such as N_eff, attrition, ICC or residual variance is allowed if the protocol froze that possibility.

## 6.1 Power-vs-evidence firewall
The design alternative theta_design is for sample-size planning only. It is not a second promotion hurdle, cannot be changed after outcomes, and must never be chosen from the observed effect. Result adjudication still uses the frozen economic hurdle H.

## 7. Result adjudication
### 7.1 Positive directional edge
For a positive edge with hurdle H:
H0: theta <= H
H1: theta > H

SURVIVES requires evidence that theta exceeds H under the frozen alpha rule.
Operationally, a compatible lower confidence bound above H is sufficient.

### 7.2 Negative conclusion for a positive-edge claim
NO_EDGE_AT_H requires evidence that an economically relevant positive edge can be excluded.
Operationally:
upper confidence bound < H

This means “this design excludes a positive effect at least as large as H”.
It does NOT mean theta = 0 and does NOT mean the mechanism is universally false.

### 7.3 Two-sided equivalence
Only when both positive and negative magnitudes are relevant:
H0: theta <= -H OR theta >= +H
H1: -H < theta < +H

NO_EFFECT_OF_MAGNITUDE_H requires the confidence interval to lie inside (-H, +H).

### 7.4 Inconclusive
If the data neither support theta > H nor exclude theta >= H:
INCONCLUSIVE

INCONCLUSIVE is not counted as scientific evidence against the class.

Allowed post-development statuses:
- SURVIVES
- NO_EDGE_AT_H
- INCONCLUSIVE
- MECHANISM_UNSUPPORTED
- EDGE_EXISTS_BUT_INACCESSIBLE
- EXECUTION_BLOCKED
- DESIGN_INVALID
- SOURCE_BLOCKED

## 8. Prospective forward accumulation
Legitimate:
- spec remains unchanged;
- new observations did not exist at the original freeze;
- the sequential/forward plan was frozen before the new look;
- result is labeled confirmation/non-confirmation, not new discovery.

Forbidden rescue:
- changing horizon, subset, venue, threshold, event definition or direction after seeing outcomes;
- adding filters because the curve looked better;
- relabeling a failed development result as a new hypothesis without a genuinely new economic mechanism.

## 9. Multiplicity ledger
Every family must have:
- economic_hypothesis_id;
- primary_claim_id;
- trial_index;
- analysis lineage;
- alpha/FDR policy;
- all material variants recorded, including failures.

Rules:
- one primary confirmatory claim per scientific shot;
- repeated looks require a pre-frozen sequential alpha/e-value rule;
- discovery-wide selection must account for all tried variants;
- ensembles must count the full candidate universe, not only survivors;
- holdout evidence is not treated as independent if the holdout influenced model choice.

No single universal correction is mandated:
- strict confirmatory families may use alpha spending / family-wise control;
- broad discovery screens may use FDR;
- strategy-selection ensembles should use selection-aware procedures (e.g. SPA/Reality Check/DSR where appropriate).
The method must be frozen before the relevant outcomes.

## 10. Ensemble Lab
Combining weak signals is allowed only if:
- each member has a pre-existing economic mechanism and frozen transformation;
- the eligible member universe is declared before ensemble evaluation;
- inclusion is not based on the final evaluation set;
- weights/risk scaling are frozen before holdout/forward;
- simple equal-risk / 1/N style weights are preferred unless an optimization procedure is itself nested and pre-registered;
- costs are netted realistically;
- correlation/diversification claims are evaluated out of sample;
- all tried member sets/configurations enter the multiplicity ledger.

No “best combination after trying 200 combinations” may be called confirmatory.

## 11. Cemetery readjudication
Legacy outcomes may be used ONLY for triage.

Legacy families can be re-labeled:
- LEGACY_NEGATIVE_POWER_UNKNOWN
- LEGACY_NEGATIVE_VALID_AT_H
- UNDERPOWERED_SUSPECT
- SOURCE_BLOCKED
- MECHANISM_UNSUPPORTED
- EXECUTION_BLOCKED
- FORWARD_RETEST_CANDIDATE

Historical performance can prioritize which family deserves future data.
It cannot retroactively produce SURVIVES.

Any confirmation after readjudication requires:
- unchanged or newly pre-registered spec;
- genuinely new/untouched forward data;
- new multiplicity entry;
- no reuse of the old outcome as confirmation.

## 12. Search stop rule
There is NO universal K=8, K=12 or other magic family count.

Two statements are distinct:

SEARCH_STOPPED_ECONOMICALLY
= the expected marginal value of testing the next family is below its marginal research/opportunity cost,
or the operator explicitly ends the research budget.

NO_ACCESSIBLE_EDGE_FOUND_AMONG_TESTED_FAMILIES
= descriptive statement about the tested inventory.

NO_ACCESSIBLE_EDGE_IN_THIS_SEARCH_SPACE
= allowed only if the search space was exhaustively and defensibly enumerated and covered.

Priors are maintained by economic class. Failures in non-exchangeable classes do not automatically reduce the prior of a distinct class.

## 13. Non-authorities
This freeze does NOT:
- authorize live trading;
- authorize orders;
- authorize account reads, wallets, deposits or withdrawals;
- modify existing micro-live authority;
- merge anything to main;
- promote any legacy family.

## 14. Adoption rule
A family is “V2 compliant” only when its own branch contains:
1. a completed PREOUTCOME_GATE_V2 JSON receipt;
2. validator PASS;
3. a commit hash that freezes the receipt before outcome access.

Until then, the family remains governed by its existing authority.
