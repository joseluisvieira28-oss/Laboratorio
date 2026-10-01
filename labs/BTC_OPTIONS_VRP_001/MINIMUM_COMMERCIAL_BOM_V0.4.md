# BTC-OPTIONS-VRP-001 — Minimum commercial source BOM V0.4

Date: 2026-10-01. Procurement specification only; purchases and vendor contacts not performed.

## Fixed scientific envelope

Use the frozen OVRP-EXEC-BBO-ATM30-7D-STATICDELTA-002 rules from canonical V0.3. Attempt all 192 Thursday 08:00 UTC anchors, 2021-04-01 through 2024-11-28, with exits seven days later (last exit 2024-12-05). A minimum 120 executable anchors is a gate, not a quota for picking successful dates. Preserve the four-hour option windows, 25–35 DTE/30 target, same-strike call+put, amounts, static hedge, fees/stress and <=30-second BBO staleness. Do not buy/open 2025/2026.

## Smallest data items

| Item | Necessary content | Bounded acquisition |
|---|---|---|
| BTC option-chain selection | Original instrument identity, exchange/local timestamp, expiry, strike, right, bid/ask prices AND quantities, underlying/index, IV/Greeks required by the frozen delta rule | All BTC strikes/eligible expiries within frozen selection windows; never select contracts using later outcomes |
| Option execution BBO | Point-in-time best bid/ask price and size, event ordering, instrument metadata/tick size, freshness evidence | Only selected call/put contracts in frozen entry/exit windows after source-only chain selection; ensure as-of state initialization |
| BTC-PERPETUAL static hedge | BBO prices/sizes, timestamp, tick/contract units and required index reference | Frozen hedge entry/exit windows only, including initialization; no intraweek rehedge data requirement |
| Integrity | Provider provenance/licence, UTC semantics, gaps/coverage, object hashes, symbol mapping and known capture incidents | Receipts plus immutable manifest; distinguish measured data from modeled data |

If the vendor delivers daily files only, the entry+exit calendar is the union of 193 Thursdays, not four full calendar years. Initial bulk shape: options_chain/OPTIONS and quotes/OPTIONS plus quotes/BTC-PERPETUAL on those dates; filter to BTC and required windows after acquisition. Selected-contract quote files may reduce transfer once prospectively selected. Full-depth L2, all other venues/currencies, options trades and off-window history are not minimum requirements when authoritative BBO event data supplies the frozen semantics. This is transfer minimization, not permission to substitute cadence, midpoint, OI or volume for size.

## Commercial access constraints checked today

Tardis remains the schema-proven fallback. Its docs state subscriptions only, no fixed-range/custom exports. Annual Academic/Solo/Pro has a four-year lookback; bought now, that omits the beginning of the frozen 2021 window. Full 2021 coverage therefore needs an entitlement explicitly reaching 2021-04-01, such as Business yearly, not an assumed inexpensive recent plan. Options-only entitlement must also be checked for BTC-PERPETUAL; a Deribit derivatives entitlement can cover both legs. Public all-derivatives Business list is $3,500/month with yearly history access ($42,000/year arithmetic, not a personalized quote). A single-exchange entitlement may cost less, but an exact checkout quote was not requested or generated. [Pricing](https://tardis.dev/#pricing), [billing/range rules](https://docs.tardis.dev/faq/billing-and-subscriptions.md).

optionsDX corrected census retains the exact monthly/frequency prices; all intraday variants cost above zero. Before considering any purchase, prove timestamp/size semantics sufficient for <=30-second freshness and full frozen anchor coverage. EOD/30-minute/15-minute/5-minute data and an advertised minutely grid do not by themselves prove that gate. Catalogue endpoints are metadata only; cart/checkout is not used.

Volar's advertised annual archive is a price reference, not an admissible replacement: its public chain schema lacks displayed sizes and the archive stops September 2024; modeled bridge is excluded. CoinAPI/Laevitas total cost, exact pre-2025 coverage and bounded retrieval must be established separately. No free-credit activation, wallet signature or paid request is authorized.

**Actual cash spent: USD 0. Exact minimum purchasable package and total cash cost: not established without a legitimate vendor quote/entitlement check. No purchase proposal is approved by this BOM.**

## Reopen sequence

Legitimately available measured pre-2025 BBO+size corpus → immutable source-only acquisition authority before opening payload → bounded acquisition and provenance/freshness/coverage source gate → require PASS with >=120 frozen executable anchors. Only an existing authority explicitly authorizing the next gate can permit continuation. Canonical V0.3 describes rules but is not, by itself, an execution authorization. The old trade-print authority is for a different MVE and cannot authorize the BBO MVE. Outcomes remain closed until authority is proved.
