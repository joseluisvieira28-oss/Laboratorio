# Data Schema V0.3

The canonical representation is normalized. One event table is joined to field values,
evidence snapshots and NFP revision rows. This avoids a wide row whose provenance is
ambiguous when different fields come from different documents.

## `events`

| Column | Type | Rule |
|---|---|---|
| event_id | text PK | `US_CPI_YYYY-MM-DD` or `US_NFP_YYYY-MM-DD` |
| event_family | enum | `CPI`, `EMPLOYMENT_SITUATION` |
| reference_period | `YYYY-MM` | period reported, not release month |
| scheduled_release_local | timestamp without offset | normally 08:30 |
| release_timezone | text | exactly `America/New_York` |
| scheduled_release_utc | timestamp | DST-derived |
| actual_publication_utc | timestamp nullable | only when authoritative |
| cutoff_utc | timestamp | actual publication if proven, else schedule |
| status | enum | anti-leakage status |

## `observations`

One row per event, field and role.

| Column | Type | Rule |
|---|---|---|
| event_id | FK | event |
| field | enum | `headline_cpi_mom`, `headline_cpi_yoy`, `core_cpi_mom`, `core_cpi_yoy`, `nfp_change_k`, `unemployment_rate`, `ahe_mom`, `ahe_yoy` |
| role | enum | `actual_first_release`, `consensus` |
| value | decimal nullable | null never becomes zero |
| unit | enum | `percent`, `percentage_points`, `thousands_persons` |
| statistic | enum nullable | `median`, `mean`, `consensus_label`, `house_forecast` |
| evidence_id | FK | field-specific evidence |
| vintage_status | enum | `FIRST_RELEASE`, `PRE_RELEASE_SNAPSHOT`, `VALIDATOR_ONLY` |
| confidence | enum | `A`, `B`, `INCOMPLETE` |

Surprise values are deliberately not stored at source-gate stage. A later authorized
transform may compute `actual_first_release - consensus` only for complete events.

## `evidence`

| Column | Type | Rule |
|---|---|---|
| evidence_id | text PK | stable identifier |
| publisher | text | exact publisher |
| source_url | text | canonical URL |
| mirror_of | text nullable | original publisher if syndicated |
| published_at_utc | timestamp nullable | required for consensus |
| modified_at_utc | timestamp nullable | preserve edits |
| archive_capture_utc | timestamp nullable | archive timestamp |
| retrieved_at_utc | timestamp | required |
| sha256 | char(64) | hash of raw bytes |
| media_type | text | response media type |
| license_note | text | use/redistribution note |
| temporal_proof | enum | `PRE_T0_DIRECT`, `PRE_T0_ARCHIVE`, `POST_T0_ONLY`, `UNRESOLVED` |

## `nfp_revisions`

| Column | Type | Rule |
|---|---|---|
| event_id | FK | release where revision became known |
| revised_reference_period | `YYYY-MM` | prior month |
| previously_reported_k | decimal | value known before this release |
| revised_at_release_k | decimal | value printed in this release |
| revision_delta_k | decimal | revised minus previously reported |
| evidence_id | FK | same BLS release receipt |

## `source_receipts`

Each run records tool version, input manifest hash, output hashes, start/end UTC, network
errors, HTTP status, redirects and a guard block confirming no outcome access, no 2025,
no 2026, no exchange mutation and no trading.
