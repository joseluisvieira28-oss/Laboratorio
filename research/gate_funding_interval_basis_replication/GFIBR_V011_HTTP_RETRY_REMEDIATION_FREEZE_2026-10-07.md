# GFIBR V0.1.1 HTTP RETRY REMEDIATION FREEZE
Date: 2026-10-07

Trigger:
- Source-gate run 37577983124 remained inside source-only cadence validation for an extended period.
- No mark/index/return/PnL outcomes were opened.
- The source runner retries all HTTP errors, including deterministic 4xx responses, up to seven times.

Allowed technical remediation:
- preserve 429 retry/backoff;
- preserve retry/backoff for 5xx/network errors;
- fail immediately on deterministic non-429 HTTP 4xx responses such as invalid/unavailable contracts;
- preserve source universe, candidate rules, cadence inference, sample gates, concentration gate and verdict taxonomy unchanged.

Forbidden:
- no mark/index values;
- no funding-rate r values read/used;
- no event-rule changes;
- no threshold changes;
- no 2026;
- no main merge/trading/private endpoints.

Run 37577983124 remains preserved.
