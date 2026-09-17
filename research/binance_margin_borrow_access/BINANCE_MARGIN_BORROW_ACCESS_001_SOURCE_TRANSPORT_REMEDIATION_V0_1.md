# BINANCE-MARGIN-BORROW-ACCESS-001 — SOURCE TRANSPORT REMEDIATION V0.1

Date: 2026-09-17  
Status: **SOURCE-ONLY / OUTCOME-BLIND / TRANSPORT REMEDIATION ONLY**

## Problem found

The initial no-`catalogId` Binance CMS list route does not behave as a single globally paginated announcement stream. It returns multiple catalogs, each with a bounded article slice. Treating `pageNo` as a global chronological cursor therefore produced a false enumeration boundary and did not recover the prospectively fixed 2023/2024 positive-control article codes.

This is a source-transport/provenance failure, not an economic result.

## Frozen remediation

Use Binance's public catalog-specific announcement route for catalog `48`:

`/bapi/composite/v1/public/cms/article/catalog/list/query?catalogId=48&pageNo=<n>&pageSize=20`

Catalog 48 is the Binance announcement category historically/currently used for `New Cryptocurrency Listing` / access-expansion notices and is independently observed to contain Cross Margin access announcements.

The event universe is still not defined by a search engine. Search/web results were used only to diagnose the CMS transport semantics and to identify the official catalog transport.

The catalog must be paginated deterministically until the returned release dates cross below `2023-01-01T00:00:00Z`. It may not stop after a convenient event count.

## Official article body route

For each margin-looking catalog article, resolve canonical article content through Binance's public CMS detail route:

`/bapi/composite/v1/public/cms/article/detail/query?articleCode=<code>`

The article code from the catalog and the article code returned by the detail object must agree. The detail payload's title/release time/body is the canonical structural text used to determine whether the notice explicitly introduces new borrowable assets on Cross Margin.

Direct support-page HTML is no longer treated as a body transport because it can be client-rendered and omit article text from the raw response.

## Scientific rules unchanged

Unchanged:
- 2023-01-01 through 2024-12-31 scientific event window;
- explicit Cross Margin new-borrowable semantics;
- prior Spot listing requirement before any Discovery;
- confound adjudication before outcomes;
- borrow-cost provenance requirement before executable strategy claims;
- no prices, returns, basis, PnL, authenticated exchange API, account data or 2025/2026 access.

The two pre-frozen positive controls remain unchanged and are used only to verify source completeness/provenance:
- `a74f935eaa2247889d58e33ec23313bb` (2023)
- `6674719e209641bda688729852d35fb5` (2024)
