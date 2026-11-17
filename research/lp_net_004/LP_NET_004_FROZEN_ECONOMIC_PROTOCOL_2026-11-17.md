# LP-NET-004 — Pre-registered L2 forensic liquidity economics gate (17 Nov 2026)

**Authority:** research only. No wallets, transactions, credentials, purchases, paid feeds, deployment, merges or capital. This investigation does not resurrect LICP-001 or promote the retrospective LP-NET-002 NFTs as a 2026 signal. **Nine fixed Uniswap v3 stablecoin pools** on Base, Arbitrum and OP Mainnet are frozen in `FROZEN_L2_CANDIDATE_UNIVERSE_2026-11-17.json` *before* any new automated API snapshot.

## Main question
Does an L2 reduce *confirmed, total* entry/exit/maintenance costs enough for a pre-defined concentrated-LP policy to outperform identical-inventory HODL and conservative USD cash on a 7-/30-day prospective horizon, after all execution costs, protocol fees, LVR, depeg and bad states?

## Two distinct data levels

### SOURCE LEVEL — can run now
1. Per frozen pool, record GeckoTerminal network/pool 24h volume and reserve with raw response SHA-256/time; cross-check DexScreener pair address, chain, h24 volume and liquidity. Denominators/24h windows aren't guaranteed identical; allow up to 35% discrepancy but NEVER treat agreement as executable return.
2. Query **Ethereum L2 mainnet** native public RPC for chainId, pool `token0()`, `token1()`, `fee()`, `tickSpacing()`, `slot0()`, `liquidity()` and `eth_gasPrice`. These verify Uniswap v3 state **at observed block**. `liquidity()` is active in-range raw liquidity L (unitless), **not TVL in USD** and not an LP's position fraction. No automatic conversion to LP yield.
3. Uniswap governance executed 2026-03-06 expansion to Base, Arbitrum and OP Mainnet and tier-wise adapter for v3 protocol fees (https://vote.uniswapfoundation.org/proposals/94). Docs at https://developers.uniswap.org/docs/protocols/protocol-fee/concepts/fees show v3 nominal 1bp -> LP 0.75bp, nominal 5bp -> LP 3.75bp under 25% protocol cut. **Read `slot0.feeProtocol` per pool; nibble 4 implies 25% cut per direction, nibble 0 implies none.** A v3 pool must have `feeProtocol` checked, not assumed from a web page.
4. Gas observation: `eth_gasPrice` is real network base+priority per gas unit; pre-registered 250,000 mint + 200,000 exit = 450,000 gas **scenario** for V3 NFT operations, with 3x stress. L1-data posting fee and real gasUsed depend on chain, calldata and execution path; unproven => **not total executable cost**. A hypothetical pool-fee revenue calculation from 24h volume is total pool income, not any user's share.
5. Must verify pair token addresses are credible stablecoin tokens and token decimals; canonical USDC vs bridged/USDT0 is a meaningful distinct risk. For candidate discovery, search index supplied addresses treated as hypotheses, not authoritative contract identity.
6. Initial screen: h24 volume ≥ $100k, reserves ≥ $500k, two-source volume/liquidity within 35%; onchain chain/fee/tokens and current protocol cut verified; no reported token depeg outside $0.995–$1.005. If one element missing -> SOURCE_BLOCKED/WATCH, not GO. Transparent non-cherry-picked list includes failures.

### ECONOMIC GATE — cannot pass from T0 alone
Frozen notional {1000,5000,20000} USD and {7,30} days. Fee revenue forecast must be based on **point-in-time active range position L and realized swap distribution across ticks/directions**, protocol fee tier, time-in-range, LVR and gas used with L1 fee. Compare same-inventory HODL and idle USDC/USD cash. Use 30+ days prospectively collected tick/liquidity/swap/fee-growth events and immutable pre-selection/exits; ensure approp. feeGrowthInside and collected-amount accounting on a no-tx shadow ledger. A realized pool-level fee approximation does **not** meet this gate. Ignore advertised APR, yield farming incentives unless actually captured, and any strategy chosen after outcomes. Estimate fees under risk scenarios only, mark them assumptions.
Only if independent forward, after ALL costs, positive downside-conscious incremental edge, real fillability and meaningful capital capacity may any separate small-capital live pilot be proposed for **new user approval**. This PR never transacts.

## What counts as useful failure
- Missing pool on one indexer or RPC ≠ empty pool, ≠ NO_EDGE.
- Source with <$500k or <$100k volume => fails current universe screen; no retrospective drop.
- `feeProtocol`, active tick, price/gas/L1 posting fees unavailable => no economic GO regardless of technical CI PASS.
- One screenshot or 24h volume spike ≠ repeatable 30-day yield.
- New fees and protocol governance may change after snapshot.

## Pinned evidence
Repo parent: LP-NET-003 PR #361; on Ethereum mainnet prior empirical reconstruction showed two small historical positions were negative relative to HODL after gas under full-tx scenario; single $210k, ~742-day positive historical LP outcome was retroactively chosen and fails a frozen $0.995 DAI entry screen. **None are L2 economics.**
