# BINANCE-MARGIN-BORROW-ACCESS-001 — PRIOR SPOT CLOSEOUT V0.1

Date: 2026-09-17  
Status: **PRIOR_SPOT_PRIMARY_PASS**  
Branch: `binance-margin-borrow-access-v0.1`

## Canonical execution

- GitHub Actions run: `35269000941`
- canonical aggregate job: `105366121957`
- manifest classification: `PRIOR_SPOT_MANIFEST_PASS`
- manifest asset-event rows: 100
- same-announcement Spot confounds: 4
- rows requiring archive proof: 96
- manifest SHA-256: `c3d32fdeefd5f1970ec85d15e1e87fd7c11b65c0844e40389b51dc16fad9013c`
- canonical artifact: `BINANCE_MARGIN_BORROW_ACCESS_001_PRIOR_SPOT_V0_1`
- canonical artifact id: `10517374109`
- canonical artifact ZIP digest: `sha256:bb966915fd7175e7f7b92a2918bb4bd0722e7b3ebd90345df6f07d6a01fd12ca`

## Canonical result

`PRIOR_SPOT_PRIMARY_PASS`

- `PRIOR_SPOT_ARCHIVE_PASS`: **96**
- `ACCESS_CONFOUND`: **4**
- `PRIOR_SPOT_PRIMARY_UNRESOLVED`: **0**
- proved event years: **2023 and 2024**
- 8 / 8 deterministic probe shards: PASS
- missing candidate ids: 0
- duplicate candidate ids: 0

The four `ACCESS_CONFOUND` rows were prospectively identified because the same official announcement inseparably introduced initial Spot listing/trading for the asset. They are excluded from the clean mechanism universe before any outcome is opened.

For all 96 retained asset-events, an official Binance Vision `.CHECKSUM` for a Spot kline archive dated strictly before the event-information date was recovered. The market-data ZIP itself was not downloaded or parsed in this source gate.

## Safety

This gate opened no market-data values, OHLCV, returns, basis, borrow rates, borrow inventory, PnL, win rate, PF or drawdown. It used no authenticated Binance API/account data and performed no order, wallet, alert, webhook, exchange mutation or live-trading action. No 2025/2026 scientific path was requested.

## Consequence

The prior-Spot provenance requirement is satisfied for the 96 clean asset-events. This result is provenance only; it is not evidence of a trading edge or profitability.
