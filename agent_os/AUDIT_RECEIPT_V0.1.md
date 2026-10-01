# CRYPTO LAB AGENT OS V0.1 — INITIAL AUDIT RECEIPT

Date: 2026-10-01
Scope: repository structure + authority routing only.
Scientific mutation: NONE.
Execution mutation: NONE.
Main merge: NONE.

## Findings

### F1 — Main is not the complete institutional truth
At audit time, main exposed only 53 tree paths while the repository contained 578 branches. Material governance, research and execution authorities live on non-main refs.

Risk: an agent that reads main only can make a materially incomplete decision.

Control: AGENTS.md requires exact-ref authority resolution.

### F2 — Authority planes are distributed
Lifecycle Governance V4, Promotion Policy V3, operator risk, candidate freezes, receipts, closeouts and runtime truth are not one document and must not be collapsed.

Control: five-plane model in agent_os/README.md.

### F3 — Newer date does not automatically mean supersession
Historical MEXC standing micro-live authority and later operator-lane authorities contain materially different execution envelopes. Later operator authority explicitly scopes/supersedes only where stated.

Risk: filename/date-based selection can apply the wrong leverage, risk or candidate state.

Control: explicit-supersession rule + fail-closed unresolved same-plane conflicts.

### F4 — Scientific and execution truth must remain independent
Governance V4 and Promotion V3 preserve scientific evidence; operator forks explicitly state no scientific credit.

Control: cross-plane override forbidden.

### F5 — Existing Governance V4 already supplies the correct scientific backbone
Agent OS does not invent a new death/promotion policy. It routes agents to frozen authorities and preserves exact-experiment precedence.

## Installed V0.1 controls
- AGENTS.md universal entrypoint
- agent_os/README.md
- agent_os/AUTHORITY_INDEX_V0.1.json
- scientific-governance skill
- authority-resolution skill
- /preflight-lab command
- /closeout-lab command

## Deferred deliberately
- no automated branch deletion/archive;
- no candidate reclassification;
- no runtime deployment;
- no order/exchange mutation;
- no main merge;
- no generated full 578-branch census yet;
- no CI enforcement until the routing model is reviewed against representative labs.

## Verdict
V0.1 is a useful control-plane foundation. Next legitimate expansion is a machine-readable lineage/candidate registry generator plus validation against representative cases: one terminal NO_EDGE, one SOURCE_BLOCKED, one Tier 2 candidate, one forward-only candidate, and one operator-execution lane.
