# One-shot staging evidence write test

Run the offline CI (V2, EPE, V3), then — on this specific commit message only — write a **synthetic** dry-run receipt to `evidence/deribit-v3-staging-2026-11-09` using the repository's own scoped GitHub Actions token.

The write test contains no real market observations, no Deribit API request, no prospective entries, no trading and no schedule. The evidence branch is NOT the production cohort branch.

Evaluation gate: inspect actual GitHub Actions job logs, remote SHA and the synthetic record via the GitHub connector. If the token lacks `contents:write` or branch rules prohibit the push, record the error and keep cloud activation NO-GO.
