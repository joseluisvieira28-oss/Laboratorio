# DEFI-LIQUIDATION-SHOCK-001 — SAVE11 OFFICIAL API TIMESTAMP/PARAMETER DIAGNOSTIC V0.2

Date: 2026-09-23
Status: TECHNICAL SOURCE-ROUTE DIAGNOSTIC / OUTCOME-BLIND / FAIL-CLOSED

V0.1 locator result is preserved unchanged:
`SAVE11_OFFICIAL_API_LOCATOR_BOUNDARY_MISS`.

This V0.2 does NOT rescue or reinterpret V0.1. It answers only why the official API returned structured liquidation-attempt records but zero records under the prospectively frozen V0.1 timestamp filter.

Target route:
`https://api.solend.fi/history-v2/liquidation-attempts`

Frozen reference window:
- start Unix seconds: `1721417452`
- end Unix seconds: `1721433600`

## Prospectively frozen query variants

1. bare route
2. `start=<seconds>&end=<seconds>`
3. `start_time=<seconds>&end_time=<seconds>`
4. `startTimestamp=<seconds>&endTimestamp=<seconds>`
5. `from=<seconds>&to=<seconds>`
6. `start=<ISO8601>&end=<ISO8601>`

No variant is selected after seeing values; all six are executed and retained as a transport/schema matrix.

## Persisted evidence allowed

For each variant:
- HTTP status
- response byte count
- response SHA256
- number of recursively discovered objects containing all four keys:
  `signature, slot, success, timestamp`
- timestamp scalar type counts
- numeric timestamp minimum and maximum
- counts that fall inside the frozen window under three fixed interpretations:
  - raw Unix seconds
  - floor(raw / 1000) Unix milliseconds
  - floor(raw / 1000000) Unix microseconds
- count of string timestamps parseable as ISO8601 and inside the window

Forbidden persisted evidence:
- signatures
- fee payer
- market/reserve/user/account identifiers
- amounts
- prices
- token values
- balances
- PnL/returns/direction

Response SHA256 is allowed as source identity evidence; raw response bodies are not persisted.

## Interpretation

This diagnostic can identify likely query-parameter or timestamp-scale behavior only.
It cannot promote the official API to historical authority and cannot override RAW on-chain census results.

Classification:
- `SAVE11_OFFICIAL_API_TIMESTAMP_DIAGNOSTIC_COMPLETE` when at least one JSON 2xx response with candidate-shaped records is observed;
- `SAVE11_OFFICIAL_API_TIMESTAMP_DIAGNOSTIC_BLOCKED` otherwise.

Firewalls:
prices=false; amounts=false; balances=false; usd_values=false; signatures_persisted=false; returns=false; pnl=false; direction=false; market_outcomes=false; live_trading=false; orders=false; wallets=false; exchange_mutation=false; paid_source=false; account_creation=false; merge_main=false.
