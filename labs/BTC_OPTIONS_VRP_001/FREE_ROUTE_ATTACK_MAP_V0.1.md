# BTC-OPTIONS-VRP-001 — FREE ROUTE ATTACK MAP V0.1

Date: 2026-09-19
Branch: `btc-options-vrp-free-route-attack-v0.1`
Authority: `OVRP-EXEC-FREE-ROUTE-001-SOURCE`

## Scientific boundary

This is a source-only, outcome-blind procurement attack. The parent Discovery remains `DISCOVERY_PASS_VRP_EXISTS`. The old execution MVE remains closed as `EXECUTION_DATA_LIQUIDITY_INSUFFICIENT` with 19 executable episodes versus its frozen minimum 120. Nothing in this branch may rewrite, extend or rescue that MVE.

No returns, PnL, expectancy, PF, drawdown, future realized variance, 2025/2026 data, live trading, exchange mutation, parameter tuning or merge to main is authorized.

## Priority order

### P1 — Cryptarbitrage free 2024H1 parquet
Public Deribit Insights material states that a free parquet file contains hourly snapshots of all BTC options from 2024-01-13 through 2024-07-27. Attack only provenance, direct-file recovery, SHA256, schema, timestamp frequency and BBO/size coverage. Current state: `DIRECT_FILE_LINK_RECOVERY_PENDING`.

### P2 — Blockchain Research Center order-book database
Published research states a database contains 8,444,664 Deribit order-book snapshots collected 2021-04-01 through 2022-04-01 and includes BTC options and futures. The current BRC request page describes member-only research data and presently labels its Deribit dataset primarily as BTC futures/LOB, so dataset identity must be reconciled before use. Current state: `ACCESS_AND_DATASET_IDENTITY_VERIFICATION_PENDING`.

### P3 — optionsDX public sample
The public Deribit option-chain schema exposes timestamp, instrument, expiry, strike, right, underlying, bid/ask prices, bid/ask sizes, OI, volume, Greeks and mark IV. The public sample target is `https://www.optionsdx.com/wp-content/uploads/2022/01/btc_sample.csv`. Current runtime could identify the target but did not retrieve the CSV bytes, so this is not yet a payload pass. Current state: `SCHEMA_PASS_PAYLOAD_RETRIEVAL_PENDING`.

### P4 — CoinAPI signup-credit probe
Already frozen separately as `OVRP-EXEC-SOURCE-COINAPI-PROBE-001`. It requires a user-owned API credential/payment-method account. Keep at zero cash spend and do not cross into paid overage. Current state: `USER_CREDENTIAL_GATED`.

### P5 — Tardis commercial fallback
Already proven structurally feasible under `OVRP-EXEC-SOURCE-TARDIS-PROBE-002`. Do not purchase yet. First minimize required fields/dates and estimate the smallest legitimate commercial request. Current state: `LAST_RESORT_COST_ESTIMATION_ONLY`.

## Cost-minimization principle

A future execution MVE must not automatically buy full-depth L2. First determine prospectively whether top-of-book `options_chain` snapshots with timestamp, bid/ask price and amount are sufficient for the exact frozen execution semantics. Dedicated quote/L2 data is required only if the future MVE explicitly needs information not present in point-in-time option-chain BBO.

This is a data-cost decision only, not a performance-based model change.

## Stop rules

1. No weakening prior source thresholds after observing failures.
2. No use of external published strategy PnL to select our parameters.
3. No substitution of another venue into the existing Deribit parent MVE.
4. No user credential, card, wallet, API key or payment is requested until all public zero-cost routes are exhausted.
5. If free routes are insufficient, produce a bounded purchase bill of materials and exact expected cash cost before asking for authorization.
