# CMM-001 — SOURCE TRANSPORT REMEDIATION V0.2

Date: 2026-09-25

## Trigger
Source Gate V0.1 returned 4/5 PASS. Binance BTCUSDT funding failed only because the GitHub Actions runner received HTTP 451 from the public REST transport.

## Allowed correction
Transport only:
- frozen variable remains BTCUSDT perpetual funding;
- frozen deterministic probes remain January 2021, 2022, 2023 and 2024;
- frozen minimum remains >=80 valid funding records per probe;
- no BTC returns, PnL, 2025 or 2026 outcomes may be opened.

V0.2 uses Binance's public Data Vision monthly fundingRate archive and verifies the provider-published SHA256 CHECKSUM for every tested ZIP.

## Explicit non-change
No hypothesis, threshold, direction, horizon, cost, component weight, period or promotion criterion is changed.

Historical open-interest remains excluded from V0.1. This remediation is not permission to expand the model after the freeze.

## Classification semantics
A failed V0.2 remains SOURCE_BLOCKED and is not NO_EDGE.
A passed V0.2 authorizes only drafting a separate pre-Discovery authority; it does not itself authorize Discovery.
