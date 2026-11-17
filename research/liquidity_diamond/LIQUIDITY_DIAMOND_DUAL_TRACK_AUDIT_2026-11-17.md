# LIQUIDITY DIAMOND — Dual-track forensic economic audit (2026-11-17)
**Authority:** Research-only; no orders, spend, credentials, wallet actions, deployment, protected holdout opening, changes to parent labs, or merges.
**Status:** LP economics = RESEARCH_GO / ECONOMIC_UNPROVEN; liquidation-shock trade = EXISTING_LAB_ONLY / NO NEW TRADE GO.
**Allocation heuristic:** LP-net-profit 65%, shock/source adjudication 35%. Allocation of research effort, NOT allocation of capital or estimated success probabilities.

## Direct evidence recovered from canonical Crypto Lab
1. AMM-LVR-CROSSVENUE-001 is a *CEX–DEX arbitrage searcher* experiment, NOT a test of returns from depositing liquidity. Ledger ROLLUP_V0.1 contains 1,556 unique transactions and 1,748 swaps on 25 UTC dates; 910 evaluable end-of-block states at 1,000 USDT/T0, 25 pre-inclusion-positive (2.75%). Full-cost accessibility remains UNPROVEN, economic eligible count claimed 0, PnL not computed. DEX/CEX searcher economics must not be presented as LP returns. Source: https://github.com/joseluisvieira28-oss/Laboratorio/blob/amm-lvr-crossvenue-001-v0.1/labs/amm-lvr-crossvenue-001/forward_ledger/ROLLUP_V0.1.json (blob SHA 96e263eadec468461da3fa246c8abe22ed84c828).
2. LICP-001 terminal forward closeout dated 2026-10-14: 20 episodes, 18 valid outcomes, 2/18 positive, mean BASE net −16.374554 bps and STRESS −32.374554 bps. TERMINAL NO_EDGE for that identity: do not retry same threshold/direction/cost variations. https://github.com/joseluisvieira28-oss/Laboratorio/blob/liquidation-cascade-propagation-v0.1/research/liquidation_cascade/LICP_001_FORWARD_ECONOMIC_CLOSEOUT_2026-10-14.md (blob SHA 4aca43193d55d693f82859f10c97cceb8554bf1a).
3. LIQUIDATION-PRESSURE-002-FORWARD source calibration (not outcome): 2,917 raw liquidation records over 25.36 h, 869 nonempty 5-second windows, q95 frozen candidates for BTC/ETH/SOL/XRP/DOGE (BNB insufficient in calibration); economic_outcomes_opened=false, pnl_computed=false. Existing orderbook replay and source gate engineering PASS are not profit. https://github.com/joseluisvieira28-oss/Laboratorio/blob/liquidation-pressure-002-forward-v0.1/labs/LIQUIDATION_PRESSURE_002_FORWARD/calibration/source_calibration_status_v0_1.json (blob SHA 952b12631c1a06b15a981b8ef07b40dd0a1f15cc).

## Independent public LP position-source probe: results and data-quality gates
Dataset: https://github.com/ThanosDrossos/IL_Measurement ; MIT; paper SAC'25 (DOI 10.1145/3672608.3707833). README states 30,058 *burn-event* observations in nine Uniswap v3 pools, not 30,058 independent positions. CSV parse: separator ';', decimal ','; fetch through GitHub public connector, no untrusted transactions/execution. On 2026-11-17, examined the following **complete CSVs where readable**; the large remaining full files were not returned by connector and must NOT be treated as checked. Economic diagnostic for these files was sum(lossVersusHODLExact + event_feesUSD), *before* gas, protocol fees, swaps, risk, taxes, independent verification, position deduplication and model consistency. Do NOT interpret as tradeable net profit.

| Complete CSV | Rows | Distinct event IDs | Unexpected positive IL rows | Negative fee rows | Naive USD sum (NOT PnL) | Git blob SHA |
|---|---:|---:|---:|---:|---:|---|
| DAI_USDC_500 (0.05%) | 414 | 397 | 80 | 2 | +234,012.02 | ab68f0cf6690b57cd26e018a854b2c020947c934 |
| DAI_USDC_100 (0.01%) | 816 | 785 | 133 | 0 | +182,712.57 | a33090679d99868abc057564948fe4ad20557be7 |
| USDC_WETH_10000 (1%) | 690 | 651 | 107 | 1 | −3,111,990,876.26 | 80a36c21be612580b271f6817124a7affc3d0646 |
| USDC_WETH_100 (0.01%) | 473 | 450 | 58 | 0 | −21,262,924.86 | 5474fa89e3b9f75df238770bec286ff98a9ad067 |
| MKR_WETH_10000 (1%) | 87 | 86 | 24 | 0 | +176,714.65 | f057eac64330d955e80fafd98a2b5163dd646714 |

