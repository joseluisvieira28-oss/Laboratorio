---
description: Create a Governance V4-compatible closeout/tombstone without rewriting science.
---

For the exact lab:
1. Resolve authority with /preflight-lab logic.
2. Preserve the canonical scientific classification exactly.
3. Record LAB_ID/MVE_ID, parent mechanism, frozen authority, canonical evidence hash, outcome-open status, closure reason, forbidden rescues, unopened protected data, reopening trigger, successor permissibility and contamination boundary.
4. Keep scientific verdict, operational lifecycle and mechanism state separate.
5. BLOCKED/DATA/PROVENANCE/TECHNICAL/INSUFFICIENT states remain non-scientific; never convert them to NO_EDGE.
6. Do not delete evidence or branches and do not merge main.
