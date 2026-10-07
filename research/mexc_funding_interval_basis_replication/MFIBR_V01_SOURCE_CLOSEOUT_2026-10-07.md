# MEXC-FUNDING-INTERVAL-BASIS-REPLICATION-001
## V0.1 SOURCE CLOSEOUT
Date: 2026-10-07
Status: EXTERNAL_SOURCE_BLOCKED — NO MARKET OUTCOMES OPENED

### Authority
Source/mechanism freeze:
- MFIBR_V01_SOURCE_MECHANISM_FREEZE_2026-10-07.md

Source-only transport remediation:
- MFIBR_V011_OFFICIAL_ANNOUNCEMENTS_API_TRANSPORT_REMEDIATION_FREEZE_2026-10-07.md
- freeze commit: 5220b82f0a1877cb128430c496b9e978498a04df

### What was proven
1. Official MEXC announcements enumeration is available through:
   GET https://api.mexc.com/api/v3/announcements
2. Probe run 37677669464 returned HTTP 200 and paginated through page 200, reaching November 2023 and therefore crossing the frozen 2024-01-01 archive boundary.
3. The public funding-history mechanics route is usable.
4. CollectCycle probe run 37678103064:
   - symbol: OBT_USDT
   - total historical rows reported: 3866
   - historical pagination: 4 pages at page_size 1000
   - mechanics-only records around the probed transition showed 4h before and 1h after
   - fundingRate was not accessed/printed/used.
5. No fair-price, index-price, basis, return or PnL outcome was opened.

### Remaining blocker
Canonical MEXC article pages are not readable from the GitHub Actions runtime.

Article transport probe run 37678289043 tested:
- /support/articles/<article-id>
- /en-GB/support/articles/<article-id>
- /announcements/article/<slug>

All returned HTTP 403 / Access Denied.

The official announcements API provides title/URL/postTime but not enough article-body detail to resolve every 2024-2025 funding-frequency candidate under the frozen V0.1 eligibility rule. In particular, some official titles identify only a calendar date or a multi-contract adjustment and require canonical article content to establish exact effective UTC timestamp, affected contracts and/or new cycle.

Therefore a complete eligible universe cannot be demonstrated without silently lowering the frozen provenance/eligibility standard.

### Verdict
EXTERNAL_SOURCE_BLOCKED

This is an operational/source-provenance verdict, not evidence for or against the economic edge.

### No rescue
Do not:
- treat search-engine snippets as the authoritative complete universe;
- infer missing effective timestamps from later market records;
- drop candidates whose article body is inaccessible;
- lower provenance requirements after the census;
- open MEXC market outcomes under V0.1.

A future MEXC attempt requires an official/public article-detail transport or another legitimate official MEXC source frozen before market outcome access.

### Governance
- main unchanged;
- no trading/orders/wallets/account reads;
- no authenticated/private endpoint;
- no exchange mutation/spending;
- no post-outcome tuning.

### Outcome-access declaration
No MEXC fundingRate value was read/used.
No MEXC fair/index candle value, basis, return or PnL outcome was opened.
