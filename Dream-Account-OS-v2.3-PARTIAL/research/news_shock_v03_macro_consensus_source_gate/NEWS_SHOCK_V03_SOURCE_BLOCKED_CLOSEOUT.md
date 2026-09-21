# News Shock Lab V0.3 — Source-blocked closeout

Closeout date: 2026-09-21  
Final status: **FORMALLY CLOSED — SOURCE_BLOCKED**

## 1. Original hypothesis

V0.3 proposed testing whether the direction of a macroeconomic surprise—defined from the
difference between the first-release value and the market consensus available before the
official release—has a reproducible relationship with a later market response. CPI required
headline and core inflation; Employment Situation/NFP required payrolls, unemployment and
average hourly earnings, including the release-time revision context.

This closeout does not test, estimate or reinterpret that hypothesis. It records that the
critical consensus input could not be established under the frozen evidence standard.

## 2. Why point-in-time consensus was mandatory

A surprise is not identifiable from an actual alone. Its expectation leg must be the value
that market participants could have known strictly before T0. A current historical calendar
row, a post-release article saying what economists had expected, or a reconstructed forecast
can contain future edits or hindsight. Without field-level pre-T0 provenance, the sign and
magnitude of a purported surprise are not scientifically auditable.

The frozen rule therefore required, for every consensus field: event identity, field
identity, value, publication or snapshot timestamp strictly before T0, timezone, source
provenance, and immutable versioning or an audit trail that distinguishes the contemporary
forecast from later corrections.

## 3. Initial Source Gate

The initial gate ended `SOURCE GATE: PARTIAL`.

- BLS archived CPI and Employment Situation releases were accepted as the authority for
  release time, first-release actuals and revisions known at release.
- ALFRED was accepted only as a vintage cross-check, not as consensus authority or the
  release-instant authority.
- Pre-release Reuters polls and timestamped institutional research were potentially usable
  field by field, but complete 2021–2024 coverage was not demonstrated.
- Mutable calendar pages, post-release reports, snippets, undated material and datasets
  without provenance were not accepted as pre-T0 evidence.

The gate authorized a manifest-first, outcome-blind 2021 census; it did not authorize a
V0.3 backtest.

## 4. Frozen 2021 census

The complete census enumerated all 24 scheduled 2021 releases before consensus research:
12 CPI and 12 Employment Situation/NFP events. It preserved 108/108 official actual and
release-time revision fields, while accepting 0/108 consensus fields. All 24 events remained
`CONSENSUS_PROVENANCE_INCOMPLETE`; complete-event coverage was 0/24.

The result was `2021 CENSUS: BLOCKED`. Missing values remained missing. No difficult event
was omitted, no post-release report was promoted, and no criterion was weakened to improve
coverage.

## 5. Institutional capability probe

The probe froze the sample deterministically before checking institutional documentation:

- CPI: `US_CPI_2021-01-13`, T0 `2021-01-13T13:30:00Z`;
- NFP: `US_NFP_2021-01-08`, T0 `2021-01-08T13:30:00Z`.

It demonstrated pre-T0 consensus for 0/4 required CPI fields and 0/4 required NFP fields.
No accessible test or public documentation chain proved both field completeness and a
pre-T0 version that can be audited today. The frozen decision was therefore
`D — NO DEFENSIBLE SOURCE IDENTIFIED`, not an assertion that a particular paid product is
known to solve the problem.

## 6. Sources evaluated

The source work covered these distinct roles and candidates:

| Source or family | Relevant capability | Closeout disposition |
|---|---|---|
| BLS archived schedules/releases | Official T0, first-release actuals, NFP revisions known at release | Valid actual authority; not a consensus source |
| FRED/ALFRED | Vintage corroboration | Validation only; not consensus authority |
| Reuters public pre-release material | Poll/expectation reporting | Potentially usable only with complete pre-T0 evidence; no accepted 2021 fields |
| Institutional research publications | Dated analyst forecasts | Potentially usable field by field; no field-complete accepted route |
| Reuters/LSEG Workspace/Eikon and Refinitiv datasets | Licensed news/calendar/poll products | Documentation insufficient for the exact pre-T0 field-level test; no entitlement available |
| Bloomberg | Terminal/enterprise economic calendar | Documentation insufficient; no entitlement available |
| FactSet | Economic consensus/calendar | Documentation insufficient; no entitlement available |
| Dow Jones/Factiva | Timestamped publication archive | Partially capable for article chronology; field completeness not established |
| Econoday | Institutional calendar/feed | Documentation insufficient for forecast vintage timestamps |
| Haver Analytics | Macro databases and revisions | Consensus record and pre-T0 versioning not demonstrated |
| Macrobond / Consensus Economics | Point-in-time series and forecast publications | Partially capable, but target release/field coverage not demonstrated |
| Trading Economics | Historical Economic Calendar API | Historical forecast timestamp/vintage not demonstrated; not point-in-time safe for this gate |
| Public calendar aggregators and mirrors | Historical actual/forecast/previous display | Discovery or validation only where rows may be mutable or source chain is incomplete |
| Wayback/archives | Preserved page chronology | Usable only when snapshot precedes T0 and payload is complete; a later snapshot is not proof |
| GitHub/Kaggle datasets and search snippets | Leads to possible sources | Discovery only; never authority without an auditable source chain |

