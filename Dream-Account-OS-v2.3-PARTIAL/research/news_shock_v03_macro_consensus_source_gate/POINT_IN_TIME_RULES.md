# Point-in-Time and Anti-Leakage Rules

1. Scope is 2021–2024. Reject 2025 and 2026 records at schema validation.
2. Outcomes, prices, returns, PnL and post-event market reactions are prohibited inputs.
3. Event membership comes from the BLS release calendar, not data availability or outcome.
4. T0 uses `America/New_York` with DST-aware conversion.
5. Consensus evidence must be strictly pre-T0 and field-explicit.
6. A post-release article cannot be sole proof of a pre-release value.
7. Retrieval timestamp is never a substitute for publication timestamp.
8. Same-day date-only evidence fails unless a trusted archive proves a pre-T0 capture.
9. Preserve raw bytes, URL, HTTP metadata where available, retrieval UTC and SHA-256.
10. Preserve original publication and modification timestamps; later edits create a new
    version and cannot silently replace the old one.
11. Actuals come from the first archived BLS release. Current series values are validators,
    not substitutes.
12. CPI values must use the release's stated precision. Do not recompute rounded changes
    from revised index levels.
13. NFP revisions include only information printed in that release. Later revisions are
    future knowledge.
14. Missing values remain null with a reason code; never coerce missing to zero.
15. Every value carries its own evidence reference. Mixed-source records are labelled.
16. Duplicate `event_id` or duplicate family/release timestamp is a hard failure.
17. Release date, reference period and event family must agree with the BLS schedule and
    release heading.
18. Conflicting authoritative values produce `SOURCE_CONFLICT`, not averaging.
19. A source snapshot with a hash change after acceptance produces
    `SOURCE_VERSION_DRIFT_BLOCKED` until reconciled.
20. Corpus acceptance is all-or-explicit: incomplete events may remain in the manifest but
    cannot enter a surprise calculation.

## Required status codes

- `COMPLETE_SINGLE_SOURCE`
- `COMPLETE_MIXED_SOURCE`
- `CONSENSUS_PROVENANCE_INCOMPLETE`
- `ACTUAL_PROVENANCE_INCOMPLETE`
- `PUBLICATION_TIME_UNRESOLVED`
- `SOURCE_CONFLICT`
- `SOURCE_VERSION_DRIFT_BLOCKED`
- `OUT_OF_SCOPE_BLOCKED`

No source failure may be labelled `NO_EDGE`.
