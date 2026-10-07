# MEXC-MULTI-STABLE-BASIS-001 — CALIBRATION TRANSPORT REMEDIATION V0.3.1

Date: 2026-10-07
Status: TECHNICAL ONLY / PRE-OUTCOME

Parent freeze:
`PROSPECTIVE_PREOUTCOME_FREEZE_V0.3.md`

Failed calibration run:
- workflow run 37645886508
- verdict: `PROSPECTIVE_SOURCE_BLOCKED_CALIBRATION`
- BTC exact common minutes: 8,000 / 11,520
- ETH exact common minutes: 8,000 / 11,520
- exact identical 69.4444% coverage on both underlyings
- economic outcomes opened: false
- forward returns calculated: false
- execution PnL calculated: false

Diagnosis:
The Spot normalization fetch requested 720-minute chunks. Runtime returned only 500 rows per request, yielding exactly 1,000 normalization minutes per day across two requests and therefore 8,000 common minutes across eight days.

Official MEXC Spot API documentation states K-line default 500 and maximum 1000. Runtime behavior is treated as authoritative for transport.

Remediation:
- change Spot K-line retrieval chunk size ONLY from 720 minutes to 480 minutes;
- use three 480-minute requests per UTC day;
- preserve the exact same calibration dates, six perpetual contracts, normalization routes, q99 nearest-rank rule, >=95% coverage gate and all economic science.

The provisional q99 values printed by the failed run are INVALID and MUST NOT become authority because the frozen coverage gate failed.

No threshold rule, horizon, direction, sample gate, cost, asset or economic outcome rule may change.

Rerun the same predictor-only calibration once under corrected paging.
