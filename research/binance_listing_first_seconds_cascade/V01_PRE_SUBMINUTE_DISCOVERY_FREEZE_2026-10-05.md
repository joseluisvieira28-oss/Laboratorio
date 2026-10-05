# BINANCE-LISTING-FIRST-SECONDS-CASCADE-002
## V0.1 PRE-SUBMINUTE DISCOVERY FREEZE
Date: 2026-10-05
Status: FROZEN BEFORE ANY 2025 SUB-MINUTE TRADE OUTCOME INSPECTION

## Scientific lineage
BINANCE-LISTING-INFORMATION-CASCADE-001 established two facts:
1. A clean 2022-2023 discovery sample showed a large announcement-time information shock.
2. The independently preregistered 2025 delayed-entry holdout failed:
   NO_EXECUTABLE_EDGE_HOLDOUT for entry >=60 seconds after T0 and a 15-minute primary exit under the frozen 50 bps cost stress.

That closed result MUST NOT be rescued or reinterpreted.

This new family asks a different economic question:
How quickly does Binance spot-listing information propagate into a pre-existing external spot market during the first seconds after the official public announcement?

## Role of calendar periods
2025 = DEVELOPMENT / MECHANISM CHARACTERIZATION ONLY.
2025 can never be used as a confirmatory holdout for this family.

2026 = UNOPENED CONFIRMATORY / FORWARD HOLDOUT.
No 2026 market outcomes may be inspected under this family until a later explicit pre-outcome freeze is created.

2024 remains quarantined from confirmatory use.

## Event authority
T0 = official Binance public CMS releaseDate timestamp already established by the outcome-blind 2025 census.

Frozen 2025 non-stable / non-fiat-like candidate pool:
- AIXBT
- CGPT
- COOKIE
- TRUMP
- 1000CHEEMS
- TST
- SYRUP
- KMNO
- WLFI
- PUMP
- AVNT
- ASTER
- GIGGLE
- F (SynFutures)
- BANK (Lorenzo Protocol)
- MET (Meteora)

Known T0 milliseconds:
- AIXBT / CGPT / COOKIE: 1736499327639
- TRUMP: 1737259542151
- 1000CHEEMS / TST: 1739085031264
- SYRUP / KMNO: 1746530720814
- WLFI: 1756691345082
- PUMP: 1757590673797
- AVNT: 1757908021934
- ASTER: 1759736929954
- GIGGLE / F: 1761361338417
- BANK / MET: 1763028026501

No 2025 candidate may be added after this freeze.

## V0.1 source
Primary historical microstructure source:
Gate official Historical Quotation archive, SPOT filled orders / deals.

Canonical archive pattern:
https://download.gatedata.org/spot/deals/YYYYMM/MARKET-YYYYMM.csv.gz

Expected deal schema:
timestamp, dealid, price, amount, side

Gate documentation states SPOT filled-order historical downloads are available from January 2023.

## Outcome-blind source census
For each frozen candidate, first test only:
- monthly archive existence;
- machine-readable gzip/CSV;
- timestamp precision;
- presence of trades in required pre/post windows;
- exact asset identity on Gate;
- evidence that the Gate market existed >=24h before Binance T0.

The source census MUST NOT emit or persist prices or returns.

Identity/ticker collisions are fail-closed.
F, BANK, MET and any other ambiguous ticker require explicit Gate identity proof before inclusion.

## Source-valid event criteria
An event is source-valid only if ALL are true:
1. exact asset identity is defensible;
2. Gate spot market existed >=24h before T0;
3. official Gate deals archive for the event month is accessible;
4. at least one trade exists in [T0-24h, T0-1h];
5. at least one trade exists in [T0-10s, T0);
6. at least one trade exists in [T0, T0+60s];
7. timestamps provide sub-second resolution or a documented resolution sufficient to order trades within seconds.

If fewer than 8 distinct events are source-valid:
V0.1 = SOURCE_BLOCKED_SUBMINUTE.

If n >= 8:
the 2025 DEVELOPMENT characterization may open exactly once under the metrics below.

