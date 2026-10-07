# CLAUDE × DEEPSEEK × CRYPTO LAB — METHOD ADJUDICATION V0.1
Date: 2026-10-07
Decision owner: Crypto Lab governance, not either challenger.

## ADOPTED
### From Claude
- Ex-ante POWER GATE before outcomes.
- MDE/power tied to an economic hurdle H, not a fixed sample count.
- UNDERPOWERED_PRE and UNDERPOWERED_BANKED as non-negative states.
- NO_EDGE must be design/H-specific.
- Prospective accumulation of genuinely new data under unchanged specs.
- Ensemble research can combine weak mechanistically distinct signals only with selection-aware governance.
- Legacy outcomes may prioritize a retest but cannot confirm it.
- Preserve single-shot, pre-outcome freeze, no rescue, fail-closed and untouched holdout logic.

### From DeepSeek
- Separate scientific existence from operator accessibility.
- Mandatory economic mechanism questions: service, risk, friction, bilateral rationale, competition barrier, capture path.
- EDGE_EXISTS_BUT_INACCESSIBLE is distinct from NO_EDGE.
- Public/known edges can persist because of risk, capital, mandate, regulation, capacity or execution frictions.
- Research stopping is partly an economic-budget decision, not a magic p-value rule.
- Priors should be maintained by economic class, not blindly across non-exchangeable hypotheses.
- Source honesty: marketing/commercial claims cannot be promoted to scientific evidence without independent support.

## MODIFIED BEFORE ADOPTION
- TOST is reserved for true two-sided equivalence. Directional edge detection/exclusion uses the appropriate one-sided hurdle test/CI logic.
- H is parametrized per family. It is not universally 2× costs or costs+10 bps.
- Target power defaults to 80% as a policy choice, with pre-outcome justification required for deviations.
- Multiple testing is handled by a frozen policy suited to the task (FWER/alpha spending, FDR, selection-aware tests), not one universal Bonferroni rule.
- Ensemble size has no magic maximum; complexity must be frozen and paid for in selection/multiplicity.
- Search stopping separates “we stop spending research budget” from “we proved the space empty”.

## REJECTED
- Universal N >= 12, N >= 40 or N >= 100 as scientific sufficiency.
- Universal K >= 8 or K >= 12 families before stopping.
- Universal H = 2× costs.
- Universal +10 bps safety buffer.
- Observed power calculated from the observed effect.
- Non-significance => NO_EDGE.
- “All public timestamped mechanisms have already been arbitraged away.”
- “The only rational conclusion is to stop.”
- “An edge requires the counterparty to be irrational.”
- Retroactive resurrection by lowering costs or changing horizon on already-open outcomes.
- Killing a short holdout merely because a confidence lower bound is below zero when the design cannot possibly estimate the target with that precision.
- Treating commercial/marketing yield claims as priors without source-quality discounts.

## NEW CANONICAL EVIDENCE STATES
Pre-outcome:
- MECHANISM_UNSUPPORTED
- ACCESSIBILITY_UNRESOLVED
- EDGE_EXISTS_BUT_INACCESSIBLE
- SOURCE_BLOCKED
- UNDERPOWERED_PRE
- TEST_AUTHORIZED

Post-development:
- SURVIVES
- NO_EDGE_AT_H
- NO_EFFECT_OF_MAGNITUDE_H (only true two-sided equivalence)
- INCONCLUSIVE
- EXECUTION_BLOCKED
- DESIGN_INVALID

Legacy-only:
- LEGACY_NEGATIVE_POWER_UNKNOWN
- LEGACY_NEGATIVE_VALID_AT_H
- UNDERPOWERED_SUSPECT
- FORWARD_RETEST_CANDIDATE

## LAB METRICS V2
The lab should report:
1. fraction of attempted families killed before outcomes for mechanism/accessibility/source reasons;
2. fraction reaching Power Gate;
3. fraction TEST_AUTHORIZED with power >= frozen target;
4. SURVIVES / NO_EDGE_AT_H / INCONCLUSIVE counts;
5. number of independent economic hypotheses and total material variants tried;
6. source-blocked vs underpowered vs execution-blocked counts;
7. forward confirmation rate of development survivors;
8. research cost per scientifically adjudicated family.

A healthy lab is not the one with the most survivors.
It is the one that minimizes false promotion while also avoiding false “NO_EDGE” labels caused by an experiment that could never answer the question.
