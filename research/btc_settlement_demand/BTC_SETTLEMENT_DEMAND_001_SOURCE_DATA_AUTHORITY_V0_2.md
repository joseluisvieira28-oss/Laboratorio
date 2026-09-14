# BTC-SETTLEMENT-DEMAND-001 — SOURCE/DATA GATE AUTHORITY V0.2

STATUS: FROZEN PRE-OUTCOME / SOURCE-DATA GATE ONLY
FAMILY_ID: BTC-SETTLEMENT-DEMAND-001
SOURCE_GATE_ID: BSD-TXCOUNT-002
DRIVE_AUTHORITY_ID: 1zSEtz0CWJAyV9CEF5JQHEF7QrJmf8dFV
DRIVE_AUTHORITY_SHA256: 74d310d5fbd2efdb4c4596dfebf7e18a19f7f43a93caa94a844c71f3c22d7f8b

BSD-TXCOUNT-001 remains CLOSED as PROVENANCE_FAILURE. V0.1 used timespan=2922days from 2017-01-01, which reaches 2025-01-01 and caused one protected source observation before fail-close. V0.2 changes only this administrative source boundary to timespan=2921days, which terminates exactly on 2024-12-31. No market outcome was opened and no economic rule was tuned.

## Governance
Research-only; fail-closed; no live trading; no exchange mutation; no main merge; no deployment; no post-outcome tuning; no cherry-picking. 2025 and 2026 are forbidden in V0.2. No BTC market-price values, returns, PnL, signal performance or protected-year values may be acquired or computed.

## Economic mechanism
Confirmed transaction count measures realized Bitcoin base-layer settlement activity. Frozen qualitative relation remains unchanged: stronger confirmed settlement demand -> better subsequent BTC performance. No trading transform, threshold, horizon, cost, percentile or execution rule is frozen yet.

## Frozen primary source
Provider: Blockchain.com Charts & Statistics API
Endpoint: https://api.blockchain.info/charts/n-transactions
Metric: n-transactions / Confirmed Transactions Per Day only
SOURCE_START: 2017-01-01T00:00:00Z
SOURCE_END: 2024-12-31T23:59:59Z
Frozen request: start=2017-01-01, timespan=2921days, format=json, sampled=false

## Source/Data Gate
Expected semantics: name=Confirmed Transactions Per Day; unit=Transactions; period=day. Zero observations >=2025-01-01. Unique UTC dates. Values finite/non-negative. Minimum >=2500 unique daily observations and >=7 calendar years. Preserve raw bytes, exact request URL, response headers, manifests and SHA256. No alternate chart, no exchange market data, no interpolation/fill.

## Guards
price_values_opened=false
signal_series_computed=false
returns_computed=false
pnl_computed=false
performance_statistics_computed=false
access_2025=false
access_2026=false

## Terminal states
SOURCE_DATA_PASS / SOURCE_AUTH_BLOCKED / DATA_FAILURE / PROVENANCE_FAILURE / INSUFFICIENT_SAMPLE / TECHNICAL_FAILURE. NO_EDGE prohibited.

If SOURCE_DATA_PASS, stop. A separate prospective pre-Discovery authority must freeze the actual MVE before any BTC market return is opened.
