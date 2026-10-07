# GFIBR V0.1.3 SOURCE TRANSPORT RETRY REMEDIATION FREEZE
Date: 2026-10-07

Trigger:
- Source run 37577983124 remained in the source-gate step for an extended period.
- Current transport retries every HTTP client error up to seven times with exponential backoff.
- Historical or unavailable contracts can legitimately return deterministic 4xx responses; retrying such responses cannot create source data and only delays enumeration.
- No mark/index outcomes, funding-rate r values, returns or PnL have been opened.

Allowed remediation:
- keep retry/backoff for HTTP 429, 5xx, and transient network exceptions;
- fail immediately on deterministic HTTP 4xx other than 429;
- record that asset-event as source unavailable and continue under the existing frozen eligibility/missing-source rules;
- preserve all source/event/sample gates and all parser semantics unchanged.

Forbidden:
- no outcome access;
- no funding-rate r access;
- no threshold/event-rule changes;
- no 2026;
- no main merge/trading/private endpoints.

Existing runs remain preserved.