**Adversarial anomalies:** positive lossVersusHODLExact in several files is unexpected for a conventionally defined loss-vs-holding benchmark (may reflect inconsistent hourly prices/partial closure/baseline construction; do not assert fraud or simply delete rows). Multiple identical `position_id#block` IDs need transaction-log proof before deduplication (could be legitimate partial burns). The 1% USDC/WETH file includes event `517651#17627451`: lossVersusHODLExact=−3,073,414,576.73 USD, event_feesUSD=−14,870,356.18 USD, initialValue=3,088,284,932.91 USD; dominates the aggregate and requires byte/chain reconstruction. Source README says 2022-05-01 to 2024-04-01 but some CSV timestamps examined lie in 2021 and beyond 2024-04-01; reconcile row/event time ranges before training. No post-hoc exclusion can be called scientific profitability. The nine *sample* CSVs are first-position slices, nonrandom and explicitly unsuitable for ranking pools; their exploratory positive results MUST NOT be promoted.

**Current economics changed:** official Uniswap docs note protocol fee activation on select v3 pools starting December 2025; when enabled the 0.05% tier may pay LPs 0.0375% rather than all 0.05%, and 0.01% tier 0.0075%. Verify each pool and effective block; do not project old gross fee rates into 2026. https://developers.uniswap.org/docs/get-started/concepts/fees
**Data access blocker:** DefiLlama free APY `/pools` and `/chart/{pool}` retired Nov 13, 2026 according to official docs. Do not design a new free-data pipeline around these endpoints. https://api-docs.defillama.com/ and https://newsletter.defillama.com/p/your-exchange-s-numbers-might-not-be-real-here-s-how-to-check

## Economic decision (both tracks)
**Track A — LP-NET-001: GO SOURCE/RECONSTRUCTION ONLY, NO CAPITAL.**
1. Reconstruct closed positions from onchain mint/increase, decrease, collect, NFT owner, tick range, prices and gas; distinguish each burn from each position. Reconcile raw anomalies with independent event receipts and true token decimals, token pricing and contemporaneous source.
2. Freeze pool candidate universe and all fee/protocol-fee schedules *before* evaluating outcomes. Comparators: same inventory HODL, wide LP, static concentrated LP, no LP, and explicit gas-adjusted net on same capital and same dates. Avoid advertised APY as realized returns.
3. Core incremental equation: `LP terminal tokens marked in USD + collected fees - HODL terminal inventory - open/close/rebalance gas - swaps/slippage - hedge/funding - applicable protocol/hook fees`. Report dollar PnL, % of initial capital and opportunity costs separately; mark `UNKNOWN` when flow is not independently reconstructed.
4. Chronological train/validation/untouched holdout, non-overlapping exit rules, cluster by pool/day/owner, bootstrap confidence, out-of-range time, adverse tail and ability to close with depth. If API key or external costs are needed, stop and request separate approval, never buy automatically.
5. PASS only if point-in-time event-level reconstruction and independently executable net after all real frictions, positive under conservative sensitivities and OOS survives with pre-registered policy. Otherwise SOURCE_BLOCKED/INCONCLUSIVE/NO_EDGE as applicable.

**Track B — LIQUIDITY-SHOCK-002: AUDIT THE ALREADY ACTIVE LP2 FIRST.**
1. Preserve LP2 exact frozen source, q95, event horizon, direction, cost assumptions and source timestamp; LICP-001 terminal NO_EDGE is closed. Do NOT rename the identical LICP strategy or retrospectively tune it.
2. If LP2 has no terminal future economic result, classify ECONOMIC_UNPROVEN; do not substitute reconstruction/parity/technical PASS for PnL. Check independent markouts vs randomized-time and volatility-regime controls, quote availability at time of signal, bid-ask/size/slippage/fee/funding/latency, missed trades and capacity.
3. Only propose a new *distinct* depth-withdrawal mechanism if pre-registered causal distinction is proven and underlying top-of-book/depth events and timestamped future fills can be sourced. Do not open any protected holdout or use capital.

## Current closeout
- Source + forensic audit: PASS (the reported records were read directly); a new real LP backtest was **NOT RUN**.
- LP economic GO: NO; potential worth testing but published CSV has unresolved anomalies and current 2026 fees differ.
- Shock economic GO: NO; LICP TERMINAL NO_EDGE, LP2 source-only, no new independent net result.
- Budget: 0 CHF; no secrets, trades, deployment or merge.
- Future decision hinge: recomputed clean position-level LP incremental return net of all costs on an independent time split; LP2 exact frozen forward economic receipt. Without these: no promotion.
