# News Shock Lab V0.3 — Institutional Consensus Source Probe

Audit date: 2026-09-21

## Final decision

**D — NO DEFENSIBLE SOURCE IDENTIFIED**

The probe found promising institutional capabilities, but no documentation-plus-test chain
that proves a consensus value was published before T0 for both selected events and can be
audited today. The V0.3 lab remains `SOURCE_BLOCKED`.

## Frozen, outcome-blind sample

Before any institutional lookup, the probe selected the lexicographically first event in
each family from the frozen 2021 manifest:

- `US_CPI_2021-01-13`, T0 `2021-01-13T13:30:00Z`;
- `US_NFP_2021-01-08`, T0 `2021-01-08T13:30:00Z`.

The selection receipt was committed separately. No market outcome, price, return, PnL,
post-event direction, 2025, or 2026 research data was accessed.

## Core technical finding

Trading Economics is the strongest normalized candidate found. Its documentation provides:

- stable calendar/event identity;
- event release datetime documented as UTC;
- actual, previous, forecast, provider forecast, revision, source, and unit fields;
- historical queries going back before the required window; and
- an explicit claim that point-in-time calendar data preserves original values.

It still fails the present gate. The published schema does not expose when `Forecast` was
published or snapshotted. `LastUpdate` is the most recent event-row update/insertion, and
documented examples show it at or after the release. Query start/end dates select historical
events, not a demonstrated `as_of` vintage. Consequently, a returned historical forecast
cannot by itself answer “was this exact value public before T0?”

Factiva offers the strongest chronology mechanism: archived article content plus publication
metadata. It could prove a particular Reuters or other article existed before T0, but no
public evidence established field completeness for the frozen CPI and NFP specifications.

Macrobond advertises revision history/point-in-time data and a Consensus Economics
integration. Public material did not tie that capability to event-specific CPI/NFP survey
medians or demonstrate payroll, unemployment, AHE MoM, and AHE YoY together.

For Bloomberg, LSEG/Refinitiv, FactSet, Econoday, and Haver, commercial capability is
plausible but the accessible documentation did not expose enough schema, version, and
timestamp detail to pass. No entitlement was present for a read-only target test.

## Two-event result

| Test | Required consensus fields | Proven before T0 | Result |
|---|---|---:|---|
| CPI | headline MoM/YoY; core MoM/YoY | 0/4 | Timestamp provenance not demonstrated |
| NFP | payrolls; unemployment; AHE MoM/YoY | 0/4 | Field completeness and timestamp provenance not demonstrated |

No consensus values were accepted or added to the scientific census.

## Why the decision is D rather than C

`ACCESS BLOCKED` would assert strong evidence that one specific inaccessible product solves
the problem. This probe did not reach that threshold. It found products that may solve part
or all of it, but their public documentation did not demonstrate the exact pre-T0 forecast
version and full field coverage. Buying access would therefore be speculative.

## Reproducibility and receipts

The repository preserves the sample freeze, source matrix, access audit, normalized source
documentation receipt, and file hashes. Public documentation URLs are recorded with retrieval
date and exact claim scope. Hashes of normalized receipts are not represented as hashes of
vendor web pages.

## Smallest authorized next step

Wait for a vendor sample export or legitimate existing entitlement that covers the two frozen
events. The sample must expose field-level consensus, statistic, forecast timestamp/vintage,
timezone, event ID, and immutable audit/version ID. Then repeat only the two-event probe.
