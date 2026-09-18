# COINBASE-BINANCE-LEADLAG-001 — SOURCE / DISCOVERY CLOSEOUT V0.1

Date: 2026-09-18
Branch: coinbase-binance-leadlag-v0.1
Frozen MVE: CBLL-USDT-5M-Z3-001

## CANONICAL CLASSIFICATION

DATA_FAILURE

Reason:
- BTC synchronized 5m coverage = 97.5176% < frozen 99.5%
- ETH synchronized 5m coverage = 94.9615% < frozen 99.5%

The frozen protocol required a full contiguous prior rolling window and >=99.5% synchronized coverage. Those gates were not met.

## SOURCE SEMANTICS

Coinbase historical candle data is not guaranteed to publish a candle for intervals without ticks. Therefore the exact public candle route used by this frozen USDT-quoted MVE is structurally incompatible with the 99.5% synchronized-bar requirement for these products.

## ECONOMIC DIAGNOSTICS — NON-CANONICAL / NON-PROMOTABLE

Because DATA_FAILURE occurred before scientific adjudication, the following diagnostics do not constitute a valid economic verdict:
- resolved trades observed: 138
- base mean net R: -0.0147049
- base PF: 0.953234
- stress mean net R: -0.1147049
- stress PF: 0.689615
- bootstrap daily lower 95%: -0.0251985
- 2022 base mean net R: +0.0033450
- 2023 base mean net R: -0.1277544
- BTC base mean net R: -0.0206567
- ETH base mean net R: -0.0059897

These diagnostics provide no basis for source-rule rescue.

## NO RESCUE

Do not lower the 99.5% source gate, switch post-outcome to Coinbase USD products, fill missing candles synthetically, change timeframe, invert direction, change threshold or alter costs under this MVE ID.

This closeout preserves DATA_FAILURE / no promotion. It is not relabelled NO_EDGE.

2024 protected validation remained unopened.
2025/2026 unopened.
Live trading false.
Exchange mutation false.
Merge to main false.
