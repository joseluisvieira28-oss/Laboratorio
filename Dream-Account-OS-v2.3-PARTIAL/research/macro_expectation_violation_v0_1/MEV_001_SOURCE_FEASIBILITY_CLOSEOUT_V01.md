# MEV-001 — SOURCE FEASIBILITY CLOSEOUT V0.1

Date: 2026-09-27  
LAB_ID: MACRO-EXPECTATION-VIOLATION-001

## Verdict

**SOURCE_BLOCKED_NO_AUTHORIZED_INTRAMINUTE_TRADFI_PATH**

This is a SOURCE verdict only.
It is NOT NO_EDGE and contains zero economic outcome evidence.

## Required source object

The frozen mechanism requires reconstructing the traditional-market state by
T0+180 seconds for scheduled CPI, Employment Situation and FOMC announcements.

Required external channels:
1. CME Nasdaq-100 futures family.
2. CME U.S. 2-Year Treasury futures family.

The source must preserve timestamps and allow the event-time path to be reconstructed
at no worse than one-minute granularity. A feed whose values are only available as a
single quote >=10 minutes after the event cannot establish the frozen 180-second state.

## Source checks

### A. CME public delayed quotes
Official CME public delayed quote pages state that futures quotes are delayed by at
least 10 minutes. CME also states that website market data is reference-only and should
not be used as validation against or as a complement to its real-time Market Data
Platform.

Result: FAIL for the MEV 180-second decision-state requirement.

References:
- https://www.cmegroup.com/market-data/browse-data/delayed-quotes.html
- https://www.cmegroup.com/trading/about-quotes.html

### B. CME Real-Time Futures & Options Data API
CME offers a direct WebSocket market-data API with top-of-book/trade information.
The product is commercial: CME describes it as pay-for-data-you-consume access.

Under current Crypto Lab authority, paid-data purchase is not authorized.

Result: TECHNICALLY SUITABLE IN PRINCIPLE / NOT AUTHORIZED.

Reference:
- https://www.cmegroup.com/market-data/real-time-futures-and-options-data-api.html

### C. Official U.S. Treasury 2-year yield series
Treasury's official par yield curve is daily. Treasury states that the underlying
indicative quotations are obtained at approximately 3:30 PM each business day.

This cannot reconstruct the first 180 seconds after an 08:30 or 14:00 macro release.

Result: FAIL for intraminute event-state reconstruction.

References:
- https://home.treasury.gov/policy-issues/financing-the-government/interest-rate-statistics/
- https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve

### D. Yahoo Finance futures route
Yahoo's own market-coverage documentation states that CME data is delayed by 10
minutes. The route is also a third-party informational service rather than a direct
timestamp-authority source for this research contract.

Result: FAIL for 180-second decision-state authority.

Reference:
- https://help.yahoo.com/kb/SLN2310.html

### E. Cboe delayed quote pages
Cboe's delayed quote pages explicitly prohibit automated extraction of the delayed
quote table. This route is therefore not an acceptable automated research collector.

Result: FAIL on usage/collection compatibility.

Reference:
- https://www.cboe.com/delayed_quotes/qqq/

### F. Nasdaq Data Link
Nasdaq Data Link offers delayed/historical bars, but no no-cost, permission-clean,
exchange-time NQ + 2Y futures path was established in this gate.

Result: NOT ESTABLISHED / no authority to assume free entitlement.

Reference:
- https://www.nasdaq.com/products/data/data-link/api

### G. CME DataMine
CME DataMine exposes historical Time & Sales, Top-of-Book and other high-resolution
datasets, but its API is entitlement-based and its documentation describes access to
purchased/entitled historical files after licensing/order setup.

This is useful as a future historical/provenance route, but it does not provide the
currently authorized free prospective real-time path required by MEV-001.

Result: TECHNICALLY RELEVANT / ENTITLEMENT OR PURCHASE REQUIRED / NOT AUTHORIZED.

References:
- https://www.cmegroup.com/datamine.html
- https://www.cmegroup.com/datamine/datamine-api.html

### H. Databento CME feed
Databento is listed by CME as a market-data provider and offers CME futures tick,
top-of-book and minute data. Its public pricing describes paid live access and
usage/subscription pricing. New-user credits apply to onboarding/historical use but do
not establish a standing permission-clean free live feed for the 2027 decision-time
requirement under current authority.

Result: TECHNICALLY SUITABLE IN PRINCIPLE / LIVE ENTITLEMENT NOT CURRENTLY AUTHORIZED.

References:
- https://www.cmegroup.com/solutions/market-tech-and-data-services/technology-vendor-services/databento.html
- https://databento.com/futures
- https://databento.com/pricing

## Exhaustion decision

The blocker was actively attacked across direct exchange pages, official U.S. Treasury
data, delayed third-party routes, historical exchange datasets and a licensed CME vendor.
No currently authorized zero-cost route was established that simultaneously satisfies:

- NQ + 2Y Treasury futures;
- <=60-second event-time reconstruction;
- availability compatible with a T0+180s decision;
- timestamp provenance;
- machine-use permission;
- deterministic contract identity;
- prospective 2027 capture.

Therefore further source hunting is now anti-zombie work unless an objective reopening
trigger occurs. The correct state remains SOURCE_BLOCKED rather than weakening the source
contract.

## Current scientific state

MEV-001 remains:
- M1 MECHANISM: PASS
- M2 SOURCE: BLOCKED
- target observation: LOCKED
- outcomes: LOCKED
- promotion credit: NONE

No historical substitute is authorized.
No delayed-quote approximation is authorized.
No proxy substitution to daily Treasury yields is authorized.
No QQQ cash-market substitution is authorized for 08:30 ET CPI/NFP events.

## Objective reopening triggers

This exact source gate may reopen without changing the science only if one of these
exogenous conditions becomes true:

1. authorized access exists to CME intraminute NQ + 2Y Treasury futures data with
   documented source timestamps and machine-use rights; or
2. a genuinely free/public provider is identified that can prove equivalent event-time
   coverage, timestamp integrity and automated-use permission; or
3. the operator separately authorizes a paid-data path under a new operational authority,
   without changing MEV-001 science.

If the instrument set, decision clock, event families or mechanism changes, use a new
LAB_ID.

## Anti-zombie rule

Do not repeatedly scrape public delayed websites.
Do not downgrade source quality until something fits.
Do not open crypto outcomes while the traditional source side is missing.
Do not infer NO_EDGE from this blocker.

END STATE:
SOURCE_BLOCKED / MECHANISM SCIENTIFICALLY UNRESOLVED.
