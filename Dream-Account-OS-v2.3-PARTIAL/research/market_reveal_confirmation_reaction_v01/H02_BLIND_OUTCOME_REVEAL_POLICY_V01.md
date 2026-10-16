# MRCR H02 — Blind Outcome Reveal Policy V0.1
Status: FROZEN / TARGET OUTCOMES LOCKED
Date: 2026-09-25

The outcome-reveal decision may use only:
- official eligible event-family counts;
- decision-time ACCEPTANCE / REJECTION / ABSTAIN labels;
- distinct classified event IDs;
- whether the frozen 2027 calendar has been exhausted.

The reveal gate may not read:
- future returns;
- PnL;
- economic scores;
- target-direction success rates;
- subgroup outcomes.

Actions are deterministic:

1. All event-family and state-count minima met:
   READY_FOR_SINGLE_OUTCOME_REVEAL.

2. Minima not met and official 2027 calendar not exhausted:
   HOLD_OUTCOMES_LOCKED_CONTINUE_BLIND_COLLECTION.

3. Minima not met at official 2027 calendar exhaustion:
   CLOSE_INSUFFICIENT_SAMPLE_WITHOUT_OUTCOME_REVEAL.

The single reveal still requires the separate TARGET_OBSERVATION_OPEN authority
and exact final protocol/calendar/implementation bindings.

No repeated outcome looks are permitted.
