---
name: authority-resolution
description: Mandatory whenever multiple freezes, policies, receipts, branches, execution authorities or runtime states could apply.
---

# Authority Resolution

Read AGENTS.md and agent_os/AUTHORITY_INDEX_V0.1.json first.

## Resolution order
- Scope by exact identity and authority plane.
- Prefer explicit supersession statements.
- Never infer supersession from a later date alone.
- Exact experiment science outranks summaries and registries for that identity.
- Execution/operator authority cannot promote science.
- Runtime truth cannot change frozen science.
- A global policy does not silently replace a candidate-specific prospective freeze.
- If unresolved same-plane conflict remains: FAIL_CLOSED.

## Required conflict receipt fields
- identity;
- plane;
- authority A branch/commit/path;
- authority B branch/commit/path;
- conflicting clauses;
- explicit supersession found: yes/no;
- safe action allowed while unresolved;
- prohibited mutation.
