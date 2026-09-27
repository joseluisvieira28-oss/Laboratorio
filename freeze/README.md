# Freeze

Every adversarial review begins from an immutable candidate freeze.

Minimum freeze fields are defined in `adversarial_review/review_bundle_schema_v0_1.json`.

A freeze must identify the candidate/version, mechanism, failure mode, controlling authority, sources, code commit, parameters, entry/exit rules, costs, protected periods and promotion gates.

If the freeze cannot be reconstructed, the review is `BLOCKED`.

If strategy science changes after outcomes are inspected, create a new candidate/version and a new freeze.
