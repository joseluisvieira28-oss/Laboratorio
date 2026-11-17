# LP-NET-004 — Multichain L2 stablecoin LP forensic economic closeout
**As of 2026-11-17 UTC.** READ ONLY: 0 CHF spent; 0 orders, 0 wallets, no merge/deployment. All nine candidates frozen before external API snapshots.

## Direct independent evidence
- Authoritative first capture: [GH Actions run 44180139682](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/44180139682), artifact **14372980099**, original `l2_frozen_pools_snapshot.json` SHA-256 `8c28d45226600e65a63a8bdd42b6155c77f83e5392b9ea49cd68fe13bd606f7b`. Captured 2026-11-17T21:28:29–21:28:50 UTC.
- Confirmatory new-time source + frozen-T0 per-position model: [GH Actions run 44181037754](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/44181037754), artifact **14371173814**; **18/18 offline scientific guard tests PASS**. Contains a new 21:33 UTC source snapshot and an analysis using **unchanged original 21:28 UTC Arbitrum T0**. Do not replace first T0 based on later markets.
- GeckoTerminal and DexScreener raw response hashes and observations recorded separately; Ethereum v3 `slot0()`, `liquidity()`, `fee()`, `token0()`, `token1()`, `tickSpacing()`, token `decimals()`, and `eth_gasPrice` directly read via public RPC; observed RPC `eth_chainId` = 8453 (Base), 42161 (Arbitrum), 10 (OP). Public RPC endpoints `https://mainnet.base.org`, `https://arb1.arbitrum.io/rpc`, `https://mainnet.optimism.io`.
- For all 9 Uniswap v3 pool contracts, current `slot0.feeProtocol` was **0x44**, so each token-direction protocol share was 1/4 of total swap fees. LPs received 3/4 by parameter; 1bp pools = 0.75bp LP effective swap fee, 5bp = 3.75bp. Governance [Uniswap protocol fee expansion](https://vote.uniswapfoundation.org/proposals/94) executed March 2026. **No assumption that nominal 1bp swap fee wholly belongs to LPs.**
- IMPORTANT: initial multiple `eth_call(...,"latest")` per pool was a near-time snapshot over a ~21s window, NOT an atomic same-block state; current `active_liquidity_raw_L` is in V3 liquidity units, not a cash-value TVL. Source estimates and scenarios should remain tagged `T0_NEAR_TIME_NOT_ATOMIC_BLOCK` until a block-pinned replay.

## Frozen 9-pool screen as observed
Screen predeclared: two public source agreement within 35% (when available), no token depeg outside [0.995,1.005], 24h trading ≥$100k, reported reserves ≥$500k and onchain fee/token identity. Any missing source is BLOCKED, not economic failure.

| Chain | Uniswap v3 pool | Pool address | First-snapshot 24h volume USD | First-snapshot reserves USD | First verdict |
|---|---|---|---:|---:|---|
| Base | USDT/USDC 0.01% | 0xd56da2b74ba826f19015e6b7dd9dae1903e85da1 | $85,613 | $230,133 | FAIL volume and reserve |
| Base | DAI/USDC 0.01% | 0xc18f50d6a832f12f6dcaaeee8d0c87a65b96787e | $58,993 | $7,728 | FAIL volume and reserve |
| Base | DAI/USDC 0.05% | 0x19a8b1542b807cd6a76fcbb5ff5f53c6169f36d7 | $4 | $363 | FAIL volume and reserve |
| Arbitrum | USDC/USDT 0.01% | 0xbe3ad6a5669dc0b8b12febc03608860c31e2eef6 | $2,358,890 | $833,073 | SOURCE_PASS, **WATCH_ONLY** |
| Arbitrum | DAI/USDC 0.01% | 0xf0428617433652c9dc6d1093a42adfbf30d29f74 | $11,348 | $3,996 | FAIL depeg-safety in first T0, also fails volume/TVL |
| Arbitrum | DAI/USDC 0.05% | 0xd37af656abf91c7f548fffc0133175b5e4d3d5e6 | SOURCE_BLOCKED HTTP 429 | SOURCE_BLOCKED | SOURCE_BLOCKED, **NOT economic NO_EDGE** |
| Optimism | USDC/USDT 0.01% A | 0xf1f199342687a7d78bcc16fce79fa2665ef870e1 | SOURCE_BLOCKED HTTP 429 | SOURCE_BLOCKED | SOURCE_BLOCKED in first T0 |
| Optimism | USDC/USDT 0.01% B | 0xa73c628eaf6e283e26a7b1f8001cf186aa4c0e8e | SOURCE_BLOCKED HTTP 429 | SOURCE_BLOCKED | SOURCE_BLOCKED in first T0 |
| Optimism | USDC/USDT 0.05% | 0x2926736c30ef3649f9e6b5c5918ea88871f79f2b | SOURCE_BLOCKED HTTP 429 | SOURCE_BLOCKED | SOURCE_BLOCKED in first T0 |

The **second separate 21:33 UTC capture** resolved the 429 throttles: Arbitrum DAI/USDC 0.05% volume ~$69.5/day, reserves $49,214; OP two 1bp pools volume ~$9,322/$23,374 and reserves ~$23,149/$38,718, all below frozen minima. OP 5bp had $8.79 volume and ~$1,795 reserves but its reported stablecoin USD price failed peg criterion; either way not eligible. In second capture only Arbitrum USDC/USDT 0.01% passes **SOURCE_PASS WATCH_ONLY**. This is not market-wide proof that all other pools or venues are unprofitable.
USDC used on Arbitrum pool token0 is native `0xaf88d065e77c8cc2239327c5edb3a432268e5831`, USDT token1 `0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9`; verified by RPC+both provider token addresses. Other token contract risks and transferability still must be analyzed before any live step.

## Arbitrum USDC/USDT 1bp: exact as-of T0 inputs
- 24h volume $2,358,890.3746899, provider-reported TVL $833,072.5722; DexScreener independent volume $2,360,169.96, liquidity $834,116.61. Relative disagreement approx 0.054% (volume) and 0.125% (reserve).
- True V3 `slot0.tick` 9, raw active liquidity `L=2,308,923,818,433,281`, sqrtPriceX96 `79265088968403800356309100528`; onchain token1/token0 price ~1.000932372; decimals 6/6.
- `feeProtocol=0x44`, meaning nominal swap 0.01% => 0.0075% fee for active LPs. Entire pool hypothetical **$176.9168/day** in fees based on **last 24h volume**, not individual LP income.
- `eth_gasPrice` 20,020,000 wei, ETH/USD spot $1,806.53. Frozen 450,000 gas-unit simple entry+exit scenario costs **~$0.0163 excluding additional L1 data posting fees**; this is not measured gasUsed or actual total executable mint/burn cost. The actual chain fee can be higher.

## Frozen exact Uniswap v3 capital-share scenarios (NON-EXECUTED)
We used the v3 `sqrt(P)` position liquidity formula to determine user liquidity L added at the current spot in each precommitted symmetric price range; instantaneous share `L_user/(L_active+L_user)`. Assumptions: active L remains fixed, all reported 24h volume repeats every day and every swap crosses the current tick while position stays in its band, protocol fee remains 25%, no gas growth. **Do not label result an executable APY or forecast.**

| $5,000 notional | Width about spot | Hypothetical instantaneous fee-share | Gross fees in 30d (static) | Simple annual gross extrapolation (NOT APY) |
|---|---:|---:|---:|---:|
| Range ±0.10% | 0.10% each side | 0.2164% of present L | **$11.49** | **2.795%** |
| Range ±0.25% | 0.25% each side | 0.0867% of present L | **$4.60** | **1.120%** |
| Range ±0.50% | 0.50% each side | 0.0434% of present L | **$2.30** | **0.561%** |

Nine scenarios (notionals $1k,$5k,$20k × half widths 0.10%,0.25%,0.50%) all had stationary, fee-only simple annual extrapolation **below an illustrative 4% cash hurdle**, even **before** inventory/LVR losses, rebalance costs, gas data posting, chain/bridge risk and missed periods. The 4% hurdle is a hypothetical independent comparison, **NOT an actual current account or yield offer**. Also the model is **not a mathematical guaranteed upper bound**: future active L or volume can change (some favorable, some unfavorable). No conclusion about future profitability from one snapshot alone.

## Past-only range diagnostics — not a future backtest
- Additional source: GeckoTerminal pool token-price OHLCV, 1-hour candles using `currency=token&token=base&before_timestamp=<2026-11-17T21:28:29Z>`. SHA256 `f20c8702b6637c61bc29183e5a3f201ac763e257ee4ab5ac06586fd580f8742c`; 719/720 prior hourly candles from 2026-10-18 22:00 UTC to 2026-11-17 20:00 UTC (missing hour remains unknown).
- Latest historical close 1.001032 vs T0 pool spot 1.000932; orientation approximately consistent.
- Number of historical candles whose **entire hourly low-to-high** was within T0-anchored band: ±0.10%=694/719 (96.52%), ±0.25%=704/719 (97.91%), ±0.50%=705/719 (98.05%). Possible intersection 719/719 for all, meaning some historical candles had excursions beyond the band.
- **This is not forward time-in-range, not an individual LP fee share or prospective return.** OHLCV price aggregation cannot reconstruct order-by-order tick traversals or collected feeGrowthInside. A backward test anchored to today's chosen price is a diagnostics-only exercise, with inherent hindsight.

## Decision
1. **GO SOURCE & PROSPECTIVE DESIGN ONLY for Arbitrum USDC/USDT 0.01%** (not GO capital). Eight other frozen candidates fail or are source-blocked in first T0; later repeated evidence suggests they remain economically weak at current snapshot.
2. **NO-GO economic promotion:** even the most generous of three fixed-range static fee scenarios for $5k falls below illustrative 4%/yr cash before risks. This is competition, NOT gas, dominating.
3. Do NOT build another trading bot, deposit or sell APY. Preserve raw T0 and second T1 separately; keep existing terminal negative strategies closed.
4. If continuation is justified, the next experimental gate is *fixed-tick archive event replay*: at one block anchor, read tick liquidityNet and `feeGrowthGlobal{0,1}X128`, and simulate hypothetical L in a frozen range as swap prices cross ticks over 7–30 days. Include actual L2 data fees, swap/entry costs, and mark inventory HODL vs a no-LP comparator. Require independent verification and *future* trade-free outcomes; no retroactive threshold optimization.
5. If no net OOS edge over low-risk benchmarks after costs, close this family and move research elsewhere. No live use without separate user approval.
