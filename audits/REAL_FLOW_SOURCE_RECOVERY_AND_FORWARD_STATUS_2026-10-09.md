# CRYPTO LAB — REAL FLOW SOURCE RECOVERY HANDOFF (2026-10-09)

Authority: operational audit only. No change to frozen scientific hypotheses, no trading or exchange/account mutation.

## 1. ABSORPTION-FAILED-AUCTION-001 — SOURCE_STALE_CONFIRMED
Canonical active branch: `absorption-failed-auction-v0.1`.
Real receipt path: `absorption_failed_auction/forward/COLLECTOR_STATE.json`.
Parent: `TV-FOOTPRINT-CALIBRATION-001` MM-V1 `BINANCE:BTCUSDT` spot, UTC 5-minute footprint.
Frozen prospective event boundary: 1790860200000 ms, 2016 immediately preceding *valid consecutive* 5-minute bars required for rolling baseline; source transport >=99%; no outcomes opened until >=100 FAILED_AUCTION and >=100 EFFICIENT_ACCEPTANCE over >=30 UTC dates.

As of 2026-10-09T10:48Z audit:
- last committed authentic current intake `TVFP_2026-10-01.csv`: final 5-minute bar close `1790864700000` (2026-10-01 14:25 UTC), 174 rows.
- last immutable Vault daily archive `2026-09-30` ending at `1790812500000`: source archive is **202.89 hours old**.
- committed forward state has 16 eligible bars, ALL NON_EXTREME, 0 FAILED_AUCTION, 0 EFFICIENT_ACCEPTANCE.
- audited intake age **188.39h**, audited Ledger last close matches intake.
- read-only diagnostic run https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37919833377; 14/14 synthetic tests PASS, observed state `SOURCE_STALE_OR_LEDGER_LAG__NO_NEW_FORWARD_EVIDENCE`.
- immutable audit artifact 11610789926.

### What this DOES and DOES NOT prove
The GitHub evidence chain is stale. This does NOT by itself prove whether the TradingView alert stopped, the Render receiver stopped, Render logs expired, or daily archival ceased. GitHub collector status `FORWARD_EVENT_COLLECTION_ACTIVE` meant code completed over a static intake, NOT fresh sensor acquisition. Rerunning with unchanged intake has no scientific value.

### Exact upstream recovery actions
Operator/account owner needs to:
1. In TradingView, check that `SRC Crypto Lab Market Microscope V1` still compiles, is applied to `BINANCE:BTCUSDT` **5m**, shows `Footprint AVAILABLE`, and its alert remains enabled for **Any alert() function call** at bar close. Do not modify source indicators, market identity or scientific parameters.
2. In Render workspace `Laboratorio`, inspect research-only service `tv-footprint-calibration-ingest-v01` (documented service id `srv-daqgvt0u01pc7384vsa0`) and recent application logs for authentic `TVFP_RECEIPT` records. Never disclose the secret webhook token. The endpoint's `GET /health` is liveness only; it cannot prove authentic closed-bar delivery.
3. If authentic receipts exist in unexpired logs, export raw verified records into an immutable new UTC daily Vault snapshot, preserving dedup keys and SHA-256 identity. If logs do not contain missing bars or expired, **preserve gaps**: no fake TradingView footprint reconstruction from Binance aggTrades or OHLCV, no backdating, no manual interpolation.
4. Source restart must not immediately claim rolling baseline readiness: original V0.1.1 protocol requires **2016 immediately preceding consecutive valid 5-minute bars** before a new candidate bar can be classified. At 288 bars/day this implies **seven complete consecutive UTC days** of new valid 5m observations after any irreparable gap. Preserve all earlier accepted episodes and source coverage records rather than deleting prior evidence.
5. Source owner must publish a new integrity receipt and causal boundary, then use the existing original source-only protocol and failing-closed continuity before any event collection/return unlock. Exact science remains unchanged.
6. Consider longer-term durable storage for the immutable telemetry log; existing Render app logs are a temporary seven-day ledger and cannot replace permanent, verified snapshots.

We could not inspect the private Render workspace directly: connector requires the user to choose a workspace explicitly. No account changes have been attempted.

## 2. LICP-001 — STILL FORWARD_INSUFFICIENT
Canonical branch `liquidation-cascade-propagation-v0.1`.
2026-10-09 latest completed run before next continuation: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37904459817
- 11 valid shard receipts, 14 unique raw IDs, **10 independent qualifying BTC_CONFIRMED episodes** in two UTC dates (2026-10-05 and 2026-10-08).
- Need FIRST 20 independent episodes across >=3 UTC dates; no backfill across gaps, costs 16bps base/32bps stress and 60-second direction frozen.
- New single read-only 600s shard launched: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37919982538, head `73f4f4f2de21a550a88b8f025e634ccacff12fc7`. Exact new verdict must be read from finished immutable artifact rather than inferred.
- No live trading or account reads.

## 3. LIQUIDATION-PRESSURE-002-FORWARD — VALID SOURCE, EXTREMELY LOW EVENT RATE
Canonical branch `liquidation-pressure-002-forward-v0.1`. 
- Public Bybit `allLiquidation` source-only q95 threshold calibrated over 25.36h, 2,917 raw liquidations, 5 eligible assets plus BNB ineligible due to <30 5s windows; this is SOURCE_CALIBRATION_PASS, not economic evidence.
- Frozen economic 5s burst reversal / 30s L2 depth execution needs >=500 independent q95 events, >=75 in >=3 symbols, >=14 distinct UTC dates.
- Authoritative first 45-minute capture run https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/36036229107 generated only **1 completed independent event**; `INSUFFICIENT_FORWARD_SAMPLE`. Duplicate launch 36036237576 NON_AUTHORITATIVE; do not pool.
- Do not declare a tradable edge from engineering/calibration PASS. Avoid spawning duplicate capture pipelines without a durable dedup-preserving collection schedule.

## 4. Statistically confirmed but economically tiny flow mechanism
`EXTREME-FLOW-REVERSION-OOS-001`: 2025 untouched OOS, 948 events, +2.4075bps average gross fade and -0.5925bps average net at even 3bps RT. **Mechanism survives; execution edge unproven**. Terminal scientific identity is closed; do not rescue by cherry-picking venue/cost assumptions.

## Priority after this handoff
A. Restore actual TradingView telemetry source with owner-controlled alert/Render log inspection, strictly preserving source gaps and seven-day warmup before future Failed-Auction event classification.
B. Continue canonical LICP first-20 episodic forward, preserving artifact SHA receipts and costs.
C. Maintain LP2 frozen calibration and collection state without duplicate overlapping runs.
D. Do not promote any of these to automatic live execution without independently defensible transaction-cost and capacity evidence.

No main merge, orders, wallets, Render mutation, authenticated exchange access or post-outcome tuning.
