# HYPE-BUYBACK-FLOW-001 — SOURCE-ONLY SCIENTIFIC CLOSEOUT
Date: 2026-10-10 UTC
**FINAL CURRENT GATE STATE: SOURCE_BLOCKED** (historical AF execution identity, continuous complete source, and PIT latency not proven).
This does **NOT** mean NO_EDGE or no AF buys. The financial hypothesis has NOT been tested. NO TRADING AUTHORITY.

## 0. Non-negotiable authority
Read 2026-10-08 science all fronts audit (audit/science-only-all-fronts-2026-10-08), 2026-10-09 global net edge audit (parent branch), old ETH demand fees mixed and BTC fee-pressure NO EDGE. No resurrection or historical outcome reuse. New MVE is structurally distinct: fee-induced protocol buying of HYPE/USDC, not gas fee burn, funding cash carry, or CEX liquidation.

Read pre-source authority committed BEFORE calls:
`research/hype_buyback_flow_001/SOURCE_GATE_AUTHORITY_V0_1.md` commit `71d4d33fe73c0a91d266ce23410d9cd63a33733d`.
Read error-bound transport amendment committed BEFORE transport-only variant calls:
`research/hype_buyback_flow_001/SOURCE_TRANSPORT_AMENDMENT_V0_1_1.md` commit `0097bda9291606a049e1f9c22f3bfeef9fdc59aa`.

## 1. Official mechanism = verified; predictive edge = NOT investigated
Hyperliquid fee docs identify the Assistance Fund system address `0xfefefefefefefefefefefefefefefefefefefe` and L1-automatic conversion of fees to HYPE; documentation currently characterizes fund HYPE as permanently burned. DO NOT infer buy orders from transfers, fee amounts, spot balances, HYPE burning, or token unlocks.
Official source: https://hyperliquid.gitbook.io/hyperliquid-docs/trading/fees
A third-party tracker published 2026-10-10 approx $1.36bn cumulative buys, $72.2m trailing 30d and 47.9m HYPE; NOT independently verified in this lab. Tracker methodology includes reconstructed holdings curve in earlier periods and labels HYPE fund tokens as held, versus official burned wording. This is not an accepted exact-fill source nor an accepted realtime timestamped signal.

## 2. Exact source-only empirical evidence
Canonical GitHub Actions run: **38040421803 SUCCESS (CI only)**, source status **SOURCE_BLOCKED**.
URL: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38040421803
Workflow head SHA: `70a7c3a8fccde02e78d2b993e84c0c408e35a7b7`; workflow `.github/workflows/hype-buyback-source-gate-v01.yml`.
Job ID: `114179387132`.
Artifact ID: `11665551811` (expires 2026-11-09), immutable archive SHA256 `471b224ce8452373fec1761a5d7a1c23c327697770f5ccc55d52cfaed1838ee6`.
Three synthetic integrity regressions PASS, no external Python dependencies.
All HTTP queries unauthenticated public `POST https://api.hyperliquid.xyz/info`, no private account or credentials, no exchange mutation, no S3 transfer, zero capital, zero outcome price-response tests.

Source results 2026-10-10 09:10 UTC:
1. `spotMeta`: HTTP 200, valid HYPE(150)/USDC(0), canonical spot coin `@107`, raw bytes 136601; SHA256 `a84545ef4addc99185c5124f216902af6375ea43e8c64637bb546e3738863fc5`. NB universe zero-based array position 105 is NOT the spot name @107.
2. `userFillsByTime` with official AF, 24h window, aggregateByTime=false: HTTP 422, body "Failed to deserialize the JSON body into the target type". Error-body SHA256 `6448c95b4fb0147552cb0c95b53f9b5e5ff810da3c115d9e61c7c49430894a31`. Because recent query failed, old 90-day query not executed; DO NOT equate failure with zero AF buys.
3. Frozen transport-only A `userFillsByTime` minimal 1-hour body: HTTP 422, same error.
4. Frozen transport-only B `userFills` minimal body: HTTP 422, same error.
5. Frozen transport-only C public market `recentTrades @107`: HTTP 200, count 10, all 10 rows carried a buyer/seller `users` pair; exact `users[0] == AF`: 0/10. Raw SHA256 `8e788a2f4f7a8b4c64a1437acc8438f228b7a8cf8dfb3107e7ada46fe853d95b`. **10 recent market trades are not a representative sample**, and absence of AF in 10 trades is not absence of AF buybacks.
6. The point-in-time observed/ingested timestamps in each preserved response are NOT historical block-publication latency. Historical participant identity, 90d continuous completeness, zero-gap retention and best quotes/depth missing.

