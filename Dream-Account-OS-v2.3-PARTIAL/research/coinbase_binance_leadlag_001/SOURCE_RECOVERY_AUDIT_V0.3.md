# COINBASE-BINANCE-LEADLAG-001 — SOURCE RECOVERY AUDIT V0.3

Scope: SOURCE / PROVENANCE ONLY
Branch: coinbase-binance-leadlag-v0.1
Parent MVE: CBLL-USDT-5M-Z3-001
Parent scientific state: DATA_FAILURE / M2 SOURCE
Outcome status: LOCKED / NOT REOPENED

## HISTORICAL STATE PRESERVED

V0.1 source gate remains failed:
- BTC synchronized 5m coverage: 97.5176%
- ETH synchronized 5m coverage: 94.9615%
- frozen minimum for each: 99.5%

This is DATA_FAILURE, not NO_EDGE.

V0.2 remains immutable:
- free public recovery had not been identified at that time;
- Coinbase Data Marketplace tick-level trade data was frozen as the paid official fallback;
- purchase/SFTP required explicit user authorization.

## SEPTEMBER 2026 UPDATED SOURCE ATTACK

### 1. Coinbase Advanced Trade Public Market Trades

Official Coinbase documentation exposes a Public Market Trades route with historical start/end parameters. A new additive V0.3 authority was frozen before acquisition.

Minimal V0.3 source-only probe:
- products: BTC-USDT, ETH-USDT only;
- frozen source samples inside 2022-2023 only;
- no Authorization header;
- no price/size values persisted;
- no candles, returns, lead-lag, correlations, future direction or PnL.

Observed:
- all four requests returned HTTP 200;
- historical trades were returned for both products at early-2022 and late-2023 sample windows;
- required trade schema present;
- no duplicate trade IDs in parsed samples;
- no product mismatch;
- no parsed trade timestamp outside requested windows;
- no sample reached the 1000-trade response limit.

Immutable source-only receipt SHA256:
c0a391d87e5f15bc3758abd1dd9e564accafc3420560873f3ecc42b616dbbd2a

### 2. Advanced Trade route firewall failure

The exact endpoint response is a market snapshot that also includes best bid / best ask fields outside the historical trades array.

The probe intentionally did not persist or analyze those values. Nevertheless, the raw transport can include current market metadata. Under the lab's frozen protected-period firewall, this prevents treating the route as a clean historical-only 2022-2023 acquisition channel.

Classification for canonical full acquisition:
PROVENANCE_FAILURE — PROTECTED-PERIOD RESPONSE CONTAMINATION RISK

The successful transport receipt is preserved unchanged; it is not rewritten into a failure. The additive firewall closeout governs scientific eligibility.

### 3. Coinbase Exchange GET /products/{product_id}/trades

This official public endpoint is historical-capable by cursor pagination and has a clean trades-only response, but current documentation exposes latest-first access plus before/after cursors, not a timestamp start/end anchor.

Under the current freeze, walking from latest data backwards would traverse protected years before reaching 2023. No official timestamp-to-cursor bootstrap for the frozen historical window was identified.

Classification:
SOURCE_ROUTE_NOT_EXECUTABLE_UNDER_CURRENT_PROTECTED_PERIOD_FIREWALL

No request was executed on this route for recovery.

### 4. Public cloud / archive search

No official Coinbase Exchange tick/trade public archive on AWS/GCP or equivalent cloud public dataset was identified that proves the exact BTC-USDT and ETH-USDT 2022-2023 corpus with required provenance and protected-period isolation.

### 5. Tardis free historical route

Tardis documents Coinbase Pro historical market data from exchange feeds and offers unauthenticated CSV only for the first day of each month.

That free sampling policy cannot provide near-continuous 2022-2023 coverage and therefore cannot satisfy the frozen 99.5% source gate.

Classification:
SOURCE_DATA_INSUFFICIENT for the free tier.

