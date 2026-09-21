# CPI single-event capability probe

## Frozen selection

- Event: `US_CPI_2021-01-13`
- Scheduled T0: `2021-01-13T13:30:00Z` / 08:30 America/New_York
- Selection: first lexicographic CPI `event_id` in the frozen manifest.
- Selection was committed before institutional source research.

## Required proof

The frozen specification requires separate consensus evidence for headline CPI MoM,
headline CPI YoY, core CPI MoM, and core CPI YoY. A generic “CPI forecast” is not enough.

## Probe result

No provider produced an auditable record for this event. No consensus value was copied,
inferred, or accepted.

Trading Economics documents a historical economic-calendar schema with event identifiers,
`Date`, `Forecast`, `TEForecast`, and `LastUpdate`. Its point-in-time page says historical
events preserve original values before revisions. However:

1. the request dates select the event range, not an independently demonstrated
   `as_of_timestamp` or forecast vintage;
2. the schema has no `ForecastPublishedAt` or `ForecastSnapshotAt` field;
3. `LastUpdate` is defined as the most recent update/insertion timestamp and the examples
   show it at or after the official release;
4. public documentation did not demonstrate four separate CPI fields for the selected
   event with snapshots strictly before T0; and
5. authenticated access was unavailable, so the target payload could not be inspected.

Reuters/LSEG, Bloomberg, FactSet, Econoday, Haver, and Macrobond may carry event forecasts,
but their public materials did not demonstrate the required target-event schema plus
pre-T0 forecast version. Factiva could preserve a contemporaneous article timestamp, but
no evidence established that one pre-release article contains all four required fields.

## Capability verdict

`TIMESTAMP_PROVENANCE_NOT_DEMONSTRATED`

This is a source-capability result only. The event remains unchanged in the frozen census.
