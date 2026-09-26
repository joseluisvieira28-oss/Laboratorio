# COINBASE-BINANCE-LEADLAG-001 — FINAL SCIENTIFIC VERDICT V0.4

Date: 2026-09-26  
Branch: `coinbase-binance-leadlag-final-verdict-v0.4`  
Parent branch: `coinbase-binance-leadlag-v0.1`  
Frozen MVE: `CBLL-USDT-5M-Z3-001`

## FINAL CANONICAL CLASSIFICATION

**DATA_FAILURE / HYPOTHESIS_NOT_ADJUDICATED / NO_PROMOTION**

Additive source-recovery classification:

**FREE_PUBLIC_SOURCE_RECOVERY_EXHAUSTED_UNDER_FROZEN_FIREWALL**

This is a final closeout of the currently authorized, free/public source-recovery path. It is **not** relabelled `DISCOVERY_NO_EDGE`, because the frozen source gate failed before economic adjudication was scientifically eligible.

## FROZEN PROTOCOL PRESERVED

No hypothesis, asset, quote currency, timeframe, threshold, rolling window, entry rule, stop, target, hold duration, cost assumption, sample floor, bootstrap rule, validation gate, or protected-period boundary was changed.

Hard firewalls remain:
- research only;
- no live trading;
- no exchange mutation;
- no orders;
- no merge to main;
- no Render deployment;
- no post-outcome tuning;
- no 2024/2025/2026 outcome opening under this lineage.

## SOURCE GATE RESULT

Frozen minimum synchronized 5-minute coverage per asset: **99.5%**.

Observed V0.1 discovery-source coverage:
- BTC: **97.5176%**
- ETH: **94.9615%**

Both fail the frozen gate.

The official Coinbase Exchange candle documentation explicitly states that historical rate data may be incomplete and that no data is published for intervals where there are no ticks. This confirms that the original official-candle route is structurally capable of producing missing 5-minute buckets and therefore cannot be assumed to satisfy the frozen 99.5% continuity requirement.

Official reference:
- https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/products/get-product-candles

## SOURCE-RECOVERY ATTACK — FINAL STATE

### 1. Coinbase Exchange historical candles

Status: **FAILED FROZEN COVERAGE GATE**

The route is official and reproducible, but observed synchronized coverage remains below 99.5% for both BTC-USDT and ETH-USDT.

Synthetic fill, last-price carry, interpolation, quote switching, timeframe switching, or lowering the coverage threshold are prohibited by the frozen protocol.

### 2. Coinbase Advanced Trade Public Market Trades

Status: **PROVENANCE_FAILURE UNDER PROTECTED-PERIOD FIREWALL**

V0.3 proved historical trades can be returned for 2022-2023 windows, but the transport response also contains current market snapshot metadata (best bid / best ask) outside the historical trade array.

Under the already-frozen protected-period firewall this route cannot be promoted into canonical full acquisition without changing the source authority after observing the route behavior.

The V0.3 source receipt remains valid; this closeout does not rewrite it.

### 3. Coinbase Exchange GET /products/{product_id}/trades

Status: **NOT EXECUTABLE UNDER CURRENT FIREWALL**

The official route is latest-first and cursor-paginated using before/after trade IDs. The official documentation does not provide a timestamp-to-cursor bootstrap. Reaching 2022-2023 from the current head would require traversing protected later periods.

Official reference:
- https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/products/get-product-trades

### 4. Official free historical archive

Status: **NO QUALIFYING OFFICIAL FREE ARCHIVE IDENTIFIED**

No official Coinbase public archive was identified that provides the exact BTC-USDT and ETH-USDT 2022-2023 tick corpus with the required provenance, continuity semantics, and protected-period isolation.

### 5. Coinbase Data Marketplace tick-level trades

Status: **QUALIFYING FIRST-PARTY PAID FALLBACK EXISTS, NOT ACQUIRED**

Coinbase officially offers Exchange tick-level trade data, including executed trades with microsecond UTC timestamps, trade IDs, price, quantity and side. Coinbase documentation shows historical one-time purchase/licensing and SFTP delivery, and gives a BTC-USDT historical file example with per-folder SHA256 manifests.

Official references:
- https://help.coinbase.com/en/data-marketplace/getting-started/data-marketplace-products
- https://help.coinbase.com/en/data-marketplace/getting-started/coinbase-data-marketplace
- https://help.coinbase.com/en/data-marketplace/access-data/download-files
- https://help.coinbase.com/en/data-marketplace/access-data/verify-downloads

No purchase, contract, credential exchange, SFTP activation, or paid-data acquisition is authorized or performed by this closeout.

Crucially, even a complete tick corpus does **not** guarantee the 99.5% gate will pass. Under the frozen reconstruction semantics, a genuine zero-trade 5-minute bucket remains `MISSING_BUCKET_NO_SYNTHETIC_FILL`.

## ECONOMIC DIAGNOSTICS — PRESERVED BUT NON-CANONICAL

The prior source-failed run observed:
- resolved trades: **138**
- base mean net R: **-0.0147049**
- base profit factor: **0.953234**
- stress mean net R: **-0.1147049**
- stress profit factor: **0.689615**
- bootstrap 95% lower daily portfolio R: **-0.0251985**
- 2022 base mean net R: **+0.0033450**
- 2023 base mean net R: **-0.1277544**
- BTC-only base mean net R: **-0.0206567**
- ETH-only base mean net R: **-0.0059897**
- max positive month share: **0.4232214**
- minimum leave-one-trade-out mean net R: **-0.0279509**

These diagnostics would not support promotion, but they remain non-canonical because the source gate failed first. They must not be upgraded into a `NO_EDGE` claim.

## FINAL VERDICT

For the frozen MVE `CBLL-USDT-5M-Z3-001`:

- **EDGE_SURVIVES:** NO
- **DISCOVERY_NO_EDGE:** NOT SCIENTIFICALLY ADJUDICATED
- **DATA_FAILURE:** YES
- **SOURCE RECOVERY VIA FREE/PUBLIC ROUTES:** EXHAUSTED UNDER CURRENT FIREWALL
- **2024 INDEPENDENT VALIDATION:** CLOSED / UNOPENED
- **2025/2026:** CLOSED / UNOPENED
- **PROMOTION:** NO
- **MICRO-LIVE:** NOT ELIGIBLE

### Operational disposition

**ARCHIVE / NO FURTHER FREE-PUBLIC ATTACK UNDER THIS MVE.**

The only scientifically legitimate reopening condition is acquisition of a first-party historical tick corpus for the exact frozen BTC-USDT and ETH-USDT 2022-2023 window, followed by a source-only reconstruction using the already-frozen semantics.

If that corpus still produces <99.5% synchronized coverage for either asset, the MVE remains permanently closed as `DATA_FAILURE`.

No parameter rescue is permitted.
