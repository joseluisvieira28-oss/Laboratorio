# RW-HL-EXITFLOW-001 — SOURCE FIRST / PRE-OBSERVATION AUTHORITY V0.1
Date: 2026-10-09
Status: **SOURCE_GATES_ONLY / NO ECONOMIC HYPOTHESIS AUTHORIZED FOR RETURNS**
Base: audit/science-only-all-fronts-2026-10-08
Trading authority: NONE

## Authenticated origin of the idea, and its limits
Robot Wealth / Kris Longmore, `Hyperliquid Carry Looks Trendy` (published 2025-09-14):
https://edgealchemy.robotwealth.com/p/hyperliquid-carry-looks-trendy
The original author compares cross-sectional Binance carry with Hyperliquid, argues negative funding ("shorts pay longs") on HL is associated with further price decline rather than the usual mean reversion, and **speculates** informed sellers may be quietly using perps rather than spot. He suggests that a rise in OI while price falls around new listings could reveal structurally motivated shorting and warns of short squeezes. It is a HYPOTHESIS, not an authenticated identification of insiders, causal proof, or guaranteed short opportunity. His factor examples include frictionless returns; no transferable independently net-of-cost edge certified here.

IMPORTANT: This is a *written public article*, not proof that we inspected full YouTube video transcripts.

## Prior Crypto Lab duplication barriers
- `PERP-LAUNCH-POSTLAUNCH-SHORT-001`: already froze **SHORT newly launched Binance USD-M token / LONG BTC 24h**, 83 qualified 2023 listings, but frozen result `INSUFFICIENT_DISCOVERY_SAMPLE`, 0 source-complete pairs under its then-used source transport. 2024 protected outcomes remain unopened. Our new study must NOT claim generic post-launch short as novel or resurrect its failed data route.
- `PERP-LAUNCH-BASIS-CONVERGENCE-001`: 2023 Discovery after costs NO EDGE, 2024 remained closed. Never rename launch basis fade to HL sell pressure.
- `PERP-LAUNCH-IMPULSE-REVERSION-001`: already frozen short/long the 15m launch impulse versus BTC. Cannot recast that geometry as new.
- `FUNDING-DISPERSION-DN-001`: historical Bybit/OKX funding carry exploration `SOURCE_BLOCKED`. Pure funding differential is already a studied economic family.
- `DCV-001`: funding × open interest × realized volatility triple interaction failed frozen Discovery; no retuned filter on same historical data.
- `MEXC-LAUNCHPOOL-REWARD-TOKEN-SELLPRESSURE-001`: source blocked for 2025/26 reward-token launch market outcomes (4/11 vs frozen min 10) and 2026 exposure recorded. Do not recycle that cohort.
- Many additional exact funding/basis/launch candidate branches exist; a new lab requires independent *Hyperliquid seller-flow* source, genuine contemporaneous OI, and prospectively collected first-seen universe.

## Proposed economically motivated mechanism (UNTESTED)
Potentially constrained / informed sellers may open new short exposure in small newly listed perps; when rising OI coincides with persistently negative realized funding (shorts pay longs) and **already observed** weak contemporaneous price, the selling pressure may persist. This is NOT an ability to identify insider wallets, true funding motives, hidden position sides, or anyone's nonpublic information; OI increases equally with an opposing long, so interpretation is circumstantial.

The only novel candidate relative to older Binance postlaunch SHORT is an explicitly pre-observed **Hyperliquid-specific OI growth + negative funding** source and a matched causal comparator (e.g. matched liquid mature perps / Binance crossvenue), NOT new listings or short signals alone.

**DO NOT construct actual triggers, lookback N, threshold, exact entry/exit, stop, fees, risk/position sizing, forecast horizon, selected coins, OOS/economic test before the prospective/source gates and separate immutable scientific freeze.** All 2026 outcomes remain forward-locked and must not be backfilled as if prospectively observed.

