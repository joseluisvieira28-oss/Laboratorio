# DIGUI-007 — prospective risk / traction test (frozen protocol v0.1)

**Created:** 2026-11-17 UTC. **Risk:** NO-GO for live trading, copy trading, investment recommendations or automated order submission.

## What this job actually does
- No wallets, credentials, transactions, signing, private endpoints or funds.
- At each run, query first **two pages** of GeckoTerminal Solana newly created pools, time-stamp start and end, save original JSON and SHA-256.
- Read up to **four** detected base mints with DEX Screener token-pairs and Solana mainnet **read-only** RPC (`getAccountInfo`, `getTokenLargestAccounts`); include full raw responses and hash. Failure is preserved as `PARTIAL_DATA_UNVERIFIED`, **never** marked "safe".
- Optionally query latest **1000** finalized signatures referencing the official Pump.fun creation program as a coverage *diagnostic* only. A signature is not proof of a newly created mint; 1000-page truncation and public RPC rate-limits can occur.
- Follow a deterministic subset of exactly two mints selected at each run by SHA-256 of the mint only, tracking each for up to 36 hours (max 40 active), with fresh pool-price and liquidity observations and explicit censoring on source failures.\n- Archive one `snapshot.json` and `snapshot.sha256` per GitHub Actions run. Hourly/two-hourly artifacts are **not** the full launch universe. Upload on CI failures when possible.
- Schedule runs every 2 hours only on calendar dates Nov 17–30 and Dec 1–17 (with a 2026 programmatic API shutoff), and runs **only when workflow is on default branch**, not from a draft PR. GitHub scheduled runs may be late, skipped or disabled; successful runs are counted individually. Target: >=30 elapsed calendar days of legitimate observations, not assumed from schedule config.

## Data quality and explicit limits
- GeckoTerminal `new_pools` is a discovery feed for AMM pools, NOT the entire Pump.fun creation history and excludes coins that never have a tradeable pool or age out before collection.
- Token account concentration is **not** ultimate wallet owner concentration. Program escrow, pools, bonding curves and splits can dominate it.
- A flag for active mint/freeze authority, low liquidity or large token-account concentration is a **cautionary measurement**, not evidence of intentional fraud.
- No cluster reconstruction, graph-based wallet linkage or 'smart money' labels are provided by this collector. Those require independent point-in-time history, provenance and backfills, absent here.
- An absent token, HTTP 429, missing price or bad RPC response must remain missing/unknown.
- Price discovery, transaction cost and guaranteed exit liquidity are **not** established by a historical price/FDV or max-return label.

## Explicit prospective validation (for subsequent independent settlement)
1. Freeze inclusion: all observations that were actually archived, with coverage, run gaps, mint/pair deduplication and source availability; preserve every observation, including failing/liquidityless cases. Do not silently label missing price as zero or exclude dead tokens without a sensitivity analysis.
2. After **>=24h** and **>=7 days**, compute separate observed outcomes when the pair can be matched and repriced from an independent source; keep censored/unobserved separately.
3. Measure abrupt liquidity declines (e.g. >80% across 24h), mint/freeze changes and large holder account movements separately. Call them *observable risk events*, **not proven scams/rug pulls**, absent chain-transaction verification.
4. Compare a frozen base ranker (price/volume/liquidity at capture) against risk-enriched one. Select thresholds on a separate calibration period; reserve a later **independent** period of >=30 days for test if coverage allows. Do not reuse June DIGUI-006 four-day test as independent validation.
5. Economic test only **after** as-of validation: costed marketable entry at first quote **after** signal + realistic random/95th-percentile delay; model fees, priority costs, slippage, actual exit quotes/depth and transaction failures. Compare against no-trade, randomized liquidity/age-matched entries and a simple price/volume-only baseline. Tokens whose exits cannot be executed count as losses/censored adversarially, not 2x winners.
6. Gate: statistical gain must persist across non-overlapping days and market regimes AND lower tail risk / executable expectancy must remain positive under conservative execution assumptions. Otherwise **NO-GO**.

## Predeclared blocking reasons
- Snapshot unavailable or API coverage not broad enough.
- Field-time provenance or holder identity unverified.
- No forward comparison cohort, no independent safety outcomes, no marketable exit.
- More than one of the above = scientific *INCONCLUSIVE*, economic **NO-GO**.

## Source APIs
- Official Pump.fun program documentation: https://github.com/pump-fun/pump-public-docs/blob/main/docs/PUMP_PROGRAM_README.md
- Solana RPC methods: https://solana.com/docs/rpc/http
- GeckoTerminal new pools: https://api.geckoterminal.com/docs/index.html
- DexScreener API: https://docs.dexscreener.com/api/reference

**No promise of profit; no automatic trades.**
