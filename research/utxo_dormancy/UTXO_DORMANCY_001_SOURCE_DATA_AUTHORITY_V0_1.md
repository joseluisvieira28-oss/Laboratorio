# UTXO-DORMANCY-001 — COIN DAYS DESTROYED — SOURCE/DATA GATE AUTHORITY V0.1

STATUS: FROZEN PRE-OUTCOME / SOURCE-DATA GATE ONLY

PROGRAM: CRYPTO GAP ANALYSIS V2 — NEW MECHANISM FRONTIER #15

## Governance
Research-only. Fail-closed. No live trading. No exchange mutation. No exchange POST/PUT/PATCH/DELETE. No merge to main. No deployment. No post-outcome tuning. No cherry-picking. 2025 LOCKED. 2026 LOCKED. No BTC market-price values, returns, PnL, signal performance, protected-year outcomes or market outcome datasets may be acquired or computed under this authority.

## Anti-duplication
Drive, GitHub and File Library were searched before freeze. No canonical UTXO dormancy / Coin Days Destroyed / TxTfrValDayDst laboratory or materially equivalent mechanism was recovered. This mechanism is distinct from OHLC/indicator transforms, funding/OI, generic taker flow, options skew, macro surprise/transmission, miner hash/difficulty stress, staking queues, stablecoin supply, cross-chain bridges, protocol fees and Curve stablecoin peg stress.

FAMILY_ID: UTXO-DORMANCY-001
SOURCE_GATE_ID: UD-CDD-001
DRIVE_AUTHORITY_SHELL_ID: 1FcQvRBRM_C9KJOg_RNvdEvqRPLLFWi-SihewMB-Wf7o

## Economic mechanism
Coin Days Destroyed measures value-weighted age of UTXOs when they are spent. A rise in old-coin reactivation can represent latent long-term-holder supply becoming economically active.

Frozen qualitative future-hypothesis direction: greater old-coin reactivation / dormancy destruction -> worse subsequent BTC performance.

This direction is frozen before any source values or market outcomes are opened. No trading threshold, transform, horizon, cost, percentile, rebalance or execution rule is frozen yet.

## Frozen primary source
Provider: Coin Metrics Community API v4.
Endpoint: https://community-api.coinmetrics.io/v4/timeseries/asset-metrics
Asset: btc only.
Metric: TxTfrValDayDst only.
Frequency: 1d only.
Paging: paging_from=start.
SOURCE_START: 2017-01-01T00:00:00Z.
SOURCE_END: 2024-12-31T23:59:59Z.

The request MUST explicitly contain both start_time and end_time. It MUST NOT request PriceUSD, ReferenceRate, market-price fields, another on-chain factor, mining metrics or any exchange dataset. It MUST NOT query latest/current data.

## Source/Data Gate requirements
1. The Community endpoint is accessible without private credentials and returns only the requested btc/time/TxTfrValDayDst payload plus provider status metadata if supplied.
2. Zero observations dated 2025 or 2026 are permitted.
3. Daily timestamps must be deterministic, unique and UTC-aligned; duplicate dates are enumerated.
4. TxTfrValDayDst must be present, parseable, finite and non-negative.
5. Minimum clean sample: >= 2,000 non-null daily observations inside the frozen window and >= 6 distinct calendar years represented. This is a source adequacy gate, not an outcome gate.
6. Missing dates/nulls/non-finite values remain visible. No interpolation, forward fill, backward fill or fabricated backfill.
7. Raw HTTP response bytes for every page, exact request URLs/parameters, response headers when available, manifests and SHA256 hashes are preserved.
8. Only TxTfrValDayDst may be inspected. TxTfrValDayDstMean, UTXO age metrics, price-normalized variants and alternate dormancy metrics are prohibited in this V0.1 Source Gate.
9. No Binance/Coinbase/Bybit/Kraken or other exchange market-data source may be contacted.
10. price_values_opened=false; signal_series_computed=false; returns_computed=false; pnl_computed=false; performance_statistics_computed=false; access_2025=false; access_2026=false.

## Terminal source states
SOURCE_DATA_PASS — frozen metric has sufficient reproducible pre-2025 history for prospective MVE design.
SOURCE_AUTH_BLOCKED — legitimate access requires unavailable credentials/entitlement.
DATA_FAILURE — accessible data fail completeness/validity requirements.
PROVENANCE_FAILURE — source identity, timestamps, frozen boundary or leakage guards fail.
INSUFFICIENT_SAMPLE — clean source exists but misses frozen sample floor.
TECHNICAL_FAILURE — implementation/transport failure; not scientific evidence.
NO_EDGE is prohibited at this stage.

## Provisional MVE boundary
If and only if SOURCE_DATA_PASS is recorded, a separate prospective pre-Discovery authority must freeze the TxTfrValDayDst transform, threshold, holding horizon, execution timing, costs and promotion gates before any BTC return is opened. No choice may be selected from market outcomes.

## Current authorized action
Implement and execute the isolated outcome-blind Source/Data Gate only. Stop before the first BTC market-price value, return or PnL.
