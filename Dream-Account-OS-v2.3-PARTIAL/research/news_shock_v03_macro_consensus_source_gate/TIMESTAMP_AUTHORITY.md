# Timestamp Authority

## T0 hierarchy

1. Documented actual publication timestamp from BLS, if distinct from schedule.
2. BLS archived release embargo timestamp.
3. BLS archived schedule timestamp.

The BLS schedule labels all times Eastern Time. Convert with the IANA zone
`America/New_York`, never a fixed `-05:00` or `-04:00` offset. At 08:30 local, T0 is
13:30 UTC in EST and 12:30 UTC in EDT.

## Consensus cutoff

An evidence item passes only when its resolved publication timestamp is strictly earlier
than T0. Equality fails. Retrieval time does not replace publication time. A date-only
source published on the event date fails because it cannot prove publication before
08:30. A date-only source from an earlier local calendar day may pass only when its
publisher timezone is known and the latest possible instant on that date is still before
T0; otherwise it remains incomplete.

Publisher edits must be handled as separate versions. Store `published_at_utc`,
`modified_at_utc`, raw content hash, archive capture timestamp and retrieval timestamp.
If `modified_at_utc >= T0` and the original bytes are unavailable, the evidence fails.

## Scheduled versus actual publication

The schedule defines the default boundary, but exceptional early, late, corrected or
reissued releases require an exception receipt. A later BLS reissue does not replace the
first-release payload. Preserve both hashes and link the erratum. If actual publication
time cannot be established for a documented exception, classify the event
`PUBLICATION_TIME_UNRESOLVED`.

## NFP revisions at T0

“Revision known at release” means only revisions printed in the Employment Situation
release available at that T0. Later monthly or annual benchmark revisions are future
knowledge. Store each revised reference month with `previously_reported`,
`revised_at_release`, and `revision_delta`, plus the release receipt hash.

## Audit answer

The question “Was consensus X publicly available before T0?” returns YES only if:

- exact value, unit, field definition and consensus statistic are explicit;
- source identity and raw content are preserved;
- publication time resolves to UTC and is `< T0`;
- no later edit is being mistaken for the pre-release version; and
- the evidence is not merely a post-release recollection of a forecast.

All other cases return NO or UNRESOLVED, never an inferred YES.