Commercial Tardis access is not preferred over the first-party Coinbase Data Marketplace fallback for this MVE.

## OFFICIAL PAID FALLBACK

Coinbase Data Marketplace offers Exchange Tick Level Trade data. Official documentation states:
- all executed trades are represented;
- microsecond UTC timestamps;
- base, quote, trade ID, price, quantity and side;
- one-time historical purchases are supported;
- SFTP delivery after purchase/license activation;
- exact BTC-USDT files are shown in Coinbase's own historical download example;
- per-folder manifest files include SHA256 checksums.

Frozen purchase specification if separately authorized:
- product: Coinbase Exchange Tick Level Trade;
- pairs: BTC-USDT and ETH-USDT only;
- period: frozen 2022-2023 source window only;
- one-time historical purchase;
- request the smallest pair/date subset Coinbase will sell;
- request a no-cost sample, if available, covering representative V0.1 missing intervals before purchase;
- SFTP plus manifests/SHA256.

Current official Help documentation does not publish a price for this exact historical subset and routes customers to Sales/contracting. Do not invent a price.

NO PURCHASE IS AUTHORIZED BY THIS AUDIT.

## 5-MINUTE RECONSTRUCTION SEMANTICS

If a valid tick corpus is later authorized, V0.3 froze:
- UTC Unix-epoch-aligned 300-second half-open buckets;
- exact Coinbase BTC-USDT / ETH-USDT market identity;
- chronological source timestamp ordering;
- ambiguous same-timestamp price ordering => source integrity failure, not invented tie-break;
- duplicate trade_id byte-equivalent => deduplicate once;
- conflicting duplicate => source integrity failure;
- OHLC from authoritative trades only;
- volume = sum base-asset trade size;
- zero-trade bucket = MISSING_BUCKET_NO_SYNTHETIC_FILL;
- no interpolation;
- no last-price carry.

## IMPORTANT LIMITATION

Tick-level data does not guarantee the frozen 99.5% gate will pass.

If the missing REST candle intervals were genuine zero-trade intervals, they remain missing under the frozen MVE even with perfect tick data. The paid source is therefore a high-fidelity adjudication route, not a guaranteed rescue.

## CURRENT SCIENTIFIC DECISION

Free/reproducible route satisfying every frozen requirement: NO, not yet.

Best source for definitive adjudication: Coinbase Data Marketplace Exchange Tick Level Trade, subject to separate purchase authorization.

Can 99.5% currently be claimed: NO.

Current classification:
DATA_FAILURE / M2 SOURCE
with additive V0.3 PROVENANCE_FAILURE on the Advanced Trade snapshot acquisition route.

No NO_EDGE verdict exists.

## NEXT AUTHORIZED ACTION

Before paying:
1. request from Coinbase Data Marketplace Sales a no-cost sample and exact quote for the frozen pair/date subset;
2. ask whether the sample can cover representative V0.1 missing 5m intervals;
3. do not purchase, exchange credentials, generate SFTP access, or open any protected outcome without explicit authorization;
4. if a sample is supplied, run a new frozen source-only sample adjudicator against the missing-interval semantics before deciding whether a full purchase is justified.

Official references:
- Coinbase Advanced Trade / Get Public Market Trades documentation and Coinbase App API changelog.
- Coinbase Exchange / Get product trades and pagination documentation.
- Coinbase Data Marketplace / Products offered.
- Coinbase Data Marketplace / Getting started.
- Coinbase Data Marketplace / Download files.
- Coinbase Data Marketplace / Verify downloads.
- Tardis.dev / Coinbase Pro historical data details and Downloadable CSV files.

Hard firewalls remain:
research-only; no live trading; no exchange mutation; no orders; no wallets; no alerts/webhooks; no main merge; no Render; no post-outcome tuning; no 2024 outcome opening; no 2025/2026 source/outcome opening under this lineage.
