# DEFI-LIQUIDATION-SHOCK-001 — SOURCE GATE OPERATIONAL CHECKPOINT V0.3A

Date: 2026-09-22
Posture: `SOURCE_ONLY / OUTCOME_BLIND / FAIL_CLOSED`

This checkpoint records operational state only. It does not change decoder identity, scientific hypotheses, event definitions, thresholds, outcomes or promotion state.

## Closed first-success boundaries

### Kamino Lend
`KAMINO_FIRST_SUCCESS_BOUNDARY_RPC_PASS`
- 2023-11-17T14:48:24Z
- slot 230572965
- RAW-verified

### Save/Solend 0x11
`SAVE11_FIRST_SUCCESS_BOUNDARY_RPC_PASS`
- 2024-07-19T19:30:52Z
- slot 278496102
- RAW-verified

These are closed and MUST NOT be reopened.

## marginfi V0.3 operational cancellation

Run: `35771014450`
Conclusion: `cancelled`
Scientific verdict: NONE

The run completed and persisted raw signature pages through page 205 before cancellation.

Recovery:
- classification: `MARGINFI_V03_CANCEL_RECOVERY_CURSOR_EXTRACTED`
- accepted page: 205
- page SHA256: `72fce2cff5cc66d3b8881fbd7e9b6d17743f2c8fb30370073fd337ca3276f6b0`
- resume signature: `53dZ2HZHdFMisHmhPS1BS4pXhaD98YggaS7zYwshBFwza5mntJTANDvWthxagjgxc39eTg8eCq5eoyqFfTrKVW6m`
- slot: `238600457`
- blockTime: `1703805655`
- tx status: success
- parent artifact: `10713843479`
- artifact SHA256: `d33e966a59d76af2096920e4f169a406d7dcf7fcf4bf17509ab5000abdf727c3`

## Save 0x0c V0.3 operational cancellation

Run: `35771022352`
Conclusion: `cancelled`
Scientific verdict: NONE

Artifact contained `signatures_page_0218.json`, but logs only confirmed fully processed page 217.

Fail-closed rule:
- page 218 is preserved as orphan evidence but REJECTED as an authoritative resume cursor.

Conservative recovery:
- classification: `SAVE0C_V03_SAFE_CURSOR_PAGE217_EXTRACTED`
- accepted page: 217
- page SHA256: `f21c44c8525bd11b0f1227d709cce16b1a79e10429570faa6766dfa1111a269c`
- resume signature: `4XfzrMP3m4vJSBmnsoqA9kG3pjRhjBvbCRrTeh3162FSzBoyVegaFxiCWxyaxrf5yxEGmtjoyM5qA5W9KUHLAyfu`
- slot: `175929092`
- blockTime: `1675484461`
- tx status: failed attempt; cursor only
- parent artifact: `10714501324`
- artifact SHA256: `b5284d198c7e5101bdd2ac5c0136c51248dbf002e1f42051e84091ab098bbf6b`

## Transport strategy change

The scientific contract is unchanged, but 5000-page backward monoliths are no longer the preferred transport.

Two safer routes are now prepared:
1. short durable checkpointed continuations from the recovered cursors;
2. prospectively frozen early-boundary anchor search, which adjudicates the earliest interval first and expands only according to a pre-frozen chronological schedule.

Prepared early-boundary branches:
- `dls-marginfi-early-boundary-anchor-v0.1`
- `dls-save0c-early-boundary-anchor-v0.1`

No early-boundary source run has been launched yet; Drift remains the current primary source sub-gate.

## Drift historical S3 route

Historical documentation establishes:
- market trades/funding are market-scoped;
- `liquidationRecords` are USER-scoped: `user/{accountKey}/liquidationRecords/{year}/{YYYYMMDD}`.

Therefore the earlier market-scoped liquidation existence probes are technically invalid for liquidation-route adjudication.

GET-status-only V0.3:
- run: `35772066480`
- classification: `DRIFT_S3_GET_STATUS_CONTROL_NOT_FOUND`
- body bytes read: 0
- documented market trade/funding control paths returned 404.

Interpretation:
`CURRENT_HISTORICAL_S3_DOCUMENTED_OBJECT_ROUTE_NOT_SERVING_CONTROLS`

This is a source/transport state, not `NO_EDGE`. Do not continue guessing S3 object paths unless new provenance evidence appears.

## Drift early-chain route

Current preferred source route:
- target upper cursor time: `2022-12-01T00:00:00Z`
- frozen lower boundary: `2022-11-04T15:17:54Z`
- program: `dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH`

V0.1 used full block transaction detail and is transport-heavy.
V0.2 is a technical supersession using Solana `getBlock(transactionDetails="accounts")`, preserving the exact target/program/chronology while fetching only signatures and account keys.

V0.2 run: `35773123164`

If the upper anchor passes, the next authorized source-only action is one complete earliest-slice resolver for all four frozen Drift liquidation discriminators simultaneously.

## Firewall

No prices.
No returns.
No PnL.
No future direction.
No protected 2025/2026 market outcomes.
No live trading.
No orders.
No wallets.
No exchange mutation.
No paid source.
No account creation.
No merge to main.