## 7. Exact reason for rejection and blockage

The blocking defect is narrow and explicit: no route demonstrated, for both frozen events,
all required consensus fields together with a timestamp or vintage strictly before T0,
timezone, event/field identity, provenance, and immutable versioning or an audit trail.

Some candidates expose a historical forecast value but not when that forecast version was
published. Others preserve publication chronology but do not establish all required fields
or a consistent consensus methodology. Commercial claims without a target-event export were
not promoted to technical evidence. Access alone was not treated as proof that a product
would pass.

## 8. Anti-hindsight guarantees preserved

- Consensus timestamps must be strictly earlier than the actual publication time, or the
  scheduled T0 when no independently documented actual-publication exception exists.
- `America/New_York` controls the 08:30 release clock; UTC conversion is DST-aware.
- Revised actuals, revised consensus, current mutable rows and post-release articles cannot
  replace a contemporaneous record.
- Date-only evidence cannot pass a same-day 08:30 cutoff.
- Missing fields remain null and are never converted to zero or inferred.
- Duplicate/release-date mismatches fail validation.
- Raw or normalized evidence is identified honestly and hashed; normalized-record hashes
  are not represented as hashes of unavailable vendor bytes.
- No price, return, volume, yield response, PnL or other outcome informed source selection.
- No 2025, 2026 or protected holdout was opened for this source investigation.

## 9. Tests executed

The repository tests enforce the frozen 24-event universe, unique identifiers, 2021-only
scope, DST-correct ET/UTC conversion, strict pre-T0 consensus timestamps, null preservation,
rejection of post-release evidence, absence of market outcomes, required provenance/hashes,
the deterministic two-event institutional sample, allowed source classifications, and the
exact decision `D — NO DEFENSIBLE SOURCE IDENTIFIED`.

The closeout adds machine-readable guards for the terminal status, untested-hypothesis
interpretation, exact reopening sample and fields, immutable reopening requirements, and
reference commit. Test results are recorded in the closeout commit message and repository
history; passing tests validate artifact consistency, not source availability.

## 10. Branches, commits and receipts

| Stage | Branch | Reference |
|---|---|---|
| Initial Source Gate | `news-shock-v03-macro-consensus-source-gate` | `908e409732437c549d3cb1d05dd580e5d38bd5db` |
| 2021 census | `news-shock-v03-2021-consensus-census` | `a8b0d09c`, `fc4f7a1a` |
| Institutional probe | `news-shock-v03-institutional-source-probe` | `4f92b072`, `bed52332`; remote head `4460415c0c89e6b1b1edf39291f8bf1cf22c7c72` |
| Formal closeout | `news-shock-v03-source-blocked-closeout` | closeout commit on this branch |

The evidence chain is preserved in the source-gate directory: event manifest, census and
field-coverage CSVs, source-yield/conflict/unresolved reports, institutional source matrix,
single-event probe reports, access constraints, selection freeze receipt, documentation
receipt, and SHA-256 manifests.

## 11. What remains scientifically valid

**V0.2: SCIENTIFICALLY VALID DESCRIPTIVE RESULT**

V0.2 remains a descriptive result within its own frozen scope. This V0.3 source failure does
not revise, extend or invalidate it.

The following V0.3 infrastructure also remains valid: BLS first-release authority,
manifest-first enumeration, explicit T0 and DST handling, field-level evidence records,
null preservation, provenance hashing, outcome-blind source assessment, and fail-closed
acceptance controls.

## 12. What cannot be claimed

**V0.3: SOURCE_BLOCKED**

`SOURCE_BLOCKED` must not be converted into `NO_EDGE` or `FAILED HYPOTHESIS`. The V0.3
hypothesis was not tested because the critical point-in-time consensus input could not be
established defensibly. No V0.3 surprise corpus, directional result, backtest, edge estimate,
threshold, weight, transformation or trading conclusion is authorized.

## 13. Explicit reopening condition

V0.3 may be reopened only after one of these legitimate new inputs exists: a sample export,
an already-authorized institutional entitlement, or a new public source. The first future
validation must reuse exactly the same two events—never easier replacements—and demonstrate:

- for `US_CPI_2021-01-13`: headline MoM, headline YoY, core MoM and core YoY consensus;
- for `US_NFP_2021-01-08`: payrolls, unemployment, AHE MoM and AHE YoY consensus;
- for every field: consensus value, timestamp/vintage strictly before T0, timezone, event
  identifier, provenance, and immutable version or auditable version history.

Until all requirements pass on both events, no new census, 2022–2024 extension, 2025/2026
access, V0.3 outcome analysis, backtest, purchase/trial, source-hierarchy change or merge to
`main` is authorized.

## Terminal record

**NEWS SHOCK LAB V0.3: FORMALLY CLOSED — SOURCE_BLOCKED**

No further cycles are authorized for this hypothesis unless the reopening condition above
is triggered.
