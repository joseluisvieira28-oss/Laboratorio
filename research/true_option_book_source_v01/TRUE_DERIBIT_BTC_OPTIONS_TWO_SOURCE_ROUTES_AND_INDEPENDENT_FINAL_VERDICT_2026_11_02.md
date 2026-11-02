# CRYPTO LAB — TRUE BTC OPTIONS PUBLIC REAL BOOK FEASIBILITY: TWO OFFICIAL ROUTES, INDEPENDENT ORIGINAL-SOURCE AUDITS — FINAL 2026-11-02

**VERDICT: SOURCE_DIAMOND / 0.01 BTC_USDC_OPTION_REAL_PUBLIC_BBO_SOURCE_GO_FOR_SHADOW_RESEARCH / REAL_NET_EDGE_UNPROVEN / NO_LIVE_GO.** First legitimate true BTC options public-order-book source, original fills NEVER observed. This is a real information infrastructure improvement, NOT a profitable-trading strategy yet.

## What was already shut, never recycled
- PR #202 Options-SpotPerp-001-V2.1: legacy named OPTIONS is **MEXC BTC spot/perpetual** strategy, not options. 2025 OOS historical gross break-even < 16bps market-market fee floor, plus forward reported 19 model gross negative; NO-GO and stop-order execution unproven.
- PR #261 genuinely different Deribit-type BTC_OPTIONS VRP-selling V2: parent volatility premium is not a filled-trade net edge; 30D two-sided short call+put 0/52 valid matched sellers, 7D trade pairs 0 => execution route NO-GO.
- PR #325/#326 Kraken genuine options RFQ has no publicly observable real bid/ask in two Kraken FUTURES 223-metadata instruments/tickers endpoints (219 flexible +4 inverse; not evidence that Kraken does not have options); MEXC Event Futures 10m fixed-on-submission dynamic payout, no Event API trades, no independently verified actual quote/index settlement source.

## New independently validated genuinely different venue/product: Deribit BTC options public L2 books
Official production API with no account, auth, capital, login, keys:
- /api/v2/public/get_index_price?index_name=btc_usd
- /api/v2/public/get_book_summary_by_currency?currency=BTC&kind=option
- /api/v2/public/get_order_book?instrument_name=BTC-6NOV26-78000-C&depth=5
- /api/v2/public/get_order_book?instrument_name=BTC-6NOV26-78000-P&depth=5.
Pre-source freeze **8a67fa44d1ed0148cf5dff19990992cb80d94a33** before opening Deribit quotes, exactly 4 public GET, 3-14 day maturity + 2.5% strike tolerance + deterministic 7d/ATM priority, 0.1 contract each leg, no selection after book outcomes.
**First-party source CI SUCCESS** https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/41455540344 ; original source artifact **13146457847** ZIP SHA256 **f9745a0b624e1064021b9e094398500a131941595766097ddc7544ddc550de0c**. Four original raw SHA:
(1) 55e6caffd1e833afd55cde0644a2d2d680423f4b52bdf0837c236961b06e8707
(2) 064a9d4c6d840b2db0f10369f37ab2d27978c55a6da22cb02c3525ba42e0881e
(3) 443891262500b9cd96e5fea108cb119321ac247f9d671e3f835330f527dc7fed
(4) 00c62663a51067e4dc14ead517088b63ed6427caf4662c5bc37584cbf5950925.
898 original BTC inverse option summaries, frozen pair C/P actual quote at **2026-11-02 13:44 UTC**, expiry **2026-11-06 08:00 UTC**, strike 78,000 USD, original BTC index 78,048.15 USD:
| True inverse option | Best BID (BTC per contract) | Best ASK (BTC per contract) | Bid volume (contracts) | Ask volume (contracts) |
|--|--:|--:|--:|--:|
| BTC-6NOV26-78000-C | 0.0165 | 0.0175 | 21.5 | 17.9 |
| BTC-6NOV26-78000-P | 0.0155 | 0.0165 | 10.4 | 64.3 |
Original source age 0.349sec and 0.978sec as of readings. 0.1 each long-straddle buy ask premium **0.00340 BTC** ~**265.363710 USD** at original BTC index; instant immediate exit at bids 0.00320 BTC; two-entry and two-exit estimated standard Deribit fee **0.00012 BTC total** (buy+sell each leg MIN(0.0003 BTC,0.125*option premium)*qty); crossed-spread loss 0.00020 BTC; total hypothetical instant roundtrip **0.00032 BTC** ~**24.975408 USD**, **9.4117647% of initial premium**. THESE ARE QUOTED SNAPSHOT COSTS not paid fills, current BTC USD conversion is index-only not actual FX settlement.
**INDEPENDENT OFFLINE ORIGINAL SOURCE AUDIT SUCCESS** https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/41455877064 ; audit artifact **13146592627** ZIP SHA256 **25517028c0113a651a738da65b37243ab15b293bbf73b3f346fc0deec74950e0**: first-party 4/4 original JSON raw SHA, 898 option summaries, independently deterministic pair identity, both original books' BID/ASK and L2 amounts, official contract minimum depth, all raw fee math reproduces original to 1e-12.