## G0: Actual permitted free sources
Public market-only Hyperliquid `POST https://api.hyperliquid.xyz/info`:
- `{"type":"metaAndAssetCtxs"}` gives CURRENT joined asset metadata and OI/mark/funding/volume.
- `{"type":"meta"}` provides current listed universe (not historical listing times).
- `{"type":"fundingHistory","coin":"BTC","startTime":...,"endTime":...}` provides realized historical funding, but not OI.
- These endpoints require no account address, signatures, user ledgers, wallets or authentication; they are POST for a public read, NOT trading/exchange mutations.
- `fundingHistory` + `metaAndAssetCtxs` are different time regimes; never present a 2026 live OI value as if it were 2023/24 OI.
- Source: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint/perpetuals

Hyperliquid official historical archive documents `s3://hyperliquid-archive/asset_ctxs/YYYYMMDD.csv.lz4` for historical asset contexts including OI. **Requester-pays transfer and access costs are mandatory** by official docs, and updates are monthly with possible gaps:
https://hyperliquid.gitbook.io/hyperliquid-docs/historical-data
NO S3 access/no spend authorized in this task.

Public Binance exchange metadata / funding can later act as comparator, but do NOT assume Binance and HL universes or assets are equivalent. Binance account/auth endpoints prohibited.

## G1: Pre-observation source proof allowed
1. Obtain one authenticated-free, public `metaAndAssetCtxs` response ONLY; validate length of `universe` matches contexts, unique names, numeric OI/mark/funding, no account fields. Save data as a T0 *source snapshot with receive timestamp* and SHA256, distinct from any future economic return.
2. Take exactly ONE second public snapshot after **60–120 seconds** purely to establish collection continuity, current universe identity and monotone receive times. If values differ, that is not predictive inference; no 2026 future markouts/price delta, no PnL.
3. Optional bounded historical `fundingHistory` probe for BTC, 2024-01-01..2024-01-02, reporting ONLY record count, first/last timestamps and key set (never funding outcomes / price results).
4. No `candleSnapshot` (recent 5k candle cap), no S3, no paid API. Public requests <= 4 total, no looping/rate-limit evasion.
5. Artifact must be **fail-closed** on malformed schema, no account/user fields, no data substitution, no training labels. Preserve raw JSON snapshots only in temporary GH Actions artifact (not as executable signals); avoid posting actual market values into PR summaries. Mark `CAPTURE_ONLY, OUTCOME_BLIND, NO_TRADING`.

## G2: Future actual prospective authority prerequisites
- Continuous daily/hourly observations persisted BEFORE outcomes to a trusted, immutable, checksum-bound store.
- Explicit first-observed universe introduction vs exact official listing time: first-observed is an interval-censored source observation, NOT certified exact T0. Require official timestamp evidence separately.
- Minimum complete time and asset coverage; predefined missing/duplicates/restart handling; historical source gaps preserved.
- Source for comparable public tradable spreads, maker/taker route, funding sign conventions; no authenticated account use without new instruction.
- Independent full **numerical hypothesis and economic freeze** BEFORE any return/markout is opened; minimum event counts and registered costs; 2026 episodes forward-only.

## Decision logic
- If public API current OI/funding unavailable: `SOURCE_BLOCKED`.
- If public API works but free historical OI for exact 2023–24 unavailable: `HISTORICAL_OI_UNAVAILABLE_NO_SPEND / PROSPECTIVE_SOURCE_POSSIBLE`.
- Even if G1 passes: `SOURCE_SNAPSHOT_PASS_ONLY`, NOT `MECHANISM_SURVIVES`, `NO_EDGE`, `QUASE_DIAMANTE` or `MICRO_LIVE_GO`.
- No claims of historical OOS profit without actual authenticated source and a separate freeze.
- No main merge, orders, authenticated exchanges, wallets, capital, Render deploy/mutation, 2025/2026 protected outcome access or post-outcome tuning.
