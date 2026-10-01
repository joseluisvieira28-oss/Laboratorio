# CRYPTO LAB — AGENT ENTRYPOINT V0.1

Status: CONTROL-PLANE ONLY / NON-SCIENTIFIC / FAIL-CLOSED
Branch: crypto-lab-agent-os-v0.1

## Mission
This file is the universal entrypoint for agents working in the Crypto Lab repository. It does not replace experiment-specific freezes, receipts, closeouts, promotion policy, execution authority, or runtime truth.

## Mandatory startup sequence
1. Read `agent_os/AUTHORITY_INDEX_V0.1.json`.
2. Identify the exact LAB_ID / candidate / runtime / operator lane.
3. Resolve authority by exact identity and precedence, never by filename recency alone.
4. Read the exact frozen experiment protocol + canonical execution receipt + terminal closeout when they exist.
5. Check Governance V4 lifecycle rules.
6. Check Promotion Policy V3 only if promotion/adjudication is in scope.
7. For execution work, resolve the latest candidate/operator execution authority separately from scientific authority.
8. If authorities conflict and supersession is not explicit, FAIL CLOSED and produce an authority-conflict receipt before mutation.

## Scientific invariants
- No post-outcome tuning.
- No protected-data peek unless a valid prospective authority explicitly opens it.
- Never relabel SOURCE_BLOCKED / DATA_FAILURE / PROVENANCE_FAILURE / TECHNICAL_FAILURE / INSUFFICIENT_SAMPLE as NO_EDGE.
- Never resurrect a terminal exact experiment under the same identity.
- A materially changed mechanism requires a new immutable identity.
- Source feasibility is not edge evidence.
- Operational metadata is not scientific truth.
- No promotion credit from operator/execution forks unless a frozen scientific authority explicitly grants it.
- Preserve negative evidence and contamination boundaries.

## Repository invariants
- No merge to main without explicit operator authorization.
- Do not delete branches as a side effect of research.
- Technical fixes under the same scientific identity require proof that relevant outcomes remained unopened.
- Record exact branch/ref/SHA for authorities used in consequential decisions.

## Execution boundary
Execution authority and scientific authority are separate. Never infer live permission from Tier status alone. Never infer scientific promotion from successful live/operator execution.

See `agent_os/README.md` and the skills under `.claude/skills/`.