## New more capital-accessible TRUE BTC_USDC linear USDC settled options product
**Important distinct product**: https://support.deribit.com/hc/en-us/articles/31424932728093-Linear-USDC-Options documents BTC_USDC min **0.01 contract**, multiplier 1 BTC per contract, USD stablecoin premium and settlement index; no assumption of same costs as BTC inverse, no cross-venue arbitrage. Frozen specific 0.01 source protocol commit **e1afbaf5d9c3977641945b10ae7d21da4dfca82a** BEFORE new data, public official production:
1. /api/v2/public/get_index_price?index_name=btc_usdc
2. /api/v2/public/get_book_summary_by_currency?currency=USDC&kind=option
3/4 original same 6NOV26 strike C/P BTC_USDC symbols, deterministically selected independent of order books (actual 12 eligible pairs).
**Original first-party public source SUCCESS** https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/41456328296 ; source artifact **13147450267** ZIP SHA256 **838e99db9d7d36ebf4304e4ca261023ec90e6abbe984a618c187854b892ba782**.
Four original raw SHA:
(1) b43dfbd3044606e37e31bbb12c8c7cc92d4cf8ab8da8e28145ed3c19802ecd22
(2) 5134d63d0f602ee8271208eb7a141c2e78ab2f53ebfc302bacc8089751d1cac7
(3) 88e505bbe2a4df33fa8fcc903efd22a0160d97679f18c21968181ac9a592616b
(4) ef8bcb5d6040c80f445d5a9b552356d33d36028ed3307f72640d6bb7011c3cce.
Original official BTC/USDC index at **2026-11-02 13:49 UTC** = 77,908.37 USDC; true 2952 USDC option summaries (including not necessarily all BTC). Frozen pair BTC_USDC-6NOV26-78000-C, BTC_USDC-6NOV26-78000-P, expiry **2026-11-06 08:00 UTC**; genuine public two-sided book:
| True linear option | Best BID (USDC per full 1BTC contract) | Best ASK (USDC per full 1BTC contract) | BID size contracts | ASK size contracts |
|--|--:|--:|--:|--:|
| BTC_USDC-6NOV26-78000-C | 1240 | 1260 | 0.7 | 16.0 |
| BTC_USDC-6NOV26-78000-P | 1280 | 1300 | 10.0 | 17.14 |
As-of book age 0.672 and 0.476 seconds. For **0.01** contract each, straddle entry buy ask premium = **25.600 USDC**; hypothetical instant exit at BID = **25.200 USDC**; crossed spread loss = **0.400 USDC**; standard 4 original venue option fees min(0.0003*original BTC_USDC index,0.125*option price USDC)*contract count = **0.93490044 USDC**; full instant roundtrip transaction+spread cost = **1.33490044 USDC**, **5.21445484375% of initially paid 25.60 USDC premium**. This is **NOT** actual realized gain/loss or futures market trading; no money placed. At expiry the purchased straddle premium can be lost in full if BTC ends near strike, independent of instant roundtrip cost. If holding through expiry, model actual 30minute index TWAP payout and delivery fee separately. Do not claim 2026 future price outcomes or profitability.
**INDEPENDENT OFFLINE SOURCE AUDIT SUCCESS** https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/41456617431 ; artifact **13147890285**, ZIP SHA256 **1915d3276453ee697e85294b8d967e7f4f88dd74152136f1afc475c36a52621a**, 4/4 original raw SHA and independent deterministic 12 pair selection, all original USDC prices/quantities, min contract, exact fees & total 1.33490044USDC reproduced without importing original algorithm.

## Caution: two different ASYNCHRONOUS snapshots, no arb claim
First BTC-inverse source 13:44 UTC; second BTC_USDC linear source 13:49 UTC, differ in underlying/index/settlement currency/size and quote instant. They cannot be used to assert direct option mispricing, profitable cross-venue parity, or superiority in economic edge. The linear min0.01 is **approximately 10 times smaller nominal contract order size**, leading to small demonstrated cash premium in the later independent snapshot and materially more feasible zero-trade source observation. It is NOT a verified beneficial trading strategy; individual Swiss option trader eligibility still requires official account-level checks. Deribit Switzerland not in public restricted list as checked 2026-11-02 but is not account acceptance or KYC.

## Concrete economic next step — and stop rules
**GO-SHADOW-RESEARCH only for Deribit public BTC_USDC linear true options at min0.01**: the exact LIVE QUOTE source exists and original cost is measurable in USDC on a min-size contract. For economic edge, independently PRE-REGISTER future event universe (matching strike+expiry), exact exchange index 30-minute TWAP at expiry, realistic trading fee+delivery and expected book available at decision, time drift, no repeated midprice substitutions; collect read-only prospective pairs and realized settlement outcomes; require sufficient independent sample and economic positive lower CI **after all costs**, else STOP. A single quote, even a beautiful one, is NEVER profitable edge. Do not open 2025/26 after-the-fact to optimize rejected old strategies; new distinct options research requires new pre-outcome freeze and fresh untouched outcomes.
**NO-LIVE-GO all**: Kraken actual options RFQ unauthenticated source unavailable, MEXC Event Futures no API payout source, MEXC perp V2.1 remains rejected. All source API GETs were PUBLIC read-only official endpoints, no auth/private/wallet/order/capital and zero paid provider, no change to main.
PUBLIC repo privacy: do not upload any brokerage account screenshots, personal identity, private offer IDs/secrets into public repository.
