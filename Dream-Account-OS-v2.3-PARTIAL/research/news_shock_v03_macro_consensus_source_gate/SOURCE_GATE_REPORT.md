# NEWS SHOCK LAB V0.3 — Macro Consensus Source Gate

Audit date: 2026-09-21
Scientific window: 2021-01-01 through 2024-12-31
Outcome access: forbidden and not required
2025: not authorized by this gate
2026: closed

## Decision

**SOURCE GATE: PARTIAL**

The official-actual side is reproducible. BLS archived CPI and Employment Situation
releases identify the scheduled embargo time, contain the values published at that
release, and, for Employment Situation, state the revisions known at that release.
BLS is therefore the actual and release-clock authority. ALFRED is a useful independent
vintage control, but its daily vintage granularity and typical one-business-day loading
lag mean that it is not the release-instant authority.

The consensus side is not yet complete enough for a corpus-wide PASS. A defensible free
route exists for individual events: a contemporaneous pre-release Reuters poll/article
or a dated bank research document that explicitly states the required fields, captured
with publication time, retrieval time, raw bytes and SHA-256. The prior V0.3A work proves
this route for many CPI events from 2022 onward, but it does not establish complete CPI
and NFP coverage for 2021–2024. In particular, a single stable free API with immutable
historical survey snapshots and all required NFP fields was not found.

No event may enter the analysis corpus until every required field has independent
point-in-time evidence or an explicit field-level incomplete status. Post-release pages
that merely report what a poll had predicted do not by themselves prove that the value
was publicly available before T0.

## Scope reconciliation

Existing `NEWS_SHOCK_LAB_V03A_*` artifacts are a closed CPI-only experiment. They are
read-only prior evidence, not a corpus to modify. The present gate:

- adds no outcome data;
- does not rerun or reinterpret V0.3A;
- does not authorize 2025 or any protected holdout;
- extends the source architecture to CPI and Employment Situation/NFP for 2021–2024;
- requires event-level receipts before a future dataset build.

## Recommended authority chain

### Official actuals and revisions

1. BLS archived release HTML/text captured byte-for-byte.
2. BLS archived schedule for the planned 08:30 America/New_York release.
3. ALFRED vintage observation as an independent daily-vintage cross-check.
4. A second contemporaneous report only as a discrepancy detector.

For CPI, preserve first-release headline and all-items-less-food-and-energy monthly and
12-month changes. Never derive a rounded release value from a currently revised index
series when the archived release states it directly.

For Employment Situation, preserve the release's nonfarm payroll change, unemployment
rate, average hourly earnings change (MoM and/or YoY, with the exact frozen field
definition), and the two prior-month payroll revisions stated in that same release.

### Consensus

1. Pre-release Reuters poll/article with an explicit timestamp before T0.
2. Timestamped pre-release institutional research PDF/page (BMO, Scotiabank, TD,
   Wells Fargo or equivalent) containing the exact field.
3. An independent pre-release source for validation where available.

The consensus statistic must be copied exactly as described (`median`, `mean`, or
publisher-labelled `consensus`). Vendor mixing is allowed only field-by-field with
explicit source identity and `MIXED_SOURCE` status; it can never be presented as a
single-vendor survey.

## Coverage finding

| Component | 2021–2024 finding | Gate result |
|---|---|---|
| BLS release calendar / T0 | Complete route exists | PASS |
| CPI first-release actuals | Complete archive route exists | PASS |
| NFP/payroll first-release actuals | Complete archive route exists | PASS |
| Unemployment actuals | Complete archive route exists | PASS |
| Earnings actuals | Complete archive route exists | PASS |
| NFP prior-month revisions known at release | Explicit in release text | PASS |
| CPI consensus, all required fields | Feasible event-by-event; full 2021–2024 census not proven here | PARTIAL |
| NFP consensus, payroll/unemployment/earnings | Feasible for some events; full field-complete census not proven | PARTIAL |
| Free immutable consensus API | None defensibly established | FAIL |

## Source-class conclusions

- **AUTHORITATIVE:** BLS archived schedules and archived releases for T0, actuals and
  release-known revisions.
- **USABLE_WITH_CONTROLS:** ALFRED for vintage corroboration; pre-release Reuters and
  timestamped institutional research for consensus; Wayback captures when capture time
  precedes T0 and the archived payload is complete.
- **SECONDARY_VALIDATION_ONLY:** MarketWatch, AP, Nasdaq/Yahoo Reuters mirrors and other
  timestamped contemporary reporting when origin and publication time are preserved.
- **DISCOVERY_ONLY:** Investing.com, Forex Factory, Trading Economics public pages,
  Econoday public mirrors, CME/FedWatch, GitHub and Kaggle datasets.
- **REJECTED:** current mutable calendar rows as historical proof; post-release articles
  as sole consensus proof; current FRED/BLS series as first-release values; undated PDFs;
  snippets; datasets without raw provenance; inferred or reconstructed consensus.

See `SOURCE_MATRIX.csv` and `REJECTED_SOURCES.md` for field-level rationale.

## Timestamp conclusion

Both CPI and Employment Situation are scheduled at 08:30 Eastern Time for the audited
window. Store `America/New_York`, the local wall clock and the UTC conversion. This is
13:30 UTC during EST and 12:30 UTC during EDT; fixed offsets are prohibited. The BLS
archive's embargo statement is the release-instant authority. A schedule time alone is
not proof of the exact actual publication instant; if a documented delay/early release
exists, store it as an exception and fail closed until resolved.

The consensus cutoff is strictly `< actual_publication_timestamp_utc` when an actual
publication timestamp is independently documented; otherwise it is strictly `<
scheduled_release_timestamp_utc`. Date-only evidence does not pass an 08:30 same-day
cutoff.

## Final answer

- Best actual authority: BLS archived CPI / Employment Situation release.
- Best consensus source: pre-release Reuters poll/article, backed by a separately
  timestamped institutional research document where available.
- Best independent validator: ALFRED for actual vintages; a second independent
  pre-release publication for consensus.
- Coverage: official actual/revision route is complete for 2021–2024; consensus route is
  only partially demonstrated and requires a 96-event field-level census (48 CPI + 48
  Employment Situation releases, subject to schedule verification).
- Main unresolved risk: no stable free immutable source proves every historical consensus
  field before T0, especially NFP earnings and release-known survey composition.
- Can the V0.3 dataset be built without hindsight? **PARTIAL** — yes for events that pass
  the event receipt; not yet for a complete 2021–2024 corpus.

## Smallest next authorized step

Run an outcome-blind 2021-only consensus evidence census using the event manifest and
archive raw pre-release evidence. Stop after coverage counts and missing-reason receipts.
Do not open prices, returns, 2025 or 2026.