Prior runs for diagnostic accountability:
- 38040251218 (`02648b2...`) official metadata PASS, AF fills HTTP failure.
- 38040291203 (`997932b...`) technical error capture exposes 422.
- 38040320526 (`b037962...`) public response body captured.
Only 38040421803 is the transport-variant canonical run. Prior CI success is **not** source pass.

## 3. Alternative data viability
Official Hyperliquid WebSocket `trades` includes `users:[buyer,seller]` and ms timestamps, so forward exact AF attribution might be possible in principle on new, continuous real-time observations; the current REST `recentTrades` only returned 10 and cannot rebuild years/days. Real-time public source identity is not proof of a complete archive, and no persistent zero-gap collector exists here.
Official archive `s3://hl-mainnet-node-data/node_fills_by_block` contains historical fills; official docs caution requester must pay transfer, so **not downloaded**. S3 requester-pays and any paid mirror are forbidden. API `userFillsByTime` limits 2,000/page and most recent 10,000 user fills even if public-account transport is fixed, preventing unqualified full-history claims.
Third-party ASXN/Dune/Strata may supply cumulative or reconstructed daily spend estimates; not upgraded to exact-fill identity or causal publication time. Third-party summaries cannot substitute for primary immutable fills/market BBO.

## 4. Economics and confounders
Even if AF continuously bids, fee-induced demand is tied to trading already happening. Buyer flow and HYPE price may be contemporaneous, an endogenous variable, without exploitable forward lead. Official base spot schedule: taker 0.070%/side (=14 bps taker/taker roundtrip); maker 0.040%/side (=8 bps two-sided), conditional on fill. Actual route must add contemporaneous bid/ask spread, latency, market impact/slippage, funding if derivative hedge, opportunity/capital cost and venue lot/depth. Never call low-tier fee discounts without eligibility.
Supply confounders: core-contributor vesting, discretionary transfers vs actual spot selling, ecosystem distributions/rewards and burns. Vesting ≠ forced immediate spot selling.

## 5. Strict scientific consequence
- Source identity: pair PASS; Assistance Fund attributable exact executions via public endpoint NOT VERIFIED.
- History: complete continuous AF buy-fill source for 90 UTC days NOT VERIFIED.
- Actual volume per hour/day: NOT CALCULATED; never substitute estimates from fees or wallet balance.
- Latency / PIT: NOT VERIFIED.
- Market-depth executable BBO histories: NOT VERIFIED.
- Discovery: NOT RUN. OOS/holdout: NOT OPENED. Forward PnL: NOT RUN.
- **Single final status at this stage: SOURCE_BLOCKED**, not INSUFFICIENT_SAMPLE (we have not proven a complete source from which to enumerate samples), not NO_EDGE, not SURVIVES.
- No economic prediction rule has been calibrated/frozen; do not pretend an outcome-tested rule exists.

## 6. Conditions to legitimately reopen via new source-first gate
A distinct no-cost verifiable PRIMARY archive or complete continuously retained public `trades` stream with `users`, HYPE spot identity, exact event/block timestamps, first-seen wall clock + latency, dedupe `(block_time,coin,tid)`, source gaps detectable and durable receipts, for >=90 UTC days/ >=60 active days. Then prove matched contemporaneous HYPE/USDC BBO and fee-route capital minima. ONLY THEN commit a single measurable primary pre-outcome strategy rule, thresholds, horizons, costs, null/control, BTC benchmark, sample/power and protected windows BEFORE untouched market price outcomes. If source never qualifies, preserve this closeout and stop; no parameter rescue.
