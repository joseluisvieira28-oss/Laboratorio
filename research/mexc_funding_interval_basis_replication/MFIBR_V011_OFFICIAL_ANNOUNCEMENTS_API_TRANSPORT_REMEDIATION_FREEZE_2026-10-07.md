# MEXC-FUNDING-INTERVAL-BASIS-REPLICATION-001
## V0.1.1 OFFICIAL ANNOUNCEMENTS API TRANSPORT REMEDIATION FREEZE
Date: 2026-10-07
Status: SOURCE-ONLY TRANSPORT REMEDIATION — FROZEN BEFORE ANY MARKET OUTCOME

### Trigger
The originally probed official MEXC web archive route returned HTTP 403 from the GitHub Actions runner.

MEXC now exposes an official public announcements endpoint:
- GET https://api.mexc.com/api/v3/announcements
- parameters used: language=en-US, page, limit
- response metadata used: title, url, postTime, language and pagination metadata.

A source-only probe on this branch demonstrated HTTP 200 and pagination from current announcements through page 200, which is already before the frozen 2024-01-01 source boundary.

### Scientific identity
This remediation changes only transport/enumeration.
It does NOT change:
- frozen calendar 2024-2025;
- event eligibility;
- required publication-before-effective ordering;
- collectCycle rules;
- source sample gates;
- concentration gate;
- outcome endpoints;
- later analysis hypothesis;
- verdict taxonomy.

The official API is treated as an official MEXC archive/search mechanism under V0.1 section 4/7. Canonical announcement URL and article identifier remain required for every eligible event.

### Source-stage safety
Allowed:
- title, canonical URL/article ID, postTime, language;
- funding-history symbol, settleTime and collectCycle only;
- row counts/pagination/schema metadata.

Forbidden:
- fundingRate values;
- fair/index candle values;
- basis;
- price returns;
- volume;
- PnL.

### Outcome-access declaration
At this freeze:
- no MEXC fundingRate value has been read/used;
- no MEXC fair/index market value has been opened;
- no MEXC basis/return/PnL outcome has been opened.
