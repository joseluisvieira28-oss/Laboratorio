# UPBIT-KRW-LISTING-SHOCK-001 — SOURCE CLOSEOUT V0.2.9

Date: 2026-09-27
Branch: `upbit-krw-listing-shock-source-closeout-v0.2.9`

## CANONICAL CURRENT STATE

> **SOURCE_ACCESS_BLOCKED / DISCOVERY_NOT_OPENED / NO_PROMOTION**

This is **not** `DISCOVERY_NO_EDGE`.

No Binance OHLCV, return, stop/target, NET10/NET20, bootstrap or PnL outcome was opened under this lineage.

## FROZEN SCIENTIFIC QUESTION

MVE:
`UKLS-UPBIT-KRW-BINANCE-SPOT-001`

Frozen question:
When Upbit publicly announces first-time KRW market support for a token that has already traded on Binance Spot USDT for at least 24 hours, does a positive access/liquidity shock remain exploitable on Binance after a realistic five-minute delay?

Frozen event window:
2023-01-01 through 2024-12-31.

Source gate required:
- >=30 qualified events
- >=25 distinct symbols
- >=10 events in 2023
- >=10 events in 2024
- exact frozen Upbit title parser
- price fields unopened until SOURCE_DATA_PASS.

## DIRECT FIRST-PARTY SOURCE

Modern official endpoint:
`https://api-manager.upbit.com/api/v1/announcements`

Reverified from the GitHub research runtime:
HTTP 403.

Legacy official routes:
`/api/v1/notices`

Current probe:
HTTP 404.

Current Upbit WWW notice frontend and external-announcements first-party root:
HTTP 403.

No proxy rotation, CAPTCHA bypass, residential proxy, authenticated scraping or anti-bot evasion was authorized.

## WAYBACK SOURCE RECOVERY

### V0.2.2 — index candidate

Run:
`36321378859`

Wayback CDX proved archived first-party Upbit API captures exist.

Observed index metadata:
- ANNOUNCEMENTS: 60 capture rows, earliest 2024-02-15, latest 2024-12-19
- NOTICES: 48 capture rows, earliest 2023-01-02, latest 2024-08-27

Classification:
`WAYBACK_FIRSTPARTY_ARCHIVE_CANDIDATE`

### V0.2.3 / V0.2.3A — payload/schema transport

Archived JSON replay was technically possible after gzip/brotli-aware transport remediation.

This established archive usability but did not establish full source equivalence or complete historical enumeration.

### V0.2.6 — title-linked legacy/modern equivalence

Run:
`36323912166`

Observed:
- LEGACY accepted captures: 13
- LEGACY accepted detail captures: 4
- LEGACY distinct exact titles: 23
- MODERN accepted captures: 34
- MODERN accepted detail captures: 7
- MODERN distinct exact titles: 136
- comparable exact titles across families: **0**
- exact timestamp-field equivalence count: **0**

Classification:
`TITLE_LINKED_EQUIVALENCE_NOT_PROVEN`

Therefore `created_at/updated_at` from the legacy schema may not be silently treated as equivalent to `first_listed_at/listed_at` from the modern schema.

### V0.2.7 — archive list continuity

Run:
`36324161275`

LEGACY:
- usable snapshots: 20
- coverage start: 2022-12-30
- coverage end: 2024-01-11
- continuity breaks: 11

MODERN:
- usable snapshots: 11
- coverage start: 2024-02-08
- coverage end: 2024-12-19
- continuity breaks: 10

Cross-family overlap:
**0 seconds**

Modern end-boundary pass:
**false**

Classification:
`ARCHIVE_LIST_CONTINUITY_NOT_PROVEN`

This fails the requirement for a complete, unbiased 2023-2024 announcement universe.

## COMMON CRAWL RECOVERY

### V0.2.5A / V0.2.5B

Standard Common Crawl index and URL-index transports failed under the tested paths.

### V0.2.5C — raw CDX transport

Run:
`36325097130`

The raw Common Crawl CDX shard transport itself passed:
- selected shard readable
- secondary index rows: 1,253,964

Classification:
`COMMON_CRAWL_RAW_INDEX_TRANSPORT_PASS`

### V0.2.5D — raw index census

Run:
`36325369192`

Observed across the frozen 15 crawl blocks:
- matched exact Upbit list rows: **0**
- modern 2023 exact list HTTP200 captures: **0**
- modern 2024 exact list HTTP200 captures: **0**
- legacy 2023 exact list HTTP200 captures: **0**
- legacy 2024 exact list HTTP200 captures: **0**
- technical failures: **0**

Classification:
`COMMON_CRAWL_NO_EXACT_LIST_CAPTURE`

Common Crawl therefore does not repair the missing Wayback list continuity.

## NUMERIC DETAIL CENSUS

V0.2.8 tested whether archived numeric detail URLs could independently define a complete event universe.

Initial high-load query returned Wayback HTTP 503 and is treated as transport-only evidence.

V0.2.8A/V0.2.8B were frozen as lower-load transport remediations. Their results do not alter the closeout requirement:

Even a detail-index candidate would still need to prove:
1. complete event-universe coverage across the full 2023-2024 window;
2. unbiased enumeration;
3. legacy/modern timestamp semantic equivalence or one single schema spanning the full window;
4. source integrity before any Binance outcomes open.

Those requirements are not presently satisfied.

## CURRENT UPBIT API NOTE

In 2026 Upbit introduced an official Announcement WebSocket with fields including:
- category
- first_listed_at
- listed_at
- URL / UUID

It is real-time only and therefore does not retroactively provide the frozen 2023-2024 event universe.

## FINAL SOURCE VERDICT

- complete official 2023-2024 enumeration: **NOT ESTABLISHED**
- direct first-party transport from research runtime: **BLOCKED**
- Wayback archive existence: **PROVEN**
- Wayback complete list continuity: **NOT PROVEN**
- legacy/modern timestamp-schema equivalence: **NOT PROVEN**
- Common Crawl exact list recovery: **NO**
- source gate: **NOT PASSED**
- Binance market outcomes: **NOT OPENED**
- discovery economics: **NOT ADJUDICATED**
- 2025 independent validation: **LOCKED**
- 2026 protected holdout: **LOCKED**
- promotion: **NO**
- micro-live: **NO**
- live trading: **NO**
- main merge: **NO**

Canonical classification:

> **SOURCE_ACCESS_BLOCKED / DISCOVERY_NOT_OPENED / NO_PROMOTION**

## REOPEN CONDITIONS

The source gate may reopen only if a prospectively frozen source route can establish the complete 2023-2024 Upbit KRW-support announcement universe under the existing parser and timestamp semantics.

Admissible examples:
1. restored first-party historical announcements access;
2. an official historical export/API from Upbit;
3. archive coverage that independently proves complete enumeration and timestamp schema equivalence;
4. another authoritative first-party dataset with auditable provenance.

No source-minimum reduction, year-window reduction, manual event addition, parser rescue, symbol rescue, or outcome-driven source change is authorized.
