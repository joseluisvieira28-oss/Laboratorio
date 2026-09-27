# ETH-BLOCKSPACE-STATE-TRANSITION-001 — REFEREE RULES V0.1

Date: 2026-09-27
Status: FROZEN BEFORE SUCCESSOR ECONOMIC OUTCOMES

Referee adjudicates only the new successor identity.

Possible states:
- SOURCE_BLOCKED
- INSUFFICIENT_MATURITY
- FORWARD_NO_EDGE
- FORWARD_SURVIVES
- CONTAMINATION_FAILURE
- PROVENANCE_FAILURE

Hard precedence:
1. lookahead / protected-parent access / post-outcome rule change => CONTAMINATION_FAILURE;
2. source identity or timing failure => PROVENANCE_FAILURE;
3. valid data below maturity => INSUFFICIENT_MATURITY;
4. valid mature economics failing frozen BASE/STRESS requirements => FORWARD_NO_EDGE;
5. valid mature economics passing frozen requirements => FORWARD_SURVIVES.

FORWARD_SURVIVES is not Diamond, Tier 1, micro-live or capital authority. Any promotion remains a separate policy decision.
