# COINBASE-BINANCE-LEADLAG-001 — SOURCE RECOVERY AUDIT V0.2

Date: 2026-09-18
Branch: coinbase-binance-leadlag-v0.1
Parent MVE: CBLL-USDT-5M-Z3-001
Scope: SOURCE / PROVENANCE ONLY
Outcome status: LOCKED / NOT REOPENED

## CANONICAL PARENT STATE

The parent MVE remains:

DATA_FAILURE

Frozen source gate:
- BTC synchronized 5m coverage >= 99.5% required
- ETH synchronized 5m coverage >= 99.5% required

Observed under V0.1:
- BTC synchronized coverage: 97.5176%
- ETH synchronized coverage: 94.9615%

No economic verdict is created by this audit.

## EXACT FAILURE CAUSE

The V0.1 Coinbase route used the official Exchange REST historical candles endpoint for BTC-USDT and ETH-USDT.

Coinbase's current official documentation explicitly states that historical rate data may be incomplete and that no candle data is published for intervals where there are no ticks. Therefore the V0.1 route is structurally capable of producing missing 5-minute buckets even when transport and parsing are correct.

This confirms the old failure is a source-density / observable-availability problem, not a transient network failure.

## PROHIBITED RESCUES

This audit does NOT authorize:
- lowering the 99.5% synchronized-coverage gate;
- filling missing Coinbase candles synthetically;
- last-price carry-forward;
- switching Coinbase BTC-USDT/ETH-USDT to USD or USDC products;
- changing timeframe;
- changing rolling window or z threshold;
- changing direction, stops, targets, hold, costs or execution rules;
- opening 2024;
- opening 2025 or 2026;
- computing or re-reading economic outcomes.

## CURRENT OFFICIAL HIGH-FIDELITY ROUTE

Coinbase currently offers historical Exchange tick-level trade data through Coinbase Data Marketplace.

Official product documentation states:
- tick-level trade datasets capture executed trades for listed Exchange assets;
- timestamps are normalized at microsecond granularity;
- base / quote / price / quantity / side are provided;
- historical purchases are available;
- download examples explicitly include BTC-USDT files for 2022.

This is a materially higher-fidelity official source than grouped REST candles because bars can be reconstructed directly from authoritative trades.

However:
- it is a paid/licensed product;
- access requires purchase, contract/license and SFTP credentials;
- genuine zero-trade 5-minute intervals would still remain empty under the frozen MVE and may therefore continue to fail the 99.5% gate.

## SCIENTIFIC DECISION

FREE PUBLIC SOURCE RECOVERY: NOT IDENTIFIED

PAID OFFICIAL SOURCE RECOVERY: TECHNICALLY PLAUSIBLE / UNTESTED / AUTHORIZATION REQUIRED

The parent remains DATA_FAILURE. It is not relabelled NO_EDGE.

A source-only V0.2 recovery may execute only after separate explicit authorization to purchase/use the required Coinbase historical tick data and access credentials.

Until then:
- 2024 remains protected and unopened;
- 2025/2026 remain unopened;
- live trading false;
- exchange mutation false;
- orders false;
- merge to main false.

## CURRENT EXTERNAL SOURCE REFERENCES

- Coinbase Exchange API — Get product candles:
  https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/products/get-product-candles
- Coinbase Data Marketplace — Products offered:
  https://help.coinbase.com/en/data-marketplace/getting-started/data-marketplace-products
- Coinbase Data Marketplace — Download files:
  https://help.coinbase.com/en/data-marketplace/access-data/download-files
- Coinbase Data Marketplace — Getting started:
  https://help.coinbase.com/en/data-marketplace/getting-started/coinbase-data-marketplace
