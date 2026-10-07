# MLMXD V0.1.6 — COMPLETE PUBLIC ANNOUNCEMENT CENSUS REMEDIATION
Date: 2026-10-07
Status: OUTCOME-BLIND TECHNICAL SOURCE REMEDIATION

Prior diagnostics established:
- the MEXC public announcements endpoint returns 20 rows per page;
- the correct pagination parameter is `page`;
- `postTime` provides an epoch publication timestamp;
- HTML tag-page requests did not provide a complete reproducible archive enumeration;
- no market prices or outcomes have been opened.

Permitted remediation:
1. enumerate the public MEXC announcements endpoint page-by-page;
2. stop only after all rows are older than the frozen 2024-10-18 census start;
3. retain rows through 2026-09-30 inclusive only;
4. select only announcement rows whose title contains Launchpool;
5. fetch only those official MEXC article bodies;
6. apply the already-frozen explicit-MX-eligibility rule;
7. use public API postTime as the canonical publication timestamp;
8. cluster eligible events with the already-frozen <=60 minute rule.

Forbidden:
- no market-price access;
- no return/PnL access;
- no event-rule changes;
- no calendar change;
- no sample-gate change;
- no outcome-informed filtering.

This remediation exists solely to obtain a complete source census.
