# RW-HL-EXITFLOW-001 — ECONOMIC MECHANISM / SOURCE-ONLY AUDIT (2026-10-09)

**State: PROSPECTIVE SOURCE POSSIBLE / HISTORICAL OPEN INTEREST NOT FREE VIA VERIFIED OFFICIAL ROUTE / NO EDGE VERDICT.**
Trading authority: NONE. No orders, accounts, wallets, exchange mutation, purchases, Render or main merge.

## Original idea and scientific interpretation
Primary source: Kris Longmore (Robot Wealth), `Hyperliquid Carry Looks Trendy` (2025-09-14):
https://edgealchemy.robotwealth.com/p/hyperliquid-carry-looks-trendy

The article compares broad carry factors on Hyperliquid vs Binance. In the examples, Binance carry tends toward funding plus price moves favorable to the funding-ranked trade, but extreme "shorts pay longs" Hyperliquid signals frequently coincide with **continued declines**, meaning going LONG merely to collect negative funding can lose more on mark-to-market than the funding earned.
The author hypothesizes *informed / economically motivated selling* including possibly holders unwilling or unable to sell spot, and proposes watching newly listed perps, growing open interest and falling price. He explicitly warns about squeezes and calls most of these trades possible lines of inquiry, not ready-to-deploy edge.
**Do not claim verified insiders or proven manipulation**: OI records both sides of every opened contract; negative funding supports a perp discount, not seller identity.
Attribution is to the published original written article, not an end-to-end review of the full YouTube channel.

## Distinctness vs existing Crypto Lab freezes
1. Generic postlaunch SHORT / LONG BTC is already frozen in `PERP-LAUNCH-POSTLAUNCH-SHORT-001` (83 2023 launches; `INSUFFICIENT_DISCOVERY_SAMPLE`, zero analyzable complete pairs due to source transport). Cannot call new-listing shorts a new hypothesis.
2. `PERP-LAUNCH-BASIS-CONVERGENCE-001` failed net 2023 Discovery on 83 events; same basis dislocation may not be relaunched with a new name.
3. `PERP-LAUNCH-IMPULSE-REVERSION-001` already opened a 15-minute post-listing token-vs-BTC impulse condition; no cosmetic inversion.
4. `DCV-001` already assessed generic funding x OI x realized volatility and failed 2021–2023 Discovery; its 2024/2025/2026 protected outcomes remain untouched.
5. `FUNDING-DISPERSION-DN-001` crossvenue funding source was blocked; crossvenue carry by itself is NOT novel.
6. Incrementally distinct candidate is **VENUE-CONDITIONED observed OI growth and funding sign** on Hyperliquid PLUS verified official chronological listing identity; a causal contemporaneous matching comparator is necessary before any economics. The original author did not provide frozen exact math.

## Actual no-cost source result
[Official G1 source run #37938587198](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37938587198):
- Public Hyperliquid `metaAndAssetCtxs` successfully retrieved **178 simultaneously valid** market contexts twice, 75 sec apart on 2026-10-09 13:41 and 13:42 UTC.
- Each observation contains OI, current mark, current funding, 24h notional volume where present, and aligned market IDs; the raw receipts have distinct SHA256.
- Public `fundingHistory` on BTC for the FIRST 24h of 2024 returned 24 causal hourly rate records. This verifies that *historical funding* can be queried for that narrow window, NOT that all 2023–2024 assets have funding archive.
- 14 synthetic tests passed, no economic future data loaded, no profitable/nonprofitable signal tested.
- [Immutable source artifact](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37938587198/artifacts/11620221130).
- Official historical asset contexts/OI: `s3://hyperliquid-archive/asset_ctxs/YYYYMMDD.csv.lz4`. This is **requester-pays**, described as possibly incomplete and uploaded monthly. No AWS or paid provider queried. https://hyperliquid.gitbook.io/hyperliquid-docs/historical-data
- Third-party OI history may be displayed on Dune, Pinax or other dashboards, but *no free, deterministic, downloadable, source-timestamp-audited full corpus* has been established. Therefore no canonical 2023/24 historical OI study authorized.
- `metaAndAssetCtxs` current market universe does not certify actual first listing T0; first seen in collector is only bounded by observation cadence.

## Hard economic feasibility floor — not a trade authorization
Official fee docs (at the time of research): https://hyperliquid.gitbook.io/hyperliquid-docs/trading/fees
- Standard base perps taker **0.045% per fill = 4.5bps**, simple entry+exit **9bps** fees only.
- Standard base maker **0.015% per fill = 1.5bps**, idealized roundtrip **3bps** fees only (unrealistic 100% passive fill upper bound; maker adverse selection, queue and misses still count).
- HIP-3, deployer, growth-mode, volume-tier, referral and collateral conditions can materially affect actual fees and routing; do NOT assert these retail base figures are the user's account fees.
Official funding docs: https://hyperliquid.gitbook.io/hyperliquid-docs/trading/funding
- Hyperliquid funding settles **hourly**.
- When funding is **negative**, *shorts pay longs*. A "sell-pressure" SHORT pays funding rather than collecting it. This is a true headwind (and highly adverse in a squeeze).
- Illustrative hypothetical 24h SHORT with funding -0.01% each hour (1bp/hr): short funding cost 24bps plus 9bps base taker entry/exit = **33bps** hurdle BEFORE spread, slippage, impact, BTC hedge risk if any and liquidation/squeeze losses.
- The illustration is **not an observed market average or a proposed trigger**. Profits need realized drop significantly beyond adverse financing and realistic fills/capacity. No post-outcome cost rescue.

## Next authorized source-only operations
- Verify durable prospective OI capture on an isolated research branch, initial 3 current-universe snapshots 60sec apart. Commit SHA-linked immutable records to branch; no predictions or PnL.
- Design robust source continuity monitoring before event formation: exact universe identity, delisted/renamed assets, timestamps, signed funding rate, notional OI unit, mark/oracle basis, missed bars/restarts, and audit hashes.
- To study actual "new listing" regime, obtain verified event T0 from venue notifications or the exchange's canonical listing event, NOT "first appearance" of an unscheduled collector.
- To promote a candidate, require an independent, fully pre-frozen **economics** hypothesis (thresholds, sample floor, comparator, executable fills, funding accrual, spread, slippage, capacity, stop/squeeze risk, OOS); none exists yet.
- If no free historical OI with trustworthy point-in-time provenance emerges, classify historical 2023/24 thesis `HISTORICAL_OI_SOURCE_BLOCKED_NO_SPEND` and use only new forward observations legitimately sampled before outcomes.

No third-party sign-in requested, no paid S3, no trading, no exchange mutations, no account reads. Historical negative funding, current OI and future prices must never be mixed into a backfilled hypothetical strategy.