## Frozen DEVELOPMENT metrics
For each source-valid event:

P0:
price of the final trade strictly before T0, restricted to [T0-10s, T0).

First-post latency:
timestamp(first trade >= T0) - T0, in milliseconds.

Announcement-time returns:
R1s  = last trade price at or before T0+1s divided by P0 minus 1, if at least one post-T0 trade exists by 1s.
R5s  = last trade price at or before T0+5s divided by P0 minus 1.
R10s = last trade price at or before T0+10s divided by P0 minus 1.
R30s = last trade price at or before T0+30s divided by P0 minus 1.
R60s = last trade price at or before T0+60s divided by P0 minus 1.

For horizons with no post-T0 trade yet, the metric is NULL rather than forward-filled from pre-T0.

Volume / activity:
- count of trades in 0-1s, 0-5s, 0-10s, 0-30s, 0-60s;
- quote-volume in the same windows;
- baseline median trade count per non-overlapping 5s block in T0-10m through T0-1m;
- baseline median quote-volume per non-overlapping 5s block over the same interval;
- corresponding activity-shock ratios.

Reaction-speed metrics:
- signed R1/R60, R5/R60, R10/R60 and R30/R60 only when R60 is non-zero and the same-direction ratio is meaningful;
- earliest trade timestamp reaching 50% of the signed R60 displacement;
- earliest trade timestamp reaching 80% of the signed R60 displacement.

## Frozen hypothetical detection-latency grid
Development-only latency grid:
- 250 ms
- 500 ms
- 1 s
- 2 s
- 5 s
- 10 s
- 30 s
- 60 s

For each latency L:
entry = first trade at or after T0+L.
Record actual_entry_latency_ms.
Primary characterization exit = last trade at or before T0+60s.
Gross capture return = exit / entry - 1.

No interpolation.
If no trade is available after a latency threshold before T0+60s, that latency observation is NULL.

Development cost-sensitivity grid, descriptive only:
- 20 bps round-trip
- 50 bps round-trip
- 100 bps round-trip

No development result constitutes a tradability or live-trading claim.

## Development questions fixed in advance
V0.1 must answer:
1. What fraction of the 60-second displacement is already absorbed by 1s, 5s, 10s and 30s?
2. How much gross return remains after 250ms, 500ms, 1s, 2s, 5s, 10s, 30s and 60s?
3. Is any latency bucket positive in median and reasonably distributed across events rather than dominated by a single observation?
4. Does activity/volume explode contemporaneously with the price displacement?
5. Is the economically interesting window measured in tens of seconds, single-digit seconds, or effectively sub-second?

## Development interpretation rules
This stage is NOT a confirmatory survival gate.

Permitted development labels:
- ACTIONABLE_WINDOW_CANDIDATE
- HFT_ONLY_OR_TOO_FAST
- NO_CONSISTENT_FIRST_SECONDS_EFFECT
- SOURCE_BLOCKED_SUBMINUTE

An ACTIONABLE_WINDOW_CANDIDATE requires, descriptively:
- n >= 8 source-valid events;
- at least one latency bucket >=1s with positive median gross capture to 60s;
- >=60% positive hit rate at that same bucket;
- positive leave-one-out median at that same bucket;
- no single event >35% of summed positive returns at that same bucket.

This is a development filter only.
It does NOT authorize 2026 outcome inspection.

## 2026 firewall
If 2025 development produces an ACTIONABLE_WINDOW_CANDIDATE:
a separate V0.2 2026 PRE-OUTCOME FORWARD FREEZE is mandatory before any 2026 market outcome is opened.

That later freeze must lock:
- announcement detection transport;
- polling/websocket method;
- measured detection latency;
- venue binding rules;
- exact entry trigger;
- exact exit rule;
- fees/slippage;
- stale-data handling;
- duplicate-event handling;
- forward timestamp boundary;
- pass/fail gates.

No 2026 outcome may influence those choices.

## Governance
Research-only.
No main merge.
No live trading.
No orders.
No private exchange endpoints.
No account reads.
No wallets.
No post-outcome tuning presented as confirmation.
