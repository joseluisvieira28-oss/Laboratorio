# NFP single-event capability probe

## Frozen selection

- Event: `US_NFP_2021-01-08`
- Scheduled T0: `2021-01-08T13:30:00Z` / 08:30 America/New_York
- Selection: first lexicographic Employment Situation `event_id` in the frozen manifest.
- Selection was committed before institutional source research.

## Required proof

The capability route must independently identify payrolls, unemployment, AHE MoM, and
AHE YoY consensus. “NFP consensus” cannot stand in for unemployment or earnings.

## Probe result

No provider produced an auditable, field-complete record for this event. No consensus value
was copied, inferred, or accepted.

Trading Economics publicly demonstrates a calendar `Forecast` field and distinct indicator
pages/categories, including nonfarm payrolls and average hourly earnings. It does not expose
an explicit timestamp for when each historical `Forecast` value became public. `LastUpdate`
belongs to the whole event row and can be at/after release, so it cannot prove the forecast
snapshot preceded T0. Public documentation also did not establish that both AHE MoM and AHE
YoY were archived for this exact January 2021 release.

Factiva can preserve timestamped Reuters/publication content, which could validate a
specific pre-release article. It remains only partially capable because an article may omit
unemployment or one/both AHE measures, and syndicated copies are not independent surveys.

The remaining institutional vendors had no public target-event payload or sufficiently
detailed vintage schema. Their commercial availability is not scientific evidence.

## Field verdict

| Required field | Capability result |
|---|---|
| Payrolls consensus | Value likely available commercially; pre-T0 vintage not demonstrated |
| Unemployment consensus | Value likely available commercially; pre-T0 vintage not demonstrated |
| AHE MoM consensus | Exact historical coverage and pre-T0 vintage not demonstrated |
| AHE YoY consensus | Exact historical coverage and pre-T0 vintage not demonstrated |

Overall: `FIELD_COMPLETENESS_AND_TIMESTAMP_PROVENANCE_NOT_DEMONSTRATED`.
